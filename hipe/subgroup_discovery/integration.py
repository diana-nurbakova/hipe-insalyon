"""Pipeline integration for discovered subgroups (Specs §6).

Three integration options, all interoperable with the hybrid RF + MASK
classifier:

* Option A — append "matches subgroup k" indicator features and retrain.
* Option B — flip predicted FALSE → PROBABLE for instances matching a
  high-quality PROBABLE subgroup (zero retraining).
* Option C — translate subgroups to natural-language rules for prompt
  injection.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np

from hipe.subgroup_discovery.mcmc import Subgroup


# --------------------------------------------------------------------- A

def add_subgroup_features(
    X: np.ndarray,
    subgroups: Sequence[Subgroup],
) -> tuple[np.ndarray, list[str]]:
    """Append one binary "matches subgroup" column per subgroup to ``X``.

    Returns the augmented array and the new column names.
    """
    X = np.asarray(X)
    if not subgroups:
        return X.astype(np.float32, copy=True), []
    sg_features = np.zeros((X.shape[0], len(subgroups)), dtype=np.float32)
    for k, s in enumerate(subgroups):
        # Use the original-precision X so subgroup boundaries match exactly.
        sg_features[:, k] = s.matches(X).astype(np.float32)
    aug = np.hstack([X.astype(np.float32, copy=False), sg_features]).astype(
        np.float32, copy=False
    )
    names = [
        f"sg_{(s.target_class or 'POS').lower()}_{k}"
        for k, s in enumerate(subgroups)
    ]
    return aug, names


# --------------------------------------------------------------------- B

def apply_overrides(
    preds: Sequence[str],
    X: np.ndarray,
    subgroups: Sequence[Subgroup],
    *,
    target: str = "PROBABLE",
    only_from: Iterable[str] = ("FALSE",),
    min_nwracc: float = 0.4,
    min_precision: float = 0.0,
    verbose: bool = True,
) -> tuple[list[str], int]:
    """Flip predictions matching a discovered subgroup to ``target``.

    Parameters
    ----------
    preds : sequence of str
        Existing classifier predictions.
    X : (N, D) array
        Feature matrix in the same space the subgroups were discovered on.
    subgroups : sequence of Subgroup
        Should target the class we want to override *to* (``target``).
    only_from : iterable of str
        Predictions in this set are eligible for override. Defaults to
        ``("FALSE",)`` so we only rescue PROBABLE from FALSE.
    min_nwracc, min_precision : float
        Quality gates on the subgroups before they're allowed to fire.
    """
    preds = list(preds)
    only_from_set = set(only_from)
    overrides = 0
    if len(preds) == 0 or not subgroups:
        if verbose:
            print(f"Overrides: 0 -> {target}")
        return preds, 0

    X = np.asarray(X)
    eligible_match = np.zeros(X.shape[0], dtype=bool)
    for s in subgroups:
        if s.nwracc < min_nwracc or s.precision < min_precision:
            continue
        eligible_match |= s.matches(X)

    for i, was_match in enumerate(eligible_match):
        if not was_match:
            continue
        if preds[i] in only_from_set and preds[i] != target:
            preds[i] = target
            overrides += 1

    if verbose:
        from_str = "/".join(sorted(only_from_set))
        print(f"Overrides: {overrides} {from_str} -> {target}")
    return preds, overrides


# --------------------------------------------------------------------- C

def subgroup_to_prompt_rule(
    sg: Subgroup,
    *,
    target: str | None = None,
) -> str:
    """Render one subgroup as a single natural-language rule.

    Output format follows Specs §6.3 — antecedent in plain English, target
    consequent, plus precision / NWRAcc / support stats so the LLM can weigh
    the rule strength.
    """
    target = target or sg.target_class or "POSITIVE"
    return (
        f"When {sg.pattern_desc} → consider {target} "
        f"(precision {sg.precision * 100:.0f}% on training, "
        f"NWRAcc={sg.nwracc:.3f}, support={sg.support_pos}/{sg.support})"
    )


def subgroups_to_prompt_block(
    subgroups: Sequence[Subgroup],
    *,
    target: str | None = None,
    header: str = "Discovered class-discriminative rules:",
) -> str:
    """Pack a list of subgroups into a bulleted prompt block."""
    if not subgroups:
        return ""
    lines = [header]
    for sg in subgroups:
        lines.append("- " + subgroup_to_prompt_rule(sg, target=target))
    return "\n".join(lines)


# -------------------------------------------------------------- summaries

def summarize(
    subgroups: Sequence[Subgroup],
    *,
    feature_names: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Lightweight serialisable summary for logs / reports."""
    rows: list[dict[str, Any]] = []
    for k, s in enumerate(subgroups):
        names = feature_names if feature_names is not None else s.feature_names
        active_names = (
            [names[f] for f in np.where(s.active)[0]]
            if names is not None
            else [int(f) for f in np.where(s.active)[0]]
        )
        rows.append(
            {
                "rank": k + 1,
                "target_class": s.target_class,
                "pattern": s.pattern_desc,
                "active_features": active_names,
                "n_active": s.n_active(),
                "nwracc": round(float(s.nwracc), 4),
                "support": int(s.support),
                "support_pos": int(s.support_pos),
                "precision": round(float(s.precision), 4),
            }
        )
    return rows
