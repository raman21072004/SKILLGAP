# SkillGap-NLP — Complete Presentation & Viva Preparation Guide
**Course:** CSE-472 · Deep Learning for Natural Language Processing (Section K2P24KB)  
**Presenters:** Vaibhav Markandey (`12409100`) & Raman Kumar (`12414116`)  
**Faculty:** Prof. Sufanpreet Kaur  
**Project:** SkillGap-NLP — *An Explainable Deep Learning Approach to Skill Gap Analysis Between Resumes and Job Descriptions*

> **How to use this guide tonight (60–90 minutes):**
> 1. Do the **Urgent 5-Minute Fixes** below (your PPTX Slide 8 and IEEE Paper still have placeholder cells!).
> 2. Read **Part 1** to understand every Deep Learning & NLP concept in plain English.
> 3. Practice **Part 3 (Slide-by-Slide Script)** out loud once or twice.
> 4. Rehearse the **3-Minute Live Demo (Part 4)** once on your laptop.
> 5. Skim **Part 5 (Professor Q&A)** and keep **Part 6 (Cheat Sheet)** open before your turn.

---

## 0. URGENT: Fixes Checked & Found in Your Slides & Paper

Before tomorrow's presentation, fix these **3 real placeholders** that we found when checking `paper_and_slides/`:

### Fix 1 — PPTX Slide 8 (`[run]` placeholders)
Slide 8 currently shows `[run]` in the **Dense MiniLM** and **Hybrid rules** rows. Replace them with the **real measured numbers** from `docs/evaluation_results.md`:

| Method | Precision | Recall | F1 | False pos. rate |
|---|---:|---:|---:|---:|
| Keyword | 0.962 | 0.610 | 0.746 | 0.036 |
| TF-IDF | 1.000 | 0.073 | 0.136 | 0.000 |
| **Dense MiniLM** | **1.000** | **0.098** | **0.178** | **0.000** |
| **Hybrid rules** | **0.963** | **0.634** | **0.765** | **0.036** |

Also update the footnote date on Slide 8 if desired (measured on CPU with `sentence-transformers/all-MiniLM-L6-v2`, mean latency `697.06 ms/case`, skill extraction F1 `0.935`).

### Fix 2 — PPTX Slide 7 (Test count is even better now!)
Slide 7 currently says: `50 engine tests pass; API suite runs locally`.  
You can update it (or state aloud) to: **`65 backend + 10 frontend tests (75 total) pass locally`**, plus full end-to-end smoke test passing.

### Fix 3 — IEEE Paper (`SkillGap-NLP_IEEE_Paper.docx` / `.pdf`)
If you are also submitting or showing the paper:
- **Page 1 (Author affiliation):** Still says `[University name], India` under both names — replace with your actual university name (e.g., *Lovely Professional University, India*).
- **Page 3 (Table II):** Still has `—` dashes for **Dense MiniLM** and **Hybrid rules** — fill in the exact table above (`TP/FP`: Dense MiniLM = `4/0`, Hybrid = `26/1`).
- **Page 3 (Fig. 2):** You can replace the 2-bar chart with the generated 4-method chart in `docs/evaluation_chart.png`.

---

## Part 1: Deep Learning in NLP — Explained From Scratch

You do **not** need heavy math to explain this well. Understand the **story of NLP evolution** — your project literally walks through all 4 eras of NLP!

```
Era 1: Rules & Keywords    -> Exact string matching (fast, strict, blind to paraphrases)
Era 2: Classical Vector NLP -> Bag of Words & TF-IDF (word counts & rarity, still no meaning)
Era 3: Static Embeddings    -> Word2Vec & GloVe (dense meaning vectors, 1 vector per word)
Era 4: Deep Transformers    -> BERT -> Sentence-BERT -> all-MiniLM-L6-v2 (context-aware sentence meaning)
```

---

### 1.1 Text Preprocessing (Turning Raw Text into Clean Input)

Computers cannot read English directly — they only understand numbers. Preprocessing cleans text before converting it to numbers.

| Concept | Plain-English Meaning | Example | How Our Project Uses It |
|---|---|---|---|
| **Normalization** | Fix messy spacing, curly quotes (`“ ”`), dashes (`–`), Unicode inconsistencies (NFKC). | `"Machine  Learning – “NLP”"` → `'Machine Learning - "NLP"'` | Done first while keeping line structure intact. |
| **Tokenization** | Splitting text into pieces (tokens/words). | `"Built APIs in C++"` → `["Built", "APIs", "in", "C++"]` | **Custom tech-aware regex** so `C++`, `C#`, `Node.js`, `CI/CD`, `scikit-learn` don't get broken apart! |
| **Stop-word removal** | Removing very common low-information words (`the`, `is`, `and`, `of`). | `"the model in python"` → `["model", "python"]` | **Protects tech terms** (`c`, `r`, `go`, `it`, `ai`) so they are never accidentally deleted! |
| **Stemming (Porter)** | Crude rule-based chopping of word endings. Fast, sometimes produces fake words. | `"studies"` → `"studi"`, `"developers"` → `"develop"` | Shown in **NLP Lab only**. **NOT** used for skill matching because `"pandas"` becomes `"panda"` and `"Kubernetes"` becomes `"kubernet"`! |
| **Lemmatization** | Dictionary + grammar-aware conversion to the real base word (lemma). | `"studies"` → `"study"`, `"better"` → `"good"` | Uses NLTK WordNet (or spaCy `en_core_web_sm` fallback) for BoW/TF-IDF representations. |
| **N-grams** | Contiguous sequences of `n` tokens (unigrams = 1 word, bigrams = 2 words). | Bigrams of `"deep learning model"` → `["deep learning", "learning model"]` | TF-IDF uses **unigrams + bigrams (1–2 grams)** so `"machine learning"` stays together as one feature. |
| **OOV (Out-of-Vocabulary)** | A word a model has never seen during training. | `"blockchainz"` → `<UNK>` | Static models (Word2Vec/GloVe) have no vector for OOV words. Transformers avoid OOV using **subword tokenization** (WordPiece). |

> **Key Design Point to Say in Viva:** We keep **separate text representations** — we NEVER destroy the original resume text, because we need exact character offsets (`start`, `end`) to highlight the real evidence sentence in the UI!

---

### 1.2 Classical Vector Space Models: Bag of Words (BoW) & TF-IDF

#### Bag of Words (BoW)
- Build a vocabulary of all unique words across documents.
- Represent each document as a vector of **word counts**.
- **Problems with BoW:**
  1. Ignores word order (*"dog bites man"* = *"man bites dog"*).
  2. Common words dominate counts.
  3. **Huge & Sparse** (mostly zeros — e.g., 10,000 dimensions with only 15 non-zeros).
  4. **Zero semantic understanding:** `"Python"` and `"Flask"` or `"classifier"` and `"text classification"` are completely orthogonal (zero overlap!).

#### TF-IDF (Term Frequency – Inverse Document Frequency)
Improves BoW by giving **higher weight** to words that appear frequently in *this* document (**TF**) but rarely across *other* documents (**IDF**).

- **Formula (scikit-learn smooth IDF + sublinear TF used in our code):**
  $$\text{tf}(t, d) = 1 + \ln(\text{count}(t, d))$$
  $$\text{idf}(t) = \ln\!\left(\frac{1 + N}{1 + \text{df}(t)}\right) + 1$$
  $$\text{tfidf}(t, d) = \text{tf}(t, d) \times \text{idf}(t), \quad \text{followed by } L_2 \text{ normalization}$$
- **Why TF-IDF alone fails on resumes:** A skill query is very short (`"Text Classification"`) while a resume bullet is longer and paraphrased (`"Trained an LSTM model in PyTorch to classify movie reviews as positive or negative"`). Because they share almost no exact words, TF-IDF cosine stays tiny (in our evaluation, TF-IDF recall was only **7.3%**!).

#### Sparse vs. Dense Vectors (Classic Exam/Viva Question!)
| Property | Sparse Vector (BoW / TF-IDF) | Dense Vector (Word2Vec / GloVe / MiniLM) |
|---|---|---|
| **Size (Dimensions)** | Equal to vocabulary size (hundreds to 100,000+) | Fixed & small (50-d for GloVe/W2V, **384-d** for MiniLM) |
| **Values** | Mostly `0` (e.g., 95%+ zeros) | Almost all non-zero floating-point numbers |
| **Meaning / Synonyms** | No (`"car"` and `"automobile"` have 0 similarity) | Yes (similar meanings point in similar directions) |
| **Interpretability** | High (each column = a specific word) | Low (individual numbers are latent learned features) |

---

### 1.3 Static Neural Word Embeddings: Word2Vec & GloVe

> **Core Idea — The Distributional Hypothesis (J. R. Firth, 1957):**  
> *"You shall know a word by the company it keeps."*  
> If `"PyTorch"` and `"TensorFlow"` keep appearing in sentences like *"Trained a neural network in ___"*, a neural network learns to place their vectors close together!

#### Word2Vec (Mikolov et al., 2013)
A shallow neural network trained on sliding context windows around words:
1. **CBOW (Continuous Bag of Words, `sg=0`):**
   - **Input:** Surrounding context words → **Predicts:** Center word.
   - Example: `["trained", "a", ___, "in", "pytorch"]` → predicts `"model"`.
   - **Trait:** Averages context; faster to train; smoother for frequent words.
2. **Skip-Gram (`sg=1`):**
   - **Input:** Center word → **Predicts:** Each surrounding context word.
   - Example: `"pytorch"` → predicts `"trained"`, `"model"`, `"neural"`, `"gpu"`.
   - **Trait:** Slower, but **better for rare words and small corpora**.
3. **Negative Sampling (`negative=5` in our code):** Instead of updating weights for every word in the vocabulary (expensive softmax), the network only pushes the real context word closer and 5 randomly sampled "wrong" words farther away.

#### GloVe (Global Vectors — Pennington, Socher & Manning, 2014)
- Word2Vec only sees **local sliding windows** one sentence at a time.
- **GloVe** first builds a **global word–word co-occurrence count matrix** $X_{ij}$ over the entire corpus (e.g., Wikipedia + Gigaword, 6 billion tokens), then learns vectors via matrix factorization so that:
  $$w_i \cdot w_j + b_i + b_j \approx \log X_{ij}$$
- **Word Analogies (Linear Substructure):** Because directions encode semantic relationships:
  $$\vec{\text{king}} - \vec{\text{man}} + \vec{\text{woman}} \approx \vec{\text{queen}}$$
  *(Verified live in our installed `glove-wiki-gigaword-50`: returns `queen` with cosine similarity **0.8524**!)*

#### Limitations of Static Embeddings (Why We Needed Transformers!)
1. **One vector per word (No Polysemy):** `"Python"` (programming language) and `"python"` (snake) — or `"Java"` (language) and `"Java"` (island) — get the exact same static vector regardless of sentence context!
2. **Word-level only:** Averaging word vectors for a whole sentence loses grammar and phrasing.
3. **OOV problem:** If a new tool name wasn't in the training vocabulary, static embeddings fail.

> **Honest Project Note (Important for Prof. Kaur!):**  
> In our project, **Word2Vec and GloVe are ONLY in the NLP Lab** to demonstrate the course syllabus. Our Word2Vec is trained on a small 742-sentence synthetic tech corpus (`data/corpus/tech_corpus.txt`), so we explicitly tell users it's educational, not production quality. The **actual resume matching engine** uses a pretrained **Transformer (Sentence-BERT / MiniLM)**.

---

### 1.4 Deep Learning & Transformers: BERT → Sentence-BERT → `all-MiniLM-L6-v2` (THE CORE OF CSE-472!)

This is the most important part for a **Deep Learning in NLP** presentation. Understand these 4 steps cleanly:

#### Step 1: What is a Transformer & Self-Attention?
- Older sequence models (RNNs / LSTMs) read sentences **one word at a time**, left-to-right, struggling with long sentences and slow to parallelize.
- **Transformers (Vaswani et al., 2017 — "Attention Is All You Need")** read **all words at once** using **Self-Attention**.
- **Self-Attention in one sentence:** Every word computes an attention score with every other word in the sentence so its representation absorbs context.
  - Example: In *"Trained a classifier that labels reviews as positive or negative"*, `"classifier"` attends strongly to `"labels"`, `"reviews"`, `"positive"`, `"negative"` — producing a deep contextual representation that means *sentiment / text classification*!
- **Subword Tokenization (WordPiece):** Splits unseen words into known pieces (e.g., `"FastAPI"` → `["fast", "##api"]`), largely solving the OOV problem.

#### Step 2: BERT (Devlin et al., 2018)
- **Bidirectional Encoder Representations from Transformers**: reads context from **both left and right** simultaneously.
- Pretrained on massive text using Masked Language Modeling (predicting hidden words).
- **Problem for Retrieval / Matching:** Standard BERT is a **Cross-Encoder** — to compare 22 job requirements against 25 resume sentences, you'd have to run BERT $22 \times 25 = 550$ separate times! Way too slow. Also, raw BERT sentence embeddings are poorly aligned for cosine similarity.

#### Step 3: Sentence-BERT / SBERT (Reimers & Gurevych, 2019)
- Fine-tunes a Transformer using a **Siamese / Bi-Encoder architecture**:
  - Pass Sentence A through the Transformer → **Mean Pooling** (average all token vectors) → Vector $u$.
  - Pass Sentence B through the **same** Transformer (shared weights) → **Mean Pooling** → Vector $v$.
  - Train with **Contrastive Learning** on millions/billions of text pairs so semantically similar sentences get high cosine similarity and unrelated sentences get low cosine similarity.
- **Huge Speed Win:** Encode 22 requirements once + 25 resume sentences once = only **47 forward passes** (not 550!), then compute all $22 \times 25$ similarities with a single instant matrix multiply (`qn @ sn.T`)!

#### Step 4: `all-MiniLM-L6-v2` (Wang et al., 2020) — Our Exact Model!
- **MiniLM = Deep Self-Attention Distillation:** A smaller "student" Transformer is trained to mimic the self-attention behavior of a much larger "teacher" Transformer.
- **Exact specs in our project:**
  - **Architecture:** 6 Transformer layers (`L6`), ~22M parameters (~90 MB download)
  - **Output size:** **384-dimensional** L2-normalized dense vector per sentence
  - **Training:** Contrastively fine-tuned on **1 billion+ sentence pairs**
  - **Runtime:** Runs smoothly on **CPU** via PyTorch + `sentence-transformers` (loaded in **1.84 seconds** on our machine; cached per process + LRU embedding cache so repeated sentences aren't re-encoded!).
  - **Inference only (Zero-shot):** We did **not** fine-tune MiniLM because we don't have thousands of human-labelled resume pairs, and fine-tuning a 22M-parameter transformer on 69 synthetic labels would severely **overfit**.

---

### 1.5 Cosine Similarity (How Vectors Are Compared)

Given two vectors $a$ and $b$:
$$\cos(a, b) = \frac{a \cdot b}{\|a\|\,\|b\|}$$

- **Range:** `-1` (opposite) to `+1` (identical direction); for TF-IDF (non-negative), `0` to `1`.
- **Angle intuition:**
  - Angle = $0^\circ \Rightarrow \cos = 1.0$ (exact same direction/meaning)
  - Angle = $90^\circ \Rightarrow \cos = 0.0$ (orthogonal / unrelated)
- **Why Cosine instead of Euclidean distance?**
  - Euclidean distance is skewed by **document length** (a long paragraph has bigger vector magnitude than a short phrase).
  - Cosine measures only the **angle (direction)**, ignoring length!
  - And when vectors are L2-normalized ($\|a\|=\|b\|=1$), cosine similarity simplifies to a fast **dot product** ($a \cdot b$), and Euclidean distance is monotonically tied to it ($\|a-b\|^2 = 2 - 2\cos(a,b)$).

---

### 1.6 Visualizing High-Dimensional Embeddings: PCA vs. t-SNE

Humans can't see in 50-D (GloVe/Word2Vec) or 384-D (MiniLM), so we project vectors to **2-D** in the NLP Lab:

| Property | PCA (Principal Component Analysis) | t-SNE (van der Maaten & Hinton, 2008) |
|---|---|---|
| **Type** | **Linear** projection | **Non-linear** manifold projection |
| **Deterministic?** | **Yes** (same input → exact same plot) | **No / Stochastic** (we fix `seed=42` for reproducibility) |
| **What it preserves** | **Global variance** (overall spread & big distances) | **Local neighborhoods** (keeps nearby points close) |
| **Key Metric / Parameter** | Reports **Explained Variance %** (how much information was kept) | Uses **Perplexity** (must be `< number of points`; our app warns & auto-adjusts!) |
| **Big Caveat to Mention** | Can miss curved non-linear clusters | **Distances between clusters and cluster sizes in t-SNE are NOT meaningful!** |

---

### 1.7 Classification Evaluation Metrics

Here, **Positive = "the resume demonstrates the required skill"**:
- **TP (True Positive):** Candidate demonstrates it, system says YES.
- **FP (False Positive):** Candidate does NOT demonstrate it, system says YES (**COSTLIEST ERROR!** Over-crediting a missing skill misleads the student).
- **FN (False Negative):** Candidate demonstrates it, system says NO (missed paraphrase).
- **TN (True Negative):** Candidate does NOT demonstrate it, system says NO.

$$\text{Precision} = \frac{TP}{TP + FP} \qquad \text{Recall} = \frac{TP}{TP + FN} \qquad F_1 = \frac{2 \cdot P \cdot R}{P + R} \qquad \text{FPR} = \frac{FP}{FP + TN}$$

---

## Part 2: Complete Walkthrough of SkillGap-NLP

### 2.1 One-Sentence Pitch
> *"SkillGap-NLP compares a resume against a job description, classifies every single job requirement with exact sentence-level evidence using a hybrid of taxonomy rules and Sentence-Transformer (`all-MiniLM-L6-v2`) embeddings, computes a transparent weighted coverage score, and builds a prerequisite-ordered learning roadmap."*

### 2.2 The Core Problem (Why Existing Tools Fail)
1. **Keyword / ATS checkers miss too much (Low Recall):**
   - If a resume says *"Trained an LSTM model in PyTorch to classify movie reviews as positive or negative"*, a keyword checker sees **zero overlap** with `"Text Classification"`.
   - Also treats a word dumped in a `SKILLS` list identically to real project experience.
2. **Pure Semantic / Deep Learning matchers credit too much (False Positives):**
   - Because Java and Python appear in nearly identical sentences on the internet, embeddings place them close together. A naive semantic matcher gives high cosine similarity for `"Built backend services in Java"` against `"Python"`!
   - A single opaque number like `"73% Match"` tells a student **nothing** about what to fix.

### 2.3 Our 5-Stage Pipeline (Matches Slide 4 & Paper Fig. 1)

1. **Stage 1 — Secure Document Extraction & Sectioning (`app/nlp/extraction/`)**
   - Supports PDF (`PyMuPDF`), DOCX (`python-docx`, including tables), TXT, or pasted text.
   - Security checks: extension allow-list + **magic-byte signature** (`%PDF-`, ZIP + `word/document.xml`) + 5 MB streaming size cap + scanned-PDF detection (tells user OCR is required rather than silently failing).
   - Splits into sections (`header`, `summary`, `education`, `experience`, `projects`, `skills`, `certifications`) and sentences with **exact character offsets (`start`, `end`)**.
   - Masks URLs and emails with spaces (preserving offsets!) so `github.com/user/react-app` isn't falsely detected as React, and skips the contact header.

2. **Stage 2 — Hybrid Skill & Requirement Extraction (`app/nlp/skill_extraction/`)**
   - Uses a curated **100-skill taxonomy across 18 categories** (`data/skill_taxonomy/taxonomy.json`), each with canonical name, aliases (`k8s` → `Kubernetes`, `postgres` → `PostgreSQL`), related skills, prerequisites, difficulty level, and description.
   - Longest-alias-first custom-boundary regex: prevents `"Java"` matching inside `"JavaScript"`, prevents `"C"` matching inside `"C++"`, prevents `"SQL"` matching inside `"PostgreSQL"`, and matches short ambiguous skills (`C`, `R`, `Go`, `Excel`) **case-sensitively**.
   - Labels candidate mention strength: **`demonstrated`** (in Experience/Projects or with action verbs like *built/trained*), **`listed`** (Skills section only), or **`mentioned`** (elsewhere).
   - Labels JD requirements as **`nice_to_have`** (cue words like *preferred*, *a plus*, *bonus*, *nice to have*) or **`must_have`** (default; weight `2.0` vs `1.0`).
   - Also surfaces high-TF-IDF job terms outside the taxonomy for manual review (never silently invents skills).

3. **Stage 3 — Three Parallel Matching Signals (`app/nlp/skill_gap/analyzer.py`)**
   For every job requirement $r$ against every non-header resume sentence $s$:
   - **Keyword:** Is $r$ (or an alias) in `candidate_skills`?
   - **TF-IDF Cosine:** Vectorize skill name + aliases with all resume sentences (1–2 grams, sublinear TF, smooth IDF, L2 norm), take $\max_s \cos(r, s)$.
   - **Dense Semantic (`all-MiniLM-L6-v2`):** Encode query `"Skill: description"` (e.g., `"Text Classification: assigning labels such as sentiment to text documents"`) and every resume sentence into 384-d vectors, take $\max_s \cos(a_r, a_s)$.
   - **Transparent Fallback:** If PyTorch/MiniLM isn't installed, automatically falls back to TF-IDF and shows a clear warning banner (`fallback_used = true`) — never hides degradation!

4. **Stage 4 — Deterministic Classification Rules + Same-Category Conflict Check**
   Applied strictly in order:
   1. **Direct match (`Shown` — Green):** Skill or alias is explicitly named in the resume. **Counts toward coverage.**
   2. **Strong semantic (`Verify` — Amber):** Not named, but $\max \text{sim} \ge \text{strong threshold}$ (`0.60` dense / `0.20` TF-IDF) **AND** the best-matching sentence does **NOT** name a *different* skill of the **same category**. **Does NOT count toward coverage until the user confirms it!**
   3. **Related (`Related` — Violet):** Either $\max \text{sim} \ge \text{related threshold}$ (`0.45` dense / `0.10` TF-IDF) — *including matches capped by the conflict rule!* — OR a taxonomy-related skill is present in the resume (e.g., `MySQL` for `PostgreSQL`). **Does NOT count.**
   4. **Missing (`Not shown` — Red):** Otherwise. Goes into the learning roadmap.

   > **The Star Rule (Slide 5 — Memorize This!):**  
   > Suppose the job asks for **Python** (category: *Programming Languages*), and the resume says *"Built backend services in Java"*. Even if a semantic model gives a cosine similarity of **0.95**, our code sees that the sentence names **Java**, which is a *different* skill in the same category (*Programming Languages*), so it **caps the verdict at `Related`** instead of `Verify`! (Proven by unit test `test_java_does_not_prove_python`.)

5. **Stage 5 — Explainable Coverage, Deterministic Explanations & Roadmap**
   - **Coverage Formula (never blended with document similarity!):**
     $$\text{Coverage} = 100 \times \frac{\sum_{r \in \text{Accepted}} w_r}{\sum_{r \in \text{All}} w_r}$$
     where $w_r = 2$ (must-have) or $1$ (nice-to-have), and Accepted = `direct_match` + user-confirmed corrections.
   - **Deterministic Explanations:** Template-filled strictly from the actual matched sentence, section, score, and rule — **no LLM generates text**, so it is **impossible to hallucinate fake resume evidence!**
   - **Learning Roadmap (`app/nlp/recommendations/roadmap.py`):** Every non-direct requirement becomes a task with priority (`high` = missing must-have; `medium` = related must-have or missing nice-to-have; `low` = related nice-to-have), ordered via **Kahn's Topological Sort** over skill prerequisites (e.g., `Cloud Computing` comes before `AWS`), paired with curated projects & docs from `data/learning_resources/catalog.json`. Progress tracking (`Not started → Learning → Practiced → Completed`) is **self-reported** and never artificially inflates verified coverage!

---

### 2.4 Exact Walkthrough on the Bundled Sample Resume (`Aarav Sharma` vs `Junior NLP Engineer`)

Know these **real live numbers** from our running app:
- **22 requirements extracted** from `sample_job_description.txt`:
  - **17 Must-Have** ($\times 2 = 34$ weight)
  - **5 Nice-to-Have** ($\times 1 = 5$ weight)
  - **Total Weight = 39**
- **12 Shown (`direct_match`):** `Python`, `SQL`, `Deep Learning`, `PyTorch`, `Docker`, `Machine Learning`, `Natural Language Processing`, `Word Embeddings`, `Communication`, `REST APIs`, `Git`, `Flask` (all must-have → weight $12 \times 2 = \mathbf{24}$)
  - **Exact Coverage:** $24 / 39 \times 100 = \mathbf{61.5\%}$!
- **1 Verify (`strong_semantic`):** **`Text Classification`** — caught by `all-MiniLM-L6-v2` from *"Trained an LSTM model in PyTorch to classify movie reviews as positive or negative; reported precision, recall and F1-score."* (Not counted in `61.5%` until user confirms; if confirmed → $26 / 39 = \mathbf{66.7\%}$!)
- **7 Related:**
  - Must-have: `PostgreSQL` (has `MySQL` + `SQL`), `TensorFlow` (has `PyTorch`), `Transformers` (has `NLP`/LSTM), `FastAPI` (has `Flask` + `REST APIs`)
  - Nice-to-have: `CI/CD`, `Kubernetes`, `MLOps`
- **2 Missing (Nice-to-Have):** `AWS`, `Cloud Computing`
- **Roadmap:** **10 ordered learning tasks** (`Cloud Computing` ordered before `AWS` via topological sort!).

---

### 2.5 Real Evaluation Results & Smart Error Analysis (How to Impress Prof. Kaur!)

On our **20-case, 69-requirement synthetic test set** (`data/evaluation/eval_set.json`, 41 positive, 28 negative — written to test exact mentions, paraphrases, same-category traps, listed-only skills, and sub-tools):

| Method | Precision | Recall | F1 | FPR | TP / FP |
|---|---:|---:|---:|---:|---:|
| Keyword (taxonomy) | 0.962 | 0.610 | 0.746 | 0.036 | 25 / 1 |
| TF-IDF (threshold 0.20) | 1.000 | 0.073 | 0.136 | 0.000 | 3 / 0 |
| Dense MiniLM (threshold 0.60) | 1.000 | 0.098 | 0.178 | 0.000 | 4 / 0 |
| **Hybrid rules** | **0.963** | **0.634** | **0.765** | **0.036** | **26 / 1** |

- **Skill extraction (vs expected lists):** Precision **1.000**, Recall **0.879**, F1 **0.935**.
- **Mean latency:** `697.06 ms/case` (first case includes model loading ~13.3s; subsequent cases are milliseconds!).

#### Deep Error Analysis (Per-Case Gems From `docs/evaluation_results.json`)
If the professor asks *"Why is Dense MiniLM recall only 0.098?"*, **THIS answer will impress them massively:**
1. **Intentional Precision-First Threshold (`0.60`):** Because false positives are worse than misses in career advice, our uncalibrated default threshold (`0.60`) is very strict. At `0.60`, Dense MiniLM achieved **1.000 Precision and 0.000 False Positive Rate** — zero hallucinations!
2. **Real Hybrid Gain (`c11`):** On *"Implemented quicksort, Dijkstra's shortest path and dynamic programming solutions in C++"*, Keyword missed `Algorithms`, while **MiniLM caught `Algorithms` (`strong_semantic`)** — boosting Hybrid Recall (`0.610 → 0.634`) and F1 (`0.746 → 0.765`) with **zero extra false positives**.
3. **Why Many MiniLM Paraphrases Landed in `Related` (`0.45–0.60`) Instead of `Verify` (`>= 0.60`):**
   - Look at `c03` (*"Trained a classifier that labels product reviews as positive or negative..."*): MiniLM scored `Text Classification` in the `0.45–0.60` (`related`) band on that brief 1-sentence excerpt, whereas on the fuller **sample resume** sentence (*"Trained an LSTM model in PyTorch to classify movie reviews..."*) it crossed `>= 0.60` (`Verify`)!
   - Look at `c10` (*"Cleaned and explored a messy census dataset with pandas..."*): Dense MiniLM **DID** score `Data Analysis >= 0.60`, **but** our same-category conflict rule capped it at `Related` because `pandas` is also in the *Data Analysis* category! That shows a real trade-off: the conflict rule stops `Java → Python` false positives, but can occasionally be conservative when a library (`pandas`) and its parent field (`Data Analysis`) share a category.
4. **Keyword's Only False Positive (`c15`):** *"Performed an OWASP Top 10 review of a web app and fixed **SQL injection** and XSS issues."* Keyword matched `"SQL"` inside `"SQL injection"` — proving why keyword matching alone lacks semantic context!
5. **What Calibration Would Fix:** Lowering or calibrating the dense threshold (e.g., around `0.48–0.55` on a *separate* validation split, NOT tuned on the test set!) and distinguishing *parent-field* vs *sibling-tool* conflicts would substantially raise MiniLM & Hybrid recall while preserving low FPR.

---

### 2.6 Architecture & Security Summary (Matches Slide 7)
- **Three-layer architecture:** React 18 + TypeScript + Tailwind v4 + Recharts + Zustand + Zod (`frontend/`) → FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic (`backend/`) → PostgreSQL / SQLite (**12 database tables**; full resume text stored once).
- **Clean separation:** `backend/app/nlp/` has **zero FastAPI or SQLAlchemy imports**, so the NLP engine can be unit-tested independently and reused by `scripts/run_evaluation.py`.
- **Security & Privacy:**
  - Passwords hashed with **`scrypt`** ($N=2^{14}, r=8, p=1$) + random 16-byte salt + constant-time `hmac.compare_digest`.
  - Sessions use **HS256 JWT** inside an **`httpOnly`, `SameSite=Lax` cookie** (immune to XSS `localStorage` theft).
  - Strict **ownership checks** (`user_id` filter on every query; foreign IDs return `404` so data existence never leaks).
  - Resume text is **never logged**; originals are not stored on disk by default; full JSON **Export** and cascading **Account Deletion** are built in.
  - **Ethics:** Infers zero protected attributes (no gender, age, ethnicity, college-tier bias), never ranks candidates, clearly positioned as a **career-development aid, not a hiring judge**.

---

## Part 3: Slide-by-Slide Speaking Script (Slides 1–9)

Target duration: **~8–10 minutes total** (~1 minute per slide) + **3–4 minutes live demo**.  
Speaker assignments below match the notes already inside your `.pptx` (both partners should still understand every slide!).

### Slide 1 — Title (`Vaibhav`, ~40 sec)
- **On screen:** *SkillGap-NLP — Which job requirements does your resume actually prove?*
- **What to say:**
  > "Good morning ma'am and everyone. I am Vaibhav Markandey, along with my teammate Raman Kumar. Our CSE-472 Deep Learning for NLP project is **SkillGap-NLP**. The core question we solve is right on the title: *which requirements of a job description does your resume actually prove?* Rather than giving a black-box score, we show exact evidence for every single skill. Let's look at why existing tools fall short."

### Slide 2 — The Problem (`Vaibhav`, ~55 sec)
- **On screen:** *Resume checkers fail in two opposite ways* (Keyword misses paraphrases vs. Semantic credits Java as Python)
- **What to say:**
  > "Current resume checkers fail in two opposite ways. First, **keyword matchers miss too much**: if a student writes *'Trained a classifier that labels reviews as positive or negative'*, there is zero keyword overlap with *'Text Classification'*. They also treat a skill dumped in a list the same as two years of project work.  
  > Second, **pure deep-learning semantic matchers credit too much**: embeddings place Java and Python very close in vector space, so *'Built backend services in Java'* looks like Python experience — and a single similarity percentage explains nothing.  
  > So our goal was a **hybrid system**: broad enough to catch paraphrases, strict enough to demand real evidence, and transparent enough to cite the exact resume sentence."

### Slide 3 — Output & Four Verdicts (`Raman`, ~60 sec)
- **On screen:** *Every requirement gets a verdict and the sentence behind it* (`Shown`, `Verify`, `Related`, `Not shown`, `61.5%`, PyTorch example)
- **What to say:**
  > "Instead of one opaque score, SkillGap-NLP classifies every single requirement in the job description into one of **four clear verdicts**:
  > - **Shown (Green):** The skill or an alias is explicitly named in the resume — this counts toward coverage.
  > - **Verify (Amber):** No exact keyword, but a resume sentence is semantically similar via our Transformer model — it highlights the sentence and asks the user to confirm.
  > - **Related (Violet):** Only a transferable skill is present, like MySQL when PostgreSQL is required.
  > - **Not shown (Red):** No evidence found — automatically sent to the learning roadmap.  
  > On our sample resume against a Junior NLP Engineer role, weighted coverage is **61.5%** (24 out of 39 weight points), and every shown skill links directly to its real sentence, like this PyTorch project bullet."

### Slide 4 — Five-Stage Pipeline & Architecture (`Raman`, ~65 sec)
- **On screen:** *From two documents to evidence in five stages* (`Read → Extract → Keyword/TF-IDF/MiniLM → Decide → Coverage/Evidence/Roadmap`)
- **What to say:**
  > "Our pipeline runs in five clean stages.  
  > First, **Read**: we validate and extract text from PDF, DOCX, or plain text, detect resume sections, and preserve exact character offsets for every sentence so we can highlight evidence accurately.  
  > Second, **Extract**: a curated 100-skill taxonomy across 18 categories normalizes aliases like `k8s` to `Kubernetes`, respects tricky boundaries like `C++` vs `C`, and separates must-have from nice-to-have job requirements.  
  > Third, **Score**: we run three methods in parallel — exact keyword matching, TF-IDF cosine similarity, and **MiniLM dense sentence embeddings**, which is our deep learning component (a 6-layer distilled Sentence-BERT transformer producing 384-dimensional vectors).  
  > Fourth, **Decide**: deterministic rules combine those signals into one of the four verdicts.  
  > Finally, we output the coverage score, sentence-level explanations, and a prerequisite-ordered roadmap. Architecturally, the NLP engine has zero web or database imports, so it is unit-tested in isolation and reused directly by our evaluation script."

### Slide 5 — Core Contribution: Conflict Rule & Coverage Formula (`Vaibhav`, ~65 sec)
- **On screen:** *Similarity suggests; only evidence counts* (Java→Python rule + Coverage formula + Thresholds)
- **What to say:**
  > "This slide is the heart of our design: **similarity suggests, only evidence counts**.  
  > To block semantic false positives, we enforce a **same-category conflict rule**: if the most similar resume sentence names a *different* skill from the same category, the verdict is capped at **Related**, no matter how high the cosine score is. In our unit test, even when we force a cosine similarity of **0.95** between *'Built backend services in Java'* and *Python*, the system caps it at **Related** rather than falsely crediting Python.  
  > Second, our **coverage score** is a transparent weighted ratio: sum of weights of shown requirements divided by total weight times 100 — must-haves weigh 2, nice-to-haves weigh 1. Verify items only count after the user confirms them, and document-level similarity is shown separately, never blended in. We also state clearly that our thresholds (`0.60/0.45` dense, `0.20/0.10` TF-IDF) are configurable defaults, not yet calibrated."

### Slide 6 — Interactive NLP Lab (`Raman`, ~60 sec)
- **On screen:** *The NLP Lab runs the whole syllabus on your own text* (9 modules)
- **What to say:**
  > "Because this is a Deep Learning for NLP course project, we also built an interactive **NLP Lab** with nine live modules covering the entire syllabus on any text you type:
  > 1. **Preprocessing** (tokenization keeping `C++`/`Node.js`, stopwords, Porter stemming vs. lemmatization, n-grams, and OOV).
  > 2. **Bag of Words & TF-IDF** (count matrix, sparsity, IDF weights, cosine).
  > 3. **Sparse vs. Dense** side-by-side (TF-IDF vs. 384-d MiniLM embedding).
  > 4. **Word2Vec** comparing **CBOW vs. Skip-Gram** with configurable window and vector size.
  > 5. **Pretrained GloVe** (`glove-wiki-gigaword-50`, 400,000 words × 50-d).
  > 6. **Cosine Similarity breakdown** (dot product, vector norms, and angle in degrees).
  > 7. **Word Analogies** (like `king - man + woman = queen`, which returns `queen` at `0.8524` in GloVe, plus explaining why small-corpus Word2Vec fails).
  > 8. **PCA & t-SNE** 2-D projections with explained variance, fixed seed, and perplexity controls.
  > 9. **Method comparison** running keyword, TF-IDF, and MiniLM side by side.  
  > Every tab honestly states which library produced the output and its limitations."

### Slide 7 — Full-Stack Engineering & Security (`Vaibhav`, ~55 sec)
- **On screen:** *A complete web application, not a notebook* (Stack table, ~9,000 lines, features, tests)
- **What to say:**
  > "This is a complete full-stack web application of about 9,000 lines of Python and TypeScript across 10 pages and ~30 API endpoints — not just a Jupyter notebook.  
  > The frontend is React, TypeScript, Tailwind, and Recharts; the backend is FastAPI with SQLAlchemy across 12 tables and Alembic migrations; and the NLP stack combines NLTK, spaCy, scikit-learn, Gensim, PyTorch, and Sentence Transformers.  
  > Users can correct any verdict — we store the correction alongside the original verdict as future evaluation data and immediately recompute coverage and re-sync the roadmap.  
  > Security is built in: `scrypt` salted password hashing, `httpOnly` JWT cookies, per-user ownership checks, magic-byte upload validation, and full JSON export or account deletion. All **65 backend tests** (engine, API, PDF, DOCX, Word2Vec) and **10 frontend tests** — **75 tests total** — plus an end-to-end smoke test pass locally."

### Slide 8 — Evaluation Results (`Raman`, ~70 sec)
- **On screen:** *Keywords are precise but miss 4 in 10 shown skills* (Make sure `[run]` is replaced with real numbers!)
- **What to say:**
  > "We evaluated all four methods on a 20-case, 69-requirement synthetic test set (41 demonstrated, 28 not) with zero tuning on the test set.  
  > - **Keyword matching** achieved high precision (**0.962**, just 1 false positive — matching `SQL` inside `'SQL injection'`) but missed 16 paraphrased or implied skills (**0.610 recall**, **0.746 F1**).
  > - **TF-IDF alone** had **1.000 precision** but only **0.073 recall** (3 of 41) because short skill phrases rarely overlap lexically with longer sentences.
  > - **Dense MiniLM alone** at our strict `0.60` threshold achieved **1.000 precision** and **0.000 false-positive rate**, with **0.098 recall** (`0.178 F1`) — showing how conservative the `0.60` cutoff is.
  > - **Hybrid rules** combined both to reach the best overall result: **0.963 precision**, **0.634 recall**, **0.765 F1**, and **0.036 FPR** — catching paraphrased skills like *Algorithms* (from quicksort, Dijkstra, and DP) with zero extra false positives.  
  > Skill extraction itself reached **1.000 precision, 0.879 recall, and 0.935 F1**. We emphasize honestly that this dataset is small and synthetic, so these numbers illustrate relative method behavior rather than real-world hiring accuracy."

### Slide 9 — Ethics, Limitations & Future Work (`Vaibhav`, ~50 sec)
- **On screen:** *A career aid that shows its evidence, never a hiring judge*
- **What to say:**
  > "To conclude, SkillGap-NLP is intentionally designed as a **career-development aid for students, never an automated hiring judge**. It infers no protected traits, never ranks candidates, never logs resume text, and gives users full export and deletion control.  
  > We are transparent about our current limitations: a fixed 100-skill taxonomy, uncalibrated default thresholds, a small single-annotator synthetic test set, and no OCR yet for scanned PDFs.  
  > Our clear next steps are collecting a two-annotator human dataset with Cohen's kappa to properly calibrate thresholds, adding a cross-encoder re-ranker for borderline cases, training a skill NER model for out-of-taxonomy skills, and adding OCR and multilingual support.  
  > Thank you, ma'am! We'd be happy to show a quick live demo and answer your questions."

---

## Part 4: 3-Minute Live Demo Playbook

### Pre-Flight (Do 10 minutes before your turn!)
1. Open PowerShell in the project folder `C:\Users\ASUS\OneDrive\Desktop\NLP project` and run:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\run.ps1
   ```
   *(Or manually in 2 terminals: `cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000` and `cd frontend; npm run dev`.)*
2. Open **http://localhost:5173/** in Chrome/Edge and verify **http://localhost:8000/docs** opens.
3. **Warm up MiniLM once before presenting** by running one quick analysis on `data/sample_data/sample_resume.txt` + `data/sample_data/sample_job_description.txt` (this pre-loads the model into RAM in ~2 seconds so your live demo runs instantaneously — and works completely **offline** because all models are already cached locally!).

### Exact Demo Click Path (3 Minutes)
1. **New Analysis (~30 sec):**
   - Upload `data/sample_data/sample_resume.txt`, show clean extracted text & sections.
   - Paste `data/sample_data/sample_job_description.txt`, select **Deep semantic (`all-MiniLM-L6-v2`)**, click **Run analysis**.
2. **Results Page (~60 sec):**
   - Point to **61.5% weighted coverage** and the colored **Evidence Bar** (green = Shown, amber = Verify, violet = Related, red = Not shown; faded = nice-to-have).
   - Click **`PyTorch` (Shown)** → show exact amber highlight on the real resume sentence.
   - Click **`Text Classification` (Verify)** → *"Look! The resume never says 'Text Classification', it says 'classify movie reviews as positive or negative' — MiniLM caught the paraphrase, and asks us to verify!"*
   - Click **`PostgreSQL` (Related)** → *"Shows MySQL/SQL are related, not falsely credited as PostgreSQL."*
   - Click **Correct this result** on `Text Classification` → confirm it → show coverage smoothly jump from **61.5% to 66.7%** and roadmap update!
   - Scroll to **Method Comparison** (Keyword vs TF-IDF vs MiniLM side-by-side).
3. **Roadmap (~25 sec):**
   - Open **Roadmap** tab → show **10 tasks** ordered by prerequisites (`Cloud Computing` before `AWS`), practice projects, curated docs, and checklist. Mention progress is self-reported and never fakes resume coverage.
4. **NLP Lab (~60 sec — High Marks for CSE-472!):**
   - **Preprocessing:** Type `"Developers were building REST APIs in C++ and Node.js"` → show `C++`/`Node.js` preserved + Stemming (`develop`) vs Lemmatization (`developer`).
   - **Sparse vs Dense:** Show high-dimensional sparse TF-IDF vs compact 384-d MiniLM vector.
   - **Word2Vec (CBOW vs Skip-Gram):** Compare neighbors on `"python"` or `"docker"`.
   - **Analogies (GloVe):** Run `king + woman - man` → live result **`queen` (0.8524)**!
   - **PCA & t-SNE:** Show 2-D embedding cluster map (point out explained variance in PCA and perplexity/seed in t-SNE).

---

## Part 5: Professor Viva Q&A Bank (30+ Likely Questions & Crisp Answers)

### A. Deep Learning & Transformer Questions
1. **Q: Where exactly is the Deep Learning in your project?**  
   **A:** In the semantic matcher (`app/nlp/embeddings/sentence_encoder.py`). We use **`sentence-transformers/all-MiniLM-L6-v2`**, a 6-layer distilled Transformer running on **PyTorch**. It encodes each job requirement description and each resume sentence into 384-dimensional contextual embeddings, and computes cosine similarity to detect paraphrases like *"classify movie reviews as positive or negative"* → *"Text Classification"*.

2. **Q: Why `all-MiniLM-L6-v2` instead of full BERT or GPT/LLMs?**  
   **A:** Three reasons: (1) Standard BERT isn't trained for cosine sentence similarity and needs expensive pairwise cross-encoding; `all-MiniLM-L6-v2` is a Sentence-BERT bi-encoder distilled to 6 layers (~90 MB), running fast on CPU (~1.84s load). (2) Unlike generative LLMs (GPT), it cannot **hallucinate** fake skills or fake resume sentences — every verdict is grounded in an actual sentence offset. (3) It runs **100% locally & privately** without sending personal resumes to third-party cloud APIs.

3. **Q: Did you train or fine-tune the Transformer? Why not?**  
   **A:** No, we use it pretrained for inference (zero-shot). Fine-tuning a 22M-parameter Transformer requires thousands of human-labelled pairs; fine-tuning on our small 69-label synthetic set would massively overfit and destroy generalization.

4. **Q: What is Knowledge Distillation (in MiniLM)?**  
   **A:** A compression technique where a small "student" Transformer (6 layers, 384-d) is trained to mimic the internal self-attention distributions of a larger "teacher" Transformer (12 layers, 768-d), keeping most of the accuracy at a fraction of the compute and memory cost.

5. **Q: How does Sentence-BERT differ from vanilla BERT?**  
   **A:** Vanilla BERT takes `[CLS] Sent A [SEP] Sent B [SEP]` together (Cross-Encoder: $O(N \times M)$ slow). Sentence-BERT encodes Sent A and Sent B independently with shared weights (Siamese Bi-Encoder) + **mean pooling** over token outputs, trained with contrastive loss so cosine similarity directly measures semantic closeness in $O(N + M)$ time.

6. **Q: Why use mean pooling over `[CLS]` token in Sentence-BERT?**  
   **A:** Reimers & Gurevych (2019) showed mean pooling across all non-padding token embeddings outperforms the single `[CLS]` vector for semantic textual similarity tasks.

7. **Q: What is a Bi-Encoder vs. Cross-Encoder? (And why is Cross-Encoder in your Future Work?)**  
   **A:** A **Bi-Encoder** encodes query and sentence separately → very fast for searching all sentences, slightly less fine-grained. A **Cross-Encoder** reads query and sentence together with full cross-attention between every token → slower, but higher accuracy on borderline cases. In future work, we would use MiniLM (bi-encoder) to shortlist top sentences and a Cross-Encoder to re-rank borderline `0.45–0.65` matches.

---

### B. Classical NLP & Static Embeddings Questions
8. **Q: Stemming vs. Lemmatization — and why don't you stem skills?**  
   **A:** Stemming uses heuristic suffix-chopping rules (Porter: `"studies"` → `"studi"`), often making non-words. Lemmatization uses vocabulary + morphology (`"studies"` → `"study"`). We never stem before skill matching because stemming destroys tech names (`"pandas"` → `"panda"`, `"Kubernetes"` → `"kubernet"`).

9. **Q: Why did you write a custom regex tokenizer instead of `nltk.word_tokenize`?**  
   **A:** Standard tokenizers split `"C++"` into `["C", "+", "+"]`, `"C#"` into `["C", "#"]`, and `"Node.js"` at the dot. Our tech-aware regex preserves `C++`, `C#`, `.NET`, `Node.js`, `CI/CD`, and `scikit-learn` intact.

10. **Q: Why does stop-word removal need a tech protection list?**  
    **A:** Standard English stopword lists include words like `"go"` (the Go language), `"it"`, `"c"`, `"r"`. Removing them blindly would erase real programming languages.

11. **Q: Bag of Words vs. TF-IDF vs. Dense Embeddings?**  
    **A:** BoW counts raw words (sparse, ignores rarity & meaning). TF-IDF down-weights common words across documents via smooth IDF (`ln((1+N)/(1+df))+1`), still sparse & lexical-only. Dense embeddings (384-d) encode semantic meaning in continuous space so paraphrases have high cosine similarity even with zero shared words.

12. **Q: CBOW vs. Skip-Gram in Word2Vec?**  
    **A:** CBOW predicts the center word from averaged surrounding context (faster, smoother for frequent words). Skip-Gram predicts each surrounding context word from the center word (slower, better for rare words and small datasets). Both use negative sampling (`negative=5`) to avoid computing full-vocabulary softmax.

13. **Q: Word2Vec vs. GloVe?**  
    **A:** Word2Vec is a **predictive** model trained on local sliding windows. GloVe is a **count-based matrix factorization** model trained on global word–word co-occurrence counts (`w_i · w_j + b_i + b_j ≈ log X_ij`). Both assign only **one static vector per word** (cannot handle polysemy or OOV).

14. **Q: Is your Word2Vec model production-quality?**  
    **A:** No — and we state that honestly in the UI. It trains with fixed seed (`seed=42`, `workers=1`, `200` epochs) on a small 742-sentence synthetic corpus (`data/corpus/tech_corpus.txt`) strictly to demonstrate CBOW vs. Skip-Gram interactively. For real analogies we load pretrained Stanford GloVe (`400,000 × 50-d`), and for resume matching we use pretrained MiniLM.

15. **Q: Why Cosine Similarity instead of Euclidean Distance?**  
    **A:** Cosine depends only on the **angle** between vectors, not vector magnitude, so a 30-word paragraph isn't penalized against a 3-word skill phrase. On L2-normalized vectors, cosine is simply the dot product and monotonically equivalent to squared Euclidean distance ($\|a-b\|^2 = 2 - 2\cos$).

16. **Q: PCA vs. t-SNE?**  
    **A:** PCA is linear, deterministic, fast, preserves global variance, and reports explained variance %. t-SNE is non-linear, stochastic (we fix `seed=42`), preserves local neighborhoods, requires `perplexity < N`, and inter-cluster distances in t-SNE should NOT be over-interpreted.

---

### C. Project Logic, Rules & Scoring Questions
17. **Q: How do you stop `"Java"` from matching `"JavaScript"` or `"C"` matching `"C++"`?**  
    **A:** Custom regex lookaround boundaries (no alphanumeric/`+#.` on the left, no alphanumeric/`+#&` on the right), matched **longest-alias-first** with overlap suppression, plus **case-sensitive** matching for `C`, `R`, `Go`, and `Excel`.

18. **Q: How do you stop `"Built backend services in Java"` from matching `"Python"` semantically?**  
    **A:** Our **same-category conflict rule** in `analyzer.py`: before assigning `strong_semantic` (`Verify`), we check every skill already extracted in that best-matching resume sentence. Because `"Java"` is in the same category (*Programming Languages*) as `"Python"`, the verdict is capped at **`Related`** even if cosine similarity is `0.95`.

19. **Q: How is the coverage score calculated, and why isn't document similarity mixed into it?**  
    **A:** $\text{Coverage} = 100 \times \frac{\sum_{r \in \text{Accepted}} w_r}{\sum w_r}$ (must-have = 2, nice-to-have = 1; only `direct_match` + user-confirmed items count). Blending an opaque document cosine score into requirement coverage would hide which exact requirements are missing, so we always display them separately.

20. **Q: How do you guarantee the system never hallucinates evidence?**  
    **A:** Two guarantees: (1) Every evidence snippet is sliced from the unmodified original resume using saved character offsets (`resume[start:end]`), tested by unit assertions. (2) Explanations are deterministic templates filled from real result fields — no generative LLM is used.

21. **Q: How is the Learning Roadmap ordered?**  
    **A:** Every non-direct requirement becomes a task with priority (`high` / `medium` / `low`), then ordered using **Kahn's Topological Sort** over prerequisite links in the taxonomy (e.g., `SQL` → `PostgreSQL`, `Cloud Computing` → `AWS`), with ties broken by priority and weight.

22. **Q: When a user marks a roadmap task "Completed", does their resume coverage increase?**  
    **A:** **No!** Roadmap progress is strictly **self-reported** and logged separately in `learning_progress`. To increase verified coverage, the user should update their resume with the new project/evidence and run a fresh analysis.

---

### D. Evaluation & Critical Thinking Questions
23. **Q: Why was TF-IDF recall only 0.073 (7.3%)?**  
    **A:** TF-IDF compares a short skill phrase against a full resume sentence. Even when exact words overlap partially, TF-IDF cosine stays low (typically `0.05–0.19`), rarely crossing `0.20`, and on paraphrases with zero shared words it scores `0.00`.

24. **Q: Why was Dense MiniLM recall only 0.098 (9.8%) at threshold 0.60?**  
    **A:** Our default `semantic_strong = 0.60` is intentionally conservative (uncalibrated) to minimize false positives — and indeed MiniLM achieved **1.000 precision and 0.000 FPR**. Many genuine paraphrases scored in the `0.45–0.60` (`Related`) band rather than above `0.60`. In addition, our hybrid still improved F1 (`0.746 → 0.765`) with zero extra false positives, and on the fuller sample resume MiniLM successfully caught `Text Classification` above `0.60`. With a proper separate validation set, calibrating the threshold (e.g., around `0.50`) would recover much higher recall.

25. **Q: Why didn't you lower the threshold right now to make your numbers look higher?**  
    **A:** Because tuning thresholds on the test set causes **data leakage** and inflates scores artificially! Our evaluation protocol (`docs/evaluation.md`) explicitly forbids tuning on `eval_set.json`; thresholds must be calibrated on a separate validation set (such as exported `user_feedback` corrections).

26. **Q: What was Keyword matching's 1 false positive?**  
    **A:** Case `c15`: *"fixed SQL injection and XSS issues"* — keyword matching saw the token `"SQL"` inside `"SQL injection"` and credited SQL database skill, even though fixing SQL injection is a cybersecurity task, not database querying!

27. **Q: What happens if PyTorch/MiniLM fails to load or isn't installed?**  
    **A:** Graceful degradation: the analyzer automatically falls back to TF-IDF, sets `fallback_used = true` with the exact error reason, and the UI displays a clear warning banner so the user always knows which backend ran.

---

### E. Engineering, Security & Ethics Questions
28. **Q: Why FastAPI + SQLAlchemy instead of Flask or Django?**  
    **A:** FastAPI gives automatic request/response validation via Pydantic v2, auto-generated interactive Swagger docs (`/docs`), native Python compatibility with PyTorch/scikit-learn/Gensim, and clean async/sync layering.

29. **Q: How do you protect resume privacy & prevent attacks?**  
    **A:** `scrypt` salted password hashing; JWT stored in `httpOnly`, `SameSite=Lax` cookies (not `localStorage`, blocking XSS token theft); ownership check (`user_id`) on every DB query returning `404` on foreign records; upload validation via extension + magic bytes + 5 MB cap + UUID server filenames (no path traversal); resume text never logged; full user data export and cascading delete.

30. **Q: What are the ethical risks of AI resume tools, and how do you mitigate them?**  
    **A:** Risks include demographic bias, opaque rejection scores, and over-reliance on imperfect NLP. We mitigate them by inferring **zero protected traits**, **never ranking candidates**, citing exact evidence sentences, letting users override verdicts, and explicitly positioning SkillGap-NLP as a **career-development aid, not a hiring decision tool**.

---

## Part 6: 5-Minute Last-Minute Cheat Sheet (Key Numbers & Facts)

| Item | Exact Verified Value |
|---|---|
| **Deep Learning Model** | `sentence-transformers/all-MiniLM-L6-v2` (6-layer distilled Transformer, **384-d**, CPU via PyTorch, loads in **1.84s**) |
| **Taxonomy Size** | **100 skills** across **18 categories** (`data/skill_taxonomy/taxonomy.json`) |
| **Default Thresholds** | Dense: strong **`0.60`**, related **`0.45`** · TF-IDF: strong **`0.20`**, related **`0.10`** (uncalibrated defaults) |
| **Coverage Formula** | $\text{Coverage} = 100 \times \frac{\sum w_{\text{accepted}}}{\sum w_{\text{all}}}$ (Must-have = **2**, Nice-to-have = **1**; Verify only after user confirmation) |
| **Sample Resume Result** | **22** requirements (**17** must-have, **5** nice-to-have, total weight **39**) → **12** Shown (weight **24**) = **61.5%**; **`Text Classification`** caught as **Verify**; **10** roadmap tasks |
| **NLP Lab Modules** | **9 tabs** (Preprocessing, BoW/TF-IDF, Sparse vs Dense, Word2Vec CBOW/Skip-Gram on **742** synthetic sentences, GloVe **`400k × 50-d`**, Cosine breakdown, Analogies [`king-man+woman=queen` `0.8524`], PCA & t-SNE, Method comparison) |
| **Evaluation Set** | **20** synthetic cases, **69** labelled requirements (**41** positive, **28** negative) |
| **Measured F1 Scores** | Keyword **0.746** (P `0.962`, R `0.610`) · TF-IDF **0.136** (P `1.000`, R `0.073`) · MiniLM **0.178** (P `1.000`, R `0.098`, FPR `0.000`) · **Hybrid 0.765** (P `0.963`, R `0.634`, FPR `0.036`) |
| **Skill Extraction Score** | Precision **1.000**, Recall **0.879**, F1 **0.935** |
| **App Scale & Tests** | ~9,000 LOC, **10** frontend pages, **~30** API endpoints, **12** DB tables, **65 backend + 10 frontend = 75 passing tests** + full smoke test |
| **Live URLs** | Frontend: `http://localhost:5173` · API Docs: `http://localhost:8000/docs` |
