# Methodology

## 1. Text representations (why they are kept separate)
| Representation | Produced by | Used for |
|---|---|---|
| Original text | extractor (NFKC + control-char cleanup, line structure kept) | Evidence offsets and highlighting. Never modified after extraction. |
| Normalised text | `normalize()` (Unicode, quotes, whitespace) | Human-readable cleaned text, input to tokenisation |
| Tokens | `tokenize()` tech-aware regex | Keeps `C++`, `C#`, `Node.js`, `CI/CD`, `scikit-learn` intact |
| Model-ready tokens | lower-case, punctuation and stop words removed, lemmatised | Bag of Words / TF-IDF |
| Skill entities | taxonomy matcher on the original text | Requirements, candidate skills, evidence |

Aggressive normalisation is deliberately avoided for skills: stemming turns *pandas* into *panda* and
*Kubernetes* into *kubernet*, and lower-casing turns the language **Go** into the verb *go*. Short
ambiguous skill names (C, R, Go, Excel) are matched case-sensitively, and stop-word removal protects
technical terms such as *c*, *r*, *go*, *it*, *ai*.

## 2. Document extraction
PDF (PyMuPDF) and DOCX (python-docx, including tables) are text-extracted only; no scripts or links are
executed. Files are validated by extension *and* signature (`%PDF-`, ZIP header + `word/document.xml`).
Scanned PDFs produce no text and the user is told OCR is required. Sections are detected from short
heading lines matched against a dictionary of known headings; each sentence/bullet keeps character offsets.

## 3. Skill extraction (hybrid)
1. **Phrase matching:** every alias in the taxonomy compiled to a regex with custom boundaries
   (left: no letter/digit/`+#.`; right: no letter/digit/`+#&`), longest alias first, overlapping matches
   suppressed. Spaces in aliases also match hyphens.
2. **Normalised matching:** URLs and emails are masked with spaces (offsets preserved) so `github.com/…`
   is not a skill; the contact header is skipped.
3. **Statistical features:** high-TF-IDF job-ad terms outside the taxonomy are shown for manual review,
   never silently added.
4. **Semantic matching** of terminology happens in the matching stage.
5. **Mention type:** *demonstrated* (experience/projects section, or an action verb such as built/trained
   outside summary/education/skills), *listed* (skills section only), *mentioned* (elsewhere).

Requirement importance: a sentence with a cue such as "nice to have", "preferred", "bonus", "a plus", or a
nearby heading containing one, is *nice-to-have*; everything else is *must-have*; must-have wins on
duplicates; user overrides always win.

## 4. Matching methods
- **Keyword:** canonical/alias present in the resume.
- **TF-IDF:** for each requirement, the lexical phrase (name + aliases) and all resume sentences are
  vectorised together (unigrams + bigrams, sublinear tf, smooth idf, L2 norm); score = max cosine.
- **Dense semantic:** `all-MiniLM-L6-v2` (6-layer MiniLM, 384-d, mean pooling, trained contrastively on
  1B+ sentence pairs). Query = "Skill: description" from the taxonomy; score = max cosine over resume
  sentences. Model loaded once per process, embeddings cached, batched encoding.

## 5. Classification rules (deterministic)
```
if skill or alias is named in resume                      -> direct_match
else s = max similarity over resume sentences (dense, or TF-IDF fallback)
     if s >= strong and best sentence does NOT name another skill of the same category
                                                          -> strong_semantic   (needs verification)
     elif s >= related or a taxonomy-related skill is present
                                                          -> related           (transferable)
     else                                                 -> missing / unverified
```
Defaults: dense strong 0.60 / related 0.45; TF-IDF strong 0.20 / related 0.10. The TF-IDF values were
set from the score range seen on the bundled sample resume (true matches ≈ 0.10–0.31), not tuned on the
evaluation set. All thresholds are configurable and uncalibrated.

If the dense model is unavailable the TF-IDF backend is used and `model_info.fallback_used = true` with
the reason; the UI shows a warning banner.

## 6. Scoring
```
coverage          = Σ weight(requirements with accepted evidence) / Σ weight(all requirements) × 100
must-have coverage = same, restricted to must-have requirements
accepted evidence = direct_match, or a user correction to direct_match
                    (+ strong_semantic only if the user enables it)
weights           = must-have 2, nice-to-have 1 (or equal weights, or custom per skill)
```
Document similarity (TF-IDF and mean-pooled sentence embeddings) is reported separately and never
merged into coverage. No composite score is produced.

## 7. Explanations
Template-based and deterministic: every sentence is filled from the actual result (matched text,
section, similarity, backend, related skills). No language model is used, so no evidence can be invented.

## 8. Roadmap
Gaps (everything not direct after corrections) become tasks. Priority: must-have + missing = high;
must-have + related/verify or nice-to-have + missing = medium; nice-to-have + related/verify = low.
Order: Kahn topological sort over prerequisite links between tasks, ties broken by priority then weight.
Projects, effort ranges and resources come from `data/learning_resources/catalog.json` (curated, labelled
as suggestions). Status changes are logged in `learning_progress` and never change verified coverage.

## 9. NLP Lab
Word2Vec is trained on a deterministic synthetic corpus (742 sentences, seed 42, `workers=1`,
`min_count=2`, 200 epochs). GloVe uses Stanford's pretrained `glove-wiki-gigaword-50`. PCA and t-SNE use
scikit-learn with fixed seeds; perplexity is reduced automatically when larger than the number of points.

## 10. Fairness and privacy
No protected attribute is extracted or inferred; contact information is detected only as present/absent
and is excluded from matching. The system ranks no candidates and makes no hiring decision.
