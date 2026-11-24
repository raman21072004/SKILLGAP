"""SkillGap-NLP FastAPI application entry point.

Run (from the backend/ folder):
    uvicorn app.main:app --reload --port 8000
API docs: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analyses, auth, health, nlp, users
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.database.session import SessionLocal, create_all_tables
from app.nlp.embeddings.sentence_encoder import get_encoder

logger = logging.getLogger("skillgap")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.effective_secret_key  # noqa: B018  fail fast in production if SECRET_KEY is missing
    if settings.auto_create_tables:
        create_all_tables()
    # Data-retention policy: purge expired analyses on startup
    try:
        from app.services.user_service import purge_expired

        with SessionLocal() as db:
            purge_expired(db)
    except Exception as exc:  # e.g. tables not migrated yet
        logger.warning("Retention purge skipped: %s", type(exc).__name__)
    if settings.preload_models:
        # Load in the background so the server starts immediately
        threading.Thread(target=lambda: getattr(get_encoder(), "load", lambda: None)(), daemon=True).start()
    logger.info("%s started (%s)", settings.app_name, settings.environment)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SkillGap-NLP API",
        version="1.0.0",
        description=(
            "Deep-learning-based skill gap analysis for resumes and job descriptions. "
            "A career-development aid - not a hiring decision engine."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,  # needed for the httpOnly session cookie
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    register_error_handlers(app)
    for module in (health, auth, users, analyses, nlp):
        app.include_router(module.router)
    return app


app = create_app()
