"""Train/test split utilities.

The HIPE-2026 baseline split is provided in
``data/v1_baseline_train_test_ids.csv`` (2,126 train / 376 test per task).
Use :func:`load_baseline_split` by default for comparability with other
methods. :func:`stratified_random_split` is a fallback that produces a
language × (at, isAt) stratified split when the baseline CSV is absent.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from random import Random

import pandas as pd

from hipe.data.instance import RelationInstance

DEFAULT_SPLIT_CSV = Path(__file__).resolve().parents[2] / "data" / "v1_baseline_train_test_ids.csv"


@dataclass(slots=True)
class SplitResult:
    train: list[RelationInstance]
    test: list[RelationInstance]
    val: list[RelationInstance] | None = None

    def summary(self) -> str:
        n_val = len(self.val) if self.val else 0
        return (
            f"SplitResult(train={len(self.train)}, "
            f"val={n_val}, test={len(self.test)})"
        )


def _read_split_csv(csv_path: str | Path, task: str) -> dict[str, str]:
    """Return ``{sample_id: split}`` for the given task ('at' | 'isAt')."""
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    df = df[df["task"] == task]
    return dict(zip(df["sample_id"], df["split"]))


def load_baseline_split(
    instances: list[RelationInstance],
    *,
    task: str = "at",
    csv_path: str | Path = DEFAULT_SPLIT_CSV,
    val_fraction: float = 0.0,
    seed: int = 42,
) -> SplitResult:
    """Split instances using the official baseline CSV.

    Parameters
    ----------
    instances : list of RelationInstance
        All loaded instances.
    task : {'at', 'isAt'}
        Which task's split to use. The two tasks share sample IDs but the
        CSV stores split rows per task; both should yield the same partition,
        but we honour the task argument explicitly.
    csv_path : path
        Path to ``v1_baseline_train_test_ids.csv``.
    val_fraction : float
        If > 0, carve a stratified validation slice off the training set.
    seed : int
        RNG seed for the optional val split.
    """
    if task not in {"at", "isAt"}:
        raise ValueError(f"task must be 'at' or 'isAt', got {task!r}")

    sample_to_split = _read_split_csv(csv_path, task)
    train: list[RelationInstance] = []
    test: list[RelationInstance] = []
    missing: list[str] = []
    for inst in instances:
        sp = sample_to_split.get(inst.sample_id)
        if sp == "train":
            train.append(inst)
        elif sp == "test":
            test.append(inst)
        else:
            missing.append(inst.sample_id)

    if missing:
        # Don't fail loudly — surface in the result so callers can decide.
        # Common cause: dataset_reference.jsonl has more samples than the CSV
        # (e.g. extra languages added after the baseline split was frozen).
        print(
            f"[load_baseline_split] {len(missing)} instances had no split assignment "
            f"(first 3: {missing[:3]})"
        )

    val: list[RelationInstance] | None = None
    if val_fraction > 0:
        val = _carve_val(train, fraction=val_fraction, seed=seed)
        train = [x for x in train if x not in val]

    return SplitResult(train=train, test=test, val=val)


def stratified_random_split(
    instances: list[RelationInstance],
    *,
    test_fraction: float = 0.15,
    val_fraction: float = 0.15,
    seed: int = 42,
) -> SplitResult:
    """Stratified random split by ``language × (at, isAt)``.

    Used as a fallback when the baseline CSV is unavailable.
    """
    rng = Random(seed)
    buckets: dict[tuple[str, str, str], list[RelationInstance]] = defaultdict(list)
    for inst in instances:
        key = (inst.language, str(inst.at), str(inst.isAt))
        buckets[key].append(inst)

    train: list[RelationInstance] = []
    val: list[RelationInstance] = []
    test: list[RelationInstance] = []
    for items in buckets.values():
        rng.shuffle(items)
        n = len(items)
        n_test = max(1, round(n * test_fraction)) if n >= 5 else 0
        n_val = max(1, round(n * val_fraction)) if n >= 5 else 0
        test.extend(items[:n_test])
        val.extend(items[n_test : n_test + n_val])
        train.extend(items[n_test + n_val :])

    return SplitResult(train=train, val=val if val_fraction > 0 else None, test=test)


def _carve_val(
    train: list[RelationInstance],
    *,
    fraction: float,
    seed: int,
) -> list[RelationInstance]:
    """Stratified subsample by language × (at, isAt) from a training pool."""
    rng = Random(seed)
    buckets: dict[tuple[str, str, str], list[RelationInstance]] = defaultdict(list)
    for inst in train:
        buckets[(inst.language, str(inst.at), str(inst.isAt))].append(inst)
    val: list[RelationInstance] = []
    for items in buckets.values():
        rng.shuffle(items)
        n = max(1, round(len(items) * fraction)) if len(items) >= 4 else 0
        val.extend(items[:n])
    return val
