"""End-to-end analysis pipeline (pure Python, no web or database code).

    resume text ─┐
                 ├─ sections + sentences ─ skill extraction ─┐
    job text ────┴─ requirement extraction (+ importance) ───┤
                                                             ├─ gap analysis (keyword / TF-IDF / semantic)
                                                             ├─ coverage score (explicit formula)
                                                             ├─ document similarity (reported separately)
                                                             └─ learning roadmap
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from app.nlp.config import NLPConfig, get_nlp_config
from app.nlp.embeddings.sentence_encoder import Encoder, get_encoder
from app.nlp.extraction.sections import detect_sections, extract_contact_presence, split_sentences, summarise_sections
from app.nlp.recommendations.roadmap import build_roadmap
from app.nlp.skill_extraction.extractor import extract_candidate_skills, extract_required_skills, unrecognized_terms
from app.nlp.skill_extraction.taxonomy import Taxonomy, get_taxonomy
from app.nlp.skill_gap.analyzer import analyze_gaps
from app.nlp.skill_gap.scoring import compute_coverage
from app.nlp.tfidf.tfidf_matcher import document_similarity


class AnalysisInputError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class AnalysisOptions:
    mode: str = "semantic"
    target_role: str | None = None
    must_have: list[str] = field(default_factory=list)
    nice_to_have: list[str] = field(default_factory=list)
    custom_weights: dict[str, float] = field(default_factory=dict)
    equal_weights: bool = False
    count_strong_semantic: bool = False


def _semantic_doc_similarity(encoder: Encoder, a_sents: list[str], b_sents: list[str]) -> float | None:
    """Mean-pooled sentence embeddings -> cosine. None if the model is unavailable."""
    if not getattr(encoder, "available", False) or not a_sents or not b_sents:
        return None
    try:
        a = encoder.encode(a_sents).mean(axis=0)
        b = encoder.encode(b_sents).mean(axis=0)
    except Exception:
        return None
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return round(float(np.dot(a, b) / denom), 4) if denom else None


def run_analysis(
    resume_text: str,
    job_text: str,
    options: AnalysisOptions | None = None,
    taxonomy: Taxonomy | None = None,
    encoder: Encoder | None = None,
    config: NLPConfig | None = None,
) -> dict:
    options = options or AnalysisOptions()
    taxonomy = taxonomy or get_taxonomy()
    config = config or get_nlp_config()
    encoder = encoder or get_encoder()
    started = time.perf_counter()

    if len(resume_text.strip()) < 30:
        raise AnalysisInputError("resume_too_short", "The resume text is empty or too short to analyse.")
    if len(job_text.strip()) < 30:
        raise AnalysisInputError("job_too_short", "The job description is empty or too short to analyse.")

    sections = detect_sections(resume_text)
    resume_sentences = split_sentences(resume_text, sections)
    candidate = extract_candidate_skills(resume_text, taxonomy)

    requirements, warnings = extract_required_skills(
        job_text, taxonomy,
        must_have_weight=config.must_have_weight,
        nice_to_have_weight=config.nice_to_have_weight,
        must_have_overrides=options.must_have,
        nice_to_have_overrides=options.nice_to_have,
        custom_weights=options.custom_weights,
        equal_weights=options.equal_weights,
    )
    if not requirements:
        warnings.append(
            "No skills from the taxonomy were found in the job description. Add required skills manually "
            "in the analysis settings or extend data/skill_taxonomy/taxonomy.json."
        )

    gap = analyze_gaps(resume_sentences, candidate, requirements, taxonomy, mode=options.mode, encoder=encoder, config=config)
    coverage = compute_coverage(gap["requirements"], count_strong_semantic=options.count_strong_semantic)
    roadmap = build_roadmap(gap["requirements"], set(candidate), taxonomy, options.target_role)

    job_sentences = [s.text for s in split_sentences(job_text)]
    doc_sim = {
        "tfidf": round(document_similarity(resume_text, job_text), 4),
        "semantic": _semantic_doc_similarity(encoder, [s.text for s in resume_sentences if s.section != "header"], job_sentences)
        if gap["semantic_available"] else None,
        "note": "Document similarity measures overall textual/semantic overlap. It is reported separately "
                "from skill coverage and does not mean the candidate is qualified.",
    }

    required_names = {r.canonical for r in requirements}
    extra_skills = [s.to_dict() for name, s in sorted(candidate.items()) if name not in required_names]

    return {
        "requirements": gap["requirements"],
        "coverage": coverage,
        "document_similarity": doc_sim,
        "candidate_skills": [s.to_dict() for _, s in sorted(candidate.items())],
        "additional_candidate_skills": [s["canonical"] for s in extra_skills],
        "unrecognized_job_terms": unrecognized_terms(job_text, taxonomy),
        "resume_sections": summarise_sections(resume_text),
        "contact_fields_detected": extract_contact_presence(resume_text),
        "model_comparison": gap["model_comparison"],
        "model_info": {
            "mode": options.mode,
            "similarity_backend": gap["similarity_backend"],
            "semantic_available": gap["semantic_available"],
            "semantic_model": getattr(encoder, "name", None),
            "fallback_used": gap["fallback_used"],
            "fallback_reason": gap["fallback_reason"],
            "thresholds": gap["thresholds"],
            "count_strong_semantic": options.count_strong_semantic,
            "equal_weights": options.equal_weights,
            "weights": {"must_have": config.must_have_weight, "nice_to_have": config.nice_to_have_weight},
        },
        "roadmap": roadmap,
        "warnings": warnings,
        "processing_ms": round((time.perf_counter() - started) * 1000, 1),
        "disclaimer": "This is a career-development aid, not a hiring decision. Skill coverage reflects what the "
                      "resume text shows, not the candidate's true ability.",
    }
