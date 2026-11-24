"""NLP Laboratory: syllabus demonstrations exposed through /api/nlp/*.

Each function returns plain JSON-serialisable dicts and reports which backend
actually produced the result, so nothing is mislabelled (e.g. Word2Vec is never
shown as GloVe, keyword fallback is never shown as deep learning).
"""

from __future__ import annotations

import numpy as np

from app.nlp.embeddings import word_vectors as wv
from app.nlp.embeddings.sentence_encoder import get_encoder, semantic_available
from app.nlp.pipeline import AnalysisOptions, run_analysis
from app.nlp.preprocessing.pipeline import PreprocessOptions, preprocessing_demo
from app.nlp.similarity.cosine import cosine_breakdown, preview_vector
from app.nlp.skill_extraction.taxonomy import get_taxonomy
from app.nlp.tfidf.tfidf_matcher import bow_demo, make_tfidf, tfidf_demo
from app.nlp.visualization.projection import pca_2d, tsne_2d


class LabError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _taxonomy_vocabulary() -> set[str]:
    vocab: set[str] = set()
    for s in get_taxonomy().skills.values():
        vocab.add(s.canonical.lower())
        vocab.update(s.aliases)
        for a in s.aliases:
            vocab.update(a.split())
    return vocab


def preprocessing(text: str, options: PreprocessOptions) -> dict:
    result = preprocessing_demo(text, options, vocabulary=_taxonomy_vocabulary())
    result["oov_vocabulary_name"] = "skill taxonomy vocabulary"
    return result


def bag_of_words(doc_a: str, doc_b: str) -> dict:
    try:
        return bow_demo([doc_a, doc_b])
    except ValueError as exc:
        raise LabError("empty_vocabulary", "The documents contain no usable terms after stop-word removal.") from exc


def tfidf(doc_a: str, doc_b: str) -> dict:
    try:
        return tfidf_demo(doc_a, doc_b)
    except ValueError as exc:
        raise LabError("empty_vocabulary", "The documents contain no usable terms after stop-word removal.") from exc


def sparse_vs_dense(text: str, corpus: list[str]) -> dict:
    """Same text as a sparse TF-IDF vector and as a dense sentence embedding."""
    docs = [text] + [c for c in corpus if c.strip()]
    vec = make_tfidf()
    try:
        matrix = vec.fit_transform(docs)
    except ValueError as exc:
        raise LabError("empty_vocabulary", "No usable terms in the text.") from exc
    row = matrix[0].toarray().ravel()
    terms = vec.get_feature_names_out()
    nz = np.nonzero(row)[0]
    top = sorted(((str(terms[i]), round(float(row[i]), 4)) for i in nz), key=lambda x: -x[1])[:12]
    out = {
        "sparse": {**preview_vector(row), "non_zero_features": [{"term": t, "weight": w} for t, w in top],
                   "representation": "TF-IDF (vocabulary-based feature space)"},
        "dense": None,
        "dense_error": None,
    }
    if semantic_available():
        enc = get_encoder()
        dense = enc.encode([text])[0]
        out["dense"] = {**preview_vector(dense), "representation": f"Sentence embedding ({enc.name})"}
    else:
        out["dense_error"] = getattr(get_encoder(), "error", "Semantic model unavailable")
    return out


def _wv_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except wv.EmbeddingUnavailable as exc:
        raise LabError(exc.code, exc.message, status=503) from exc


def word2vec(words: list[str], architecture: str) -> dict:
    model = "word2vec-skipgram" if architecture == "skipgram" else "word2vec-cbow"
    return _wv_call(wv.word_vector_info, model, words)


def cbow_vs_skipgram(words: list[str], window: int, vector_size: int) -> dict:
    return _wv_call(wv.compare_cbow_skipgram, words, window=window, vector_size=vector_size)


def glove(words: list[str]) -> dict:
    return _wv_call(wv.word_vector_info, "glove", words)


def analogy(model: str, positive: list[str], negative: list[str]) -> dict:
    return _wv_call(wv.analogy, model, positive, negative)


def embedding_status() -> dict:
    status = wv.model_status()
    enc = get_encoder()
    semantic_available()
    status["sentence_transformer"] = enc.status() if hasattr(enc, "status") else {"model": enc.name, "available": enc.available}
    return status


def similarity(text_a: str, text_b: str) -> dict:
    """Compare two texts with TF-IDF, and with dense embeddings when available."""
    vec = make_tfidf()
    try:
        m = vec.fit_transform([text_a, text_b]).toarray()
        tfidf_res = {**cosine_breakdown(m[0], m[1]), "dimensions": int(m.shape[1])}
    except ValueError:
        tfidf_res = {"cosine_similarity": 0.0, "dimensions": 0, "note": "No usable vocabulary"}
    out = {"tfidf": tfidf_res, "semantic": None, "semantic_error": None}
    if semantic_available():
        enc = get_encoder()
        e = enc.encode([text_a, text_b])
        out["semantic"] = {**cosine_breakdown(e[0], e[1]), "model": enc.name, "dimensions": int(e.shape[1])}
    else:
        out["semantic_error"] = getattr(get_encoder(), "error", "Semantic model unavailable")
    out["interpretation"] = (
        "TF-IDF similarity only rewards shared words. Dense embeddings can score paraphrases highly "
        "(e.g. 'built a sentiment classifier' vs 'text classification'). Neither score proves skill proficiency, "
        "and thresholds differ between the two methods."
    )
    return out


DEFAULT_VIS_WORDS = [
    "python", "java", "javascript", "react", "node.js", "sql", "postgresql", "mysql", "docker", "kubernetes",
    "aws", "azure", "pytorch", "tensorflow", "nlp", "transformers", "pandas", "numpy", "git", "linux",
]


def visualize(source: str, method: str, items: list[str], perplexity: float, seed: int) -> dict:
    """Project embeddings to 2-D. source: word2vec-cbow | word2vec-skipgram | glove | sentence-transformer."""
    items = [i for i in (items or []) if i.strip()] or DEFAULT_VIS_WORDS
    groups = None
    oov: list[str] = []
    if source == "sentence-transformer":
        if not semantic_available():
            raise LabError("model_unavailable", getattr(get_encoder(), "error", "Semantic model unavailable"), 503)
        tax = get_taxonomy()
        labels, texts, groups = [], [], []
        for it in items:
            skill = tax.get(it)
            labels.append(skill.canonical if skill else it)
            texts.append(skill.query_text if skill else it)
            groups.append(skill.category if skill else "Other")
        vectors = get_encoder().encode(texts)
    else:
        labels, vectors, oov = _wv_call(wv.vectors_for, source, items)
        tax = get_taxonomy()
        groups = [(tax.get(lbl).category if tax.get(lbl) else "Other") for lbl in labels]
    try:
        if method == "tsne":
            result = tsne_2d(np.asarray(vectors), labels, perplexity=perplexity, seed=seed, groups=groups)
        else:
            result = pca_2d(np.asarray(vectors), labels, groups=groups)
    except ValueError as exc:
        raise LabError("too_few_points", str(exc)) from exc
    result["source"] = source
    result["oov"] = oov
    if oov:
        result["warnings"].append(f"Skipped out-of-vocabulary items: {', '.join(oov)}")
    return result


def compare_models(resume_text: str, job_text: str) -> dict:
    """Run the full pipeline once and return the side-by-side method comparison."""
    result = run_analysis(resume_text, job_text, AnalysisOptions(mode="semantic"))
    return {
        "requirements": [
            {k: r[k] for k in ("canonical", "category", "importance", "classification", "tfidf_similarity", "semantic_similarity")}
            for r in result["requirements"]
        ],
        "methods": result["model_comparison"],
        "document_similarity": result["document_similarity"],
        "model_info": result["model_info"],
        "note": "Keyword, TF-IDF and dense embeddings are different METHODS applied to the same input; "
                "only the dense embedding method uses a deep learning model.",
    }
