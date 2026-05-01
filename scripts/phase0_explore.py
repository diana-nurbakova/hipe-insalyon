"""Phase 0 — descriptive statistics over the master dataset.

Replicates the findings cited in HIPE2026_Pipeline_Specs_v2.md §1.4 so we
have a local ground-truth before any modelling work begins.

Usage:
    uv run python scripts/phase0_explore.py
    uv run python scripts/phase0_explore.py --jsonl data/dataset_reference.jsonl
"""

from __future__ import annotations

import argparse
import statistics
from collections import Counter
from pathlib import Path

import pandas as pd

from hipe.data import RelationInstance, load_baseline_split, load_jsonl
from hipe.features.temporal import (
    DEFAULT_ISAT_WINDOW_DAYS,
    recompute_has_timex_in_window,
)

DEFAULT_JSONL = Path(__file__).resolve().parents[1] / "data" / "dataset_reference.jsonl"


def banner(title: str) -> None:
    print(f"\n{'=' * 72}\n  {title}\n{'=' * 72}")


def describe(label: str, values: list[float]) -> None:
    if not values:
        print(f"  {label:<30s} (no values)")
        return
    print(
        f"  {label:<30s} "
        f"n={len(values):<5d} "
        f"min={min(values):>9.2f} "
        f"max={max(values):>9.2f} "
        f"mean={statistics.fmean(values):>9.2f} "
        f"med={statistics.median(values):>9.2f}"
    )


def fraction_table(label: str, counter: Counter, total: int) -> None:
    print(f"\n  {label}")
    for key, count in counter.most_common():
        pct = 100.0 * count / total if total else 0
        print(f"    {str(key):<30s} {count:>5d}  ({pct:5.1f}%)")


def explore(instances: list[RelationInstance]) -> None:
    n = len(instances)
    banner(f"Dataset overview ({n} instances)")

    # Language distribution
    lang_counter = Counter(i.language for i in instances)
    fraction_table("Language distribution", lang_counter, n)

    # Label distribution
    at_counter = Counter(i.at for i in instances)
    isat_counter = Counter(i.isAt for i in instances)
    fraction_table("`at` label distribution", at_counter, n)
    fraction_table("`isAt` label distribution", isat_counter, n)

    # Joint distribution
    joint = Counter((i.at, i.isAt) for i in instances)
    fraction_table("Joint (at, isAt) distribution", joint, n)

    # Logical structure spot-checks (spec §1.4)
    banner("Logical structure spot-checks")
    n_at_false_isat_true = sum(
        1 for i in instances if i.at == "FALSE" and i.isAt == "TRUE"
    )
    print(f"  at=FALSE & isAt=TRUE  : {n_at_false_isat_true}  (spec: 0)")

    n_isat_true_at_false = sum(
        1 for i in instances if i.isAt == "TRUE" and i.at not in {"TRUE", "PROBABLE"}
    )
    print(f"  isAt=TRUE & at not in {{TRUE,PROB}}: {n_isat_true_at_false}  (spec: 0)")

    # QID coverage
    banner("Wikidata QID coverage")
    n_pers_qid = sum(1 for i in instances if i.pers_wikidata_QID)
    n_loc_qid = sum(1 for i in instances if i.loc_wikidata_QID)
    n_both_qid = sum(
        1 for i in instances if i.pers_wikidata_QID and i.loc_wikidata_QID
    )
    print(f"  Person QID  : {n_pers_qid:5d}  ({100*n_pers_qid/n:.1f}%)")
    print(f"  Location QID: {n_loc_qid:5d}  ({100*n_loc_qid/n:.1f}%)")
    print(f"  Both QIDs   : {n_both_qid:5d}  ({100*n_both_qid/n:.1f}%)")

    # Text lengths
    banner("Text length statistics (chars)")
    describe("text", [len(i.text) for i in instances])
    describe("context", [len(i.context) for i in instances])

    # Sentence position
    banner("Discourse position")
    sp = [i.sentence_position for i in instances if i.sentence_position is not None]
    describe("sentence_position", sp)
    n_lead = sum(1 for x in sp if x <= 1)
    print(f"  In lead paragraph (pos<=1): {n_lead}  ({100*n_lead/n:.1f}%)")

    # Temporal signal distribution
    banner("Temporal signal categories")
    cat_counter = Counter(i.temporal_signal_category for i in instances)
    fraction_table("temporal_signal_category", cat_counter, n)

    # Critical: explicit temporal expressions in isAt window. Per Spec
    # v3 §8.1 the isAt window was widened from the ±14-day rule baked into
    # `dataset_reference.jsonl` to "approximately one month" (~30 days);
    # re-compute from `nearest_timex_distance` rather than trusting the
    # pre-baked boolean.
    banner("Temporal expressions vs isAt label (spec §1.4 / §8.1)")
    n_isat_true = sum(1 for i in instances if i.isAt == "TRUE")
    n_legacy = sum(
        1 for i in instances if i.isAt == "TRUE" and i.has_timex_in_isat_window
    )
    n_spec = sum(
        1 for i in instances
        if i.isAt == "TRUE" and recompute_has_timex_in_window(i)
    )
    pct_legacy = 100 * n_legacy / n_isat_true if n_isat_true else 0
    pct_spec = 100 * n_spec / n_isat_true if n_isat_true else 0
    print(f"  isAt=TRUE total                          : {n_isat_true}")
    print(f"  Legacy (+/-14d, dataset field)           : {n_legacy}  ({pct_legacy:.1f}%)")
    print(f"  Spec  (~{DEFAULT_ISAT_WINDOW_DAYS}d, recomputed)              : {n_spec}  ({pct_spec:.1f}%)")
    print(f"  Spec citation: ~5.7% (16/279) refers to the legacy 14d rule;")
    print(f"  Spec v3 §8.1 says re-compute with the wider window.")

    # Person temporal status
    banner("Person temporal status")
    status_counter = Counter(i.temporal_person_status for i in instances)
    fraction_table("temporal_person_status", status_counter, n)

    # OCR quality
    banner("OCR quality")
    ocr = [i.ocr_quality for i in instances if i.ocr_quality is not None]
    describe("ocr_quality", ocr)
    n_low = sum(1 for x in ocr if x < 0.95)
    print(f"  Below 0.95: {n_low}  ({100*n_low/len(ocr):.1f}%)")


def show_split(instances: list[RelationInstance]) -> None:
    banner("Baseline split (v1_baseline_train_test_ids.csv)")
    for task in ("at", "isAt"):
        try:
            sp = load_baseline_split(instances, task=task)
        except FileNotFoundError:
            print(f"  {task}: split CSV not found, skipping.")
            return
        print(f"  task={task}: train={len(sp.train)}  test={len(sp.test)}")
        # Per-language breakdown for both splits
        for partition_name, partition in (("train", sp.train), ("test", sp.test)):
            counts = Counter(i.language for i in partition)
            counts_at = Counter((i.language, i.at) for i in partition)
            print(f"    {partition_name:5s} languages: {dict(counts)}")
            df = pd.Series(counts_at).unstack().fillna(0).astype(int)
            indented = "\n".join("      " + line for line in df.to_string().splitlines())
            print(indented)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(DEFAULT_JSONL))
    args = ap.parse_args()

    path = Path(args.jsonl)
    if not path.exists():
        raise SystemExit(f"Dataset not found: {path}")

    print(f"Loading {path} ...")
    instances = load_jsonl(path)
    print(f"Loaded {len(instances)} instances.")

    explore(instances)
    show_split(instances)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
