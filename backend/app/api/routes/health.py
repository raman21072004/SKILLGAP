from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.database.session import engine
from app.nlp.embeddings.sentence_encoder import get_encoder

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health():
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    enc = get_encoder()
    s = get_settings()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "unavailable",
        "database_backend": engine.dialect.name,
        "environment": s.environment,
        # Reports status without forcing a model download; loads lazily on first analysis
        "semantic_model": enc.status() if hasattr(enc, "status") else {"model": enc.name, "available": enc.available},
        "max_upload_mb": s.max_upload_mb,
    }
