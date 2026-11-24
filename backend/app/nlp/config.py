"""Configuration for the NLP engine.

The NLP engine is deliberately independent of FastAPI/database code so that it can
be imported, tested and explained on its own. Values are read from environment
variables with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# backend/app/nlp/config.py -> parents[3] is the repository root
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def data_dir() -> Path:
    """Directory that holds taxonomy, resource catalog, corpora and evaluation data."""
    return Path(os.environ.get("DATA_DIR", _REPO_ROOT / "data")).resolve()


@dataclass
class MatchingThresholds:
    """Similarity thresholds used to classify a requirement.

    These are *uncalibrated defaults*. Cosine similarity values are not
    comparable across models, so each backend has its own thresholds. Use the
    evaluation script (backend/scripts/run_evaluation.py) to tune them.
    """

    semantic_strong: float = field(default_factory=lambda: _env_float("SEMANTIC_STRONG_THRESHOLD", 0.60))
    semantic_related: float = field(default_factory=lambda: _env_float("SEMANTIC_RELATED_THRESHOLD", 0.45))
    tfidf_strong: float = field(default_factory=lambda: _env_float("TFIDF_STRONG_THRESHOLD", 0.20))
    tfidf_related: float = field(default_factory=lambda: _env_float("TFIDF_RELATED_THRESHOLD", 0.10))


@dataclass
class NLPConfig:
    semantic_model_name: str = field(
        default_factory=lambda: os.environ.get("SEMANTIC_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    enable_semantic_model: bool = field(default_factory=lambda: _env_bool("ENABLE_SEMANTIC_MODEL", True))
    thresholds: MatchingThresholds = field(default_factory=MatchingThresholds)
    must_have_weight: float = field(default_factory=lambda: _env_float("MUST_HAVE_WEIGHT", 2.0))
    nice_to_have_weight: float = field(default_factory=lambda: _env_float("NICE_TO_HAVE_WEIGHT", 1.0))


_config: NLPConfig | None = None


def get_nlp_config() -> NLPConfig:
    global _config
    if _config is None:
        _config = NLPConfig()
    return _config
