"""Business logic for analyses: run the NLP pipeline, persist results, serialise, correct, delete."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models import (
    Analysis,
    CandidateSkill,
    Evidence,
    JobDescription,
    LearningRoadmap,
    LearningTask,
    RequiredSkill,
    Resume,
    SkillMatch,
    User,
    UserFeedback,
)
from app.nlp.explanations.explainer import CLASS_LABELS
from app.nlp.extraction.document_extractor import clean_pasted_text
from app.nlp.extraction.sections import summarise_sections
from app.nlp.pipeline import AnalysisInputError, AnalysisOptions, run_analysis
from app.nlp.recommendations.roadmap import build_roadmap, progress_summary
from app.nlp.skill_extraction.taxonomy import get_taxonomy
from app.nlp.skill_gap.scoring import compute_coverage
from app.repositories import analysis_repo
from app.schemas.analysis import AnalysisCreate

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analysis")

DISCLAIMER = (
    "SkillGap-NLP is a career-development aid, not a hiring tool. Coverage reflects what the resume text shows, "
    "not the candidate's true ability. Semantic similarity is never treated as proof of proficiency."
)


# --------------------------------------------------------------------------- create

def create_analysis(db: Session, user: User, payload: AnalysisCreate) -> Analysis:
    settings = get_settings()

    # 1. Resolve resume text (uploaded resume and/or edited/pasted text)
    resume: Resume | None = None
    if payload.resume_id is not None:
        resume = analysis_repo.get_owned_resume(db, user.id, payload.resume_id)
    if payload.resume_text and payload.resume_text.strip():
        text = clean_pasted_text(payload.resume_text)
        if resume is not None:
            resume.text, resume.char_count = text, len(text)  # user edited the extracted text
            resume.sections = summarise_sections(text)
        else:
            resume = Resume(user_id=user.id, file_type="pasted", text=text, char_count=len(text), sections=summarise_sections(text))
            db.add(resume)
    assert resume is not None  # guaranteed by schema validation
    if len(resume.text) > settings.max_text_chars:
        raise AppError(413, "text_too_long", f"Resume text exceeds {settings.max_text_chars} characters.")

    job_text = clean_pasted_text(payload.job_description)
    job = JobDescription(user_id=user.id, title=payload.job_title, text=job_text)
    db.add(job)

    # 2. Run the NLP pipeline in a worker thread with a timeout
    options = AnalysisOptions(
        mode=payload.mode,
        target_role=payload.target_role or payload.job_title,
        must_have=payload.must_have_skills,
        nice_to_have=payload.nice_to_have_skills,
        custom_weights=payload.custom_weights,
        equal_weights=payload.equal_weights,
        count_strong_semantic=payload.count_strong_semantic,
    )
    future = _executor.submit(run_analysis, resume.text, job_text, options)
    try:
        result = future.result(timeout=settings.analysis_timeout_seconds)
    except FutureTimeout as exc:
        db.rollback()
        raise AppError(504, "analysis_timeout", "The analysis took too long. Try a shorter document or the TF-IDF mode.") from exc
    except AnalysisInputError as exc:
        db.rollback()
        raise AppError(422, exc.code, exc.message) from exc

    db.flush()  # assign resume/job ids
    analysis = _persist(db, user, resume, job, payload, options, result)
    db.commit()
    db.expire_all()  # reload relationships from the database
    logger.info("analysis %s created for user %s (%s requirements, %.0f ms)", analysis.id, user.id,
                len(result["requirements"]), result["processing_ms"])
    return analysis_repo.get_owned_analysis(db, user.id, analysis.id)


def _persist(db: Session, user: User, resume: Resume, job: JobDescription, payload: AnalysisCreate,
             options: AnalysisOptions, result: dict) -> Analysis:
    cov = result["coverage"]
    analysis = Analysis(
        user_id=user.id, resume_id=resume.id, job_id=job.id,
        job_title=payload.job_title, target_role=payload.target_role, mode=payload.mode,
        coverage_score=cov["coverage_score"] or 0.0,
        must_have_coverage=cov["must_have_coverage"], nice_to_have_coverage=cov["nice_to_have_coverage"],
        doc_similarity_tfidf=result["document_similarity"]["tfidf"],
        doc_similarity_semantic=result["document_similarity"]["semantic"],
        options={
            "must_have_skills": payload.must_have_skills, "nice_to_have_skills": payload.nice_to_have_skills,
            "custom_weights": payload.custom_weights, "equal_weights": payload.equal_weights,
            "count_strong_semantic": payload.count_strong_semantic,
        },
        model_info=result["model_info"],
        extras={
            "model_comparison": result["model_comparison"],
            "warnings": result["warnings"],
            "unrecognized_job_terms": result["unrecognized_job_terms"],
            "contact_fields_detected": result["contact_fields_detected"],
            "processing_ms": result["processing_ms"],
            "document_similarity_note": result["document_similarity"]["note"],
        },
    )
    db.add(analysis)
    db.flush()

    for cs in result["candidate_skills"]:
        db.add(CandidateSkill(analysis_id=analysis.id, canonical=cs["canonical"], category=cs["category"],
                              strength=cs["strength"], mention_count=cs["mention_count"]))

    for r in result["requirements"]:
        req = RequiredSkill(analysis_id=analysis.id, canonical=r["canonical"], category=r["category"],
                            importance=r["importance"], weight=r["weight"], requirement_text=r["requirement_text"],
                            source=r["requirement_source"])
        db.add(req)
        ev_row = None
        ev = r.get("evidence")
        if ev:
            ev_row = Evidence(analysis_id=analysis.id, canonical=r["canonical"], sentence=ev["text"], section=ev["section"],
                              start=ev["start"], end=ev["end"], match_start=ev["match_start"], match_end=ev["match_end"],
                              matched_text=ev["matched_text"], kind=ev["kind"], strength=ev["strength"])
            db.add(ev_row)
        db.flush()
        db.add(SkillMatch(
            analysis_id=analysis.id, required_skill_id=req.id, evidence_id=ev_row.id if ev_row else None,
            classification=r["classification"], exact_match=r["exact_match"], similarity=r["similarity"],
            tfidf_similarity=r["tfidf_similarity"], semantic_similarity=r["semantic_similarity"],
            similarity_backend=r["similarity_backend"], related_skills=r["related_skills_found"],
            method=(r["method"] or "")[:300], explanation=r["explanation"], next_action=r["next_action"],
            uncertainty=r["uncertainty"],
        ))

    roadmap = LearningRoadmap(analysis_id=analysis.id, target_role=options.target_role)
    db.add(roadmap)
    db.flush()
    for t in result["roadmap"]:
        db.add(_task_row(roadmap.id, t))
    db.flush()
    return analysis


def _task_row(roadmap_id: int, t: dict, status: str = "not_started", checklist_done: list | None = None) -> LearningTask:
    return LearningTask(
        roadmap_id=roadmap_id, skill=t["skill"], category=t["category"], importance=t["importance"],
        gap_type=t["gap_type"], priority=t["priority"], order=t["order"], level=t["level"], reason=t["reason"],
        prerequisites=t["prerequisites"], project=t["project"], estimated_effort=t["estimated_effort"],
        checklist=t["checklist"], checklist_done=checklist_done or [], resources=t["resources"],
        resources_note=t["resources_note"], status=status,
    )


# --------------------------------------------------------------------------- serialise

def match_to_dict(m: SkillMatch) -> dict:
    req = m.required_skill
    ev = m.evidence
    eff = m.user_classification or m.classification
    return {
        "match_id": m.id,
        "required_skill": req.canonical,
        "canonical": req.canonical,
        "category": req.category,
        "importance": req.importance,
        "weight": req.weight,
        "requirement_text": req.requirement_text,
        "requirement_source": req.source,
        "exact_match": m.exact_match,
        "classification": m.classification,
        "user_classification": m.user_classification,
        "effective_classification": eff,
        "classification_label": CLASS_LABELS.get(eff, eff),
        "similarity": m.similarity,
        "tfidf_similarity": m.tfidf_similarity,
        "semantic_similarity": m.semantic_similarity,
        "similarity_backend": m.similarity_backend,
        "related_skills_found": m.related_skills,
        "method": m.method,
        "explanation": m.explanation,
        "next_action": m.next_action,
        "uncertainty": m.uncertainty,
        "evidence": None if ev is None else {
            "text": ev.sentence, "section": ev.section, "start": ev.start, "end": ev.end,
            "match_start": ev.match_start, "match_end": ev.match_end, "matched_text": ev.matched_text,
            "kind": ev.kind, "strength": ev.strength,
        },
    }


def _coverage_from_rows(analysis: Analysis) -> dict:
    reqs = [match_to_dict(m) for m in analysis.matches]
    return compute_coverage(reqs, count_strong_semantic=bool(analysis.options.get("count_strong_semantic")))


def serialize_analysis(analysis: Analysis) -> dict:
    requirements = [match_to_dict(m) for m in analysis.matches]
    coverage = compute_coverage(requirements, count_strong_semantic=bool(analysis.options.get("count_strong_semantic")))
    tasks = [task_to_dict(t) for t in analysis.roadmap.tasks] if analysis.roadmap else []
    return {
        "id": analysis.id,
        "created_at": analysis.created_at,
        "job_title": analysis.job_title,
        "target_role": analysis.target_role,
        "mode": analysis.mode,
        "coverage": coverage,
        "document_similarity": {
            "tfidf": analysis.doc_similarity_tfidf,
            "semantic": analysis.doc_similarity_semantic,
            "note": analysis.extras.get("document_similarity_note"),
        },
        "model_info": {**analysis.model_info, "processing_ms": analysis.extras.get("processing_ms")},
        "requirements": requirements,
        "candidate_skills": [
            {"canonical": c.canonical, "category": c.category, "strength": c.strength, "mention_count": c.mention_count}
            for c in sorted(analysis.candidate_skills, key=lambda c: (c.category, c.canonical))
        ],
        "model_comparison": analysis.extras.get("model_comparison", []),
        "resume_text": analysis.resume.text if analysis.resume else None,
        "resume_sections": analysis.resume.sections if analysis.resume else [],
        "job_description": analysis.job.text if analysis.job else None,
        "warnings": analysis.extras.get("warnings", []),
        "unrecognized_job_terms": analysis.extras.get("unrecognized_job_terms", []),
        "roadmap_progress": progress_summary(tasks) if analysis.roadmap else None,
        "disclaimer": DISCLAIMER,
    }


def summarize(analysis: Analysis) -> dict:
    effs = [m.user_classification or m.classification for m in analysis.matches]
    return {
        "id": analysis.id,
        "created_at": analysis.created_at,
        "job_title": analysis.job_title,
        "target_role": analysis.target_role,
        "mode": analysis.mode,
        "coverage_score": analysis.coverage_score,
        "must_have_coverage": analysis.must_have_coverage,
        "nice_to_have_coverage": analysis.nice_to_have_coverage,
        "requirement_count": len(effs),
        "direct_count": sum(e == "direct_match" for e in effs),
        "missing_count": sum(e == "missing" for e in effs),
        "similarity_backend": analysis.model_info.get("similarity_backend"),
        "fallback_used": bool(analysis.model_info.get("fallback_used")),
    }


def task_to_dict(t: LearningTask) -> dict:
    return {
        "id": t.id, "skill": t.skill, "category": t.category, "importance": t.importance, "gap_type": t.gap_type,
        "priority": t.priority, "order": t.order, "level": t.level, "reason": t.reason,
        "prerequisites": t.prerequisites, "project": t.project, "estimated_effort": t.estimated_effort,
        "checklist": t.checklist, "checklist_done": t.checklist_done, "resources": t.resources,
        "resources_note": t.resources_note, "status": t.status, "updated_at": t.updated_at,
    }


# --------------------------------------------------------------------------- corrections

def correct_match(db: Session, user: User, analysis_id: int, match_id: int, corrected: str | None, comment: str | None) -> dict:
    analysis = analysis_repo.get_owned_analysis(db, user.id, analysis_id)
    match = next((m for m in analysis.matches if m.id == match_id), None)
    if match is None:
        raise AppError(404, "not_found", "Skill match not found in this analysis.")
    match.user_classification = None if corrected == match.classification else corrected
    db.add(UserFeedback(user_id=user.id, analysis_id=analysis.id, match_id=match.id, skill=match.required_skill.canonical,
                        original_classification=match.classification, corrected_classification=corrected, comment=comment))
    cov = _coverage_from_rows(analysis)
    analysis.coverage_score = cov["coverage_score"] or 0.0
    analysis.must_have_coverage = cov["must_have_coverage"]
    analysis.nice_to_have_coverage = cov["nice_to_have_coverage"]
    sync_roadmap(db, analysis)
    db.commit()
    db.expire_all()
    return serialize_analysis(analysis_repo.get_owned_analysis(db, user.id, analysis_id))


def sync_roadmap(db: Session, analysis: Analysis) -> None:
    """Rebuild roadmap tasks after corrections, preserving progress for skills that remain."""
    if analysis.roadmap is None:
        return
    previous = {t.skill: t for t in analysis.roadmap.tasks}
    reqs = [match_to_dict(m) for m in analysis.matches]
    candidate = {c.canonical for c in analysis.candidate_skills}
    new_tasks = build_roadmap(reqs, candidate, get_taxonomy(), analysis.roadmap.target_role)
    for t in list(analysis.roadmap.tasks):
        db.delete(t)
    db.flush()
    for t in new_tasks:
        old = previous.get(t["skill"])
        db.add(_task_row(analysis.roadmap.id, t, status=old.status if old else "not_started",
                         checklist_done=old.checklist_done if old else []))
    db.flush()


# --------------------------------------------------------------------------- delete

def delete_analysis(db: Session, user: User, analysis_id: int) -> None:
    analysis = analysis_repo.get_owned_analysis(db, user.id, analysis_id, full=False)
    resume_id, job_id = analysis.resume_id, analysis.job_id
    db.delete(analysis)
    db.flush()
    paths = analysis_repo.delete_if_unreferenced(db, user.id, resume_id, job_id)
    db.commit()
    remove_files(paths)


def remove_files(paths: list[str]) -> None:
    upload_root = Path(get_settings().upload_dir).resolve()
    for p in paths:
        path = Path(p).resolve()
        if upload_root in path.parents and path.exists():  # never delete outside the upload dir
            path.unlink()
