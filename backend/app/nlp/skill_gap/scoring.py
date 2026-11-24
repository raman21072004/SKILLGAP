"""Explicit, configurable coverage scoring.

    Coverage Score = sum(weight of requirements with ACCEPTED evidence)
                     / sum(weight of all requirements) x 100

* Accepted evidence = classification "direct_match" (an exact/alias mention in
  the resume), or any requirement the user has confirmed via a correction.
* "strong_semantic" and "related" do NOT count by default: semantic similarity
  is not proof of competence. Set count_strong_semantic=True to change that.
* Must-have and nice-to-have coverage are also reported separately.
* Document similarity (TF-IDF / embeddings) is reported SEPARATELY and is never
  blended into this number.
"""

from __future__ import annotations

ACCEPTED_DEFAULT = {"direct_match"}


def effective_classification(req: dict) -> str:
    return req.get("user_classification") or req["classification"]


def compute_coverage(requirements: list[dict], count_strong_semantic: bool = False) -> dict:
    accepted = set(ACCEPTED_DEFAULT)
    if count_strong_semantic:
        accepted.add("strong_semantic")

    total_w = sum(r["weight"] for r in requirements)
    contributions = []
    got_w = 0.0
    buckets = {"must_have": [0.0, 0.0], "nice_to_have": [0.0, 0.0]}
    counts = {"direct_match": 0, "strong_semantic": 0, "related": 0, "missing": 0}

    for r in requirements:
        cls = effective_classification(r)
        counts[cls] = counts.get(cls, 0) + 1
        ok = cls in accepted
        w = float(r["weight"])
        if ok:
            got_w += w
        b = buckets.setdefault(r["importance"], [0.0, 0.0])
        b[1] += w
        if ok:
            b[0] += w
        contributions.append({
            "canonical": r["canonical"],
            "weight": w,
            "accepted": ok,
            "points": round(100 * w / total_w, 2) if total_w else 0.0,
            "classification": cls,
        })

    def pct(a: float, b: float) -> float | None:
        return round(100 * a / b, 1) if b else None

    return {
        "coverage_score": pct(got_w, total_w) if total_w else 0.0,
        "must_have_coverage": pct(*buckets["must_have"]),
        "nice_to_have_coverage": pct(*buckets["nice_to_have"]),
        "accepted_weight": got_w,
        "total_weight": total_w,
        "counts": counts,
        "contributions": contributions,
        "formula": "coverage = Σ weight(requirements with accepted evidence) / Σ weight(all requirements) × 100",
        "accepted_classes": sorted(accepted),
    }
