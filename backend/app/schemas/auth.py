from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _check_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v) or len(v) > 255:
        raise ValueError("Enter a valid email address.")
    return v


class RegisterRequest(BaseModel):
    email: str
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        return _check_email(v)

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password must contain at least one letter and one number.")
        return v

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Name is too short.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        return _check_email(v)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    preferences: dict
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str = Field(description="Also set as an httpOnly cookie. Returned for API clients/Swagger.")
    token_type: str = "bearer"


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    preferences: dict | None = None

    @field_validator("preferences")
    @classmethod
    def limited_preferences(cls, v: dict | None) -> dict | None:
        if v is None:
            return v
        allowed = {"default_mode", "count_strong_semantic", "equal_weights", "retention_days"}
        unknown = set(v) - allowed
        if unknown:
            raise ValueError(f"Unknown preference(s): {', '.join(sorted(unknown))}")
        if "default_mode" in v and v["default_mode"] not in {"keyword", "tfidf", "semantic"}:
            raise ValueError("default_mode must be keyword, tfidf or semantic.")
        if "retention_days" in v and not (isinstance(v["retention_days"], int) and 1 <= v["retention_days"] <= 3650):
            raise ValueError("retention_days must be an integer between 1 and 3650.")
        return v


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
