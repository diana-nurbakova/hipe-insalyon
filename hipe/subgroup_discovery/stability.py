"""Cross-validated stability for discovered subgroups (Specs §7.1).

A subgroup is considered "stable" if it generalises across folds: when we
evaluate the *pattern* (not its training-fold extent) on the held-out fold,
its precision should remain non-trivial.

**Two stability criteria are reported (v3 §7.1):**

1. **String stability (legacy)** — patterns are aggregated by their canonical
   ``pattern_desc`` string. A pattern is stable if its exact string description
   crosses ``min_precision`` on at least ``min_folds`` folds. This was the v2
   default and empirically gave 0/5 across all classes: MCMC randomness produces
   different exact bounds each fold even when the underlying signal is identical.

2. **Semantic stability (recommended, v3)** — patterns are clustered across
   folds by Jaccard similarity over their extent on the *full* feature matrix.
   Two subgroups represent the "same" pattern when their full-X extents overlap
   by at least ``semantic_threshold``. A semantic cluster is stable when it has
   members from at least ``min_folds`` distinct folds, each with held-out
   precision >= ``min_precision``.
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
    semantic_stable_patterns: list[dict[str, object]]

    def n_stable(self) -> int:
        """Number of patterns stable under the string-equality criterion."""
        return len(self.stable_patterns)

    def n_semantic_stable(self) -> int:
        """Number of patterns stable under the Jaccard-cluster criterion (v3)."""
        return len(self.semantic_stable_patterns)


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


def _cluster_by_jaccard(
    sg_records: list[dict],
    threshold: float,
) -> list[list[int]]:
    """Greedy single-link clustering of subgroups by Jaccard on full-X extent.

    ``sg_records`` is a list of dicts each with at least ``"full_extent"``
    (a frozenset of row indices). Returns a list of clusters, each a list of
    indices into ``sg_records``. Greedy assignment with ``threshold`` controls
    cluster cohesion: a candidate joins the first cluster whose representative
    has Jaccard >= ``threshold``; otherwise it seeds a new cluster.
    """
    clusters: list[list[int]] = []
    reps: list[frozenset[int]] = []
    for i, rec in enumerate(sg_records):
        ext_i = rec["full_extent"]
        assigned = False
        for c_idx, rep in enumerate(reps):
            union = len(ext_i | rep)
            if union == 0:
                continue
            jaccard = len(ext_i & rep) / union
            if jaccard >= threshold:
                clusters[c_idx].append(i)
                assigned = True
                break
        if not assigned:
            clusters.append([i])
            reps.append(ext_i)
    return clusters


def cv_stability(
    X: np.ndarray,
    y: Sequence[str] | np.ndarray,
    feature_names: Sequence[str],
    *,
    target_class: str = "PROBABLE",
    n_folds: int = 5,
    min_precision: float = 0.3,
    min_folds: int = 3,
    semantic_threshold: float = 0.5,
    sd_kwargs: dict | None = None,
    random_state: int = 42,
    verbose: bool = True,
) -> StabilityReport:
    """k-fold stability evaluation for MCMC-COTP subgroups (Specs v3 §7.1).

    For each fold:
      1. Run MCMC-COTP on the training portion.
      2. Evaluate every discovered pattern on the held-out portion.
      3. Record its full-X extent (used for the semantic clustering pass).

    Then aggregate stability under two criteria:

    - **String stability:** group by canonical ``pattern_desc``; a pattern is
      stable iff held-out precision >= ``min_precision`` on at least
      ``min_folds`` folds.
    - **Semantic stability (v3):** cluster every discovered subgroup across all
      folds by Jaccard >= ``semantic_threshold`` on the full-X extent. A cluster
      is stable iff it contains members from at least ``min_folds`` distinct
      folds whose held-out precision is >= ``min_precision``.
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
    sg_records: list[dict] = []

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
            full_extent = frozenset(np.where(sg.matches(X))[0].tolist())
            sg_records.append(
                {
                    "fold": fold_idx,
                    "pattern_desc": sg.pattern_desc,
                    "train_nwracc": float(sg.nwracc),
                    "train_precision": float(sg.precision),
                    "val_precision": float(ev["precision"]),
                    "val_recall": float(ev["recall"]),
                    "val_support": int(ev["support"]),
                    "val_support_pos": int(ev["support_pos"]),
                    "full_extent": full_extent,
                    "full_extent_size": len(full_extent),
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

    # --- String-equality stability (legacy) -----------------------------------
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

    # --- Semantic / Jaccard stability (v3) ------------------------------------
    semantic_stable = _semantic_stability_from_records(
        sg_records,
        threshold=semantic_threshold,
        min_precision=min_precision,
        min_folds=min_folds,
    )

    if verbose:
        print(
            f"  string-stable patterns   : {len(stable)} "
            f"(prec >= {min_precision} on >= {min_folds}/{n_folds} folds)"
        )
        print(
            f"  semantic-stable clusters : {len(semantic_stable)} "
            f"(Jaccard >= {semantic_threshold}, prec >= {min_precision} "
            f"on >= {min_folds}/{n_folds} folds)"
        )

    return StabilityReport(
        folds=fold_results,
        stable_patterns=stable,
        semantic_stable_patterns=semantic_stable,
    )


def _semantic_stability_from_records(
    sg_records: list[dict],
    *,
    threshold: float,
    min_precision: float,
    min_folds: int,
) -> list[dict[str, object]]:
    """Cluster cross-fold subgroups by full-X extent Jaccard, then filter.

    A semantic cluster is "stable" when it contains members from at least
    ``min_folds`` distinct folds whose held-out precision >= ``min_precision``.
    """
    if not sg_records:
        return []

    clusters = _cluster_by_jaccard(sg_records, threshold=threshold)

    stable_clusters: list[dict[str, object]] = []
    for member_ids in clusters:
        members = [sg_records[i] for i in member_ids]
        good_folds = {
            m["fold"] for m in members if m["val_precision"] >= min_precision
        }
        if len(good_folds) < min_folds:
            continue
        # Pick a representative: highest val_precision, tie-break on cluster size.
        members_sorted = sorted(
            members, key=lambda m: (m["val_precision"], m["full_extent_size"]),
            reverse=True,
        )
        rep = members_sorted[0]
        all_folds = sorted({m["fold"] for m in members})
        stable_clusters.append(
            {
                "representative_pattern": rep["pattern_desc"],
                "n_members": len(members),
                "n_folds_seen": len(all_folds),
                "n_folds_stable": len(good_folds),
                "folds_stable": sorted(good_folds),
                "mean_val_precision": float(
                    np.mean([m["val_precision"] for m in members])
                ),
                "mean_val_recall": float(
                    np.mean([m["val_recall"] for m in members])
                ),
                "mean_train_nwracc": float(
                    np.mean([m["train_nwracc"] for m in members])
                ),
                "member_patterns": sorted({m["pattern_desc"] for m in members}),
            }
        )
    stable_clusters.sort(
        key=lambda r: (r["n_folds_stable"], r["mean_val_precision"]),
        reverse=True,
    )
    return stable_clusters


def semantic_stability(
    fold_subgroups: Sequence[Sequence[Subgroup]],
    X: np.ndarray,
    *,
    threshold: float = 0.5,
    min_precision: float = 0.0,
    min_folds: int = 3,
    val_evals: Sequence[Sequence[dict[str, float]]] | None = None,
) -> list[dict[str, object]]:
    """Public helper: cluster subgroups across folds by full-X extent Jaccard.

    Convenience for callers that already have per-fold subgroups (and optionally
    held-out evaluations) and want only the v3 semantic-stability list. If
    ``val_evals`` is omitted, every member is treated as having
    ``val_precision = 1.0`` so the precision filter is a no-op.
    """
    sg_records: list[dict] = []
    for fold_idx, sgs in enumerate(fold_subgroups):
        evals = (
            val_evals[fold_idx]
            if val_evals is not None and fold_idx < len(val_evals)
            else [None] * len(sgs)
        )
        for sg, ev in zip(sgs, evals):
            full_extent = frozenset(np.where(sg.matches(X))[0].tolist())
            sg_records.append(
                {
                    "fold": fold_idx,
                    "pattern_desc": sg.pattern_desc,
                    "train_nwracc": float(sg.nwracc),
                    "train_precision": float(sg.precision),
                    "val_precision": float(ev["precision"]) if ev else 1.0,
                    "val_recall": float(ev["recall"]) if ev else 0.0,
                    "val_support": int(ev["support"]) if ev else 0,
                    "val_support_pos": int(ev["support_pos"]) if ev else 0,
                    "full_extent": full_extent,
                    "full_extent_size": len(full_extent),
                }
            )
    return _semantic_stability_from_records(
        sg_records,
        threshold=threshold,
        min_precision=min_precision,
        min_folds=min_folds,
    )
