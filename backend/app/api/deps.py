"""Request dependencies: database session and the authenticated user.

The session token is read from an httpOnly cookie (not accessible to JavaScript,
so it cannot be stolen by XSS the way localStorage tokens can). A Bearer header
is also accepted for API clients and the Swagger UI.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(get_settings().cookie_name)
    auth = request.headers.get("Authorization", "")
    if not token and auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise AppError(401, "unauthorized", "Please sign in to continue.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
