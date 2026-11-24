# Instructions for the coding agent (Google Antigravity or similar)

You are setting up and verifying **SkillGap-NLP** on the user's local machine.
The code is complete. Your job is to install it, run every check, fix any real
errors you find, and start the app. Work through the steps in order and report
results honestly. Do not fake passing tests, do not invent evaluation numbers,
and do not delete features to make errors disappear.

## Context
- `backend/` FastAPI + SQLAlchemy + NLP engine (Python). `frontend/` React + Vite + TypeScript + Tailwind v4.
- The NLP engine core (`backend/app/nlp/`) was already tested: 50 unit tests passed in the authoring
  environment. The API tests (`backend/tests/test_api.py`), PDF tests, Word2Vec tests and the frontend
  build/tests could NOT be run there because packages could not be installed. Expect to fix small
  issues in those areas (version mismatches, typos, type errors).
- Python 3.11 or 3.12 is recommended (3.13 works if all wheels are available). Node 18+ (20 LTS recommended).

## Step 1 - Install
Windows (PowerShell, from project root):
```
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
```
macOS/Linux:
```
bash scripts/setup.sh
```
If the deep-learning install fails or the machine is low on disk, re-run with `-SkipML` / `--skip-ml`.
The app still works; it shows a clear "TF-IDF fallback" notice instead of semantic matching.

If the script fails part-way, run the commands from it manually (see README "Manual setup").

## Step 2 - Backend checks (from `backend/`, venv active)
```
python -m pytest                 # all tests; API tests use a temp SQLite DB, no internet needed
python -m ruff check app tests   # lint
```
All tests must pass. Tests marked "skipped" are acceptable only for optional packages that are not
installed (PyMuPDF, gensim). If a test fails, find the root cause in the application code and fix it;
only change a test if the test itself is wrong, and explain why.

## Step 3 - Frontend checks (from `frontend/`)
```
npm run build      # runs tsc --noEmit then vite build
npm test           # vitest
npm run lint
```
Fix TypeScript errors properly (correct types), not with blanket `any` or `@ts-ignore`.

## Step 4 - Run and smoke-test
Start the backend: `cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000`
(macOS/Linux: `.venv/bin/python -m uvicorn ...`). Then in another terminal:
```
cd backend && python scripts/smoke_test.py
```
Start the frontend: `cd frontend && npm run dev`, open http://localhost:5173, register, run an analysis
with `data/sample_data/sample_resume.txt` and `data/sample_data/sample_job_description.txt`, and click
through Results, Skill explorer, Roadmap, History, NLP Lab (every tab) and Settings.

## Step 5 - Optional extras
```
python scripts/download_models.py --glove     # enables the GloVe tab and GloVe analogies (~66 MB)
python scripts/run_evaluation.py              # writes docs/evaluation_results.md from real runs
```

## Step 6 - Report to the user
List: what passed, what you fixed (file + reason), anything still failing, and which optional
models are installed. Never claim a model or feature works unless you ran it.
