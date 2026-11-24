from __future__ import annotations

from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services import user_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        key=s.cookie_name, value=token, max_age=s.access_token_minutes * 60, httponly=True,
        secure=s.cookie_secure, samesite=s.cookie_samesite, path="/",
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: DbSession):
    user = user_service.register(db, payload.email, payload.full_name, payload.password)
    token = create_access_token(user.id)
    _set_session_cookie(response, token)
    return {"user": UserOut.model_validate(user), "access_token": token}


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: DbSession):
    user = user_service.authenticate(db, payload.email, payload.password)
    token = create_access_token(user.id)
    _set_session_cookie(response, token)
    return {"user": UserOut.model_validate(user), "access_token": token}


@router.post("/logout", status_code=204)
def logout():
    s = get_settings()
    response = Response(status_code=204)
    response.delete_cookie(s.cookie_name, path="/", httponly=True, secure=s.cookie_secure, samesite=s.cookie_samesite)
    return response


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
