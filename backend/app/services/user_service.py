"""Accounts, uploads, roadmap progress, dashboard statistics, export and data retention."""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models import LearningProgress, Resume, User
from app.nlp.extraction.document_extractor import ExtractionError, extract_text
from app.nlp.extraction.sections import summarise_sections
from app.nlp.recommendations.roadmap import progress_summary
from app.repositories import analysis_repo
from app.services import analysis_service

logger = logging.getLogger(__name__)

DEFAULT_PREFERENCES = {"default_mode": "semantic", "count_strong_semantic": False, "equal_weights": False}


# --------------------------------------------------------------------------- auth

def register(db: Session, email: str, full_name: str, password: str) -> User:
    if analysis_repo.get_user_by_email(db, email):
        raise AppError(409, "email_taken", "An account with this email already exists.")
    user = User(email=email, full_name=full_name, password_hash=hash_password(password), preferences=dict(DEFAULT_PREFERENCES))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = analysis_repo.get_user_by_email(db, email)
    # Same message for unknown email and wrong password (no account enumeration)
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(401, "invalid_credentials", "Incorrect email or password.")
    return user


def update_profile(db: Session, user: User, full_name: str | None, preferences: dict | None) -> User:
    if full_name:
        user.full_name = " ".join(full_name.split())
    if preferences is not None:
        user.preferences = {**DEFAULT_PREFERENCES, **(user.preferences or {}), **preferences}
    db.commit()
    db.refresh(user)
    return user


def delete_account(db: Session, user: User, password: str) -> None:
    if not verify_password(password, user.password_hash):
        raise AppError(403, "invalid_password", "Password is incorrect.")
    paths = [r.stored_path for r in user.resumes if r.stored_path]
    db.delete(user)  # cascades to resumes, jobs, analyses, roadmaps, feedback
    db.commit()
    analysis_service.remove_files(paths)
    logger.info("user account deleted")


# --------------------------------------------------------------------------- uploads

def upload_resume(db: Session, user: User, filename: str, content: bytes) -> tuple[Resume, dict]:
    settings = get_settings()
    try:
        doc = extract_text(filename, content, max_bytes=settings.max_upload_bytes)
    except ExtractionError as exc:
        status = 413 if exc.code == "file_too_large" else 422
        raise AppError(status, exc.code, exc.message) from exc
    if len(doc.text) > settings.max_text_chars:
        raise AppError(413, "text_too_long", f"Extracted text exceeds {settings.max_text_chars} characters.")

    stored_path = None
    if settings.store_uploaded_files:
        # Server-generated name only: the user's filename never touches the filesystem (no traversal)
        user_dir = Path(settings.upload_dir).resolve() / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        target = user_dir / f"{uuid.uuid4().hex}.{doc.file_type}"
        target.write_bytes(content)
        stored_path = str(target)

    safe_name = Path(filename or "resume").name[:255]
    resume = Resume(user_id=user.id, original_filename=safe_name, file_type=doc.file_type, stored_path=stored_path,
                    text=doc.text, char_count=len(doc.text), page_count=doc.page_count, sections=summarise_sections(doc.text))
    db.add(resume)
    db.commit()
    db.refresh(resume)
    logger.info("resume %s uploaded (%s, %d chars)", resume.id, doc.file_type, len(doc.text))
    return resume, {"stored_file": stored_path is not None}


# --------------------------------------------------------------------------- roadmap

def update_task(db: Session, user: User, task_id: int, status: str | None, checklist_done: list[int] | None) -> dict:
    task = analysis_repo.get_owned_task(db, user.id, task_id)
    if status and status != task.status:
        db.add(LearningProgress(task_id=task.id, from_status=task.status, to_status=status))
        task.status = status
    if checklist_done is not None:
        task.checklist_done = sorted({i for i in checklist_done if 0 <= i < len(task.checklist)})
    db.commit()
    db.refresh(task)
    siblings = [analysis_service.task_to_dict(t) for t in task.roadmap.tasks]
    return {"task": analysis_service.task_to_dict(task), "progress": progress_summary(siblings)}


def get_roadmap(db: Session, user: User, analysis_id: int) -> dict:
    analysis = analysis_repo.get_owned_analysis(db, user.id, analysis_id)
    tasks = [analysis_service.task_to_dict(t) for t in analysis.roadmap.tasks] if analysis.roadmap else []
    return {
        "analysis_id": analysis.id,
        "target_role": analysis.target_role or analysis.job_title,
        "tasks": tasks,
        "progress": progress_summary(tasks),
        "verified_coverage": analysis.coverage_score,
        "disclaimer": "Effort estimates are indicative only and do not guarantee proficiency. Resources are curated suggestions.",
    }


# --------------------------------------------------------------------------- dashboard

def dashboard(db: Session, user: User) -> dict:
    analyses = analysis_repo.all_user_analyses(db, user.id)
    missing = Counter()
    status_counts = Counter()
    for a in analyses:
        for m in a.matches:
            if (m.user_classification or m.classification) == "missing":
                missing[m.required_skill.canonical] += 1
        if a.roadmap:
            for t in a.roadmap.tasks:
                status_counts[t.status] += 1
    total_tasks = sum(status_counts.values())
    return {
        "analysis_count": len(analyses),
        "average_coverage": round(sum(a.coverage_score for a in analyses) / len(analyses), 1) if analyses else None,
        "best_coverage": max((a.coverage_score for a in analyses), default=None),
        "recent": [analysis_service.summarize(a) for a in analyses[:5]],
        "frequently_missing": [{"skill": s, "count": c} for s, c in missing.most_common(8)],
        "roadmap": {
            "total_tasks": total_tasks,
            "by_status": {s: status_counts.get(s, 0) for s in ("not_started", "learning", "practiced", "completed")},
            "completed_percent": round(100 * status_counts.get("completed", 0) / total_tasks, 1) if total_tasks else None,
        },
        "coverage_trend": [
            {"id": a.id, "date": a.created_at, "coverage": a.coverage_score, "label": a.job_title or a.target_role or f"Analysis {a.id}"}
            for a in reversed(analyses[:12])
        ],
    }


# --------------------------------------------------------------------------- export & retention

def export_user_data(db: Session, user: User) -> dict:
    analyses = analysis_repo.all_user_analyses(db, user.id)
    full = [analysis_service.serialize_analysis(analysis_repo.get_owned_analysis(db, user.id, a.id)) for a in analyses]
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "preferences": user.preferences,
                 "created_at": user.created_at.isoformat()},
        "analyses": full,
    }


def retention_days_for(user: User) -> int:
    return int((user.preferences or {}).get("retention_days") or get_settings().retention_days)


def purge_expired(db: Session) -> int:
    """Delete analyses older than each user's retention period. Returns the number deleted."""
    deleted = 0
    for user in db.scalars(select(User)).all():
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days_for(user))
        for analysis_id in analysis_repo.expired_analysis_ids(db, user.id, cutoff):
            analysis_service.delete_analysis(db, user, analysis_id)
            deleted += 1
    if deleted:
        logger.info("retention policy removed %d expired analyses", deleted)
    return deleted
