"""MCMC subgroup discovery with Closed-On-The-Positive (COTP) closure.

Follows Subgroup Discovery Specs §2-§3. Each chain explores the space of
interval patterns by alternating local moves (tighten/loosen/add/drop) with
MEET jumps grounded in pairs of positive instances. After every proposal we
*close on the positive* — tighten each active interval to the minimum bounding
rectangle of the positives that fall in its extent. Closure is monotone in
NWRAcc so it never hurts quality, and the closed pattern is the canonical
representative of its equivalence class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np


@dataclass
class Subgroup:
    """One discovered interval pattern.

    ``active`` and ``bounds`` together define the conjunctive interval pattern;
    only features where ``active[f]`` is True contribute a constraint. The
    remaining stats are evaluated on the dataset the subgroup was discovered
    on — they may differ on a held-out set (use :meth:`matches` there).
    """

    pattern_desc: str
    active: np.ndarray  # bool[n_features]
    bounds: np.ndarray  # float[n_features, 2]
    nwracc: float
    support: int
    support_pos: int
    precision: float
    extent_indices: np.ndarray
    target_class: str | None = None
    feature_names: tuple[str, ...] | None = field(default=None, repr=False)

    def matches(self, X: np.ndarray) -> np.ndarray:
        """Boolean mask: which rows of ``X`` fall in this subgroup's extent."""
        if X.ndim != 2:
            raise ValueError(f"X must be 2D, got shape {X.shape}")
        if X.shape[1] != self.active.shape[0]:
            raise ValueError(
                f"X has {X.shape[1]} features, subgroup has {self.active.shape[0]}"
            )
        # Match the precision the bounds were computed in so float32/float64
        # callers see identical extents.
        Xf = np.asarray(X, dtype=self.bounds.dtype)
        mask = np.ones(Xf.shape[0], dtype=bool)
        for f in np.where(self.active)[0]:
            mask &= (Xf[:, f] >= self.bounds[f, 0]) & (Xf[:, f] <= self.bounds[f, 1])
        return mask

    def n_active(self) -> int:
        return int(self.active.sum())


class MCMCSubgroupDiscovery:
    """MCMC-COTP sampler over interval patterns.

    See HIPE2026_Subgroup_Discovery_Specs §3.1 for the algorithm and §3.2 for
    the proposal distribution. The MEET proposal is the bottom-up move from
    MonteCloPi — it samples two positives and jumps to the interval pattern
    that tightly covers both.
    """

    PROPOSAL_MOVES: tuple[str, ...] = ("meet", "tighten", "loosen", "add", "drop")
    DEFAULT_PROBS: tuple[float, ...] = (0.25, 0.30, 0.20, 0.15, 0.10)

    def __init__(
        self,
        feature_names: Sequence[str],
        target_class: str = "PROBABLE",
        *,
        n_chains: int = 10,
        n_steps: int = 10000,
        temperature: float = 1.0,
        annealing: bool = True,
        nwracc_threshold: float = 0.3,
        redundancy_theta: float = 0.5,
        top_k: int = 10,
        min_support: int = 2,
        proposal_probs: Sequence[float] | None = None,
        random_state: int = 42,
    ) -> None:
        self.feature_names = tuple(feature_names)
        self.target_class = target_class
        self.n_chains = int(n_chains)
        self.n_steps = int(n_steps)
        self.temperature = float(temperature)
        self.annealing = bool(annealing)
        self.nwracc_threshold = float(nwracc_threshold)
        self.redundancy_theta = float(redundancy_theta)
        self.top_k = int(top_k)
        self.min_support = int(min_support)

        probs = self.DEFAULT_PROBS if proposal_probs is None else tuple(proposal_probs)
        if len(probs) != len(self.PROPOSAL_MOVES):
            raise ValueError("proposal_probs must have one entry per move")
        s = float(sum(probs))
        if s <= 0:
            raise ValueError("proposal_probs must sum to a positive value")
        self.proposal_probs = np.asarray([p / s for p in probs], dtype=np.float64)

        self.rng = np.random.RandomState(int(random_state))

        # Set on fit().
        self.X: np.ndarray | None = None
        self.y: np.ndarray | None = None
        self.n: int = 0
        self.d: int = 0
        self.positive_mask: np.ndarray | None = None
        self.positive_indices: np.ndarray | None = None
        self.n_pos: int = 0
        self.wracc_max: float = 0.0
        self.global_min: np.ndarray | None = None
        self.global_max: np.ndarray | None = None

    # ------------------------------------------------------------------ fit

    def fit(self, X: np.ndarray, y: Sequence[str] | np.ndarray) -> list[Subgroup]:
        """Discover non-redundant subgroups for ``self.target_class``."""
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y)
        if X.ndim != 2:
            raise ValueError(f"X must be 2D, got shape {X.shape}")
        if X.shape[0] != y.shape[0]:
            raise ValueError("X and y row counts must match")
        if X.shape[1] != len(self.feature_names):
            raise ValueError(
                f"X has {X.shape[1]} features but {len(self.feature_names)} names given"
            )

        self.X, self.y = X, y
        self.n, self.d = X.shape
        self.positive_mask = (y == self.target_class)
        self.positive_indices = np.where(self.positive_mask)[0]
        self.n_pos = int(self.positive_mask.sum())
        if self.n_pos < 2:
            raise ValueError(
                f"Need at least 2 instances of target_class={self.target_class!r}, "
                f"found {self.n_pos}"
            )
        p_pos = self.n_pos / self.n
        self.wracc_max = p_pos * (1 - p_pos)
        self.global_min = X.min(axis=0)
        self.global_max = X.max(axis=0)

        all_subgroups: list[Subgroup] = []
        for chain_id in range(self.n_chains):
            all_subgroups.extend(self._run_chain(chain_id))
        return self._select_non_redundant(all_subgroups)

    # ---------------------------------------------------------------- chain

    def _run_chain(self, chain_id: int) -> list[Subgroup]:
        discovered: list[Subgroup] = []
        active, bounds = self._meet_proposal()
        active, bounds = self._close_on_positive(active, bounds)
        current_score = self._compute_nwracc(active, bounds)

        for step in range(self.n_steps):
            if self.annealing:
                t = self.temperature * (1.0 - step / self.n_steps) + 0.01
            else:
                t = self.temperature

            new_active, new_bounds = self._propose(active, bounds)
            new_active, new_bounds = self._close_on_positive(new_active, new_bounds)
            new_score = self._compute_nwracc(new_active, new_bounds)

            # Per spec §3.1 step 2b: only entertain proposals with positive
            # discriminative signal, then accept by Metropolis-Hastings on
            # the score difference (annealed).
            if new_score > 0:
                log_ratio = (new_score - current_score) / max(t, 1e-12)
                if log_ratio > 0 or self.rng.random() < np.exp(log_ratio):
                    active, bounds, current_score = new_active, new_bounds, new_score

            if current_score >= self.nwracc_threshold:
                extent = self._compute_extent(active, bounds)
                support = int(extent.sum())
                if support < self.min_support:
                    continue
                extent_pos = extent & self.positive_mask
                support_pos = int(extent_pos.sum())
                discovered.append(
                    Subgroup(
                        pattern_desc=self._describe(active, bounds),
                        active=active.copy(),
                        bounds=bounds.copy(),
                        nwracc=float(current_score),
                        support=support,
                        support_pos=support_pos,
                        precision=support_pos / max(support, 1),
                        extent_indices=np.where(extent)[0],
                        target_class=self.target_class,
                        feature_names=self.feature_names,
                    )
                )
        return discovered

    # ------------------------------------------------------------- proposal

    def _propose(
        self, active: np.ndarray, bounds: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        new_active, new_bounds = active.copy(), bounds.copy()
        move = self.rng.choice(self.PROPOSAL_MOVES, p=self.proposal_probs)

        if move == "meet":
            return self._meet_proposal()

        if move == "tighten" and new_active.sum() > 0:
            f = int(self.rng.choice(np.where(new_active)[0]))
            vals = self.X[:, f]
            in_iv = vals[(vals >= new_bounds[f, 0]) & (vals <= new_bounds[f, 1])]
            if len(in_iv) > 1:
                side = self.rng.choice(["lo", "hi"])
                if side == "lo":
                    c = in_iv[in_iv > new_bounds[f, 0]]
                    if len(c) > 0:
                        new_bounds[f, 0] = float(self.rng.choice(c))
                else:
                    c = in_iv[in_iv < new_bounds[f, 1]]
                    if len(c) > 0:
                        new_bounds[f, 1] = float(self.rng.choice(c))

        elif move == "loosen" and new_active.sum() > 0:
            f = int(self.rng.choice(np.where(new_active)[0]))
            col = self.X[:, f]
            side = self.rng.choice(["lo", "hi"])
            if side == "lo" and new_bounds[f, 0] > col.min():
                c = col[col < new_bounds[f, 0]]
                if len(c) > 0:
                    new_bounds[f, 0] = float(self.rng.choice(c))
            elif side == "hi" and new_bounds[f, 1] < col.max():
                c = col[col > new_bounds[f, 1]]
                if len(c) > 0:
                    new_bounds[f, 1] = float(self.rng.choice(c))

        elif move == "add" and new_active.sum() < self.d:
            f = int(self.rng.choice(np.where(~new_active)[0]))
            new_active[f] = True
            pos_vals = self.X[self.positive_indices, f]
            picked = self.rng.choice(pos_vals, 2, replace=True)
            a, b = float(picked.min()), float(picked.max())
            new_bounds[f] = [a, b]

        elif move == "drop" and new_active.sum() > 1:
            f = int(self.rng.choice(np.where(new_active)[0]))
            new_active[f] = False
            new_bounds[f] = [self.global_min[f], self.global_max[f]]

        return new_active, new_bounds

    def _meet_proposal(self) -> tuple[np.ndarray, np.ndarray]:
        i, j = self.rng.choice(self.positive_indices, 2, replace=False)
        bounds = np.column_stack(
            [
                np.minimum(self.X[i], self.X[j]),
                np.maximum(self.X[i], self.X[j]),
            ]
        )
        return np.ones(self.d, dtype=bool), bounds

    # -------------------------------------------------------------- closure

    def _close_on_positive(
        self, active: np.ndarray, bounds: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Tighten each active interval to the MBR of positives in extent."""
        extent = self._compute_extent(active, bounds)
        pos_in = extent & self.positive_mask
        if pos_in.sum() == 0:
            return active, bounds
        closed = bounds.copy()
        for f in np.where(active)[0]:
            vals = self.X[pos_in, f]
            closed[f] = [vals.min(), vals.max()]
        return active, closed

    # ---------------------------------------------------------------- score

    def _compute_extent(self, active: np.ndarray, bounds: np.ndarray) -> np.ndarray:
        mask = np.ones(self.n, dtype=bool)
        for f in np.where(active)[0]:
            mask &= (self.X[:, f] >= bounds[f, 0]) & (self.X[:, f] <= bounds[f, 1])
        return mask

    def _compute_nwracc(self, active: np.ndarray, bounds: np.ndarray) -> float:
        extent = self._compute_extent(active, bounds)
        support = int(extent.sum())
        if support == 0 or self.wracc_max == 0:
            return 0.0
        support_pos = int((extent & self.positive_mask).sum())
        wracc = (support / self.n) * (support_pos / support - self.n_pos / self.n)
        return float(wracc / self.wracc_max)

    # ----------------------------------------------------------- describe

    def _describe(self, active: np.ndarray, bounds: np.ndarray) -> str:
        parts: list[str] = []
        for f in np.where(active)[0]:
            lo, hi = bounds[f]
            name = self.feature_names[f]
            if lo == hi:
                parts.append(f"{name}={lo:.3g}")
            else:
                parts.append(f"{name} in [{lo:.3g},{hi:.3g}]")
        return " AND ".join(parts) if parts else "(empty)"

    # ----------------------------------------------------- non-redundancy

    def _select_non_redundant(self, subgroups: list[Subgroup]) -> list[Subgroup]:
        if not subgroups:
            return []
        subgroups.sort(key=lambda s: s.nwracc, reverse=True)

        # Drop exact duplicates first.
        seen: set[str] = set()
        unique: list[Subgroup] = []
        for sg in subgroups:
            if sg.pattern_desc in seen:
                continue
            seen.add(sg.pattern_desc)
            unique.append(sg)

        # Then Jaccard-filter on extents.
        selected: list[Subgroup] = []
        for sg in unique:
            if len(selected) >= self.top_k:
                break
            redundant = False
            sg_set = set(sg.extent_indices.tolist())
            for ex in selected:
                ex_set = set(ex.extent_indices.tolist())
                inter = len(sg_set & ex_set)
                union = len(sg_set | ex_set)
                if union > 0 and inter / union > self.redundancy_theta:
                    redundant = True
                    break
            if not redundant:
                selected.append(sg)
        return selected
