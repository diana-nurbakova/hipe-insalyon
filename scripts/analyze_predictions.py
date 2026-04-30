"""Per-language and per-class breakdown of an experiment's predictions JSONL.

Reads the ``<experiment_id>_predictions.jsonl`` produced by
``run_ablation_experiment`` (one row per instance with ``at_gold``,
``at_predicted``, ``isAt_gold``, ``isAt_predicted``, ``language`` etc.)
and prints macro-recall per language plus optional confusion matrices.

Usage:
    uv run python scripts/analyze_predictions.py logs/ablations/T1.1_..._predictions.jsonl
    uv run python scripts/analyze_predictions.py <path> --by language --confusion
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from hipe.evaluation.metrics import (
    AT_LABELS,
    ISAT_LABELS,
    classification_report,
    compute_global_score,
    confusion_matrix,
    null_to_false,
)


def _load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _normalize(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        out.append(
            {
                **r,
                "at_gold": null_to_false(r.get("at_gold")),
                "at_predicted": null_to_false(r.get("at_predicted")),
                "isAt_gold": null_to_false(r.get("isAt_gold")),
                "isAt_predicted": null_to_false(r.get("isAt_predicted")),
            }
        )
    return out


def _print_section(rows: list[dict], header: str, *, show_cm: bool = False) -> None:
    if not rows:
        print(f"\n{header}: (no rows)")
        return
    at_gold = [r["at_gold"] for r in rows]
    at_pred = [r["at_predicted"] for r in rows]
    isAt_gold = [r["isAt_gold"] for r in rows]
    isAt_pred = [r["isAt_predicted"] for r in rows]
    s = compute_global_score(at_gold, at_pred, isAt_gold, isAt_pred)
    print(f"\n{header}  (n={len(rows)})")
    print(f"  Global={s['global_score']:.4f}  "
          f"MR(at)={s['macro_recall_at']:.4f}  MR(isAt)={s['macro_recall_isAt']:.4f}")
    at_d = s["at_details"]
    is_d = s["isAt_details"]
    at_recalls = " ".join(
        f"{lbl}={at_d.get(f'recall_{lbl}', 0) or 0:.2f}" for lbl in AT_LABELS
    )
    isat_recalls = " ".join(
        f"{lbl}={is_d.get(f'recall_{lbl}', 0) or 0:.2f}" for lbl in ISAT_LABELS
    )
    print(f"  recalls(at):   {at_recalls}")
    print(f"  recalls(isAt): {isat_recalls}")
    if show_cm:
        cm_at = confusion_matrix(at_gold, at_pred, AT_LABELS)
        cm_is = confusion_matrix(isAt_gold, isAt_pred, ISAT_LABELS)
        print(f"  cm(at) gold->pred:    {cm_at}  labels={list(AT_LABELS)}")
        print(f"  cm(isAt) gold->pred:  {cm_is}  labels={list(ISAT_LABELS)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("predictions_jsonl", type=Path)
    ap.add_argument("--by", choices=["language", "at_gold", "isAt_gold"], default="language",
                    help="Group rows by this field for the per-bucket breakdown.")
    ap.add_argument("--confusion", action="store_true",
                    help="Also print per-bucket confusion matrices.")
    args = ap.parse_args()

    rows = _normalize(_load_rows(args.predictions_jsonl))
    print(f"Loaded {len(rows)} rows from {args.predictions_jsonl}")

    _print_section(rows, "OVERALL", show_cm=args.confusion)

    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        key = str(r.get(args.by, ""))
        buckets[key].append(r)

    print(f"\n=== breakdown by {args.by} ===")
    for key in sorted(buckets):
        _print_section(buckets[key], f"{args.by}={key}", show_cm=args.confusion)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
