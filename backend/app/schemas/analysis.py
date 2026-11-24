from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Classification = Literal["direct_match", "strong_semantic", "related", "missing"]
Mode = Literal["keyword", "tfidf", "semantic"]
TaskStatus = Literal["not_started", "learning", "practiced", "completed"]


class ResumeUploadResponse(BaseModel):
    resume_id: int
    filename: str | None
    file_type: str
    char_count: int
    page_count: int | None
    sections: list[dict[str, Any]]
    text: str
    stored_file: bool


class AnalysisCreate(BaseModel):
    resume_id: int | None = None
    resume_text: str | None = Field(default=None, max_length=60_000)
    job_description: str = Field(min_length=30, max_length=60_000)
    job_title: str | None = Field(default=None, max_length=200)
    target_role: str | None = Field(default=None, max_length=200)
    mode: Mode = "semantic"
    must_have_skills: list[str] = Field(default_factory=list, max_length=50)
    nice_to_have_skills: list[str] = Field(default_factory=list, max_length=50)
    custom_weights: dict[str, float] = Field(default_factory=dict)
    equal_weights: bool = False
    count_strong_semantic: bool = False

    @field_validator("must_have_skills", "nice_to_have_skills")
    @classmethod
    def clean_list(cls, v: list[str]) -> list[str]:
        return [s.strip()[:100] for s in v if s and s.strip()]

    @field_validator("custom_weights")
    @classmethod
    def check_weights(cls, v: dict[str, float]) -> dict[str, float]:
        if len(v) > 100:
            raise ValueError("Too many custom weights.")
        for k, w in v.items():
            if not 0 <= w <= 10:
                raise ValueError(f"Weight for '{k}' must be between 0 and 10.")
        return v

    @model_validator(mode="after")
    def need_resume(self) -> AnalysisCreate:
        if self.resume_id is None and not (self.resume_text and len(self.resume_text.strip()) >= 30):
            raise ValueError("Provide a resume: upload a file or paste at least 30 characters of resume text.")
        return self


class AnalysisSummary(BaseModel):
    id: int
    created_at: datetime
    job_title: str | None
    target_role: str | None
    mode: str
    coverage_score: float
    must_have_coverage: float | None
    nice_to_have_coverage: float | None
    requirement_count: int
    direct_count: int
    missing_count: int
    similarity_backend: str | None
    fallback_used: bool


class Paginated(BaseModel):
    items: list[AnalysisSummary]
    total: int
    page: int
    page_size: int


class MatchCorrection(BaseModel):
    corrected_classification: Classification | None = Field(
        description="New classification, or null to revert to the system's original classification."
    )
    comment: str | None = Field(default=None, max_length=1000)


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    checklist_done: list[int] | None = Field(default=None, max_length=50)


class AnalysisDetail(BaseModel):
    """Full analysis; nested parts are documented in docs/api.md."""

    id: int
    created_at: datetime
    job_title: str | None
    target_role: str | None
    mode: str
    coverage: dict[str, Any]
    document_similarity: dict[str, Any]
    model_info: dict[str, Any]
    requirements: list[dict[str, Any]]
    candidate_skills: list[dict[str, Any]]
    model_comparison: list[dict[str, Any]]
    resume_text: str | None
    resume_sections: list[dict[str, Any]]
    job_description: str | None
    warnings: list[str]
    unrecognized_job_terms: list[dict[str, Any]]
    roadmap_progress: dict[str, Any] | None
    disclaimer: str
