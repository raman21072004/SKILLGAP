"""Bag of Words and TF-IDF representations (scikit-learn).

TF-IDF(t, d) = tf(t, d) * idf(t),  idf(t) = ln((1 + N) / (1 + df(t))) + 1   (sklearn smooth_idf)
Rows are L2-normalised, so cosine similarity is simply the dot product.

Notes for the viva:
* Bag of Words ignores word order and has no notion of meaning: "Java" and
  "Python" are orthogonal dimensions; "ML" and "machine learning" are different features.
* TF-IDF down-weights words that occur in many documents.
* We use word uni-grams + bi-grams so multi-word skills ("machine learning")
  survive as features, and a tokenizer that keeps "c++" / "node.js" intact.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

from app.nlp.preprocessing.pipeline import TECH_TOKEN_RE, get_stopwords, normalize


def _analyzer_tokens(text: str) -> list[str]:
    stop = get_stopwords()
    return [t for t in TECH_TOKEN_RE.findall(normalize(text, lowercase=True)) if any(c.isalnum() for c in t) and t not in stop]


def _tokenizer(text: str) -> list[str]:
    return _analyzer_tokens(text)


def make_tfidf(ngram_range: tuple[int, int] = (1, 2), **kwargs) -> TfidfVectorizer:
    return TfidfVectorizer(
        tokenizer=_tokenizer,
        lowercase=False,  # handled by our tokenizer
        token_pattern=None,
        ngram_range=ngram_range,
        sublinear_tf=True,
        **kwargs,
    )


def make_bow(ngram_range: tuple[int, int] = (1, 1)) -> CountVectorizer:
    return CountVectorizer(tokenizer=_tokenizer, lowercase=False, token_pattern=None, ngram_range=ngram_range)


def document_similarity(doc_a: str, doc_b: str) -> float:
    """TF-IDF cosine similarity between two documents (IDF fitted on the pair)."""
    if not doc_a.strip() or not doc_b.strip():
        return 0.0
    vec = make_tfidf()
    try:
        matrix = vec.fit_transform([doc_a, doc_b])
    except ValueError:  # empty vocabulary
        return 0.0
    return float(sk_cosine(matrix[0], matrix[1])[0, 0])


def top_terms_single_document(text: str, top_k: int = 15) -> list[tuple[str, float]]:
    """Top terms of one document, using its sentences as the IDF 'corpus'."""
    sentences = [s for s in text.splitlines() if s.strip()] or [text]
    vec = make_tfidf()
    try:
        matrix = vec.fit_transform(sentences)
    except ValueError:
        return []
    scores = np.asarray(matrix.sum(axis=0)).ravel()
    terms = vec.get_feature_names_out()
    order = np.argsort(-scores)[:top_k]
    return [(str(terms[i]), float(scores[i])) for i in order if scores[i] > 0]


def top_terms_pair(doc_a: str, doc_b: str, top_k: int = 15) -> dict:
    """Important terms of each document when IDF is fitted on both."""
    vec = make_tfidf()
    matrix = vec.fit_transform([doc_a, doc_b]).toarray()
    terms = vec.get_feature_names_out()

    def top(row: np.ndarray) -> list[dict]:
        order = np.argsort(-row)[:top_k]
        return [{"term": str(terms[i]), "score": round(float(row[i]), 4)} for i in order if row[i] > 0]

    shared = [str(terms[i]) for i in range(len(terms)) if matrix[0, i] > 0 and matrix[1, i] > 0]
    return {"doc_a": top(matrix[0]), "doc_b": top(matrix[1]), "shared_terms": shared[:50], "vocabulary_size": len(terms)}


def skill_sentence_scores(skill_phrases: list[str], sentences: list[str]) -> np.ndarray:
    """Cosine similarity matrix (skills x sentences) in a TF-IDF space fitted on both."""
    if not skill_phrases or not sentences:
        return np.zeros((len(skill_phrases), len(sentences)))
    vec = make_tfidf()
    try:
        matrix = vec.fit_transform(list(skill_phrases) + list(sentences))
    except ValueError:
        return np.zeros((len(skill_phrases), len(sentences)))
    skills_m = matrix[: len(skill_phrases)]
    sents_m = matrix[len(skill_phrases) :]
    return sk_cosine(skills_m, sents_m)


def bow_demo(documents: list[str], max_features_shown: int = 40) -> dict:
    """Bag-of-Words matrix and sparse-matrix statistics for the NLP Lab."""
    vec = make_bow()
    matrix = vec.fit_transform(documents)
    vocab = vec.get_feature_names_out()
    dense = matrix.toarray()
    total_cells = dense.size
    nnz = int(matrix.nnz)
    order = np.argsort(-dense.sum(axis=0))[:max_features_shown]
    return {
        "vocabulary": [str(vocab[i]) for i in order],
        "vocabulary_size": int(len(vocab)),
        "matrix": [[int(dense[d, i]) for i in order] for d in range(len(documents))],
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "non_zero": nnz,
        "sparsity": round(1 - nnz / total_cells, 4) if total_cells else 0.0,
        "cosine_similarity": float(sk_cosine(matrix[0], matrix[1])[0, 0]) if len(documents) >= 2 else None,
        "note": "Bag of Words counts terms only. It ignores word order and does not encode meaning.",
    }


def tfidf_demo(doc_a: str, doc_b: str, top_k: int = 15) -> dict:
    vec = make_tfidf()
    matrix = vec.fit_transform([doc_a, doc_b])
    terms = vec.get_feature_names_out()
    idf = vec.idf_
    pair = top_terms_pair(doc_a, doc_b, top_k)
    bow = make_bow((1, 2)).fit_transform([doc_a, doc_b])
    return {
        "resume_top_terms": pair["doc_a"],
        "job_top_terms": pair["doc_b"],
        "shared_terms": pair["shared_terms"],
        "vocabulary_size": int(len(terms)),
        "tfidf_cosine_similarity": round(float(sk_cosine(matrix[0], matrix[1])[0, 0]), 4),
        "bow_cosine_similarity": round(float(sk_cosine(bow[0], bow[1])[0, 0]), 4),
        "idf_examples": [
            {"term": str(terms[i]), "idf": round(float(idf[i]), 4)} for i in np.argsort(idf)[: min(10, len(terms))]
        ],
        "formula": "tfidf(t,d) = (1 + ln tf(t,d)) * (ln((1+N)/(1+df(t))) + 1), rows L2-normalised",
    }
