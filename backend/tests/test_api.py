"""API integration tests: auth, ownership, full analysis workflow, corrections, roadmap,
deletion, uploads and NLP Lab endpoints. Uses an isolated SQLite database."""

import io

import pytest

from tests.conftest import SAMPLE_JOB, SAMPLE_RESUME, register

pytest.importorskip("fastapi")


def create_analysis(client, **overrides):
    body = {"resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JOB, "job_title": "Junior NLP Engineer", "mode": "tfidf"}
    body.update(overrides)
    r = client.post("/api/analyses", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["database"] == "ok" and "semantic_model" in data


def test_register_login_me_logout(client):
    r = register(client)
    assert r.json()["user"]["email"] == "student@example.com"
    assert "password_hash" not in r.json()["user"]
    assert client.get("/api/auth/me").status_code == 200          # cookie session
    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401
    r = client.post("/api/auth/login", json={"email": "student@example.com", "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    client.cookies.clear()
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_auth_validation_and_errors(client):
    r = client.post("/api/auth/register", json={"email": "bad", "password": "short", "full_name": "A"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    register(client)
    dup = client.post("/api/auth/register", json={"email": "student@example.com", "password": "secret123", "full_name": "X Y"})
    assert dup.status_code == 409
    wrong = client.post("/api/auth/login", json={"email": "student@example.com", "password": "wrong123"})
    assert wrong.status_code == 401 and wrong.json()["error"]["code"] == "invalid_credentials"


def test_protected_routes_require_auth(client):
    for method, url in [("get", "/api/analyses"), ("get", "/api/dashboard"), ("get", "/api/nlp/models/status")]:
        assert getattr(client, method)(url).status_code == 401


def test_full_analysis_workflow(client):
    register(client)
    a = create_analysis(client)
    assert a["coverage"]["formula"].startswith("coverage")
    by = {r["canonical"]: r for r in a["requirements"]}
    assert by["Python"]["effective_classification"] == "direct_match"
    assert by["AWS"]["effective_classification"] == "missing"
    for r in a["requirements"]:
        if r["evidence"]:
            assert r["evidence"]["text"] in a["resume_text"]   # never fabricated
    assert a["model_info"]["similarity_backend"] == "tf-idf"
    assert len(a["model_comparison"]) == 3

    # list + pagination
    lst = client.get("/api/analyses?page=1&page_size=5").json()
    assert lst["total"] == 1 and lst["items"][0]["id"] == a["id"]

    # skills + roadmap
    skills = client.get(f"/api/analyses/{a['id']}/skills").json()
    assert len(skills["requirements"]) == len(a["requirements"])
    roadmap = client.get(f"/api/analyses/{a['id']}/roadmap").json()
    assert roadmap["tasks"] and roadmap["progress"]["total"] == len(roadmap["tasks"])

    # update task progress (self-reported; does not change verified coverage)
    task = roadmap["tasks"][0]
    r = client.patch(f"/api/roadmap/tasks/{task['id']}", json={"status": "completed", "checklist_done": [0, 1, 99]})
    assert r.status_code == 200
    assert r.json()["task"]["status"] == "completed" and r.json()["task"]["checklist_done"] == [0, 1]
    assert client.get(f"/api/analyses/{a['id']}").json()["coverage"]["coverage_score"] == a["coverage"]["coverage_score"]

    # dashboard
    dash = client.get("/api/dashboard").json()
    assert dash["analysis_count"] == 1 and dash["roadmap"]["by_status"]["completed"] == 1


def test_user_correction_recomputes_coverage_and_is_stored_separately(client):
    register(client)
    a = create_analysis(client)
    aws = next(r for r in a["requirements"] if r["canonical"] == "AWS")
    before = a["coverage"]["coverage_score"]
    r = client.patch(f"/api/analyses/{a['id']}/matches/{aws['match_id']}",
                     json={"corrected_classification": "direct_match", "comment": "Used AWS in internship"})
    assert r.status_code == 200, r.text
    updated = r.json()
    aws2 = next(x for x in updated["requirements"] if x["canonical"] == "AWS")
    assert aws2["classification"] == "missing"                  # original kept
    assert aws2["user_classification"] == "direct_match"
    assert updated["coverage"]["coverage_score"] > before
    roadmap = client.get(f"/api/analyses/{a['id']}/roadmap").json()
    assert "AWS" not in [t["skill"] for t in roadmap["tasks"]]  # roadmap re-synced
    # revert
    r = client.patch(f"/api/analyses/{a['id']}/matches/{aws['match_id']}", json={"corrected_classification": None})
    assert r.json()["coverage"]["coverage_score"] == before


def test_ownership_is_enforced(client):
    register(client, email="alice@example.com")
    a = create_analysis(client)
    task_id = client.get(f"/api/analyses/{a['id']}/roadmap").json()["tasks"][0]["id"]
    client.post("/api/auth/logout")
    client.cookies.clear()
    register(client, email="bob@example.com")
    assert client.get(f"/api/analyses/{a['id']}").status_code == 404
    assert client.delete(f"/api/analyses/{a['id']}").status_code == 404
    assert client.patch(f"/api/roadmap/tasks/{task_id}", json={"status": "learning"}).status_code == 404
    assert client.get("/api/analyses").json()["total"] == 0


def test_delete_analysis_removes_records(client):
    register(client)
    a = create_analysis(client)
    assert client.delete(f"/api/analyses/{a['id']}").status_code == 204
    assert client.get(f"/api/analyses/{a['id']}").status_code == 404
    assert client.get("/api/analyses").json()["total"] == 0

    from sqlalchemy import func, select

    from app.database.session import SessionLocal
    from app.models import Evidence, LearningTask, Resume, SkillMatch

    with SessionLocal() as db:
        for model in (SkillMatch, Evidence, LearningTask, Resume):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_analysis_input_validation(client):
    register(client)
    r = client.post("/api/analyses", json={"job_description": SAMPLE_JOB})
    assert r.status_code == 422
    r = client.post("/api/analyses", json={"resume_text": SAMPLE_RESUME, "job_description": "too short"})
    assert r.status_code == 422
    r = client.post("/api/analyses", json={"resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JOB, "mode": "magic"})
    assert r.status_code == 422


def test_upload_txt_and_docx_then_analyse(client):
    register(client)
    r = client.post("/api/resumes/upload", files={"file": ("cv.txt", SAMPLE_RESUME.encode(), "text/plain")})
    assert r.status_code == 201, r.text
    resume_id = r.json()["resume_id"]
    assert r.json()["stored_file"] is True
    a = create_analysis(client, resume_text=None, resume_id=resume_id)
    assert a["resume_text"].startswith("Aarav")

    docx = pytest.importorskip("docx")
    d = docx.Document()
    d.add_paragraph("PROJECTS")
    d.add_paragraph("Built REST APIs with FastAPI and PostgreSQL for a campus app.")
    buf = io.BytesIO()
    d.save(buf)
    r = client.post("/api/resumes/upload", files={"file": ("cv.docx", buf.getvalue(), "application/octet-stream")})
    assert r.status_code == 201 and "FastAPI" in r.json()["text"]


def test_upload_rejections(client):
    register(client)
    r = client.post("/api/resumes/upload", files={"file": ("virus.exe", b"MZ....", "application/octet-stream")})
    assert r.status_code == 422 and r.json()["error"]["code"] == "unsupported_file_type"
    r = client.post("/api/resumes/upload", files={"file": ("fake.pdf", b"not a pdf at all", "application/pdf")})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_signature"
    r = client.post("/api/resumes/upload", files={"file": ("../../etc/passwd.txt", b"x" * 10, "text/plain")})
    assert r.status_code == 422  # too short; and the filename is never used as a path
    big = b"a" * (6 * 1024 * 1024)
    r = client.post("/api/resumes/upload", files={"file": ("big.txt", big, "text/plain")})
    assert r.status_code == 413


def test_settings_export_and_account_deletion(client):
    register(client)
    create_analysis(client)
    r = client.patch("/api/users/me", json={"full_name": "New Name", "preferences": {"default_mode": "keyword"}})
    assert r.status_code == 200 and r.json()["preferences"]["default_mode"] == "keyword"
    assert client.patch("/api/users/me", json={"preferences": {"hack": True}}).status_code == 422
    export = client.get("/api/users/me/export").json()
    assert export["user"]["full_name"] == "New Name" and len(export["analyses"]) == 1
    assert "statement" in client.get("/api/users/me/privacy").json()
    assert client.post("/api/users/me/delete", json={"password": "wrong999"}).status_code == 403
    assert client.post("/api/users/me/delete", json={"password": "secret123"}).status_code == 204
    client.cookies.clear()
    r = client.post("/api/auth/login", json={"email": "student@example.com", "password": "secret123"})
    assert r.status_code == 401


def test_nlp_lab_endpoints(client, test_encoder):
    register(client)
    r = client.get("/api/nlp/preprocessing", params={"text": "Developers were building REST APIs in C++"})
    assert r.status_code == 200 and len(r.json()["steps"]) >= 7
    r = client.post("/api/nlp/bow", json={"doc_a": "python sql", "doc_b": "java sql"})
    assert r.json()["shape"] == [2, 3]
    r = client.post("/api/nlp/tfidf", json={"doc_a": SAMPLE_RESUME, "doc_b": SAMPLE_JOB})
    assert 0 <= r.json()["tfidf_cosine_similarity"] <= 1
    r = client.post("/api/nlp/similarity", json={"text_a": "built a sentiment classifier", "text_b": "text classification"})
    assert r.json()["semantic"] is not None                    # test encoder is active
    r = client.post("/api/nlp/vectors", json={"text": "Built APIs in Flask", "corpus": ["Trained a model"]})
    assert r.json()["sparse"]["dimensions"] > 0 and r.json()["dense"]["dimensions"] == test_encoder.dimension
    r = client.post("/api/nlp/visualize", json={"source": "sentence-transformer", "method": "pca",
                                                "items": ["Python", "Java", "Docker", "Kubernetes", "React"]})
    assert r.status_code == 200 and len(r.json()["points"]) == 5
    r = client.post("/api/nlp/visualize", json={"source": "sentence-transformer", "method": "tsne", "items": ["Python", "Java"]})
    assert r.status_code == 400 and r.json()["error"]["code"] == "too_few_points"
    r = client.post("/api/nlp/compare-models", json={"resume_text": SAMPLE_RESUME, "job_description": SAMPLE_JOB})
    assert {m["method"] for m in r.json()["methods"]} == {"keyword", "tfidf", "semantic"}
    assert client.get("/api/nlp/taxonomy").json()["skills"]


def test_word2vec_endpoints(client):
    pytest.importorskip("gensim")
    register(client)
    r = client.post("/api/nlp/word2vec", json={"words": ["python", "zzzunknown"], "architecture": "skipgram"})
    assert r.status_code == 200
    words = {w["word"]: w for w in r.json()["words"]}
    assert words["python"]["in_vocabulary"] and words["zzzunknown"]["in_vocabulary"] is False
    r = client.post("/api/nlp/word2vec/compare", json={"words": ["docker"], "window": 3, "vector_size": 30})
    assert set(r.json()["models"]) == {"cbow", "skipgram"}
    r = client.post("/api/nlp/analogy", json={"model": "word2vec-skipgram", "positive": ["king", "woman"], "negative": ["man"]})
    assert r.status_code == 200 and "results" in r.json()
    r = client.post("/api/nlp/visualize", json={"source": "word2vec-cbow", "method": "tsne", "perplexity": 5})
    assert r.status_code == 200 and r.json()["seed"] == 42
