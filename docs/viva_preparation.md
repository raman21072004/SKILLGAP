# Viva preparation

Answers are written to be technically accurate for this implementation. Practise saying them in your own words.

### Project-level
**Q. What does your project do in one sentence?**
It compares a resume with a job description, shows for every requirement whether the resume demonstrates
it with the exact supporting sentence, scores coverage with an explicit formula, and turns gaps into a
learning roadmap.

**Q. Where is the deep learning?**
In the semantic matcher: a pretrained Sentence Transformer (all-MiniLM-L6-v2, a 6-layer distilled
transformer run with PyTorch) encodes skill descriptions and resume sentences into 384-dimensional
vectors; cosine similarity between them detects paraphrases. We use it for inference only; we did not
fine-tune it because we have no large labelled dataset, and fine-tuning on a tiny set would overfit.

**Q. Why not just use the transformer for everything?**
Similarity is not proof. Embeddings place Java and Python close together, so the final verdict combines
exact taxonomy matches (high precision), similarity (recall) and rules — for example a sentence that names
a different programming language cannot validate Python.

**Q. How is the score calculated?**
Coverage = sum of weights of requirements with accepted evidence ÷ sum of all weights × 100. Must-haves
weigh 2 and nice-to-haves 1 by default. Only direct matches and user-confirmed items count. Document
similarity is shown separately and is never mixed into it.

**Q. What are the four classifications?**
Direct match (named in the resume), strong semantic (similar sentence ≥ threshold, needs verification),
related (a taxonomy-related skill is present or moderate similarity), missing/unverified.

### Preprocessing
**Q. Stemming vs lemmatisation?**
Stemming applies rules to chop suffixes (Porter: "studies" → "studi") and may produce non-words.
Lemmatisation uses a dictionary and part of speech to return the base form ("studies" → "study").
**Q. Why don't you stem before matching skills?**
It damages technical terms: "pandas" → "panda", "Kubernetes" → "kubernet". We keep original text for
skills and evidence, and only use reduced forms for BoW/TF-IDF demos.
**Q. Why a custom tokenizer?**
Standard tokenizers split "C++" into "C", "+", "+" and "Node.js" at the dot. Our regex keeps them whole.
**Q. What is OOV?**
Out-of-vocabulary: a token not in the model's vocabulary. Static embeddings have no vector for it; we
report OOV words and map them to <UNK> in the Lab. Sentence transformers avoid most OOV via sub-word tokens.

### Vector space models
**Q. Bag of Words limitation?**
Ignores order and meaning; each word is an independent dimension, so synonyms are orthogonal; vectors are
large and sparse.
**Q. TF-IDF formula?**
tf-idf(t,d) = tf(t,d) × idf(t), with scikit-learn's smooth idf = ln((1+N)/(1+df)) + 1; we use sublinear tf
(1 + ln tf) and L2-normalise rows.
**Q. Sparse vs dense?**
Sparse: dimension = vocabulary size, mostly zeros, interpretable. Dense: fixed small dimension (384),
nearly all non-zero, captures semantics, not interpretable per dimension.

### Embeddings
**Q. CBOW vs Skip-Gram?**
CBOW predicts the centre word from the averaged context; faster, better for frequent words. Skip-Gram
predicts each context word from the centre word; slower, better for rare words and small data.
**Q. Word2Vec vs GloVe?**
Word2Vec learns from local context windows with a predictive objective (negative sampling). GloVe fits
vectors to the global co-occurrence matrix: w_i·w_j + b_i + b_j ≈ log X_ij.
**Q. Is your Word2Vec good?**
No — it is trained on a 742-sentence synthetic corpus purely to demonstrate the algorithm. We say so in
the UI. The matching engine uses the pretrained sentence transformer instead.
**Q. Why do analogies fail sometimes?**
They depend on the training data; small corpora don't encode consistent relation directions. Pretrained
GloVe usually solves king − man + woman ≈ queen.

### Similarity and visualisation
**Q. Why cosine and not Euclidean distance?**
Cosine depends only on direction, so document length doesn't dominate; for L2-normalised vectors they are
monotonically related (‖a−b‖² = 2 − 2cos).
**Q. How did you choose thresholds?**
They are uncalibrated defaults; TF-IDF thresholds were set from the score range on the sample resume. The
right way is to tune them on a separate validation set and report on the test set.
**Q. PCA vs t-SNE?**
PCA is linear, deterministic, preserves global variance, reports explained variance. t-SNE is non-linear,
stochastic (we fix the seed), preserves local neighbourhoods; distances between clusters are not
meaningful; perplexity must be smaller than the number of points.

### Evaluation
**Q. How did you evaluate?**
On a 20-case, 69-label synthetic, author-labelled dataset with precision, recall, F1, false-positive rate
and latency per method (`scripts/run_evaluation.py`). We report only numbers from actual runs and state
that the dataset is synthetic and small.
**Q. Which metric matters most here?**
False positives are worse (crediting a skill the candidate doesn't show), so precision/FPR matter, but
recall matters for paraphrases — hence the hybrid with a "verify" class.
**Q. What would you do with more time?**
Human-labelled data with two annotators and Cohen's kappa, threshold calibration, a cross-encoder
re-ranker, spaCy NER for skills outside the taxonomy, OCR.

### Engineering, security and ethics
**Q. How are passwords stored?** scrypt with a random salt; verification uses constant-time comparison.
**Q. Where is the token stored?** In an httpOnly SameSite=Lax cookie, so JavaScript (and XSS) can't read it.
**Q. How do you stop users reading others' data?** Every query filters by the logged-in user's id; other
users' ids return 404.
**Q. How do you validate uploads?** Extension allow-list, magic bytes, size cap while reading,
server-generated file names (no path traversal), text-only extraction, files not stored by default.
**Q. Ethical concerns?** Bias in job ads and taxonomies, over-trusting scores. We infer no protected
characteristics, never rank candidates, show evidence for every verdict, and label the tool as a
career-development aid.
**Q. Why FastAPI?** Type-hinted request validation with Pydantic, automatic OpenAPI docs, and Python —
the same language as the NLP stack.
**Q. Why separate the NLP engine from the API?** It can be unit-tested without a server or database,
reused by the evaluation script, and explained module by module.
