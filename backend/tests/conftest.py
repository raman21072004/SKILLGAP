"""Shared fixtures. Environment is configured BEFORE the app is imported so tests use
an isolated SQLite database and never download models."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="skillgap-test-"))
os.environ.setdefault("ENVIRONMENT", "test")
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TMP / "uploads")
os.environ["ENABLE_SEMANTIC_MODEL"] = "false"   # unit tests must not need internet
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production-use-only-123"
os.environ["STORE_UPLOADED_FILES"] = "true"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_RESUME = (ROOT / "data" / "sample_data" / "sample_resume.txt").read_text(encoding="utf-8")
SAMPLE_JOB = (ROOT / "data" / "sample_data" / "sample_job_description.txt").read_text(encoding="utf-8")


@pytest.fixture
def taxonomy():
    from app.nlp.skill_extraction.taxonomy import get_taxonomy

    return get_taxonomy()


@pytest.fixture
def test_encoder():
    """Deterministic offline encoder that exercises the semantic code path."""
    from app.nlp.embeddings.sentence_encoder import HashingTestEncoder, set_encoder

    enc = HashingTestEncoder()
    set_encoder(enc)
    yield enc
    set_encoder(None)


@pytest.fixture
def client():
    pytest.importorskip("fastapi")
    pytest.importorskip("sqlalchemy")
    from fastapi.testclient import TestClient

    import app.models  # noqa: F401  (register tables before create_all)
    from app.database.session import Base, engine
    from app.main import app as fastapi_app

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(fastapi_app) as c:
        yield c


def register(client, email="student@example.com", password="secret123", name="Test Student"):
    r = client.post("/api/auth/register", json={"email": email, "password": password, "full_name": name})
    assert r.status_code == 201, r.text
    return r
