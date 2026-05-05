"""Disagreement-aware stacker for the `at` task.

Implements ``specs/HIPE2026_Disagreement_Stacker_Specs.md``.

Public surface
--------------
- :data:`AT_ORDINAL_MAP`              — ordinal map (TRUE=2, PROBABLE=1, FALSE=0)
- :func:`build_lookup_table`          — direct mode-of-gold per cell
- :func:`apply_lookup`                — apply a built lookup with fallbacks
- :func:`loo_lookup_predictions`      — leave-one-out evaluation
- :func:`resolve_with_fallbacks`      — single-tuple resolution helper
- :func:`cell_summary`                — per-cell n + modal_gold + breakdown
- :func:`compute_disagreement_features` — continuous meta-features (§3)
"""

from hipe.stacker.disagreement import (
    AT_LABELS,
    compute_disagreement_features,
)
from hipe.stacker.lookup import (
    AT_ORDINAL_MAP,
    apply_lookup,
    build_lookup_table,
    cell_summary,
    loo_lookup_predictions,
    resolve_with_fallbacks,
)

__all__ = [
    "AT_LABELS",
    "AT_ORDINAL_MAP",
    "apply_lookup",
    "build_lookup_table",
    "cell_summary",
    "compute_disagreement_features",
    "loo_lookup_predictions",
    "resolve_with_fallbacks",
]
