from __future__ import annotations

from fastapi import APIRouter, File, Query, Response, UploadFile

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.errors import AppError
from app.repositories import analysis_repo
from app.schemas.analysis import AnalysisCreate, AnalysisDetail, MatchCorrection, Paginated, ResumeUploadResponse, TaskUpdate
from app.services import analysis_service, user_service

router = APIRouter(tags=["analyses"])


@router.post("/api/resumes/upload", response_model=ResumeUploadResponse, status_code=201)
def upload_resume(user: CurrentUser, db: DbSession, file: UploadFile = File(...)):
    limit = get_settings().max_upload_bytes
    content = file.file.read(limit + 1)  # read at most limit+1 bytes: never buffer huge uploads
    if len(content) > limit:
        raise AppError(413, "file_too_large", f"File is larger than the {get_settings().max_upload_mb} MB limit.")
    resume, meta = user_service.upload_resume(db, user, file.filename or "", content)
    return {
        "resume_id": resume.id, "filename": resume.original_filename, "file_type": resume.file_type,
        "char_count": resume.char_count, "page_count": resume.page_count, "sections": resume.sections,
        "text": resume.text, "stored_file": meta["stored_file"],
    }


@router.post("/api/analyses", response_model=AnalysisDetail, status_code=201)
def create_analysis(payload: AnalysisCreate, user: CurrentUser, db: DbSession):
    analysis = analysis_service.create_analysis(db, user, payload)
    return analysis_service.serialize_analysis(analysis)


@router.get("/api/analyses", response_model=Paginated)
def list_analyses(user: CurrentUser, db: DbSession, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50)):
    rows, total = analysis_repo.list_analyses(db, user.id, page, page_size)
    return {"items": [analysis_service.summarize(a) for a in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/api/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: int, user: CurrentUser, db: DbSession):
    return analysis_service.serialize_analysis(analysis_repo.get_owned_analysis(db, user.id, analysis_id))


@router.delete("/api/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, user: CurrentUser, db: DbSession):
    analysis_service.delete_analysis(db, user, analysis_id)
    return Response(status_code=204)


@router.get("/api/analyses/{analysis_id}/skills")
def get_skills(analysis_id: int, user: CurrentUser, db: DbSession):
    detail = analysis_service.serialize_analysis(analysis_repo.get_owned_analysis(db, user.id, analysis_id))
    return {"analysis_id": analysis_id, "requirements": detail["requirements"], "candidate_skills": detail["candidate_skills"],
            "coverage": detail["coverage"]}


@router.patch("/api/analyses/{analysis_id}/matches/{match_id}", response_model=AnalysisDetail)
def correct_match(analysis_id: int, match_id: int, payload: MatchCorrection, user: CurrentUser, db: DbSession):
    """Store a user correction (kept separate from the original classification) and recompute coverage."""
    return analysis_service.correct_match(db, user, analysis_id, match_id, payload.corrected_classification, payload.comment)


@router.get("/api/analyses/{analysis_id}/roadmap")
def get_roadmap(analysis_id: int, user: CurrentUser, db: DbSession):
    return user_service.get_roadmap(db, user, analysis_id)


@router.get("/api/analyses/{analysis_id}/export")
def export_analysis(analysis_id: int, user: CurrentUser, db: DbSession):
    return analysis_service.serialize_analysis(analysis_repo.get_owned_analysis(db, user.id, analysis_id))


@router.patch("/api/roadmap/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate, user: CurrentUser, db: DbSession):
    return user_service.update_task(db, user, task_id, payload.status, payload.checklist_done)


@router.get("/api/dashboard")
def dashboard(user: CurrentUser, db: DbSession):
    return user_service.dashboard(db, user)
