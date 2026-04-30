"""Unit tests for ``hipe.subgroup_discovery``.

Covers:
- MEET proposal generates a pattern containing both seeds.
- COTP closure tightens to the MBR of positives in extent and is idempotent.
- NWRAcc edge cases: empty extent, full universe.
- Redundancy filter drops near-duplicate extents.
- Synthetic discovery: a hidden positive box is recovered.
- Integration helpers: feature augmentation + post-hoc overrides.
"""

from __future__ import annotations

import numpy as np
import pytest

from hipe.subgroup_discovery import (
    MCMCSubgroupDiscovery,
    Subgroup,
    add_subgroup_features,
    apply_overrides,
    subgroup_to_prompt_rule,
)


# --------------------------------------------------------------------- helpers

def _simple_dataset(n_per_class: int = 60, seed: int = 0):
    """A dataset where a hidden positive box covers x0 in [4,6] AND x1 in [4,6]."""
    rng = np.random.RandomState(seed)
    pos = rng.uniform(low=4.0, high=6.0, size=(n_per_class, 2))
    neg = rng.uniform(low=0.0, high=10.0, size=(n_per_class * 4, 2))
    # Drop negatives that accidentally fall in the positive box.
    keep = ~((neg[:, 0] >= 4.0) & (neg[:, 0] <= 6.0) &
             (neg[:, 1] >= 4.0) & (neg[:, 1] <= 6.0))
    neg = neg[keep][: n_per_class * 3]
    X = np.vstack([pos, neg]).astype(np.float64)
    y = np.array(["POS"] * len(pos) + ["NEG"] * len(neg))
    perm = rng.permutation(len(X))
    return X[perm], y[perm]


def _make_sd(X, y, **kwargs) -> MCMCSubgroupDiscovery:
    cfg = dict(
        feature_names=[f"x{i}" for i in range(X.shape[1])],
        target_class="POS",
        n_chains=1,
        n_steps=200,
        nwracc_threshold=0.1,
        top_k=5,
        random_state=42,
    )
    cfg.update(kwargs)
    return MCMCSubgroupDiscovery(**cfg)


# ----------------------------------------------------------------- primitives

def test_meet_proposal_contains_both_seeds():
    X, y = _simple_dataset()
    sd = _make_sd(X, y)
    sd.fit(X, y)  # populates state

    active, bounds = sd._meet_proposal()
    assert active.all()
    # Every positive in the chosen pair must be inside the meet pattern.
    extent = sd._compute_extent(active, bounds)
    # MEET of two random positives: at least those two are in the extent.
    assert (extent & sd.positive_mask).sum() >= 2


def test_close_on_positive_is_idempotent_and_tight():
    X, y = _simple_dataset()
    sd = _make_sd(X, y)
    sd.fit(X, y)

    # Start from a wide pattern that obviously contains all positives.
    active = np.ones(sd.d, dtype=bool)
    bounds = np.column_stack([X.min(axis=0) - 1, X.max(axis=0) + 1])

    a1, b1 = sd._close_on_positive(active, bounds)
    a2, b2 = sd._close_on_positive(a1, b1)

    np.testing.assert_array_equal(a1, a2)
    np.testing.assert_allclose(b1, b2)

    # Closed bounds must equal the MBR of positive instances on each axis.
    pos = X[sd.positive_mask]
    np.testing.assert_allclose(b1[:, 0], pos.min(axis=0))
    np.testing.assert_allclose(b1[:, 1], pos.max(axis=0))


def test_close_does_not_lose_positives():
    X, y = _simple_dataset()
    sd = _make_sd(X, y)
    sd.fit(X, y)

    active = np.ones(sd.d, dtype=bool)
    bounds = np.column_stack([X.min(axis=0), X.max(axis=0)])
    pos_before = sd._compute_extent(active, bounds) & sd.positive_mask

    a, b = sd._close_on_positive(active, bounds)
    pos_after = sd._compute_extent(a, b) & sd.positive_mask
    # ext+(close(p)) == ext+(p): no positive lost.
    np.testing.assert_array_equal(pos_before, pos_after)


def test_nwracc_edge_cases():
    X, y = _simple_dataset()
    sd = _make_sd(X, y)
    sd.fit(X, y)

    # Universe pattern: support == n, support_pos == n_pos -> WRAcc == 0.
    active = np.zeros(sd.d, dtype=bool)
    bounds = np.column_stack([X.min(axis=0), X.max(axis=0)])
    assert sd._compute_nwracc(active, bounds) == pytest.approx(0.0, abs=1e-9)

    # Empty extent (impossible bounds): NWRAcc == 0.
    active2 = np.ones(sd.d, dtype=bool)
    bounds2 = np.array([[1e9, 1e9 + 1]] * sd.d)
    assert sd._compute_nwracc(active2, bounds2) == 0.0


def test_nwracc_in_unit_range():
    X, y = _simple_dataset()
    sd = _make_sd(X, y)
    sd.fit(X, y)
    # Tight box around positives only — should be high but bounded.
    active = np.ones(sd.d, dtype=bool)
    pos = X[sd.positive_mask]
    bounds = np.column_stack([pos.min(axis=0), pos.max(axis=0)])
    score = sd._compute_nwracc(active, bounds)
    assert 0.0 <= score <= 1.0


# ----------------------------------------------------- discovery + redundancy

def test_discovery_recovers_hidden_box():
    X, y = _simple_dataset()
    sd = _make_sd(
        X, y,
        n_chains=4,
        n_steps=1000,
        nwracc_threshold=0.4,
        top_k=3,
    )
    subgroups = sd.fit(X, y)
    assert subgroups, "expected at least one subgroup"

    # Top subgroup should have very high precision and cover most positives.
    top = subgroups[0]
    assert top.precision >= 0.9
    n_pos = (y == "POS").sum()
    assert top.support_pos / n_pos >= 0.5
    # Both axes should be active: it's a 2D box.
    assert top.n_active() == 2


def test_redundancy_filter_drops_near_duplicates():
    feature_names = ("x0", "x1")
    extent = np.arange(20)
    a = np.array([True, True])
    b = np.array([[0.0, 1.0], [0.0, 1.0]])

    sg1 = Subgroup(
        pattern_desc="x0 in [0,1] AND x1 in [0,1]",
        active=a, bounds=b,
        nwracc=0.5, support=20, support_pos=15, precision=0.75,
        extent_indices=extent,
        target_class="POS", feature_names=feature_names,
    )
    # Same extent, slightly different description -> should be filtered.
    sg2 = Subgroup(
        pattern_desc="x0 in [0,1.0] AND x1 in [0,1.0]",
        active=a, bounds=b,
        nwracc=0.49, support=20, support_pos=15, precision=0.75,
        extent_indices=extent,
        target_class="POS", feature_names=feature_names,
    )

    sd = MCMCSubgroupDiscovery(feature_names=feature_names, target_class="POS",
                                redundancy_theta=0.5, top_k=5)
    selected = sd._select_non_redundant([sg1, sg2])
    assert len(selected) == 1
    assert selected[0].pattern_desc == sg1.pattern_desc


def test_top_k_cap():
    X, y = _simple_dataset()
    sd = _make_sd(X, y, top_k=2, n_chains=2, n_steps=300)
    out = sd.fit(X, y)
    assert len(out) <= 2


# ----------------------------------------------------------- integration API

def test_add_subgroup_features_appends_indicators():
    X, y = _simple_dataset()
    sd = _make_sd(X, y, n_chains=2, n_steps=400, nwracc_threshold=0.3)
    subgroups = sd.fit(X, y)
    assert subgroups

    aug, names = add_subgroup_features(X, subgroups)
    assert aug.shape == (X.shape[0], X.shape[1] + len(subgroups))
    assert len(names) == len(subgroups)
    sg_block = aug[:, X.shape[1]:]
    assert set(np.unique(sg_block)).issubset({0.0, 1.0})

    # First indicator column must equal the first subgroup's match mask.
    expected = subgroups[0].matches(X).astype(np.float32)
    np.testing.assert_array_equal(sg_block[:, 0], expected)


def test_apply_overrides_only_flips_eligible():
    X, y = _simple_dataset()
    sd = _make_sd(X, y, n_chains=2, n_steps=400, nwracc_threshold=0.3)
    subgroups = sd.fit(X, y)
    assert subgroups

    # Pretend the classifier said FALSE everywhere; only matchers get flipped.
    fake_preds = ["FALSE"] * X.shape[0]
    new_preds, n_over = apply_overrides(
        fake_preds, X, subgroups,
        target="POS", only_from=("FALSE",),
        min_nwracc=0.0, verbose=False,
    )
    assert n_over > 0
    matched = np.zeros(X.shape[0], dtype=bool)
    for s in subgroups:
        matched |= s.matches(X)
    assert sum(p == "POS" for p in new_preds) == int(matched.sum())


def test_apply_overrides_respects_only_from():
    X, y = _simple_dataset()
    sd = _make_sd(X, y, n_chains=2, n_steps=400, nwracc_threshold=0.3)
    subgroups = sd.fit(X, y)

    # If everyone predicts TRUE, nothing should be flipped (not eligible).
    fake_preds = ["TRUE"] * X.shape[0]
    new_preds, n_over = apply_overrides(
        fake_preds, X, subgroups,
        target="POS", only_from=("FALSE",),
        min_nwracc=0.0, verbose=False,
    )
    assert n_over == 0
    assert all(p == "TRUE" for p in new_preds)


def test_apply_overrides_min_nwracc_filters_subgroups():
    X, y = _simple_dataset()
    sd = _make_sd(X, y, n_chains=2, n_steps=400, nwracc_threshold=0.3)
    subgroups = sd.fit(X, y)
    assert subgroups

    fake_preds = ["FALSE"] * X.shape[0]
    # Set the gate above any plausible NWRAcc to disable all subgroups.
    _, n_over = apply_overrides(
        fake_preds, X, subgroups,
        target="POS", only_from=("FALSE",),
        min_nwracc=2.0, verbose=False,
    )
    assert n_over == 0


def test_subgroup_to_prompt_rule_format():
    feature_names = ("x0", "x1")
    sg = Subgroup(
        pattern_desc="x0 in [0,1]",
        active=np.array([True, False]),
        bounds=np.array([[0.0, 1.0], [-1.0, 1.0]]),
        nwracc=0.45, support=20, support_pos=14, precision=0.7,
        extent_indices=np.arange(20),
        target_class="PROBABLE", feature_names=feature_names,
    )
    txt = subgroup_to_prompt_rule(sg)
    assert "x0 in [0,1]" in txt
    assert "PROBABLE" in txt
    assert "70%" in txt
    assert "0.45" in txt


# ----------------------------------------------- input-validation guardrails

def test_fit_rejects_target_with_too_few_positives():
    X = np.random.rand(20, 3)
    y = np.array(["FALSE"] * 19 + ["RARE"])
    sd = MCMCSubgroupDiscovery(
        feature_names=("a", "b", "c"),
        target_class="RARE",
        n_chains=1, n_steps=10,
    )
    with pytest.raises(ValueError):
        sd.fit(X, y)


def test_fit_rejects_mismatched_feature_names():
    X = np.random.rand(30, 2)
    y = np.array(["POS"] * 10 + ["NEG"] * 20)
    sd = MCMCSubgroupDiscovery(
        feature_names=("a", "b", "c"),
        target_class="POS",
        n_chains=1, n_steps=10,
    )
    with pytest.raises(ValueError):
        sd.fit(X, y)
