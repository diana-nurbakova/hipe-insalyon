"""End-to-end submission pipeline for the HIPE-2026 stacked approach.

Given pre-computed base-model predictions on the **official test set** plus
the full-dataset OOF predictions (used to fit the lookup table), this
script:

1. Builds the lookup table on the full labeled set (1,251 vote-tuple -> gold
   pairs).
2. Applies it to the test-set vote tuples to produce the final `at`
   predictions.
3. Combines the stacked `at` with Gemma's `isAt` to produce a single
   predictions JSONL.
4. Optionally calls ``scripts/make_submission.py`` to emit the
   official-format submission and validate against the schema.

Conceptual ordering (matches ``HIPE2026_Stacked_Approach.md`` §8):

    A. (separate) Train final base models on the full 1,251 labeled set.
    B. (separate) Run each base model + Gemma on the official test set.
    C. THIS SCRIPT: stack + submit.

Step C is intentionally separate from training/inference so a pipeline
re-run after a hyperparameter tweak or a Gemma rerun does not require
retraining the trees / MLP again.

Usage::

    uv run python scripts/run_full_pipeline.py \\
        --train-source RF=logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl \\
        --train-source C4=logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl \\
        --train-source OrdContM1=logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl \\
        --train-source Gemma=logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl \\
        --test-source RF=submissions_input/RF_official_test_predictions.jsonl \\
        --test-source C4=submissions_input/C4_official_test_predictions.jsonl \\
        --test-source OrdContM1=submissions_input/OrdContM1_official_test_predictions.jsonl \\
        --test-source Gemma=submissions_input/Gemma_official_test_predictions.jsonl \\
        --official-input data/HIPE-2026-v1.0-impresso-test-en.jsonl \\
        --team OURTEAM --run 1 \\
        --out-dir submissions/

The order of ``--train-source`` and ``--test-source`` flags must match for
each model name (the vote-tuple key is positional).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from hipe.evaluation.metrics import null_to_false
from hipe.stacker import (
    AT_ORDINAL_MAP,
    apply_lookup,
    build_lookup_table,
    cell_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parse_source(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"--*-source expects NAME=path, got {spec!r}"
        )
    name, _, p = spec.partition("=")
    return name.strip(), Path(p.strip())


def _load_rows(path: Path) -> dict[tuple[str, str, str], dict]:
    out: dict[tuple[str, str, str], dict] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out[(r["document_id"], r["pers_entity_id"], r["loc_entity_id"])] = r
    return out


def _stack_one_split(
    sources: list[tuple[str, Path]],
    isat_source_name: str,
    *,
    purpose: str,
) -> tuple[dict[str, list[str]], list[tuple[str, str, str]],
           list[str | None], list[str | None], list[str | None]]:
    """Load each source's rows, inner-join by key, return per-model votes
    aligned by index plus the corresponding (key, at_gold, isAt_gold,
    isAt_predicted) lists."""
    by_model = {}
    for name, path in sources:
        rows = _load_rows(path)
        by_model[name] = rows
        print(f"  [{purpose}] {name:<14s}: {len(rows):4d} rows from {path}")
    keys = sorted(set.intersection(*[set(d.keys()) for d in by_model.values()]))
    print(f"  [{purpose}] shared keys: {len(keys)}")

    base_predictions: dict[str, list[str]] = {
        name: [null_to_false(by_model[name][k]["at_predicted"]) for k in keys]
        for name in by_model
    }
    at_gold: list[str | None] = []
    isAt_gold: list[str | None] = []
    isAt_pred: list[str | None] = []
    for k in keys:
        ag = ig = ip_ = None
        for name in by_model:
            r = by_model[name][k]
            if ag is None and r.get("at_gold") is not None:
                ag = r["at_gold"]
            if ig is None and r.get("isAt_gold") is not None:
                ig = r["isAt_gold"]
        # isAt prediction comes from the explicitly-named isAt source.
        if isat_source_name in by_model:
            isat_row = by_model[isat_source_name][k]
            ip_ = isat_row.get("isAt_predicted")
        at_gold.append(ag)
        isAt_gold.append(ig)
        isAt_pred.append(ip_)
    return base_predictions, keys, at_gold, isAt_gold, isAt_pred


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--train-source", action="append", required=True, type=_parse_source,
        metavar="NAME=PATH",
        help="OOF predictions JSONL for ONE base model on the labeled set "
             "(typically 1,251 instances). Repeat for each base model. The set "
             "of names must match --test-source names exactly.",
    )
    ap.add_argument(
        "--test-source", action="append", required=True, type=_parse_source,
        metavar="NAME=PATH",
        help="Predictions JSONL for ONE base model on the OFFICIAL test set. "
             "Repeat for each base model. Names must match --train-source.",
    )
    ap.add_argument(
        "--isAt-source-name", default="Gemma",
        help="Which --*-source NAME to draw isAt predictions from (default: Gemma).",
    )
    ap.add_argument(
        "--official-input", required=True, type=Path,
        help="Official test JSONL (the file released by the organisers).",
    )
    ap.add_argument("--team", required=True, help="Registered CLEF team name.")
    ap.add_argument(
        "--run", type=int, required=True, choices=[1, 2, 3],
        help="Run number (1=accuracy, 2=efficiency, 3=experimental).",
    )
    ap.add_argument("--out-dir", default="submissions", type=Path)
    ap.add_argument(
        "--predictions-out", type=Path, default=None,
        help="Where to write the merged predictions JSONL (default: "
             "submissions/<team>_run<n>_predictions.jsonl).",
    )
    ap.add_argument(
        "--tiebreaker", choices=("alphabetical", "ordinal_median", "last_model"),
        default="ordinal_median",
    )
    ap.add_argument(
        "--fallback", choices=("majority", "ordinal", "label"), default="ordinal",
    )
    ap.add_argument(
        "--fallback-label", default="FALSE",
        help="Final fallback for unseen vote tuples + null isAt predictions.",
    )
    ap.add_argument("--no-validate", action="store_true",
                    help="Skip the schema validation step.")
    ap.add_argument("--tools-dir", default=None,
                    help="Path to cloned HIPE-2026-data repo (for schema validation).")
    args = ap.parse_args()

    # Validate that train/test source NAME sets match.
    train_names = {n for n, _ in args.train_source}
    test_names = {n for n, _ in args.test_source}
    if train_names != test_names:
        ap.error(
            f"--train-source names {sorted(train_names)} != "
            f"--test-source names {sorted(test_names)}; the lookup table key "
            f"(vote tuple) requires the same model order on both sides."
        )

    # Preserve the order from --train-source so the cell key is positional.
    ordered_names = [n for n, _ in args.train_source]
    train_sources = list(args.train_source)
    test_sources_by_name = {n: p for n, p in args.test_source}
    test_sources = [(n, test_sources_by_name[n]) for n in ordered_names]

    if args.isAt_source_name not in train_names:
        ap.error(
            f"--isAt-source-name {args.isAt_source_name!r} is not among "
            f"the provided sources; isAt must come from one of {sorted(train_names)}"
        )

    print("=" * 72)
    print(f"Stacker pipeline: team={args.team} run={args.run}")
    print("=" * 72)

    # --- 1. fit lookup table on the full labeled set -----------------------
    print("\n[1/4] Loading full-labeled-set OOF predictions for lookup table...")
    train_preds, train_keys, train_at_gold, _, _ = _stack_one_split(
        train_sources, args.isAt_source_name, purpose="TRAIN",
    )
    n_with_gold = sum(1 for g in train_at_gold if g is not None)
    print(f"  rows with at_gold: {n_with_gold}/{len(train_keys)}")
    if n_with_gold < 100:
        print(f"  [warn] very few labeled rows for lookup; results will be unstable")

    lookup = build_lookup_table(
        train_preds, train_at_gold,
        tiebreaker=args.tiebreaker, ordinal_map=AT_ORDINAL_MAP,
    )
    cells = cell_summary(train_preds, train_at_gold)
    print(f"  built lookup table: {len(lookup)} populated cells "
          f"(of max {3**len(ordered_names)})")
    print(f"  top-5 cells (by N):")
    for r in cells[:5]:
        cell_str = ", ".join(f"{n}={r['cell'][n]}" for n in ordered_names)
        print(f"    ({cell_str}) -> {r['modal_gold']}  N={r['n']} {r['breakdown']}")

    # --- 2. apply lookup to test-set vote tuples ---------------------------
    print(f"\n[2/4] Loading official-test base-model predictions...")
    test_preds, test_keys, _, _, test_isAt_pred = _stack_one_split(
        test_sources, args.isAt_source_name, purpose="TEST",
    )
    test_at_pred = apply_lookup(
        test_preds, lookup,
        fallback=args.fallback,
        fallback_label=args.fallback_label,
        ordinal_map=AT_ORDINAL_MAP,
    )

    n_unseen = sum(
        1 for i in range(len(test_keys))
        if tuple(test_preds[n][i] for n in ordered_names) not in lookup
    )
    print(f"  applied lookup to {len(test_keys)} test instances")
    print(f"  unseen vote tuples (resolved via fallback): {n_unseen}")

    # --- 3. write merged predictions JSONL ---------------------------------
    print(f"\n[3/4] Writing merged predictions JSONL...")
    pred_path = args.predictions_out
    if pred_path is None:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        pred_path = args.out_dir / f"{args.team}_run{args.run}_predictions.jsonl"
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    n_isAt_null = 0
    with pred_path.open("w", encoding="utf-8") as f:
        for i, k in enumerate(test_keys):
            ip_ = test_isAt_pred[i]
            if ip_ is None:
                n_isAt_null += 1
                ip_ = args.fallback_label
            f.write(json.dumps({
                "document_id": k[0],
                "pers_entity_id": k[1],
                "loc_entity_id": k[2],
                "at_predicted": test_at_pred[i],
                "isAt_predicted": ip_,
                "at_vote_tuple": [test_preds[n][i] for n in ordered_names],
            }, ensure_ascii=False, default=str) + "\n")
    print(f"  wrote {pred_path}")
    if n_isAt_null > 0:
        print(f"  [warn] {n_isAt_null} test instances had null isAt — defaulted to {args.fallback_label}")

    # --- 4. emit official submission via make_submission.py ---------------
    print(f"\n[4/4] Generating official submission file...")
    cmd = [
        "uv", "run", "python", str(PROJECT_ROOT / "scripts" / "make_submission.py"),
        "--input", str(args.official_input),
        "--predictions", str(pred_path),
        "--team", args.team,
        "--run", str(args.run),
        "--out-dir", str(args.out_dir),
    ]
    if not args.no_validate:
        cmd.append("--validate")
        if args.tools_dir:
            cmd.extend(["--tools-dir", str(args.tools_dir)])
    print(f"  $ {' '.join(cmd)}")
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print(f"  [warn] make_submission.py exited with code {rc}")
        return rc

    print(f"\n{'='*72}\nDone — submission file in {args.out_dir}\n{'='*72}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
