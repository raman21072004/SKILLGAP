"""Data access helpers. EVERY query on user data filters by user_id (ownership)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models import Analysis, LearningRoadmap, LearningTask, Resume, SkillMatch, User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_owned_analysis(db: Session, user_id: int, analysis_id: int, full: bool = True) -> Analysis:
    stmt = select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    if full:
        stmt = stmt.options(
            selectinload(Analysis.matches).selectinload(SkillMatch.required_skill),
            selectinload(Analysis.matches).selectinload(SkillMatch.evidence),
            selectinload(Analysis.candidate_skills),
            selectinload(Analysis.roadmap).selectinload(LearningRoadmap.tasks),
            selectinload(Analysis.resume),
            selectinload(Analysis.job),
        )
    analysis = db.scalar(stmt)
    if analysis is None:
        # Same response for "missing" and "belongs to someone else" -> no information leak
        raise NotFoundError("Analysis")
    return analysis


def get_owned_resume(db: Session, user_id: int, resume_id: int) -> Resume:
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
    if resume is None:
        raise NotFoundError("Resume")
    return resume


def get_owned_task(db: Session, user_id: int, task_id: int) -> LearningTask:
    stmt = (
        select(LearningTask)
        .join(LearningRoadmap, LearningTask.roadmap_id == LearningRoadmap.id)
        .join(Analysis, LearningRoadmap.analysis_id == Analysis.id)
        .where(LearningTask.id == task_id, Analysis.user_id == user_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise NotFoundError("Task")
    return task


def list_analyses(db: Session, user_id: int, page: int, page_size: int) -> tuple[list[Analysis], int]:
    total = db.scalar(select(func.count()).select_from(Analysis).where(Analysis.user_id == user_id)) or 0
    rows = db.scalars(
        select(Analysis)
        .where(Analysis.user_id == user_id)
        .options(selectinload(Analysis.matches))
        .order_by(Analysis.created_at.desc(), Analysis.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(rows), int(total)


def all_user_analyses(db: Session, user_id: int) -> list[Analysis]:
    return list(
        db.scalars(
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .options(selectinload(Analysis.matches).selectinload(SkillMatch.required_skill),
                     selectinload(Analysis.roadmap).selectinload(LearningRoadmap.tasks))
            .order_by(Analysis.created_at.desc())
        ).all()
    )


def expired_analysis_ids(db: Session, user_id: int, before: datetime) -> list[int]:
    return list(db.scalars(select(Analysis.id).where(Analysis.user_id == user_id, Analysis.created_at < before)).all())


def delete_if_unreferenced(db: Session, user_id: int, resume_id: int | None, job_id: int | None) -> list[str]:
    """After an analysis is deleted, remove its resume/job rows if no other analysis uses them.

    Returns stored file paths that the caller must delete from disk.
    """
    from app.models import JobDescription

    paths: list[str] = []
    if resume_id is not None:
        still_used = db.scalar(select(func.count()).select_from(Analysis).where(Analysis.resume_id == resume_id))
        resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
        if resume is not None and not still_used:
            if resume.stored_path:
                paths.append(resume.stored_path)
            db.delete(resume)
    if job_id is not None:
        still_used = db.scalar(select(func.count()).select_from(Analysis).where(Analysis.job_id == job_id))
        if not still_used:
            db.execute(delete(JobDescription).where(JobDescription.id == job_id, JobDescription.user_id == user_id))
    return paths
