"""Binary classification metrics, implemented explicitly so they can be explained.

Positive class = "the resume demonstrates the required skill".
"""

from __future__ import annotations


def confusion(y_true: list[bool], y_pred: list[bool]) -> dict:
    tp = sum(t and p for t, p in zip(y_true, y_pred, strict=True))
    fp = sum((not t) and p for t, p in zip(y_true, y_pred, strict=True))
    fn = sum(t and (not p) for t, p in zip(y_true, y_pred, strict=True))
    tn = sum((not t) and (not p) for t, p in zip(y_true, y_pred, strict=True))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall_f1(y_true: list[bool], y_pred: list[bool]) -> dict:
    c = confusion(y_true, y_pred)
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    accuracy = (tp + tn) / len(y_true) if y_true else 0.0
    return {
        **c,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "accuracy": round(accuracy, 4),
        "support": len(y_true),
    }


def set_precision_recall(expected: set[str], predicted: set[str]) -> dict:
    """Precision/recall for set-valued outputs such as extracted skills."""
    tp = len(expected & predicted)
    p = tp / len(predicted) if predicted else 0.0
    r = tp / len(expected) if expected else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "predicted": len(predicted), "expected": len(expected), "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}
