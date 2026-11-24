# SkillGap-NLP

**A Deep Learning-Based Skill Gap Analysis System for Resumes and Job Descriptions**
B.Tech CSE (AI & ML) project.

SkillGap-NLP compares a resume with a job description, finds which job requirements the resume actually
shows (with the exact supporting sentence), separates real evidence from look-alike wording, computes an
explainable coverage score, and turns the gaps into a personalised learning roadmap. An NLP Lab
demonstrates every technique from the NLP syllabus on the user's own text.

> SkillGap-NLP is a career-development aid. It does not make hiring decisions, never infers protected
> characteristics, and never treats semantic similarity as proof of skill.

---

## 1. Project overview
A full-stack application: React frontend, FastAPI backend, a modular NLP engine and a relational database
(PostgreSQL in production, SQLite for zero-setup development).

## 2. Problem statement
Students apply to jobs without knowing which listed requirements their resume demonstrates. Keyword
checkers cannot tell "Java" in a skills list from two years of Java in production, they miss paraphrases
("built a sentiment classifier" vs "text classification"), and they produce unexplained percentages.
Semantic tools have the opposite failure: they rate related skills (Java vs Python) as matches.

## 3. Objectives
1. Extract text and structure from PDF/DOCX/TXT resumes safely.
2. Extract skills from both documents with a configurable taxonomy (aliases, categories, prerequisites).
3. Match requirements with three methods (keyword, TF-IDF, dense sentence embeddings) and a rule-based hybrid.
4. Classify each requirement as *shown*, *verify*, *related* or *not shown*, citing real resume evidence.
5. Compute a documented, configurable coverage score kept separate from document similarity.
6. Generate a prerequisite-ordered learning roadmap with tracked progress.
7. Demonstrate syllabus techniques (preprocessing, BoW, TF-IDF, VSM, Word2Vec, GloVe, cosine, analogies, PCA, t-SNE).
8. Evaluate methods on a labelled dataset without fabricating results.

## 4. Features
- Upload PDF/DOCX/TXT or paste text; editable extracted text; extension + file-signature validation; OCR guidance for scanned PDFs.
- Section detection (summary, education, experience, projects, skills, certifications) with character offsets.
- 100-skill taxonomy across 18 categories (`data/skill_taxonomy/taxonomy.json`) with aliases, case-sensitive short names (C, R, Go), related skills and prerequisites.
- Must-have vs nice-to-have detection, user overrides, custom/equal weights.
- Hybrid matching with explicit fallback reporting; Java-is-not-Python conflict rule.
- Evidence highlighted in place in the resume; per-requirement explanation, uncertainty and next action.
- User corrections stored separately from original verdicts; coverage and roadmap recomputed.
- Learning roadmap: priority, prerequisites, level, practice project, indicative effort, checklist, curated resources, status tracking.
- Dashboard, paginated history, deletion, JSON export, account deletion, data-retention policy.
- NLP Lab with nine interactive modules and viva explanations.
- Evaluation harness with precision/recall/F1/FPR/latency.

## 5. Technology stack
| Layer | Technologies (and why) |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS v4, shadcn/ui-style components, Framer Motion (expand/entrance), Recharts (charts), React Router, Axios, Zustand (auth state), React Hook Form + Zod (validation), Lucide icons, Sonner (toasts) |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL (psycopg 3) / SQLite, PyJWT (sessions), stdlib scrypt (password hashing) |
| NLP / ML | NLTK (tokeniser, stop words, Porter, WordNet), spaCy (optional lemmatiser), scikit-learn (BoW, TF-IDF, PCA, t-SNE), NumPy, pandas, Gensim (Word2Vec, GloVe), PyTorch + Sentence Transformers + Hugging Face Transformers (all-MiniLM-L6-v2), Matplotlib (evaluation chart) |
| Documents | PyMuPDF (PDF), python-docx (DOCX) |
| Quality / deploy | Pytest, Ruff, Vitest, Testing Library, ESLint, Docker, Docker Compose |

Plotly is not used: Recharts covers the interactive charts in the browser.
shadcn/ui components are written in the shadcn pattern (cva + Tailwind) without Radix to keep dependencies small.

## 6. System architecture
See `docs/architecture.md` for the architecture diagram, data-flow diagram and ER diagram.

```
React SPA ──/api (same-origin proxy, httpOnly cookie)──► FastAPI routes ─► services ─► NLP engine
                                                                    └──► repositories ─► PostgreSQL / SQLite
```

## 7. Folder structure
```
skillgap-nlp/
├── AGENTS.md                 instructions for a coding agent (Antigravity) to install/verify/run
├── backend/
│   ├── app/
│   │   ├── api/routes/       auth, users, analyses (+uploads, roadmap, dashboard), nlp, health
│   │   ├── core/             config, security (scrypt + JWT), errors, logging
│   │   ├── database/         engine + session
│   │   ├── models/           SQLAlchemy tables
│   │   ├── schemas/          Pydantic request/response models
│   │   ├── repositories/     ownership-checked queries
│   │   ├── services/         analysis, users/roadmap/dashboard, NLP lab
│   │   ├── nlp/              extraction, preprocessing, skill_extraction, tfidf, embeddings, similarity,
│   │   │                     skill_gap, explanations, recommendations, visualization, evaluation, pipeline.py
│   │   └── main.py
│   ├── migrations/           Alembic
│   ├── scripts/              download_models, run_evaluation, smoke_test, generate_corpus, purge_expired
│   ├── tests/                pytest (unit + API integration)
│   └── requirements*.txt
├── frontend/src/             pages, components, features (analysis, roadmap, nlp-lab), charts, services, store, tests
├── data/                     skill_taxonomy, learning_resources, sample_data, evaluation, corpus
├── docs/                     architecture, api, methodology, evaluation, user guide, report, viva prep
├── scripts/                  setup.ps1 / setup.sh / run.ps1 / run.sh
├── docker-compose.yml
└── .env.example
```

## 8. Installation (quick)
Prerequisites: **Python 3.11 or 3.12**, **Node.js 18+** (20 LTS recommended), Git. About 2 GB free disk for the deep-learning packages.

Windows:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1      # add -SkipML to skip PyTorch
powershell -ExecutionPolicy Bypass -File scripts\run.ps1
```
macOS / Linux:
```bash
bash scripts/setup.sh            # or: bash scripts/setup.sh --skip-ml
bash scripts/run.sh
```
Open http://localhost:5173 (API docs at http://localhost:8000/docs).

### Manual setup
```bash
cp .env.example .env
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-ml.txt
python scripts/download_models.py          # NLTK data, MiniLM, spaCy model
alembic upgrade head
uvicorn app.main:app --reload --port 8000
# new terminal
cd frontend && npm install && npm run dev
```

## 9. Environment setup
All settings are environment variables (see `.env.example`). Important ones:

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | random per run (dev) | JWT signing key. **Required** when `ENVIRONMENT=production`. |
| `DATABASE_URL` | SQLite in `backend/var/` | e.g. `postgresql+psycopg://user:pass@localhost:5432/skillgap` |
| `AUTO_CREATE_TABLES` | `true` | Dev convenience; set `false` and use Alembic in production |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed browser origins |
| `MAX_UPLOAD_MB` | `5` | Upload limit |
| `STORE_UPLOADED_FILES` | `false` | Keep original files (privately) or only extracted text |
| `RETENTION_DAYS` | `180` | Default retention; users can change theirs |
| `SEMANTIC_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Any Sentence Transformers model |
| `ENABLE_SEMANTIC_MODEL` | `true` | `false` forces TF-IDF fallback |
| `*_THRESHOLD` | see `.env.example` | Uncalibrated similarity thresholds |
| `MUST_HAVE_WEIGHT` / `NICE_TO_HAVE_WEIGHT` | `2` / `1` | Coverage weights |

## 10. Database setup
- **SQLite (default):** nothing to do; `backend/var/skillgap.db` is created.
- **PostgreSQL:** create a database and user, set `DATABASE_URL`, then `cd backend && alembic upgrade head`.
  ```sql
  CREATE USER skillgap WITH PASSWORD 'your-password';
  CREATE DATABASE skillgap OWNER skillgap;
  ```
- New migrations: `alembic revision --autogenerate -m "describe change"`.

## 11. Model installation
| Feature | Needs | How |
|---|---|---|
| Deep semantic matching | torch, sentence-transformers, ~90 MB model | `pip install -r requirements-ml.txt`, `python scripts/download_models.py` |
| Lemmatisation, NLTK tokeniser, stop words | NLTK data | `download_models.py` (falls back to built-ins and says so) |
| spaCy lemmatiser (optional) | `en_core_web_sm` | `download_models.py` |
| Word2Vec CBOW/Skip-Gram | gensim | in `requirements.txt`; trained at first use on the bundled synthetic corpus |
| GloVe + GloVe analogies | ~66 MB pretrained vectors | `python scripts/download_models.py --glove` |

If a model is missing, the UI and API say exactly what is missing and which fallback ran.

## 12. Start the backend
```bash
cd backend && source .venv/bin/activate    # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

## 13. Start the frontend
```bash
cd frontend && npm run dev     # http://localhost:5173 (proxies /api to :8000)
```

## 14. Docker
```bash
cp .env.example .env    # set SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```
Frontend http://localhost:8080, API http://localhost:8000/docs. The backend image bakes in CPU PyTorch,
NLTK data and MiniLM (internet needed at build time) and runs `alembic upgrade head` on start.

## 15. API documentation
Interactive docs at `/docs`. Endpoint reference in `docs/api.md`.

## 16. Example workflow
1. Register, open **New analysis**, upload `data/sample_data/sample_resume.txt`, paste
   `data/sample_data/sample_job_description.txt`, keep *Deep semantic*, run.
2. Results: coverage score, evidence bar, requirement list with evidence highlighted in the resume, method comparison.
3. Open a "not shown" requirement and correct it if the system missed something; coverage updates.
4. Roadmap: mark tasks *Learning* / *Completed*, tick checklist items.
5. NLP Lab: walk through each module during the demo.

## 17. NLP methodology
Summary below; full details in `docs/methodology.md`.
- **Representations kept separate:** original text (evidence offsets), normalised text, tokens, model-ready tokens, skill entities.
- **Skill extraction:** longest-alias-first regex matching with custom boundaries (C ≠ C++, Java ≠ JavaScript), URLs/emails masked, contact header skipped, mention type = demonstrated / listed / mentioned.
- **Matching:** keyword → TF-IDF (unigram+bigram, tech-aware tokeniser) → MiniLM sentence embeddings, cosine similarity.
- **Classification rules:** direct → strong semantic (unless the sentence names a different same-category skill) → related (taxonomy link or moderate similarity) → missing.
- **Coverage:** `Σ weight(accepted) / Σ weight(all) × 100`; only direct matches and user confirmations count by default.

## 18. Model comparison
Every analysis runs keyword, TF-IDF and dense-embedding methods on the same input and reports matched,
related and missing skills, scores, time and limitations (Results page and NLP Lab → Method comparison).
They are different *methods*; only the dense one is a deep learning model.

## 19. Evaluation methodology
`data/evaluation/eval_set.json`: 20 synthetic, author-labelled resume excerpts, 69 labelled requirements.
`python backend/scripts/run_evaluation.py` computes precision, recall, F1, false-positive rate,
skill-extraction precision/recall and latency for each method and writes `docs/evaluation_results.md`.
**No results are included in this repository**: run the script on your machine and report what it prints.
See `docs/evaluation.md` for the protocol and report template.

## 20. Known limitations
- The taxonomy (100 skills) defines what can be recognised; unknown skills are surfaced as "terms outside the taxonomy" but not matched.
- Similarity thresholds are uncalibrated defaults; the evaluation set is small and synthetic.
- Section detection is rule-based and may miss unusual headings; multi-column PDFs can extract in odd order.
- Scanned PDFs need external OCR.
- The Word2Vec demo corpus is tiny and synthetic; its neighbours/analogies are illustrative only.
- Effort estimates are indicative; resource links can go stale.
- Analysis runs synchronously with a timeout; no background job queue.

## 21. Future enhancements
OCR (Tesseract) integration; spaCy custom NER for skills outside the taxonomy; calibrated thresholds from
human-labelled data; cross-encoder re-ranking; fine-tuning on a properly split dataset; multilingual
resumes; background job queue; resource catalog admin UI.

## 22. Troubleshooting
| Problem | Fix |
|---|---|
| "Cannot reach the backend" in the UI | Start the backend on port 8000; check `VITE_BACKEND_URL` |
| Yellow "TF-IDF fallback" notice | Install `requirements-ml.txt` and run `download_models.py` with internet |
| `pip install torch` very large / fails | Use the CPU index URL shown above, or run setup with `-SkipML` |
| "No extractable text" on a PDF | It is scanned; OCR it or paste the text |
| Lemmatizer "unavailable" in the Lab | `python scripts/download_models.py` (downloads WordNet) |
| GloVe tab says not downloaded | `python scripts/download_models.py --glove`, then restart backend |
| Logged out after restarting backend | Set `SECRET_KEY` in `.env` (dev uses a random key per run) |
| PowerShell blocks scripts | Use `powershell -ExecutionPolicy Bypass -File ...` |
| `psycopg` errors on SQLite setups | Harmless unless `DATABASE_URL` points to PostgreSQL |

## 23. Academic syllabus mapping
| Syllabus topic | Where it is implemented | Where to demo |
|---|---|---|
| NLP fundamentals, normalisation | `nlp/preprocessing/pipeline.py` (`normalize`) | Lab → Preprocessing |
| Tokenisation | `tokenize` (tech-aware regex) vs NLTK `word_tokenize` | Lab → Preprocessing |
| Stop-word removal | `remove_stopwords` with protected terms | Lab → Preprocessing |
| Stemming / lemmatisation | Porter (`stem`), WordNet/spaCy (`lemmatize`) | Lab → Preprocessing |
| N-grams, vocabulary, OOV | `ngrams`, `vocabulary_stats`, `oov_analysis` | Lab → Preprocessing |
| Bag of Words | `tfidf/tfidf_matcher.py` (`CountVectorizer`) | Lab → BoW & TF-IDF |
| TF-IDF | `TfidfVectorizer` (1–2 grams), keyword-vs-TF-IDF matcher | Lab, Results → Method comparison |
| Vector space models, sparse vs dense | `services/nlp_lab_service.sparse_vs_dense` | Lab → Sparse vs dense |
| Word2Vec, CBOW, Skip-Gram | `embeddings/word_vectors.py` (Gensim, sg=0/1) | Lab → Word2Vec |
| GloVe | pretrained glove-wiki-gigaword-50 | Lab → GloVe |
| Semantic & cosine similarity | `similarity/cosine.py`, MiniLM in `embeddings/sentence_encoder.py` | Lab → Cosine similarity, every analysis |
| Word analogies | `word_vectors.analogy` | Lab → Analogies |
| PCA | `visualization/projection.py` | Lab → PCA & t-SNE |
| t-SNE | same, fixed seed, perplexity guard | Lab → PCA & t-SNE |
| Deep learning / contextual embeddings | Sentence Transformers (PyTorch) | Every semantic analysis |
| Evaluation | `nlp/evaluation/` + `scripts/run_evaluation.py` | `docs/evaluation.md` |

## Testing
```bash
cd backend && python -m pytest            # unit + API integration (temp SQLite, no internet)
cd frontend && npm test && npm run build
cd backend && python scripts/smoke_test.py   # against a running backend
```
