"""Cross-validated stability for discovered subgroups (Specs §7.1).

A subgroup is considered "stable" if it generalises across folds: when we
evaluate the *pattern* (not its training-fold extent) on the held-out fold,
its precision should remain non-trivial. We follow the spec's definition of
``precision >= 0.3`` on ``>= 3/5`` folds.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from hipe.subgroup_discovery.mcmc import MCMCSubgroupDiscovery, Subgroup


@dataclass
class FoldResult:
    fold: int
    train_subgroups: list[Subgroup]
    val_eval: list[dict[str, float]]


@dataclass
class StabilityReport:
    folds: list[FoldResult]
    stable_patterns: list[dict[str, object]]

    def n_stable(self) -> int:
        return len(self.stable_patterns)


def _eval_on_holdout(
    subgroups: Sequence[Subgroup],
    X_val: np.ndarray,
    y_val: np.ndarray,
    target_class: str,
) -> list[dict[str, float]]:
    """Compute per-subgroup support, precision, recall on a held-out fold."""
    out: list[dict[str, float]] = []
    pos_val = (y_val == target_class)
    n_pos = int(pos_val.sum())
    for sg in subgroups:
        match = sg.matches(X_val)
        support = int(match.sum())
        support_pos = int((match & pos_val).sum())
        precision = support_pos / support if support > 0 else 0.0
        recall = support_pos / n_pos if n_pos > 0 else 0.0
        out.append(
            {
                "support": support,
                "support_pos": support_pos,
                "precision": precision,
                "recall": recall,
            }
        )
    return out


def cv_stability(
    X: np.ndarray,
    y: Sequence[str] | np.ndarray,
    feature_names: Sequence[str],
    *,
    target_class: str = "PROBABLE",
    n_folds: int = 5,
    min_precision: float = 0.3,
    min_folds: int = 3,
    sd_kwargs: dict | None = None,
    random_state: int = 42,
    verbose: bool = True,
) -> StabilityReport:
    """k-fold stability evaluation for MCMC-COTP subgroups.

    For each fold:
      1. Run MCMC-COTP on the training portion.
      2. Evaluate every discovered pattern on the held-out portion.
    Then aggregate: a *pattern signature* (the canonical description string)
    is "stable" if it crosses ``min_precision`` on at least ``min_folds`` of
    the folds.
    """
    from sklearn.model_selection import StratifiedKFold

    X = np.asarray(X)
    y = np.asarray(y)

    sd_kwargs = dict(sd_kwargs or {})
    sd_kwargs.setdefault("n_chains", 10)
    sd_kwargs.setdefault("n_steps", 5000)
    sd_kwargs.setdefault("top_k", 20)
    sd_kwargs["target_class"] = target_class
    # ``random_state`` is injected per-fold below — drop any duplicate that
    # callers may have shipped via ``sd_kwargs``.
    sd_kwargs.pop("random_state", None)

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    fold_results: list[FoldResult] = []
    pattern_stats: dict[str, list[dict[str, float]]] = {}

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_va, y_va = X[val_idx], y[val_idx]

        sd = MCMCSubgroupDiscovery(
            feature_names=feature_names,
            random_state=random_state + fold_idx,
            **sd_kwargs,
        )
        if (y_tr == target_class).sum() < 2:
            if verbose:
                print(f"[fold {fold_idx}] skipped — fewer than 2 positives in train")
            continue
        subgroups = sd.fit(X_tr, y_tr)

        val_eval = _eval_on_holdout(subgroups, X_va, y_va, target_class)
        for sg, ev in zip(subgroups, val_eval):
            pattern_stats.setdefault(sg.pattern_desc, []).append(
                {
                    "fold": fold_idx,
                    "train_nwracc": sg.nwracc,
                    "train_precision": sg.precision,
                    **ev,
                }
            )

        fold_results.append(
            FoldResult(fold=fold_idx, train_subgroups=subgroups, val_eval=val_eval)
        )
        if verbose:
            mean_p = (
                float(np.mean([e["precision"] for e in val_eval])) if val_eval else 0.0
            )
            print(
                f"[fold {fold_idx}] discovered {len(subgroups)} subgroups; "
                f"mean held-out precision = {mean_p:.3f}"
            )

    stable: list[dict[str, object]] = []
    for pattern, stats in pattern_stats.items():
        good = [s for s in stats if s["precision"] >= min_precision]
        if len(good) >= min_folds:
            stable.append(
                {
                    "pattern": pattern,
                    "n_folds_stable": len(good),
                    "mean_precision": float(
                        np.mean([s["precision"] for s in stats])
                    ),
                    "mean_recall": float(np.mean([s["recall"] for s in stats])),
                    "n_folds_seen": len(stats),
                }
            )
    stable.sort(key=lambda r: (r["n_folds_stable"], r["mean_precision"]), reverse=True)
    return StabilityReport(folds=fold_results, stable_patterns=stable)
