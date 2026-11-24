"""End-to-end smoke test against a RUNNING backend (standard library only).

    python scripts/smoke_test.py                      # default http://localhost:8000
    python scripts/smoke_test.py --base http://localhost:8000

Registers a throw-away user, uploads the sample resume, runs an analysis,
updates the roadmap, corrects a match, then deletes the account.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Client:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, method: str, path: str, body=None, raw: bytes | None = None, headers: dict | None = None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        hdrs = {"Content-Type": "application/json"} if body is not None else {}
        hdrs.update(headers or {})
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=hdrs)
        try:
            with self.opener.open(req, timeout=300) as resp:
                text = resp.read().decode()
                return resp.status, (json.loads(text) if text else None)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "null")

    def upload(self, path: str, filename: str, content: bytes):
        boundary = uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
                f"Content-Type: text/plain\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
        return self.call("POST", path, raw=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}{(' - ' + detail) if detail else ''}")
    if not ok:
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--mode", default="semantic", choices=["keyword", "tfidf", "semantic"])
    args = ap.parse_args()
    c = Client(args.base)

    status, health = c.call("GET", "/api/health")
    check("health", status == 200 and health["database"] == "ok", json.dumps(health.get("semantic_model")))

    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    status, _ = c.call("POST", "/api/auth/register", {"email": email, "password": "smoke1234", "full_name": "Smoke Test"})
    check("register", status == 201)

    resume = (ROOT / "data" / "sample_data" / "sample_resume.txt").read_bytes()
    job = (ROOT / "data" / "sample_data" / "sample_job_description.txt").read_text()
    status, up = c.upload("/api/resumes/upload", "sample_resume.txt", resume)
    check("upload resume", status == 201, f"{up.get('char_count')} chars")

    t0 = time.time()
    status, a = c.call("POST", "/api/analyses", {"resume_id": up["resume_id"], "job_description": job,
                                                 "job_title": "Junior NLP Engineer", "mode": args.mode})
    check("analysis", status == 201, f"{time.time() - t0:.1f}s, coverage {a.get('coverage', {}).get('coverage_score')}%")
    info = a["model_info"]
    print(f"       backend={info['similarity_backend']} semantic_available={info['semantic_available']} fallback={info['fallback_used']}")
    for r in a["requirements"]:
        print(f"       {r['canonical']:<30} {r['importance']:<13} {r['effective_classification']}")

    status, rm = c.call("GET", f"/api/analyses/{a['id']}/roadmap")
    check("roadmap", status == 200, f"{len(rm['tasks'])} tasks")
    if rm["tasks"]:
        status, _ = c.call("PATCH", f"/api/roadmap/tasks/{rm['tasks'][0]['id']}", {"status": "learning"})
        check("update task", status == 200)

    missing = next((r for r in a["requirements"] if r["effective_classification"] == "missing"), None)
    if missing:
        status, upd = c.call("PATCH", f"/api/analyses/{a['id']}/matches/{missing['match_id']}", {"corrected_classification": "direct_match"})
        check("correction", status == 200, f"coverage now {upd['coverage']['coverage_score']}%")

    status, _ = c.call("POST", "/api/nlp/similarity", {"text_a": "built a sentiment classifier", "text_b": "text classification"})
    check("nlp lab similarity", status == 200)
    status, _ = c.call("DELETE", f"/api/analyses/{a['id']}")
    check("delete analysis", status == 204)
    status, _ = c.call("POST", "/api/users/me/delete", {"password": "smoke1234"})
    check("delete account", status == 204)
    print("\nSmoke test passed.")


if __name__ == "__main__":
    main()
