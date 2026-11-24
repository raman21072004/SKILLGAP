"""Database tables (SQLAlchemy 2.0 ORM).

Ownership: every user-owned row links back to users.id (directly or via
analyses). Deleting an analysis cascades to its requirements, matches,
evidence, roadmap, tasks, progress history and feedback.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetimes on every database (SQLite drops tzinfo otherwise)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False, index=True)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow, nullable=False)

    analyses: Mapped[list[Analysis]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    resumes: Mapped[list[Resume]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    job_descriptions: Mapped[list[JobDescription]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)


class Resume(TimestampMixin, Base):
    """The single place where full resume text is stored."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf | docx | txt | pasted
    stored_path: Mapped[str | None] = mapped_column(String(500))  # only if STORE_UPLOADED_FILES=true
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    sections: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    user: Mapped[User] = relationship(back_populates="resumes")


class JobDescription(TimestampMixin, Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(back_populates="job_descriptions")


class Analysis(TimestampMixin, Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), index=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("job_descriptions.id", ondelete="SET NULL"), index=True)
    job_title: Mapped[str | None] = mapped_column(String(200))
    target_role: Mapped[str | None] = mapped_column(String(200))
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    must_have_coverage: Mapped[float | None] = mapped_column(Float)
    nice_to_have_coverage: Mapped[float | None] = mapped_column(Float)
    doc_similarity_tfidf: Mapped[float | None] = mapped_column(Float)
    doc_similarity_semantic: Mapped[float | None] = mapped_column(Float)
    options: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    model_info: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    extras: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # comparison, warnings, sections...

    user: Mapped[User] = relationship(back_populates="analyses")
    resume: Mapped[Resume | None] = relationship()
    job: Mapped[JobDescription | None] = relationship()
    required_skills: Mapped[list[RequiredSkill]] = relationship(back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True)
    candidate_skills: Mapped[list[CandidateSkill]] = relationship(back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True)
    matches: Mapped[list[SkillMatch]] = relationship(back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True, order_by="SkillMatch.id")
    evidence: Mapped[list[Evidence]] = relationship(back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True)
    roadmap: Mapped[LearningRoadmap | None] = relationship(back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True, uselist=False)
    feedback: Mapped[list[UserFeedback]] = relationship(back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True)


class RequiredSkill(Base):
    __tablename__ = "required_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    canonical: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False)  # must_have | nice_to_have
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    requirement_text: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="extracted", nullable=False)

    analysis: Mapped[Analysis] = relationship(back_populates="required_skills")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    canonical: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    strength: Mapped[str] = mapped_column(String(20), nullable=False)  # demonstrated | mentioned | listed
    mention_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    analysis: Mapped[Analysis] = relationship(back_populates="candidate_skills")


class Evidence(Base):
    """A real passage from the resume (offsets into Resume.text)."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    canonical: Mapped[str | None] = mapped_column(String(100))
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str | None] = mapped_column(String(40))
    start: Mapped[int | None] = mapped_column(Integer)
    end: Mapped[int | None] = mapped_column(Integer)
    match_start: Mapped[int | None] = mapped_column(Integer)
    match_end: Mapped[int | None] = mapped_column(Integer)
    matched_text: Mapped[str | None] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # exact | semantic | related
    strength: Mapped[str | None] = mapped_column(String(20))

    analysis: Mapped[Analysis] = relationship(back_populates="evidence")


class SkillMatch(Base):
    __tablename__ = "skill_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    required_skill_id: Mapped[int] = mapped_column(ForeignKey("required_skills.id", ondelete="CASCADE"), index=True, nullable=False)
    evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id", ondelete="SET NULL"))
    classification: Mapped[str] = mapped_column(String(30), nullable=False)
    user_classification: Mapped[str | None] = mapped_column(String(30))  # correction; original kept above
    exact_match: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    similarity: Mapped[float | None] = mapped_column(Float)
    tfidf_similarity: Mapped[float | None] = mapped_column(Float)
    semantic_similarity: Mapped[float | None] = mapped_column(Float)
    similarity_backend: Mapped[str | None] = mapped_column(String(120))
    related_skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    method: Mapped[str | None] = mapped_column(String(300))
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    next_action: Mapped[str] = mapped_column(Text, nullable=False)
    uncertainty: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[Analysis] = relationship(back_populates="matches")
    required_skill: Mapped[RequiredSkill] = relationship()
    evidence: Mapped[Evidence | None] = relationship()


class LearningRoadmap(TimestampMixin, Base):
    __tablename__ = "learning_roadmaps"
    __table_args__ = (UniqueConstraint("analysis_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(200))

    analysis: Mapped[Analysis] = relationship(back_populates="roadmap")
    tasks: Mapped[list[LearningTask]] = relationship(back_populates="roadmap", cascade="all, delete-orphan", passive_deletes=True, order_by="LearningTask.order")


class LearningTask(Base):
    __tablename__ = "learning_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), index=True, nullable=False)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False)
    gap_type: Mapped[str] = mapped_column(String(30), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    project: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_effort: Mapped[str] = mapped_column(String(120), nullable=False)
    checklist: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    checklist_done: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    resources: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    resources_note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow, nullable=False)

    roadmap: Mapped[LearningRoadmap] = relationship(back_populates="tasks")
    progress_events: Mapped[list[LearningProgress]] = relationship(back_populates="task", cascade="all, delete-orphan", passive_deletes=True)


class LearningProgress(Base):
    """History of status changes (self-reported learning progress)."""

    __tablename__ = "learning_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("learning_tasks.id", ondelete="CASCADE"), index=True, nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)

    task: Mapped[LearningTask] = relationship(back_populates="progress_events")


class UserFeedback(TimestampMixin, Base):
    """User corrections to match classifications, stored separately for future evaluation."""

    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("skill_matches.id", ondelete="CASCADE"), index=True, nullable=False)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    original_classification: Mapped[str] = mapped_column(String(30), nullable=False)
    corrected_classification: Mapped[str | None] = mapped_column(String(30))  # None = correction reverted
    comment: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[Analysis] = relationship(back_populates="feedback")
