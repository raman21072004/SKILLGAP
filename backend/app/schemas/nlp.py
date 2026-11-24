from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MAX = 20_000


class TwoDocs(BaseModel):
    doc_a: str = Field(min_length=1, max_length=MAX)
    doc_b: str = Field(min_length=1, max_length=MAX)


class VectorsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX)
    corpus: list[str] = Field(default_factory=list, max_length=20)


class WordsRequest(BaseModel):
    words: list[str] = Field(min_length=1, max_length=30)
    architecture: Literal["cbow", "skipgram"] = "cbow"


class CompareW2VRequest(BaseModel):
    words: list[str] = Field(min_length=1, max_length=20)
    window: int = Field(default=4, ge=1, le=10)
    vector_size: int = Field(default=50, ge=10, le=200)


class AnalogyRequest(BaseModel):
    model: Literal["word2vec-cbow", "word2vec-skipgram", "glove"] = "glove"
    positive: list[str] = Field(min_length=1, max_length=5)
    negative: list[str] = Field(default_factory=list, max_length=5)


class SimilarityRequest(BaseModel):
    text_a: str = Field(min_length=1, max_length=MAX)
    text_b: str = Field(min_length=1, max_length=MAX)


class VisualizeRequest(BaseModel):
    source: Literal["word2vec-cbow", "word2vec-skipgram", "glove", "sentence-transformer"] = "word2vec-skipgram"
    method: Literal["pca", "tsne"] = "pca"
    items: list[str] = Field(default_factory=list, max_length=200)
    perplexity: float = Field(default=5.0, gt=0, le=100)
    seed: int = Field(default=42, ge=0, le=1_000_000)


class CompareModelsRequest(BaseModel):
    resume_text: str = Field(min_length=30, max_length=60_000)
    job_description: str = Field(min_length=30, max_length=60_000)
