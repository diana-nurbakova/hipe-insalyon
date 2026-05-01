"""Submission file generation + official tooling wrappers.

See ``specs/HIPE2026_Evaluation_Submission_Specs.md`` Section 4 (file format)
and Section 5 (pipeline integration).
"""

from hipe.submission.tools import (
    DEFAULT_TOOLS_ENV,
    SchemaCheckResult,
    ScorerConsistencyResult,
    ScorerResult,
    default_schema_file,
    default_tools_dir,
    establish_baseline,
    package_runs,
    run_dummy_predict,
    run_official_scorer,
    validate_submission,
    verify_scorer_consistency,
)
from hipe.submission.writer import (
    Prediction,
    PredictionKey,
    SubmissionStats,
    generate_submission_file,
    predictions_from_records,
    submission_filename,
)

__all__ = [
    "Prediction",
    "PredictionKey",
    "SubmissionStats",
    "generate_submission_file",
    "predictions_from_records",
    "submission_filename",
    "DEFAULT_TOOLS_ENV",
    "SchemaCheckResult",
    "ScorerConsistencyResult",
    "ScorerResult",
    "default_schema_file",
    "default_tools_dir",
    "establish_baseline",
    "package_runs",
    "run_dummy_predict",
    "run_official_scorer",
    "validate_submission",
    "verify_scorer_consistency",
]
