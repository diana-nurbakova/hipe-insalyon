"""Human- and machine-readable evaluation reports for HIPE-2026."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from hipe.evaluation.metrics import (
    AT_LABELS,
    ISAT_LABELS,
    classification_report,
    compute_global_score,
    confusion_matrix,
    null_to_false,
)


def generate_evaluation_report(
    experiment_id: str,
    at_gold: Sequence[str | None],
    at_pred: Sequence[str | None],
    isAt_gold: Sequence[str | None],
    isAt_pred: Sequence[str | None],
    metadata: dict[str, Any] | None = None,
    *,
    print_summary: bool = True,
) -> dict[str, Any]:
    """Build the standard evaluation report dict (and optionally print it).

    Applies the official ``null -> FALSE`` rule to predictions before scoring
    (the gold side never has nulls in the official splits, but predictions can).
    """
    at_pred = [null_to_false(p) for p in at_pred]
    isAt_pred = [null_to_false(p) for p in isAt_pred]
    at_gold = [null_to_false(g) for g in at_gold]
    isAt_gold = [null_to_false(g) for g in isAt_gold]

    scores = compute_global_score(at_gold, at_pred, isAt_gold, isAt_pred)

    report = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_instances": len(at_gold),
        "scores": scores,
        "at_classification_report": classification_report(at_gold, at_pred, AT_LABELS),
        "isAt_classification_report": classification_report(isAt_gold, isAt_pred, ISAT_LABELS),
        "at_confusion_matrix": confusion_matrix(at_gold, at_pred, AT_LABELS),
        "isAt_confusion_matrix": confusion_matrix(isAt_gold, isAt_pred, ISAT_LABELS),
        "at_labels": list(AT_LABELS),
        "isAt_labels": list(ISAT_LABELS),
        "metadata": metadata or {},
    }

    if print_summary:
        print_report(report)
    return report


def print_report(report: dict[str, Any]) -> None:
    """Pretty-print an evaluation report to stdout."""
    scores = report["scores"]
    at_d = scores["at_details"]
    is_d = scores["isAt_details"]
    bar = "=" * 60

    print(f"\n{bar}")
    print(f"EVALUATION REPORT: {report['experiment_id']}")
    print(bar)
    print(f"n_instances:         {report['n_instances']}")
    print(f"Global score:        {scores['global_score']:.4f}")
    print(f"MacroRecall(at):     {scores['macro_recall_at']:.4f}")
    for label in AT_LABELS:
        v = at_d.get(f"recall_{label}")
        v_str = "  n/a " if v is None else f"{v:.4f}"
        print(f"  recall {label:<10s} {v_str}")
    print(f"MacroRecall(isAt):   {scores['macro_recall_isAt']:.4f}")
    for label in ISAT_LABELS:
        v = is_d.get(f"recall_{label}")
        v_str = "  n/a " if v is None else f"{v:.4f}"
        print(f"  recall {label:<10s} {v_str}")
    print(bar)
    print("Confusion matrix (at)   rows=gold, cols=pred:", AT_LABELS)
    _print_cm(report["at_confusion_matrix"], AT_LABELS)
    print("Confusion matrix (isAt) rows=gold, cols=pred:", ISAT_LABELS)
    _print_cm(report["isAt_confusion_matrix"], ISAT_LABELS)
    print(bar)


def _print_cm(cm: list[list[int]], labels: Sequence[str]) -> None:
    width = max(8, *(len(lbl) for lbl in labels))
    header = " " * (width + 2) + " ".join(f"{lbl:>{width}s}" for lbl in labels)
    print(header)
    for lbl, row in zip(labels, cm):
        print(f"  {lbl:<{width}s}" + " ".join(f"{v:>{width}d}" for v in row))
