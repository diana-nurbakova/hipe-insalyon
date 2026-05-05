"""Build a disagreement-stacker hybrid prediction file.

Implements ``specs/HIPE2026_Disagreement_Stacker_Specs.md`` §2 + §5 over
prediction JSONLs already on disk:

- ``--at-source`` is repeated for each base `at` model. Their predictions are
  combined by the leave-one-out lookup-table stacker (§2.4).
- ``--isAt-source`` provides the `isAt` predictions (single model, e.g. the
  best-single isAt model). Per the spec §7.1 there's no useful disagreement
  signal on the binary task with the current base models, so we don't stack
  isAt by default.

The output is a predictions JSONL + a JSON evaluation report under the same
naming convention as :mod:`scripts.combine_split_predictions`. The report's
metadata block records the base sources, fallback policy, and stacker cell
breakdown so the run is reproducible without re-reading this script.

Examples
--------
The current best hybrid (3 base models on `at`, Gemma alone on `isAt`)::

    uv run python scripts/run_disagreement_stacker.py \\
        --at-source RF=logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_at_at-test_predictions.jsonl \\
        --at-source C4-SDov=logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test+SDov_PROBABLE_from_FALSE_nw0.05_predictions.jsonl \\
        --at-source Gemma=logs/ablations/T1_llm_zeroshot_PAB_openrouter_gemma-4-31b-it_at-test_predictions.jsonl \\
        --isAt-source logs/ablations/T1_llm_zeroshot_PAB_openrouter_gemma-4-31b-it_at-test_predictions.jsonl \\
        --experiment-id T1_hybrid_LookupStackerAt_Gemma431BIsAt
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from hipe.evaluation.report import generate_evaluation_report
from hipe.stacker import (
    AT_ORDINAL_MAP,
    cell_summary,
    loo_lookup_predictions,
)


def _load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _key(r: dict) -> tuple[str, str, str]:
    return (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])


def _parse_at_source(spec: str) -> tuple[str, Path]:
    """Parse ``NAME=path`` into (name, Path). The name labels the model in the
    vote tuple and in the report; the order across --at-source flags fixes
    the cell key."""
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"--at-source expects NAME=path, got {spec!r}"
        )
    name, _, p = spec.partition("=")
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"empty model name in {spec!r}")
    return name, Path(p.strip())


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--at-source", action="append", required=True, type=_parse_at_source,
        metavar="NAME=PATH",
        help="Repeat for each base `at` model. NAME labels the model in the "
             "vote tuple; PATH is the predictions JSONL. Order matters.",
    )
    ap.add_argument(
        "--isAt-source", required=True, type=Path,
        help="Predictions JSONL whose isAt_predicted column is used as-is.",
    )
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--log-dir", default="logs/ablations", type=Path)
    ap.add_argument(
        "--tiebreaker", choices=("alphabetical", "ordinal_median", "last_model"),
        default="ordinal_median",
        help="Within-cell tie resolution. ordinal_median (default) uses the "
             "ordinal median of the vote tuple if it sits among the tied labels — "
             "matches the §5.2 fallback intent. alphabetical is purely "
             "deterministic. last_model picks the last-listed model's vote when "
             "it is tied (useful when one model is the strongest base).",
    )
    ap.add_argument(
        "--fallback", choices=("majority", "ordinal", "label"), default="majority",
        help="Fallback strategy for unseen vote tuples (only kicks in when an "
             "instance's tuple has no neighbours in the LOO leave-out set, which "
             "is rare for the n=188 single split).",
    )
    ap.add_argument(
        "--fallback-label", default="FALSE",
        help="Label used as the final fallback (also for null isAt predictions).",
    )
    ap.add_argument(
        "--print-cells", action="store_true",
        help="Print the per-cell summary table to stdout (§9.2 introspection).",
    )
    args = ap.parse_args()

    # --- load and align the base sources by (doc, pers, loc) key -----------
    at_sources: list[tuple[str, Path, dict[tuple[str, str, str], dict]]] = []
    for name, path in args.at_source:
        rows = _load_rows(path)
        idx = {_key(r): r for r in rows}
        at_sources.append((name, path, idx))
        print(f"  at base [{name:<14s}]: {len(rows):4d} rows from {path}")
    isAt_rows = _load_rows(args.isAt_source)
    isAt_idx = {_key(r): r for r in isAt_rows}
    print(f"  isAt source        : {len(isAt_rows):4d} rows from {args.isAt_source}")

    # Inner-join over keys present in every base. Missing-anywhere keys are
    # dropped because the lookup needs all K votes to form a cell.
    keys = sorted(set.intersection(*[set(idx.keys()) for _, _, idx in at_sources]))
    keys = [k for k in keys if k in isAt_idx]
    print(f"  shared keys:           {len(keys):4d}")
    if not keys:
        ap.error("no shared (doc,pers,loc) keys across the provided sources")

    base_predictions: dict[str, list[str]] = {}
    for name, _, idx in at_sources:
        base_predictions[name] = [idx[k]["at_predicted"] for k in keys]

    # Pull at_gold from whichever base has it populated; fall back across sources
    # to handle single-target prediction files that left the opposite gold None.
    at_gold: list[str | None] = []
    for k in keys:
        g = None
        for _, _, idx in at_sources:
            cand = idx[k].get("at_gold")
            if cand is not None:
                g = cand
                break
        at_gold.append(g)

    isAt_gold = [isAt_idx[k].get("isAt_gold") for k in keys]
    isAt_pred = [isAt_idx[k].get("isAt_predicted") for k in keys]

    # --- build LOO predictions on the at side ------------------------------
    at_pred = loo_lookup_predictions(
        base_predictions, at_gold,
        tiebreaker=args.tiebreaker,
        fallback=args.fallback,
        fallback_label=args.fallback_label,
        ordinal_map=AT_ORDINAL_MAP,
    )

    cells = cell_summary(base_predictions, at_gold)
    if args.print_cells:
        print("\nStacker cell summary (rows = vote tuples; sorted by N desc):")
        names = list(base_predictions.keys())
        header = "  " + "  ".join(f"{n:<10s}" for n in names) + "  N  modal  breakdown"
        print(header)
        for r in cells:
            cell_str = "  ".join(f"{r['cell'][n]:<10s}" for n in names)
            print(f"  {cell_str}  {r['n']:>3d}  {r['modal_gold']:<8s}  {r['breakdown']}")
    print(f"\n  unique vote tuples populated: {len(cells)}")

    # --- write predictions JSONL -------------------------------------------
    args.log_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = args.log_dir / f"{args.experiment_id}_predictions.jsonl"
    with out_jsonl.open("w", encoding="utf-8") as f:
        for i, (k, ap_, ip_, ag_, ig_) in enumerate(
            zip(keys, at_pred, isAt_pred, at_gold, isAt_gold)
        ):
            row = {
                "document_id": k[0],
                "pers_entity_id": k[1],
                "loc_entity_id": k[2],
                "language": isAt_idx[k].get("language"),
                "at_predicted": ap_,
                "isAt_predicted": ip_ if ip_ is not None else args.fallback_label,
                "at_gold": ag_,
                "isAt_gold": ig_,
                "at_vote_tuple": [base_predictions[n][i] for n in base_predictions],
            }
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    print(f"  wrote {out_jsonl}")

    # --- score with the official evaluator ---------------------------------
    isAt_pred_norm = [p if p is not None else args.fallback_label for p in isAt_pred]
    metadata = {
        "spec": "HIPE2026_Disagreement_Stacker_Specs.md v1.0",
        "at_sources": [
            {"name": n, "path": str(p)} for n, p, _ in at_sources
        ],
        "isAt_source": str(args.isAt_source),
        "tiebreaker": args.tiebreaker,
        "fallback_strategy": args.fallback,
        "fallback_label": args.fallback_label,
        "n_unique_vote_tuples": len(cells),
        "vote_tuple_distribution": [
            {
                "vote_tuple": list(t),
                "n": n,
            }
            for t, n in sorted(
                Counter(
                    tuple(base_predictions[name][i] for name in base_predictions)
                    for i in range(len(keys))
                ).items(),
                key=lambda x: -x[1],
            )
        ],
        "stacker_cells": cells,
    }
    report = generate_evaluation_report(
        args.experiment_id, at_gold, at_pred, isAt_gold, isAt_pred_norm,
        metadata=metadata, print_summary=True,
    )
    out_json = args.log_dir / f"{args.experiment_id}_report.json"
    out_json.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"  wrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
