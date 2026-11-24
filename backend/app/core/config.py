"""Application settings, loaded from environment variables / .env (never hard-coded secrets)."""

from __future__ import annotations

import logging
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SkillGap-NLP"
    environment: str = "development"  # development | test | production

    # Database: PostgreSQL is the intended primary database. SQLite is a zero-setup dev option.
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'var' / 'skillgap.db').as_posix()}"
    auto_create_tables: bool = True  # dev convenience; use `alembic upgrade head` in production

    # Auth
    secret_key: str | None = None
    access_token_minutes: int = 60 * 12
    cookie_name: str = "skillgap_session"
    cookie_secure: bool = False  # set true behind HTTPS
    cookie_samesite: str = "lax"

    # CORS (comma-separated list of allowed origins)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Uploads & data handling
    max_upload_mb: int = 5
    max_text_chars: int = 60_000
    upload_dir: str = str(BACKEND_DIR / "var" / "uploads")
    store_uploaded_files: bool = False  # privacy default: keep only the extracted text
    retention_days: int = 180

    # Runtime
    analysis_timeout_seconds: int = 120
    preload_models: bool = False  # load the sentence-transformer at startup instead of on first use
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def effective_secret_key(self) -> str:
        return _secret_key(self.secret_key, self.environment)


@lru_cache(maxsize=4)
def _secret_key(configured: str | None, environment: str) -> str:
    if configured and configured != "change-me":
        return configured
    if environment == "production":
        raise RuntimeError("SECRET_KEY must be set in production.")
    logger.warning("SECRET_KEY not set: using a random development key (sessions reset on restart).")
    return secrets.token_urlsafe(48)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
