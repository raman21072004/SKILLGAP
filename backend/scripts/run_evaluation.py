"""Run the matching evaluation on data/evaluation/eval_set.json and write a report.

    python scripts/run_evaluation.py                 # uses the semantic model if installed
    python scripts/run_evaluation.py --no-semantic   # keyword + TF-IDF only

Outputs (all numbers computed now, nothing hard-coded):
    docs/evaluation_results.json
    docs/evaluation_results.md
    docs/evaluation_chart.png (if matplotlib is installed)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-semantic", action="store_true")
    args = parser.parse_args()
    if args.no_semantic:
        os.environ["ENABLE_SEMANTIC_MODEL"] = "false"

    from app.nlp.evaluation.evaluator import evaluate

    report = evaluate()
    docs = ROOT / "docs"
    (docs / "evaluation_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Evaluation results (generated)",
        "",
        f"- Run at: {report['run_at']}",
        f"- Dataset: {report['dataset']} ({report['num_cases']} cases, {report['num_labels']} labelled requirements, {report['positives']} positive)",
        f"- Semantic model: {report['semantic_model']} (available: {report['semantic_available']})",
        f"- Thresholds: {report['thresholds']}",
        "",
        f"> {report['caveat']}",
        "",
        "| Method | Precision | Recall | F1 | False positive rate | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for method, r in report["matching"].items():
        if r.get("precision") is None:
            lines.append(f"| {method} | - | - | - | - | {r.get('note', '')} |")
        else:
            lines.append(f"| {method} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} | {r['false_positive_rate']:.3f} | {r.get('note', '')} |")
    ext = report["skill_extraction"]
    lines += [
        "",
        f"Skill extraction (taxonomy matching): precision {ext['precision']:.3f}, recall {ext['recall']:.3f}, F1 {ext['f1']:.3f}",
        f"Mean latency per case: {report['latency_ms']['mean']} ms (max {report['latency_ms']['max']} ms)",
    ]
    (docs / "evaluation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        methods = [m for m, r in report["matching"].items() if r.get("precision") is not None]
        metrics = ["precision", "recall", "f1"]
        fig, ax = plt.subplots(figsize=(7, 4))
        width = 0.25
        for i, metric in enumerate(metrics):
            ax.bar([x + i * width for x in range(len(methods))], [report["matching"][m][metric] for m in methods], width, label=metric)
        ax.set_xticks([x + width for x in range(len(methods))], methods)
        ax.set_ylim(0, 1)
        ax.set_title("Matching methods on the synthetic evaluation set")
        ax.legend()
        fig.tight_layout()
        fig.savefig(docs / "evaluation_chart.png", dpi=150)
    except ImportError:
        pass

    print("\n".join(lines))


if __name__ == "__main__":
    main()
