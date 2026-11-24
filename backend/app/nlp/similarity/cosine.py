"""Cosine similarity.

    cosine_similarity(A, B) = (A . B) / (||A|| x ||B||)

* Direction: cosine depends only on the angle between vectors, not their length,
  so a long resume and a short job ad can still be compared.
* Magnitude: ||A|| is the L2 norm; for TF-IDF it grows with document length,
  which is why we normalise.
* Range: [-1, 1] in general; [0, 1] for non-negative vectors such as TF-IDF.
* Thresholds are model-specific. A score of 0.5 from TF-IDF and 0.5 from a
  sentence-transformer mean very different things.
"""

from __future__ import annotations

import numpy as np


def cosine_similarity(a: np.ndarray | list[float], b: np.ndarray | list[float]) -> float:
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    if a.shape != b.shape:
        raise ValueError(f"Vectors must have the same dimension ({a.shape[0]} != {b.shape[0]})")
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def cosine_breakdown(a: np.ndarray | list[float], b: np.ndarray | list[float]) -> dict:
    """Step-by-step computation for the NLP Lab."""
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    dot = float(np.dot(a, b))
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    sim = dot / (na * nb) if na and nb else 0.0
    return {
        "dot_product": round(dot, 6),
        "norm_a": round(na, 6),
        "norm_b": round(nb, 6),
        "cosine_similarity": round(sim, 6),
        "angle_degrees": round(float(np.degrees(np.arccos(np.clip(sim, -1.0, 1.0)))), 2),
        "formula": "cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)",
    }


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise cosine similarities between rows of a and rows of b."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    an = a / np.clip(np.linalg.norm(a, axis=1, keepdims=True), 1e-12, None)
    bn = b / np.clip(np.linalg.norm(b, axis=1, keepdims=True), 1e-12, None)
    return an @ bn.T


def preview_vector(vec: np.ndarray | list[float], max_items: int = 12) -> dict:
    """Readable preview of a (possibly very large) vector."""
    v = np.asarray(vec, dtype=float).ravel()
    nz = int(np.count_nonzero(v))
    return {
        "dimensions": int(v.shape[0]),
        "non_zero": nz,
        "sparsity": round(1 - nz / v.shape[0], 4) if v.shape[0] else 0.0,
        "norm": round(float(np.linalg.norm(v)), 4),
        "head": [round(float(x), 4) for x in v[:max_items]],
        "truncated": bool(v.shape[0] > max_items),
    }
