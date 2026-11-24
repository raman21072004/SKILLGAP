"""Dense contextual sentence embeddings (Sentence Transformers / Hugging Face).

* The model is loaded ONCE per process (thread-safe lazy singleton) and reused.
* Embeddings are cached in memory (LRU) because the same skill queries are
  encoded for every analysis.
* If the model cannot be loaded (package not installed, no internet for the
  first download, ENABLE_SEMANTIC_MODEL=false), `available` is False and
  `error` explains why. Callers MUST report the fallback; we never pretend
  keyword matching is deep learning.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from typing import Protocol

import numpy as np

from app.nlp.config import get_nlp_config

logger = logging.getLogger(__name__)


class Encoder(Protocol):
    name: str
    available: bool
    error: str | None

    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceEncoder:
    def __init__(self, model_name: str, enabled: bool = True, cache_size: int = 4096):
        self.name = model_name
        self.enabled = enabled
        self.available = False
        self.error: str | None = None
        self.load_seconds: float | None = None
        self.dimension: int | None = None
        self._model = None
        self._lock = threading.Lock()
        self._loaded = False
        self._cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._cache_size = cache_size

    def load(self) -> bool:
        with self._lock:
            if self._loaded:
                return self.available
            self._loaded = True
            if not self.enabled:
                self.error = "Semantic model disabled by configuration (ENABLE_SEMANTIC_MODEL=false)."
                return False
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                self.error = (
                    "sentence-transformers is not installed. Install ML extras: "
                    "pip install -r backend/requirements-ml.txt"
                )
                logger.warning(self.error)
                return False
            try:
                start = time.perf_counter()
                self._model = SentenceTransformer(self.name, device="cpu")
                self.load_seconds = round(time.perf_counter() - start, 2)
                self.dimension = int(self._model.get_sentence_embedding_dimension() or 0)
                self.available = True
                logger.info("Loaded semantic model %s in %ss", self.name, self.load_seconds)
            except Exception as exc:  # network errors, missing weights, incompatible versions
                self.error = (
                    f"Could not load model '{self.name}': {type(exc).__name__}. "
                    "The first run downloads ~90 MB from Hugging Face; run "
                    "'python backend/scripts/download_models.py' with internet access."
                )
                logger.warning(self.error)
            return self.available

    def encode(self, texts: list[str]) -> np.ndarray:
        if not self.load():
            raise RuntimeError(self.error or "Semantic model unavailable")
        missing = [t for t in dict.fromkeys(texts) if t not in self._cache]
        if missing:
            vectors = self._model.encode(missing, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
            for t, v in zip(missing, vectors, strict=True):
                self._cache[t] = np.asarray(v, dtype=np.float32)
                if len(self._cache) > self._cache_size:
                    self._cache.popitem(last=False)
        for t in texts:
            if t in self._cache:
                self._cache.move_to_end(t)
        return np.stack([self._cache[t] for t in texts]) if texts else np.zeros((0, self.dimension or 0))

    def status(self) -> dict:
        return {
            "model": self.name,
            "loaded": self._loaded,
            "available": self.available,
            "error": self.error,
            "dimension": self.dimension,
            "load_seconds": self.load_seconds,
        }


class HashingTestEncoder:
    """Deterministic, offline encoder for unit tests ONLY (not semantic!).

    Maps words to pseudo-random vectors; sentences sharing words get similar
    vectors. Lets tests exercise the semantic code path without downloads.
    """

    def __init__(self, dim: int = 64):
        self.name = "hashing-test-encoder"
        self.available = True
        self.error = None
        self.dimension = dim

    def _word_vec(self, word: str) -> np.ndarray:
        seed = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
        return np.random.default_rng(seed).standard_normal(self.dimension)

    def encode(self, texts: list[str]) -> np.ndarray:
        out = []
        for t in texts:
            words = [w for w in t.lower().replace(":", " ").split() if w]
            v = np.sum([self._word_vec(w) for w in words], axis=0) if words else np.zeros(self.dimension)
            n = np.linalg.norm(v)
            out.append(v / n if n else v)
        return np.asarray(out, dtype=np.float32)

    def status(self) -> dict:
        return {"model": self.name, "loaded": True, "available": True, "error": None, "dimension": self.dimension}


_encoder: Encoder | None = None
_encoder_lock = threading.Lock()


def get_encoder() -> Encoder:
    global _encoder
    with _encoder_lock:
        if _encoder is None:
            cfg = get_nlp_config()
            _encoder = SentenceEncoder(cfg.semantic_model_name, enabled=cfg.enable_semantic_model)
        return _encoder


def set_encoder(encoder: Encoder | None) -> None:
    """Override the encoder (used by tests and by model-selection settings)."""
    global _encoder
    with _encoder_lock:
        _encoder = encoder


def semantic_available() -> bool:
    enc = get_encoder()
    if isinstance(enc, SentenceEncoder):
        return enc.load()
    return enc.available
