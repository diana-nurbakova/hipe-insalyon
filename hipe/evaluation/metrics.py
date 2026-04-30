"""Official HIPE-2026 scoring primitives.

Implements macro Recall (balanced accuracy) per the guidelines (Section 3.1
of HIPE2026_Evaluation_Submission_Specs.md):

    MacroRecall = (1/|L|) * sum_{l in L} Recall(l)
    Recall(l)   = #(gold==l & pred==l) / #(gold==l)

For ``at``  the label set is ('TRUE', 'PROBABLE', 'FALSE')   (|L|=3).
For ``isAt`` the label set is ('TRUE', 'FALSE')              (|L|=2).
The global score is the unweighted mean of the two macro recalls.

Per the guidelines, any ``null`` prediction is interpreted as ``FALSE`` at
evaluation time -- :func:`null_to_false` applies that rule.

The implementation is intentionally dependency-free (pure Python) so it can
be imported without pulling in numpy / sklearn. Callers that want richer
artifacts (confusion matrices, classification reports) can use
``hipe.evaluation.report``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

AT_LABELS: tuple[str, ...] = ("TRUE", "PROBABLE", "FALSE")
ISAT_LABELS: tuple[str, ...] = ("TRUE", "FALSE")


def null_to_false(label: str | None) -> str:
    """Apply the official null -> FALSE rule."""
    return "FALSE" if label is None else label


def _validate_labels(values: Sequence[str], allowed: Sequence[str], field: str) -> None:
    extras = {v for v in values if v not in allowed}
    if extras:
        raise ValueError(
            f"Unexpected {field} labels {sorted(extras)!r}; allowed: {list(allowed)!r}"
        )


def compute_macro_recall(
    y_gold: Sequence[str],
    y_pred: Sequence[str],
    label_set: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compute per-label recall and the macro recall (balanced accuracy).

    Parameters
    ----------
    y_gold, y_pred : sequence of str
        Same-length sequences of gold and predicted labels. ``None`` is not
        allowed -- callers must apply :func:`null_to_false` first.
    label_set : sequence of str, optional
        The label set L to average over. Defaults to ``sorted(set(y_gold))``.
        Pass an explicit list (e.g. ``AT_LABELS``) when some labels may be
        absent from the gold sample so the macro mean is over the full L.

    Returns
    -------
    dict with keys ``recall_<label>`` (per-label, ``None`` if no gold support)
    and ``macro_recall`` (mean over labels with non-null support).
    """
    if len(y_gold) != len(y_pred):
        raise ValueError(
            f"y_gold and y_pred must have equal length, got {len(y_gold)} vs {len(y_pred)}"
        )

    if label_set is None:
        label_set = sorted(set(y_gold))

    results: dict[str, Any] = {}
    recalls: list[float] = []

    for label in label_set:
        gold_count = sum(1 for g in y_gold if g == label)
        if gold_count == 0:
            results[f"recall_{label}"] = None
            continue
        correct = sum(1 for g, p in zip(y_gold, y_pred) if g == label and p == label)
        recall = correct / gold_count
        results[f"recall_{label}"] = recall
        recalls.append(recall)

    results["macro_recall"] = sum(recalls) / len(recalls) if recalls else 0.0
    return results


def compute_global_score(
    at_gold: Sequence[str],
    at_pred: Sequence[str],
    isAt_gold: Sequence[str],
    isAt_pred: Sequence[str],
) -> dict[str, Any]:
    """Compute the official HIPE-2026 GlobalScoreA.

        GlobalScoreA = (MacroRecall_at + MacroRecall_isAt) / 2

    Always uses the full label sets (``AT_LABELS`` / ``ISAT_LABELS``) so the
    macro mean is over the same denominator regardless of which classes
    happen to appear in the dev sample.
    """
    _validate_labels(at_gold, AT_LABELS, "at gold")
    _validate_labels(at_pred, AT_LABELS, "at pred")
    _validate_labels(isAt_gold, ISAT_LABELS, "isAt gold")
    _validate_labels(isAt_pred, ISAT_LABELS, "isAt pred")

    at_results = compute_macro_recall(at_gold, at_pred, label_set=AT_LABELS)
    isAt_results = compute_macro_recall(isAt_gold, isAt_pred, label_set=ISAT_LABELS)

    global_score = (at_results["macro_recall"] + isAt_results["macro_recall"]) / 2

    return {
        "global_score": global_score,
        "macro_recall_at": at_results["macro_recall"],
        "macro_recall_isAt": isAt_results["macro_recall"],
        "at_details": at_results,
        "isAt_details": isAt_results,
    }


def confusion_matrix(
    y_gold: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
) -> list[list[int]]:
    """Confusion matrix as nested lists. Rows = gold, columns = pred."""
    n = len(labels)
    idx = {lbl: i for i, lbl in enumerate(labels)}
    cm = [[0] * n for _ in range(n)]
    for g, p in zip(y_gold, y_pred):
        if g in idx and p in idx:
            cm[idx[g]][idx[p]] += 1
    return cm


def classification_report(
    y_gold: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Per-label precision / recall / f1 / support, plus macro / weighted means.

    Mirrors the structure of ``sklearn.metrics.classification_report(output_dict=True)``
    for the fields we actually use. Avoids the sklearn dependency.
    """
    report: dict[str, dict[str, float]] = {}
    n_total = len(y_gold)
    macro_p = macro_r = macro_f = 0.0
    weighted_p = weighted_r = weighted_f = 0.0
    n_with_support = 0

    for label in labels:
        tp = sum(1 for g, p in zip(y_gold, y_pred) if g == label and p == label)
        fp = sum(1 for g, p in zip(y_gold, y_pred) if g != label and p == label)
        fn = sum(1 for g, p in zip(y_gold, y_pred) if g == label and p != label)
        support = tp + fn

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            (2 * precision * recall) / (precision + recall)
            if (precision + recall)
            else 0.0
        )

        report[label] = {
            "precision": precision,
            "recall": recall,
            "f1-score": f1,
            "support": support,
        }
        if support:
            n_with_support += 1
            macro_p += precision
            macro_r += recall
            macro_f += f1
            weighted_p += precision * support
            weighted_r += recall * support
            weighted_f += f1 * support

    if n_with_support:
        report["macro avg"] = {
            "precision": macro_p / n_with_support,
            "recall": macro_r / n_with_support,
            "f1-score": macro_f / n_with_support,
            "support": n_total,
        }
    if n_total:
        report["weighted avg"] = {
            "precision": weighted_p / n_total,
            "recall": weighted_r / n_total,
            "f1-score": weighted_f / n_total,
            "support": n_total,
        }
    return report
