"""Lookup-table stacker for the `at` task.

Implements the vote-tuple → mode-of-gold mapping described in
``specs/HIPE2026_Disagreement_Stacker_Specs.md`` §2 and §5.

The stacker works because, with K=3 base models and 3 labels, only 27 vote
tuples are possible. With ~188 training instances, each cell averages ~7
samples — enough to read off an empirical mode but too few to fit any
parameterised meta-classifier without overfitting. Per the spec §2.2, this
lookup IS the optimal meta-classifier for the regime.

Public surface
--------------
- :data:`AT_ORDINAL_MAP`              — default ordinal map for the `at` labels
- :func:`build_lookup_table`          — direct mode-of-gold per cell
- :func:`apply_lookup`                — apply a pre-built lookup, with fallbacks
- :func:`loo_lookup_predictions`      — leave-one-out evaluation predictions
- :func:`resolve_with_fallbacks`      — single-instance resolution helper
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

# Default ordinal map for the `at` task: TRUE > PROBABLE > FALSE.
# Used for the §5.2 level-3 fallback (ordinal median across the K votes).
AT_ORDINAL_MAP: dict[str, int] = {"TRUE": 2, "PROBABLE": 1, "FALSE": 0}


def _vote_tuples(
    base_predictions: Mapping[str, Sequence[str]],
) -> tuple[list[tuple[str, ...]], list[str]]:
    """Return (per-instance vote tuples, model name order). Validates shape."""
    if not base_predictions:
        raise ValueError("base_predictions is empty")
    names = list(base_predictions.keys())
    cols = [list(base_predictions[n]) for n in names]
    n_inst = len(cols[0])
    for n, c in zip(names, cols):
        if len(c) != n_inst:
            raise ValueError(
                f"model {n!r} has {len(c)} predictions; expected {n_inst}"
            )
    tuples = [tuple(c[i] for c in cols) for i in range(n_inst)]
    return tuples, names


def _resolve_tie(
    vote_tuple: tuple[str, ...],
    winners: list[str],
    *,
    tiebreaker: str,
    ordinal_map: Mapping[str, int] | None,
    model_names: Sequence[str] | None,
) -> str:
    """Pick one label from ``winners`` (the labels tied for max count in a cell).

    Tiebreakers:
    - ``alphabetical``  : ``sorted(winners)[0]`` — deterministic, ignores semantics.
    - ``ordinal_median``: use the ordinal median of the *vote tuple* if it sits
      among the tied winners; else fall through to alphabetical. Mirrors the
      §5.2 level-3 fallback so within-cell ties and unseen cells are resolved
      with the same logic.
    - ``last_model``    : the last-listed model's vote for this instance, if it
      is among the tied winners; else alphabetical. Practical when one base
      model is known to be strongest at the contested label.
    """
    if len(winners) == 1:
        return winners[0]
    if tiebreaker == "ordinal_median" and ordinal_map is not None:
        try:
            ordinals = sorted(ordinal_map[v] for v in vote_tuple)
            median_ord = ordinals[len(ordinals) // 2]
            inv = {v: k for k, v in ordinal_map.items()}
            cand = inv.get(median_ord)
            if cand in winners:
                return cand
        except KeyError:
            pass
    if tiebreaker == "last_model" and model_names:
        last_idx = len(model_names) - 1
        last_vote = vote_tuple[last_idx]
        if last_vote in winners:
            return last_vote
    return sorted(winners)[0]


def build_lookup_table(
    base_predictions: Mapping[str, Sequence[str]],
    gold: Sequence[str | None],
    *,
    tiebreaker: str = "ordinal_median",
    ordinal_map: Mapping[str, int] | None = None,
) -> dict[tuple[str, ...], str]:
    """Build a vote-tuple → mode-of-gold lookup table.

    Rows with ``gold is None`` are skipped (they carry no supervision signal).
    Within-cell ties are resolved by ``tiebreaker``; see :func:`_resolve_tie`.
    The default ``ordinal_median`` matches the §5.2 fallback hierarchy so
    within-cell ties and unseen cells share the same resolution logic.

    Parameters
    ----------
    base_predictions : mapping of model_name -> list[str]
        K base models, each a list of N predictions. Insertion order defines
        the vote-tuple ordering.
    gold : list[str | None]
        Length-N gold labels.
    tiebreaker : str
        ``"alphabetical"``, ``"ordinal_median"``, or ``"last_model"``.
    ordinal_map : mapping
        Required for ``tiebreaker="ordinal_median"``. Defaults to ``AT_ORDINAL_MAP``
        when not provided.

    Returns
    -------
    dict[tuple[str, ...], str]
        Map from vote tuple to predicted (modal) label.
    """
    tuples, names = _vote_tuples(base_predictions)
    if len(tuples) != len(gold):
        raise ValueError(
            f"len(gold)={len(gold)} but {len(tuples)} prediction rows"
        )
    if ordinal_map is None:
        ordinal_map = AT_ORDINAL_MAP
    cells: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    for t, g in zip(tuples, gold):
        if g is None:
            continue
        cells[t][g] += 1
    lookup: dict[tuple[str, ...], str] = {}
    for t, c in cells.items():
        best = max(c.values())
        winners = [label for label, n in c.items() if n == best]
        lookup[t] = _resolve_tie(
            t, winners,
            tiebreaker=tiebreaker, ordinal_map=ordinal_map, model_names=names,
        )
    return lookup


def resolve_with_fallbacks(
    vote_tuple: tuple[str, ...],
    lookup: Mapping[tuple[str, ...], str],
    *,
    fallback: str = "majority",
    fallback_label: str = "FALSE",
    ordinal_map: Mapping[str, int] | None = None,
) -> str:
    """Resolve one vote tuple using the §5.2 fallback hierarchy.

    1. Exact match in ``lookup``.
    2. Majority vote across the tuple (when 2+ votes agree, take their label).
    3. Ordinal median (only used when ``fallback='ordinal'`` AND no majority).
       For an even-length tuple, takes the upper-median element after sort.
    4. ``fallback_label``.

    Levels 2 and 3 only fire when the exact tuple is unseen. Level 3 is the
    elegant solution for three-way (T, P, F) ties: the ordinal median is
    PROBABLE, which is the right answer for instances where models span the
    full range of confidence.
    """
    if vote_tuple in lookup:
        return lookup[vote_tuple]
    if fallback in ("majority", "ordinal"):
        c = Counter(vote_tuple)
        modal_label, modal_n = c.most_common(1)[0]
        if modal_n >= 2:
            return modal_label
        if fallback == "ordinal" and ordinal_map is not None:
            try:
                ordinals = sorted(ordinal_map[v] for v in vote_tuple)
            except KeyError:
                return fallback_label
            median_ord = ordinals[len(ordinals) // 2]
            inv = {v: k for k, v in ordinal_map.items()}
            if median_ord in inv:
                return inv[median_ord]
    return fallback_label


def apply_lookup(
    base_predictions: Mapping[str, Sequence[str]],
    lookup: Mapping[tuple[str, ...], str],
    *,
    fallback: str = "majority",
    fallback_label: str = "FALSE",
    ordinal_map: Mapping[str, int] | None = None,
) -> list[str]:
    """Apply a pre-built lookup table to new instances. See :func:`resolve_with_fallbacks`
    for fallback semantics. The same ``base_predictions`` keys (and order) used
    when building the lookup must be used here.

    Within-cell tie-breaking is already baked into the lookup (decided when it
    was built); this function only resolves *unseen* tuples via the fallback
    hierarchy.
    """
    tuples, _ = _vote_tuples(base_predictions)
    return [
        resolve_with_fallbacks(
            t, lookup,
            fallback=fallback,
            fallback_label=fallback_label,
            ordinal_map=ordinal_map,
        )
        for t in tuples
    ]


def loo_lookup_predictions(
    base_predictions: Mapping[str, Sequence[str]],
    gold: Sequence[str | None],
    *,
    tiebreaker: str = "ordinal_median",
    fallback: str = "majority",
    fallback_label: str = "FALSE",
    ordinal_map: Mapping[str, int] | None = None,
) -> list[str]:
    """Leave-one-out predictions from the lookup-table stacker.

    For each instance i, builds a lookup table from the other N-1 rows and
    applies it to row i. This is the honest evaluation procedure on a
    fixed-size dataset — every prediction is made without seeing its own
    gold label.

    Within-cell ties (after subtracting instance i) are resolved by
    ``tiebreaker``; empty cells (singleton case after LOO subtract) fall
    through to the §5.2 hierarchy via ``fallback``.

    Time complexity is O(N * U) where U is the number of unique vote tuples
    (≤ |labels|^K). For N=188 and U=27 this is fast (<1s).
    """
    tuples, names = _vote_tuples(base_predictions)
    if len(tuples) != len(gold):
        raise ValueError(
            f"len(gold)={len(gold)} but {len(tuples)} prediction rows"
        )
    if ordinal_map is None:
        ordinal_map = AT_ORDINAL_MAP

    cells_total: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    for t, g in zip(tuples, gold):
        if g is None:
            continue
        cells_total[t][g] += 1

    out: list[str] = []
    for t_i, g_i in zip(tuples, gold):
        # Subtract this instance's contribution from its cell's counter, if any.
        cell = cells_total.get(t_i, Counter()).copy()
        if g_i is not None:
            cell[g_i] -= 1
            if cell[g_i] <= 0:
                del cell[g_i]
        if cell:
            best = max(cell.values())
            winners = [label for label, n in cell.items() if n == best]
            out.append(_resolve_tie(
                t_i, winners,
                tiebreaker=tiebreaker, ordinal_map=ordinal_map, model_names=names,
            ))
        else:
            # No other rows in this cell — fall back per the configured policy.
            out.append(
                resolve_with_fallbacks(
                    t_i, {},
                    fallback=fallback,
                    fallback_label=fallback_label,
                    ordinal_map=ordinal_map,
                )
            )
    return out


def cell_summary(
    base_predictions: Mapping[str, Sequence[str]],
    gold: Sequence[str | None],
) -> list[dict[str, Any]]:
    """Return one row per occupied cell with size, modal gold, and class breakdown.

    Used for §9.2-style stacker introspection — useful both for the report
    and for sanity checks on test-time deployment.
    """
    tuples, names = _vote_tuples(base_predictions)
    cells: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    for t, g in zip(tuples, gold):
        if g is None:
            continue
        cells[t][g] += 1
    rows: list[dict[str, Any]] = []
    for t, c in sorted(cells.items()):
        total = sum(c.values())
        best_n = max(c.values())
        modal = sorted(l for l, n in c.items() if n == best_n)[0]
        rows.append({
            "cell": dict(zip(names, t)),
            "n": total,
            "modal_gold": modal,
            "breakdown": dict(c),
        })
    rows.sort(key=lambda r: -r["n"])
    return rows
