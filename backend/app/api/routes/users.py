from __future__ import annotations

from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.schemas.auth import DeleteAccountRequest, UpdateProfileRequest, UserOut
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_me(payload: UpdateProfileRequest, user: CurrentUser, db: DbSession):
    return user_service.update_profile(db, user, payload.full_name, payload.preferences)


@router.post("/me/delete", status_code=204)
def delete_me(payload: DeleteAccountRequest, user: CurrentUser, db: DbSession):
    """Permanently delete the account and ALL associated data (POST because a password body is required)."""
    user_service.delete_account(db, user, payload.password)
    response = Response(status_code=204)
    response.delete_cookie(get_settings().cookie_name, path="/")
    return response


@router.get("/me/export")
def export_me(user: CurrentUser, db: DbSession):
    """Download all personal data as JSON (data portability)."""
    return user_service.export_user_data(db, user)


@router.get("/me/privacy")
def privacy_info(user: CurrentUser):
    s = get_settings()
    return {
        "retention_days": user_service.retention_days_for(user),
        "default_retention_days": s.retention_days,
        "stores_original_files": s.store_uploaded_files,
        "statement": (
            "We store the extracted resume text, the job description and analysis results so you can revisit them. "
            f"Original uploaded files are {'stored privately on the server' if s.store_uploaded_files else 'not stored'}. "
            "Analyses older than your retention period are deleted automatically. Contact details are never used for "
            "scoring, and no sensitive characteristics are inferred. You can export or delete everything at any time."
        ),
    }
