"""2-D projections of embeddings for visualisation (PCA and t-SNE).

These are VISUALISATION tools only; they are not used for skill matching.

PCA  - linear projection onto directions of maximum variance. Fast and
       deterministic; 'explained variance ratio' tells how much information the
       2-D picture keeps. Global distances are meaningful-ish; non-linear
       structure is lost.
t-SNE - non-linear; preserves LOCAL neighbourhoods. Cluster sizes and distances
       BETWEEN clusters are not meaningful. Results depend on perplexity and the
       random seed; cost grows ~O(n^2) for exact, O(n log n) Barnes-Hut.
"""

from __future__ import annotations

import numpy as np

MIN_POINTS_PCA = 3
MIN_POINTS_TSNE = 5
RECOMMENDED_POINTS_TSNE = 15


def pca_2d(vectors: np.ndarray, labels: list[str], groups: list[str] | None = None) -> dict:
    from sklearn.decomposition import PCA

    n = vectors.shape[0]
    if n < MIN_POINTS_PCA:
        raise ValueError(f"PCA needs at least {MIN_POINTS_PCA} points (got {n}).")
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(vectors)
    ratio = [round(float(x), 4) for x in pca.explained_variance_ratio_]
    return {
        "method": "pca",
        "points": _points(coords, labels, groups),
        "explained_variance_ratio": ratio,
        "information_retained": round(float(sum(ratio)), 4),
        "original_dimensions": int(vectors.shape[1]),
        "warnings": [] if n >= 10 else [f"Only {n} points; the projection is illustrative."],
        "explanation": (
            f"PCA kept {sum(ratio) * 100:.1f}% of the variance of the {vectors.shape[1]}-dimensional vectors. "
            "The remaining variance is lost in the 2-D view."
        ),
    }


def tsne_2d(vectors: np.ndarray, labels: list[str], perplexity: float = 5.0, seed: int = 42, groups: list[str] | None = None) -> dict:
    from sklearn.manifold import TSNE

    n = vectors.shape[0]
    if n < MIN_POINTS_TSNE:
        raise ValueError(f"t-SNE needs at least {MIN_POINTS_TSNE} points (got {n}).")
    warnings = []
    max_perp = max(1.0, (n - 1) / 3)
    if perplexity >= n:
        warnings.append(f"Perplexity {perplexity} must be smaller than the number of points ({n}); reduced to {max_perp:.1f}.")
        perplexity = max_perp
    if n < RECOMMENDED_POINTS_TSNE:
        warnings.append(f"Only {n} points: t-SNE is designed for larger collections, so treat clusters with caution.")
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=seed, init="pca", learning_rate="auto", max_iter=1000)
    coords = tsne.fit_transform(vectors)
    return {
        "method": "tsne",
        "points": _points(coords, labels, groups),
        "perplexity": perplexity,
        "seed": seed,
        "kl_divergence": round(float(tsne.kl_divergence_), 4),
        "original_dimensions": int(vectors.shape[1]),
        "warnings": warnings,
        "explanation": (
            "t-SNE preserves local neighbourhoods: points close together were close in the original space. "
            "Distances between clusters and cluster sizes are not meaningful."
        ),
    }


def _points(coords: np.ndarray, labels: list[str], groups: list[str] | None) -> list[dict]:
    return [
        {"label": labels[i], "x": round(float(coords[i, 0]), 4), "y": round(float(coords[i, 1]), 4), "group": groups[i] if groups else None}
        for i in range(len(labels))
    ]
