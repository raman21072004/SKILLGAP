# API reference

Base URL: `http://localhost:8000`. Interactive docs: `/docs` (Swagger) and `/redoc`.
Authentication: the session cookie set by login/register, or `Authorization: Bearer <access_token>`.
Errors always have the shape `{"error": {"code": "...", "message": "...", "details": [...]|null}}`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/health` | - | Database status and semantic-model status |
| POST | `/api/auth/register` | - | `{email, full_name, password}` → user + token (sets cookie) |
| POST | `/api/auth/login` | - | `{email, password}` → user + token (sets cookie) |
| POST | `/api/auth/logout` | - | Clears the cookie |
| GET | `/api/auth/me` | ✓ | Current user |
| PATCH | `/api/users/me` | ✓ | `{full_name?, preferences?}`; preferences: `default_mode`, `count_strong_semantic`, `equal_weights`, `retention_days` |
| POST | `/api/users/me/delete` | ✓ | `{password}` → deletes the account and all data |
| GET | `/api/users/me/export` | ✓ | All personal data as JSON |
| GET | `/api/users/me/privacy` | ✓ | Retention and storage statement |
| POST | `/api/resumes/upload` | ✓ | multipart `file` (pdf/docx/txt ≤ MAX_UPLOAD_MB) → `{resume_id, text, sections, ...}` |
| POST | `/api/analyses` | ✓ | Run and store an analysis (body below) |
| GET | `/api/analyses?page=&page_size=` | ✓ | Paginated history |
| GET | `/api/analyses/{id}` | ✓ | Full analysis detail |
| DELETE | `/api/analyses/{id}` | ✓ | Delete analysis and dependent records |
| GET | `/api/analyses/{id}/skills` | ✓ | Requirements, candidate skills, coverage |
| PATCH | `/api/analyses/{id}/matches/{match_id}` | ✓ | `{corrected_classification: direct_match|strong_semantic|related|missing|null, comment?}` |
| GET | `/api/analyses/{id}/roadmap` | ✓ | Ordered tasks + self-reported progress |
| GET | `/api/analyses/{id}/export` | ✓ | Analysis JSON |
| PATCH | `/api/roadmap/tasks/{task_id}` | ✓ | `{status?: not_started|learning|practiced|completed, checklist_done?: [int]}` |
| GET | `/api/dashboard` | ✓ | Counts, averages, recent analyses, frequently missing skills, roadmap status |
| GET | `/api/nlp/preprocessing?text=&lowercase=&remove_stopwords=&lemmatize=&ngram_n=` | ✓ | Step-by-step preprocessing |
| POST | `/api/nlp/bow` | ✓ | `{doc_a, doc_b}` Bag-of-Words matrix + sparsity |
| POST | `/api/nlp/tfidf` | ✓ | `{doc_a, doc_b}` top terms, IDF, TF-IDF vs BoW cosine |
| POST | `/api/nlp/vectors` | ✓ | `{text, corpus[]}` sparse TF-IDF vs dense embedding |
| POST | `/api/nlp/word2vec` | ✓ | `{words[], architecture: cbow|skipgram}` |
| POST | `/api/nlp/word2vec/compare` | ✓ | `{words[], window, vector_size}` CBOW vs Skip-Gram |
| POST | `/api/nlp/glove` | ✓ | `{words[]}` (503 `glove_missing` if not downloaded) |
| POST | `/api/nlp/analogy` | ✓ | `{model, positive[], negative[]}` |
| POST | `/api/nlp/similarity` | ✓ | `{text_a, text_b}` cosine breakdown (TF-IDF and dense) |
| POST | `/api/nlp/visualize` | ✓ | `{source, method: pca|tsne, items[], perplexity, seed}` |
| POST | `/api/nlp/compare-models` | ✓ | `{resume_text, job_description}` method comparison |
| GET | `/api/nlp/models/status` | ✓ | Word2Vec / GloVe / sentence-transformer availability |
| GET | `/api/nlp/taxonomy` | - | Skill taxonomy |

## POST /api/analyses
```json
{
  "resume_id": 12,                 // from /api/resumes/upload, or omit and send resume_text
  "resume_text": "optional pasted or edited text",
  "job_description": "full job ad (>= 30 chars)",
  "job_title": "Junior NLP Engineer",
  "target_role": "Junior NLP Engineer",
  "mode": "semantic",              // keyword | tfidf | semantic
  "must_have_skills": ["Python"],
  "nice_to_have_skills": ["AWS"],
  "custom_weights": {"Python": 3},
  "equal_weights": false,
  "count_strong_semantic": false
}
```

## Requirement object (inside analysis detail)
| Field | Meaning |
|---|---|
| `canonical`, `category`, `importance`, `weight` | The requirement |
| `classification` | Original system verdict |
| `user_classification` | User correction or null |
| `effective_classification` | What the UI and score use |
| `exact_match` | Named in the resume (alias match) |
| `tfidf_similarity`, `semantic_similarity` | Best cosine against any resume sentence (null if not computed) |
| `similarity_backend` | `sentence-transformer (model)` or `tf-idf` (fallback) |
| `evidence` | `{text, section, start, end, match_start, match_end, kind: exact|semantic|related, strength}` — always a real resume passage |
| `explanation`, `next_action`, `uncertainty` | Deterministic template text |

## Error codes (selection)
`validation_error` 422, `unauthorized` 401, `invalid_credentials` 401, `email_taken` 409, `not_found` 404,
`unsupported_file_type` / `invalid_signature` / `no_extractable_text` 422, `file_too_large` 413,
`analysis_timeout` 504, `glove_missing` / `gensim_missing` / `model_unavailable` 503, `too_few_points` 400.
