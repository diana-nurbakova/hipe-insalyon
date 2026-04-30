"""Establish the random baseline + verify our scorer matches the official one.

Runs the organizers' ``dummy_predict.py`` over a gold file, validates the
output against the official schema, scores it with both
``file_scorer_evaluation.py`` and our :mod:`hipe.evaluation.metrics`, and
flags any divergence (HIPE2026_Evaluation_Submission_Specs.md §3.4 / §3.0).

Usage::

    uv run python scripts/establish_baseline.py \
        --gold data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl \
        --tools-dir ../HIPE-2026-data
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hipe.data import collect_pair_keys, iter_official_documents, parse_official_jsonl
from hipe.evaluation import compute_global_score, null_to_false
from hipe.submission.tools import (
    establish_baseline,
    run_official_scorer,
)


def _index_predictions(pred_path: Path) -> dict[tuple[str, str, str], dict]:
    out: dict[tuple[str, str, str], dict] = {}
    for doc in iter_official_documents(pred_path):
        for pair in doc.get("sampled_pairs", []):
            key = (doc["document_id"], pair["pers_entity_id"], pair["loc_entity_id"])
            out[key] = pair
    return out


def _consistency_check(gold_path: Path, pred_path: Path, official_global: float | None,
                      official_at: float | None, official_isAt: float | None,
                      tolerance: float) -> bool:
    gold = parse_official_jsonl(gold_path)
    preds = _index_predictions(pred_path)

    at_gold: list[str] = []
    at_pred: list[str] = []
    isAt_gold: list[str] = []
    isAt_pred: list[str] = []
    for inst in gold:
        key = (inst.document_id, inst.pers_entity_id, inst.loc_entity_id)
        pp = preds.get(key, {})
        at_gold.append(null_to_false(inst.at))
        at_pred.append(null_to_false(pp.get("at")))
        isAt_gold.append(null_to_false(inst.isAt))
        isAt_pred.append(null_to_false(pp.get("isAt")))

    ours = compute_global_score(at_gold, at_pred, isAt_gold, isAt_pred)
    print("\n[consistency] our scorer vs official scorer")
    print(f"  global:           ours={ours['global_score']:.4f} "
          f"official={official_global!r}")
    print(f"  macro_recall_at:  ours={ours['macro_recall_at']:.4f} "
          f"official={official_at!r}")
    print(f"  macro_recall_isAt:ours={ours['macro_recall_isAt']:.4f} "
          f"official={official_isAt!r}")

    ok = True
    pairs = [
        ("global_score", ours["global_score"], official_global),
        ("macro_recall_at", ours["macro_recall_at"], official_at),
        ("macro_recall_isAt", ours["macro_recall_isAt"], official_isAt),
    ]
    for name, mine, theirs in pairs:
        if theirs is None:
            print(f"[consistency] could not parse {name} from official scorer output")
            continue
        if abs(mine - theirs) > tolerance:
            print(f"[consistency] DIVERGENCE on {name}: "
                  f"|{mine:.4f} - {theirs:.4f}| > {tolerance}")
            ok = False
    if ok:
        print("[consistency] our scorer matches the official scorer "
              f"within tolerance {tolerance}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gold", required=True, help="Path to gold JSONL")
    ap.add_argument("--tools-dir", default=None,
                    help="Path to the cloned HIPE-2026-data repo")
    ap.add_argument("--work-dir", default="logs/baselines",
                    help="Where to write the random predictions (default: %(default)s)")
    ap.add_argument("--report-out", default=None,
                    help="Optional JSON file to dump the baseline summary to")
    ap.add_argument("--tolerance", type=float, default=1e-4,
                    help="Tolerance for our-vs-official scorer comparison")
    args = ap.parse_args()

    gold_path = Path(args.gold)
    if not gold_path.exists():
        ap.error(f"--gold does not exist: {gold_path}")

    summary = establish_baseline(
        gold_path,
        tools_dir=args.tools_dir,
        work_dir=args.work_dir,
    )

    pred_path = Path(summary["prediction_file"])
    ok = _consistency_check(
        gold_path,
        pred_path,
        official_global=summary["global_score"],
        official_at=summary["macro_recall_at"],
        official_isAt=summary["macro_recall_isAt"],
        tolerance=args.tolerance,
    )
    summary["scorer_consistent"] = ok

    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        print(f"Wrote {out}")

    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
