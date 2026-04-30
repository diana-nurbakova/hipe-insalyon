"""Score a HIPE-2026 predictions JSONL against a gold JSONL.

Loads both files in the official nested format (one document per line with
``sampled_pairs``), aligns predictions to gold by
``(document_id, pers_entity_id, loc_entity_id)``, and runs our scorer. With
``--official-scorer`` it also shells out to ``file_scorer_evaluation.py`` so
the two outputs can be compared (HIPE2026_Evaluation_Submission_Specs.md §7.2).

Usage::

    uv run python scripts/score_predictions.py \
        --gold data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl \
        --predictions submissions/our_team_train-de_run1.jsonl \
        --experiment-id de-run1 \
        --official-scorer
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hipe.data import collect_pair_keys, iter_official_documents, parse_official_jsonl
from hipe.evaluation import generate_evaluation_report, null_to_false
from hipe.submission.tools import run_official_scorer


def _index_predictions(pred_path: Path) -> dict[tuple[str, str, str], dict]:
    out: dict[tuple[str, str, str], dict] = {}
    for doc in iter_official_documents(pred_path):
        for pair in doc.get("sampled_pairs", []):
            key = (doc["document_id"], pair["pers_entity_id"], pair["loc_entity_id"])
            out[key] = pair
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", required=True, help="Path to gold JSONL")
    ap.add_argument("--predictions", required=True, help="Path to predictions JSONL")
    ap.add_argument("--experiment-id", default="score_predictions",
                    help="Tag used in the report (default: %(default)s)")
    ap.add_argument("--report-out", default=None,
                    help="Optional JSON file to dump the full report to")
    ap.add_argument("--official-scorer", action="store_true",
                    help="Also run scripts/file_scorer_evaluation.py and "
                         "print its output for cross-checking")
    ap.add_argument("--tools-dir", default=None,
                    help="Path to the cloned HIPE-2026-data repo")
    args = ap.parse_args()

    gold_path = Path(args.gold)
    pred_path = Path(args.predictions)
    if not gold_path.exists():
        ap.error(f"--gold does not exist: {gold_path}")
    if not pred_path.exists():
        ap.error(f"--predictions does not exist: {pred_path}")

    gold = parse_official_jsonl(gold_path)
    preds = _index_predictions(pred_path)

    gold_keys = collect_pair_keys(iter_official_documents(gold_path))
    pred_keys = collect_pair_keys(iter_official_documents(pred_path))
    if gold_keys != pred_keys:
        # Soft warning; we can still score by alignment if at least the keys
        # are a subset, but ordering deviations may signal a malformed file.
        missing = [k for k in gold_keys if k not in preds]
        extra = [k for k in pred_keys if k not in {gk for gk in gold_keys}]
        print(
            f"[warn] gold/predictions ordering or membership differs: "
            f"missing={len(missing)} extra={len(extra)}",
            file=sys.stderr,
        )

    at_gold: list[str] = []
    at_pred: list[str] = []
    isAt_gold: list[str] = []
    isAt_pred: list[str] = []
    n_missing = 0
    for inst in gold:
        key = (inst.document_id, inst.pers_entity_id, inst.loc_entity_id)
        gold_at = null_to_false(inst.at)
        gold_isAt = null_to_false(inst.isAt)
        pp = preds.get(key)
        if pp is None:
            pred_at, pred_isAt = "FALSE", "FALSE"
            n_missing += 1
        else:
            pred_at = null_to_false(pp.get("at"))
            pred_isAt = null_to_false(pp.get("isAt"))
        at_gold.append(gold_at)
        at_pred.append(pred_at)
        isAt_gold.append(gold_isAt)
        isAt_pred.append(pred_isAt)

    if n_missing:
        print(f"[warn] {n_missing} gold pairs had no matching prediction "
              f"(treated as FALSE/FALSE)")

    report = generate_evaluation_report(
        args.experiment_id,
        at_gold, at_pred, isAt_gold, isAt_pred,
        metadata={
            "gold_file": str(gold_path),
            "predictions_file": str(pred_path),
            "n_missing_predictions": n_missing,
        },
    )

    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"Wrote {out}")

    if args.official_scorer:
        print("\n[official-scorer] running file_scorer_evaluation.py ...")
        try:
            res = run_official_scorer(gold_path, pred_path, tools_dir=args.tools_dir)
        except FileNotFoundError as e:
            print(f"[official-scorer] {e}", file=sys.stderr)
            return 0
        print(res.stdout)
        if res.returncode != 0:
            print(res.stderr, file=sys.stderr)
            return res.returncode
        ours = report["scores"]
        print("[diff] our scorer vs official:")
        if res.global_score is not None:
            print(f"  global:           ours={ours['global_score']:.4f} "
                  f"official={res.global_score:.4f}")
        if res.macro_recall_at is not None:
            print(f"  macro_recall_at:  ours={ours['macro_recall_at']:.4f} "
                  f"official={res.macro_recall_at:.4f}")
        if res.macro_recall_isAt is not None:
            print(f"  macro_recall_isAt:ours={ours['macro_recall_isAt']:.4f} "
                  f"official={res.macro_recall_isAt:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
