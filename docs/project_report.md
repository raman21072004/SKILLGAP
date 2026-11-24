# SkillGap-NLP — Project report material

## Title
SkillGap-NLP: A Deep Learning-Based Skill Gap Analysis System for Resumes and Job Descriptions

## Abstract
Job seekers, particularly students, struggle to judge which requirements of a job description their
resume actually demonstrates. Keyword-based screening tools ignore context and paraphrase, while purely
semantic tools over-credit related skills. SkillGap-NLP is a full-stack system that combines a
configurable skill taxonomy, classical vector-space retrieval (Bag of Words, TF-IDF) and contextual
sentence embeddings from a pretrained transformer (all-MiniLM-L6-v2) to analyse a resume against a job
description. Each requirement is classified as directly shown, semantically similar but requiring
verification, related/transferable, or not shown, using deterministic rules that cite the exact resume
sentence as evidence and prevent a sentence about one skill (e.g. Java) from validating another of the same
kind (e.g. Python). A weighted coverage score with an explicit formula is reported separately from
document-level similarity, user corrections are stored for future evaluation, and the remaining gaps are
converted into a prerequisite-ordered learning roadmap with curated resources. An integrated NLP
laboratory demonstrates tokenisation, stemming, lemmatisation, n-grams, Bag of Words, TF-IDF, Word2Vec
(CBOW and Skip-Gram), GloVe, cosine similarity, word analogies, PCA and t-SNE. The system is implemented
with React, FastAPI, SQLAlchemy/PostgreSQL, scikit-learn, Gensim and Sentence Transformers, and includes
an evaluation harness reporting precision, recall, F1 and false-positive rate on a labelled synthetic
dataset. It is positioned as a career-development aid rather than a hiring decision tool.

## Problem statement
Given a resume R and a job description J, determine for each skill requirement in J whether R provides
evidence of it, quantify overall coverage in an explainable way, and recommend how to close the gaps —
without fabricating evidence, without equating similarity with competence, and while protecting the
personal data contained in resumes.

## Objectives
1. Securely extract and structure text from PDF, DOCX and plain-text resumes.
2. Build a reusable preprocessing pipeline that keeps original, normalised, tokenised and model-ready
   representations separate.
3. Extract skills with a taxonomy supporting aliases, categories, related skills and prerequisites.
4. Implement and compare keyword, TF-IDF and dense-embedding matching.
5. Classify requirements with explainable, evidence-backed rules and a documented coverage formula.
6. Generate a personalised, prerequisite-ordered learning roadmap with progress tracking.
7. Demonstrate the NLP syllabus interactively.
8. Evaluate the methods honestly and document limitations.
9. Deliver a secure, tested full-stack application with authentication, persistence and data deletion.

## Scope and limitations
English resumes; skills limited to the taxonomy; no OCR; synthetic evaluation data; thresholds
uncalibrated. See README §20.

## Suggested report chapters
1. Introduction (problem, motivation, objectives)
2. Literature review (keyword ATS, TF-IDF retrieval, Word2Vec/GloVe, Sentence-BERT, skill taxonomies such as ESCO/O*NET)
3. System design (architecture.md diagrams)
4. Methodology (methodology.md)
5. Implementation (folder structure, key modules, API)
6. Testing and evaluation (evaluation.md, test suites)
7. Results and discussion (from your own evaluation run and screenshots)
8. Ethics, privacy and limitations
9. Conclusion and future work

## Key references
- Mikolov et al., 2013. Efficient Estimation of Word Representations in Vector Space.
- Pennington, Socher, Manning, 2014. GloVe: Global Vectors for Word Representation.
- Reimers and Gurevych, 2019. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.
- Wang et al., 2020. MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers.
- van der Maaten and Hinton, 2008. Visualizing Data using t-SNE.
- Salton and Buckley, 1988. Term-weighting approaches in automatic text retrieval.
- Jurafsky and Martin. Speech and Language Processing (3rd ed. draft).
