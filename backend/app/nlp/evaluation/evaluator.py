"""Evaluate keyword, TF-IDF, dense-semantic and hybrid matching on a labelled set.

Nothing here is hard-coded: every number is computed from the dataset at run
time. If the semantic model is not available, that method is reported as
"not evaluated" instead of being given a made-up score.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from app.nlp.config import data_dir, get_nlp_config
from app.nlp.embeddings.sentence_encoder import Encoder, get_encoder
from app.nlp.evaluation.metrics import precision_recall_f1, set_precision_recall
from app.nlp.extraction.sections import split_sentences
from app.nlp.skill_extraction.extractor import RequiredSkill, extract_candidate_skills
from app.nlp.skill_extraction.taxonomy import Taxonomy, get_taxonomy
from app.nlp.skill_gap.analyzer import analyze_gaps

METHODS = ("keyword", "tfidf", "semantic", "hybrid")


def load_dataset(path: Path | None = None) -> dict:
    path = path or data_dir() / "evaluation" / "eval_set.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def evaluate(dataset: dict | None = None, taxonomy: Taxonomy | None = None, encoder: Encoder | None = None) -> dict:
    dataset = dataset or load_dataset()
    taxonomy = taxonomy or get_taxonomy()
    encoder = encoder or get_encoder()
    config = get_nlp_config()

    y_true: list[bool] = []
    preds: dict[str, list[bool]] = {m: [] for m in METHODS}
    latencies: list[float] = []
    skipped: list[str] = []
    extraction_expected: set[str] = set()
    extraction_predicted: set[str] = set()
    semantic_available = True
    per_case = []

    for case in dataset["cases"]:
        text = case["resume"]
        sents = split_sentences(text)
        # The excerpts have no headings; treat them as experience bullets
        for s in sents:
            s.section = "experience"
        candidate = extract_candidate_skills("EXPERIENCE\n" + text, taxonomy)
        # offsets shift by the heading length; align sentence starts for the conflict rule
        for sk in candidate.values():
            for m in sk.mentions:
                m.sentence_start -= len("EXPERIENCE\n")

        reqs, labels = [], []
        for r in case["requirements"]:
            canon = taxonomy.normalize(r["skill"])
            if canon is None:
                skipped.append(f"{case['id']}:{r['skill']}")
                continue
            reqs.append(RequiredSkill(canon, taxonomy.skills[canon].category, "must_have", 1.0, r["skill"]))
            labels.append(bool(r["demonstrated"]))

        start = time.perf_counter()
        out = analyze_gaps(sents, candidate, reqs, taxonomy, mode="semantic", encoder=encoder, config=config)
        latencies.append((time.perf_counter() - start) * 1000)
        semantic_available = semantic_available and out["semantic_available"]

        comp = {c["method"]: c for c in out["model_comparison"]}
        case_preds = {}
        for i, req in enumerate(reqs):
            res = out["requirements"][i]
            p = {
                "keyword": req.canonical in comp["keyword"]["matched"],
                "tfidf": req.canonical in comp["tfidf"]["matched"],
                "semantic": req.canonical in comp["semantic"]["matched"] if comp["semantic"]["available"] else False,
                "hybrid": res["classification"] in {"direct_match", "strong_semantic"},
            }
            for m in METHODS:
                preds[m].append(p[m])
            case_preds[req.canonical] = {"expected": labels[i], **p, "classification": res["classification"]}
        y_true.extend(labels)
        extraction_expected |= {f"{case['id']}:{s}" for s in case.get("expected_extracted", [])}
        extraction_predicted |= {f"{case['id']}:{s}" for s in candidate}
        per_case.append({"id": case["id"], "predictions": case_preds})

    results = {}
    for m in METHODS:
        if m in {"semantic", "hybrid"} and not semantic_available:
            results[m] = {"evaluated": m == "hybrid", "note": "Semantic model unavailable; hybrid ran with TF-IDF fallback." if m == "hybrid" else "Semantic model unavailable - not evaluated."}
            if m == "hybrid":
                results[m].update(precision_recall_f1(y_true, preds[m]))
            continue
        results[m] = {"evaluated": True, **precision_recall_f1(y_true, preds[m])}

    return {
        "dataset": dataset.get("name"),
        "provenance": dataset.get("provenance"),
        "run_at": datetime.now(timezone.utc).isoformat(),
        "semantic_model": getattr(encoder, "name", None),
        "semantic_available": semantic_available,
        "thresholds": {
            "semantic_strong": config.thresholds.semantic_strong,
            "tfidf_strong": config.thresholds.tfidf_strong,
        },
        "num_cases": len(dataset["cases"]),
        "num_labels": len(y_true),
        "positives": sum(y_true),
        "skipped_requirements": skipped,
        "matching": results,
        "skill_extraction": set_precision_recall(extraction_expected, extraction_predicted),
        "latency_ms": {
            "mean": round(sum(latencies) / len(latencies), 2) if latencies else None,
            "max": round(max(latencies), 2) if latencies else None,
        },
        "per_case": per_case,
        "caveat": "Small synthetic, author-labelled dataset. Results indicate relative behaviour of the methods; "
                  "they are not evidence of real-world accuracy.",
    }
