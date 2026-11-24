"""NLP Laboratory endpoints (syllabus demonstrations). Require sign-in."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser
from app.core.errors import AppError
from app.nlp.pipeline import AnalysisInputError
from app.nlp.preprocessing.pipeline import PreprocessOptions
from app.nlp.skill_extraction.taxonomy import get_taxonomy
from app.schemas.nlp import (
    AnalogyRequest,
    CompareModelsRequest,
    CompareW2VRequest,
    SimilarityRequest,
    TwoDocs,
    VectorsRequest,
    VisualizeRequest,
    WordsRequest,
)
from app.services import nlp_lab_service as lab

router = APIRouter(prefix="/api/nlp", tags=["nlp-lab"])


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except lab.LabError as exc:
        raise AppError(exc.status, exc.code, exc.message) from exc
    except AnalysisInputError as exc:
        raise AppError(422, exc.code, exc.message) from exc


@router.get("/preprocessing")
def preprocessing(
    _: CurrentUser,
    text: str = Query(..., min_length=1, max_length=5000),
    lowercase: bool = True,
    remove_stopwords: bool = True,
    lemmatize: bool = True,
    ngram_n: int = Query(2, ge=1, le=4),
):
    opts = PreprocessOptions(lowercase=lowercase, remove_stop=remove_stopwords, do_lemmatize=lemmatize, ngram_n=ngram_n)
    return _run(lab.preprocessing, text, opts)


@router.post("/bow")
def bag_of_words(payload: TwoDocs, _: CurrentUser):
    return _run(lab.bag_of_words, payload.doc_a, payload.doc_b)


@router.post("/tfidf")
def tfidf(payload: TwoDocs, _: CurrentUser):
    return _run(lab.tfidf, payload.doc_a, payload.doc_b)


@router.post("/vectors")
def sparse_vs_dense(payload: VectorsRequest, _: CurrentUser):
    return _run(lab.sparse_vs_dense, payload.text, payload.corpus)


@router.post("/word2vec")
def word2vec(payload: WordsRequest, _: CurrentUser):
    return _run(lab.word2vec, payload.words, payload.architecture)


@router.post("/word2vec/compare")
def word2vec_compare(payload: CompareW2VRequest, _: CurrentUser):
    return _run(lab.cbow_vs_skipgram, payload.words, payload.window, payload.vector_size)


@router.post("/glove")
def glove(payload: WordsRequest, _: CurrentUser):
    return _run(lab.glove, payload.words)


@router.post("/analogy")
def analogy(payload: AnalogyRequest, _: CurrentUser):
    return _run(lab.analogy, payload.model, payload.positive, payload.negative)


@router.post("/similarity")
def similarity(payload: SimilarityRequest, _: CurrentUser):
    return _run(lab.similarity, payload.text_a, payload.text_b)


@router.post("/visualize")
def visualize(payload: VisualizeRequest, _: CurrentUser):
    return _run(lab.visualize, payload.source, payload.method, payload.items, payload.perplexity, payload.seed)


@router.post("/compare-models")
def compare_models(payload: CompareModelsRequest, _: CurrentUser):
    return _run(lab.compare_models, payload.resume_text, payload.job_description)


@router.get("/models/status")
def models_status(_: CurrentUser):
    return lab.embedding_status()


@router.get("/taxonomy")
def taxonomy():
    """Public: the skill taxonomy (used for autocomplete in the analysis form)."""
    tax = get_taxonomy()
    return {
        "categories": tax.categories,
        "skills": [
            {"canonical": s.canonical, "category": s.category, "aliases": list(s.aliases) + list(s.case_sensitive_aliases),
             "related": list(s.related), "prerequisites": list(s.prerequisites), "level": s.level}
            for s in tax.skills.values()
        ],
    }
