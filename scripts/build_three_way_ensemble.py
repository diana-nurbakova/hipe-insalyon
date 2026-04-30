"""Three-way ensemble: RF(at) + MASK-C4(isAt) + LLM as PROBABLE detector.

Spec v0.9 §13.2.1 Next experiment #2.

The hybrid RF(at) + MASK-C4(isAt) achieves global=0.7142 but has a known
weakness: RF barely predicts PROBABLE (3 predictions / 18 PROBABLE instances
in the test set). The LLM has the opposite bias — it over-predicts PROBABLE,
hedging (81/104 FALSE instances are predicted as PROBABLE).

The complementary nature is what makes the ensemble work: where the RF says
FALSE but the LLM says PROBABLE, flipping to PROBABLE recovers some of the
PROBABLE recall the RF misses, **without** giving up the RF's strong FALSE
recall (87/104 FALSE).

Inputs (predictions JSONLs in the standard ablation format):
  --rf-at      RF predictions for `at` target (at_predicted populated)
  --mask-isAt  MASK-C4 predictions for `isAt` target (isAt_predicted populated)
  --llm        LLM predictions covering both targets (at_predicted + isAt_predicted)

Output:
  Predictions JSONL + evaluation report at logs/ablations/<experiment_id>_*.

Logic per instance:
  at_final  = LLM_at if (RF_at == "FALSE" and LLM_at == "PROBABLE") else RF_at
  isAt_final = MASK_isAt   (always — MASK is best for the temporal task)

The flip is intentionally narrow: we trust RF's TRUE/PROBABLE picks and only
upgrade RF's FALSEs that the LLM thinks are PROBABLE. Other LLM-vs-RF
disagreements are left to RF.

Usage::

    uv run python scripts/build_three_way_ensemble.py \
        --rf-at logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_at_at-test_predictions.jsonl \
        --mask-isAt logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test_predictions.jsonl \
        --llm logs/ablations/T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test_predictions.jsonl \
        --experiment-id hybrid_plus_LLM_PROBABLE_detector_at-test
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hipe.evaluation.experiment import generate_evaluation_report


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rf-at", required=True, type=Path)
    ap.add_argument("--mask-isAt", required=True, type=Path)
    ap.add_argument("--llm", required=True, type=Path)
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--log-dir", default="logs/ablations")
    ap.add_argument("--flip-on", default="PROBABLE",
                    help="LLM label that triggers the flip-from-FALSE rule "
                         "(default: PROBABLE).")
    ap.add_argument("--from-label", default="FALSE",
                    help="RF label that may be flipped (default: FALSE).")
    args = ap.parse_args()

    rf_idx = {_key(r): r for r in _load_rows(args.rf_at)}
    mask_idx = {_key(r): r for r in _load_rows(args.mask_isAt)}
    llm_idx = {_key(r): r for r in _load_rows(args.llm)}

    keys = sorted(set(rf_idx) & set(mask_idx) & set(llm_idx))
    print(
        f"RF rows: {len(rf_idx)}  MASK rows: {len(mask_idx)}  "
        f"LLM rows: {len(llm_idx)}  intersection: {len(keys)}"
    )
    if not keys:
        raise SystemExit("No overlapping rows across the three inputs.")

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    out_path = log_dir / f"{args.experiment_id}_predictions.jsonl"

    n_flips = 0
    rows_out: list[dict] = []
    for k in keys:
        rf = rf_idx[k]
        mk = mask_idx[k]
        ll = llm_idx[k]

        rf_at = rf.get("at_predicted") or "FALSE"
        ll_at = ll.get("at_predicted") or "FALSE"
        mk_isAt = mk.get("isAt_predicted") or "FALSE"

        at_final = rf_at
        if rf_at == args.from_label and ll_at == args.flip_on:
            at_final = args.flip_on
            n_flips += 1

        # Pull each gold label from whichever side has it (some single-target
        # predictors leave the off-target gold as null).
        at_gold = rf.get("at_gold") or ll.get("at_gold") or mk.get("at_gold")
        isAt_gold = mk.get("isAt_gold") or ll.get("isAt_gold") or rf.get("isAt_gold")
        rows_out.append({
            "document_id": k[0],
            "pers_entity_id": k[1],
            "loc_entity_id": k[2],
            "language": rf.get("language") or mk.get("language") or ll.get("language"),
            "at_predicted": at_final,
            "isAt_predicted": mk_isAt,
            "at_gold": at_gold,
            "isAt_gold": isAt_gold,
            "rf_at": rf_at,
            "llm_at": ll_at,
            "mask_isAt": mk_isAt,
            "flipped": at_final != rf_at,
        })

    print(f"Flipped {n_flips} instances from RF={args.from_label} -> "
          f"LLM={args.flip_on} = {args.flip_on}")

    with out_path.open("w", encoding="utf-8") as f:
        for r in rows_out:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"Wrote predictions to {out_path}")

    at_gold = [r["at_gold"] for r in rows_out]
    at_pred = [r["at_predicted"] for r in rows_out]
    isAt_gold = [r["isAt_gold"] for r in rows_out]
    isAt_pred = [r["isAt_predicted"] for r in rows_out]
    report = generate_evaluation_report(
        args.experiment_id, at_gold, at_pred, isAt_gold, isAt_pred,
        metadata={
            "source_rf_at": str(args.rf_at),
            "source_mask_isAt": str(args.mask_isAt),
            "source_llm": str(args.llm),
            "flip_rule": f"RF={args.from_label} & LLM={args.flip_on} -> {args.flip_on}",
            "n_flips": n_flips,
        },
        print_summary=True,
    )
    out_report = log_dir / f"{args.experiment_id}_report.json"
    out_report.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote report to {out_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
