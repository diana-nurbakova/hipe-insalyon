"""HIPE-2026 official scoring + experiment harness.

See ``specs/HIPE2026_Evaluation_Submission_Specs.md`` Section 3 (metrics)
and Section 7 (development workflow).
"""

from hipe.evaluation.experiment import run_ablation_experiment
from hipe.evaluation.metrics import (
    AT_LABELS,
    ISAT_LABELS,
    classification_report,
    compute_global_score,
    compute_macro_recall,
    confusion_matrix,
    null_to_false,
)
from hipe.evaluation.report import generate_evaluation_report, print_report

__all__ = [
    "AT_LABELS",
    "ISAT_LABELS",
    "compute_macro_recall",
    "compute_global_score",
    "null_to_false",
    "classification_report",
    "confusion_matrix",
    "generate_evaluation_report",
    "print_report",
    "run_ablation_experiment",
]
