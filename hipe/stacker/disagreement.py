"""Continuous disagreement features for the meta-classifier route.

Implements ``compute_disagreement_features`` from
``specs/HIPE2026_Disagreement_Stacker_Specs.md`` §3. These features are
intended for the *continuous* meta-classifier path that becomes viable on
larger training sets; the lookup table in :mod:`hipe.stacker.lookup` is
preferred at the n=188 single-split scale.

Feature blocks (per the spec §3.1):
- vote distribution (3): vote_frac_TRUE / PROBABLE / FALSE
- entropy + agreement (3): vote_entropy, unanimous, pairwise_disagreement
- ordinal-aware (2): ordinal_range, ordinal_std
- bimodality (1): bimodal_true_false   ← strongest single PROBABLE signal
- modal (2): modal_count, modal_is_probable
- per-model (K × 2): model_{k}_agrees, model_{k}_ordinal_dist
- optional confidence (K × 3): model_{k}_confidence/max_confidence/entropy
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence

from hipe.stacker.lookup import AT_ORDINAL_MAP

AT_LABELS: tuple[str, ...] = ("TRUE", "PROBABLE", "FALSE")


def compute_disagreement_features(
    base_predictions: Mapping[str, Sequence[str]],
    *,
    labels: Sequence[str] = AT_LABELS,
    ordinal_map: Mapping[str, int] = AT_ORDINAL_MAP,
    confidences: Mapping[str, Sequence[Mapping[str, float]]] | None = None,
) -> tuple[list[list[float]], list[str]]:
    """Compute per-instance disagreement features from K base models.

    Parameters
    ----------
    base_predictions : mapping of model_name -> list[str]
        K base models, each a list of N predictions over ``labels``.
    labels : sequence of str
        Label set L. Defaults to the `at` labels.
    ordinal_map : mapping
        Maps each label to an ordinal rank. Required for ordinal_range and
        ordinal_std. Defaults to TRUE=2, PROBABLE=1, FALSE=0.
    confidences : optional mapping of model_name -> list[dict]
        Per-instance label probability distributions for each model. When
        provided, three extra features per model are emitted.

    Returns
    -------
    (features, feature_names)
        ``features`` is a list of length N; each element a list of floats of
        length len(feature_names). ``feature_names`` is in stable order.
    """
    names = list(base_predictions.keys())
    cols = [list(base_predictions[n]) for n in names]
    if not cols:
        return [], []
    K = len(names)
    N = len(cols[0])
    for n, c in zip(names, cols):
        if len(c) != N:
            raise ValueError(f"model {n!r} has {len(c)} preds; expected {N}")

    # Resolve confidence columns once for fast indexing.
    conf_cols: list[list[Mapping[str, float]]] | None = None
    if confidences is not None:
        conf_cols = [list(confidences[n]) for n in names]
        for n, c in zip(names, conf_cols):
            if len(c) != N:
                raise ValueError(
                    f"confidences[{n!r}] has {len(c)} entries; expected {N}"
                )

    # Build feature names once so column order stays stable across calls.
    feature_names: list[str] = []
    feature_names += [f"vote_frac_{l}" for l in labels]
    feature_names += ["vote_entropy", "unanimous", "pairwise_disagreement"]
    feature_names += ["ordinal_range", "ordinal_std"]
    feature_names += ["bimodal_true_false"]
    feature_names += ["modal_count", "modal_is_probable"]
    for n in names:
        feature_names += [f"model_{n}_agrees", f"model_{n}_ordinal_dist"]
    if conf_cols is not None:
        for n in names:
            feature_names += [
                f"model_{n}_confidence",
                f"model_{n}_max_confidence",
                f"model_{n}_entropy",
            ]

    pair_denom = max(K * (K - 1) // 2, 1)

    out: list[list[float]] = []
    for i in range(N):
        votes = [cols[k][i] for k in range(K)]
        counts = Counter(votes)

        row: list[float] = []
        # vote distribution
        row.extend(counts.get(l, 0) / K for l in labels)
        # entropy
        ent = 0.0
        for l in labels:
            p = counts.get(l, 0) / K
            if p > 0:
                ent -= p * math.log(p)
        row.append(ent)
        # unanimous
        row.append(1.0 if len(set(votes)) == 1 else 0.0)
        # pairwise disagreement rate
        n_disagree = sum(
            1
            for a in range(K)
            for b in range(a + 1, K)
            if votes[a] != votes[b]
        )
        row.append(n_disagree / pair_denom)
        # ordinal range and std
        try:
            ordinals = [ordinal_map[v] for v in votes]
        except KeyError as e:
            raise ValueError(
                f"label {e.args[0]!r} not in ordinal_map={dict(ordinal_map)}"
            ) from None
        row.append(float(max(ordinals) - min(ordinals)))
        mean_ord = sum(ordinals) / K
        var = sum((x - mean_ord) ** 2 for x in ordinals) / K
        row.append(math.sqrt(var))
        # bimodality
        present = set(votes)
        bimodal = ("TRUE" in present and "FALSE" in present and "PROBABLE" not in present)
        row.append(1.0 if bimodal else 0.0)
        # modal
        modal_label, modal_n = counts.most_common(1)[0]
        row.append(modal_n / K)
        row.append(1.0 if modal_label == "PROBABLE" else 0.0)
        # per-model agreement with consensus + ordinal distance
        for k in range(K):
            row.append(1.0 if votes[k] == modal_label else 0.0)
            row.append(float(abs(ordinals[k] - ordinal_map[modal_label])))
        # optional confidence features
        if conf_cols is not None:
            for k in range(K):
                conf = conf_cols[k][i]
                pred_label = votes[k]
                p_pred = float(conf.get(pred_label, 0.5))
                p_max = max(float(v) for v in conf.values()) if conf else 0.5
                ent_k = 0.0
                for v in conf.values():
                    pv = float(v)
                    if pv > 0:
                        ent_k -= pv * math.log(pv)
                row.extend((p_pred, p_max, ent_k))

        out.append(row)
    return out, feature_names


__all__ = [
    "AT_LABELS",
    "compute_disagreement_features",
]
