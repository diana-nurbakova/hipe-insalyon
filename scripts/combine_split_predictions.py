"""Combine P-A and P-B predictions JSONLs into a single split-combined report.

The "P-A + P-B split" configuration runs two single-target prompts
independently and uses each one's prediction for its own target. This
gives the model a focused single-task prompt for each label and is
sometimes more accurate than the combined P-AB single-pass.

This script joins by ``(document_id, pers_entity_id, loc_entity_id)``,
takes ``at_predicted`` from the P-A file and ``isAt_predicted`` from the
P-B file, and produces a fresh predictions JSONL + evaluation report.

Usage:
    uv run python scripts/combine_split_predictions.py \
        --pa logs/ablations/<...PA...>_predictions.jsonl \
        --pb logs/ablations/<...PB...>_predictions.jsonl \
        --experiment-id T1.1_llm_split_PA+PB_at-test
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
    ap.add_argument("--pa", required=True, type=Path, help="P-A predictions JSONL.")
    ap.add_argument("--pb", required=True, type=Path, help="P-B predictions JSONL.")
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--log-dir", default="logs/ablations")
    ap.add_argument("--fallback-at", default="FALSE")
    ap.add_argument("--fallback-isAt", default="FALSE")
    args = ap.parse_args()

    pa_rows = _load_rows(args.pa)
    pb_rows = _load_rows(args.pb)
    pa_idx = {_key(r): r for r in pa_rows}
    pb_idx = {_key(r): r for r in pb_rows}

    keys = sorted(set(pa_idx) | set(pb_idx))
    n_overlap = len(set(pa_idx) & set(pb_idx))
    print(
        f"P-A rows: {len(pa_rows)}  P-B rows: {len(pb_rows)}  "
        f"overlap: {n_overlap}  union: {len(keys)}"
    )

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    out_path = log_dir / f"{args.experiment_id}_predictions.jsonl"

    new_rows: list[dict] = []
    for k in keys:
        a = pa_idx.get(k)
        b = pb_idx.get(k)
        ref = a or b
        assert ref is not None
        # Pull each gold label from whichever side has it populated. Single-target
        # predictions (e.g. MASK runs scored against only at OR isAt) leave the
        # opposite gold field as ``None`` — without this OR-fallback the combined
        # report would silently null-coalesce all gold to FALSE on the missing
        # side, inflating the score.
        at_gold = (a or {}).get("at_gold")
        if at_gold is None:
            at_gold = (b or {}).get("at_gold")
        isAt_gold = (b or {}).get("isAt_gold")
        if isAt_gold is None:
            isAt_gold = (a or {}).get("isAt_gold")
        new_rows.append(
            {
                "document_id": k[0],
                "pers_entity_id": k[1],
                "loc_entity_id": k[2],
                "language": ref.get("language"),
                "at_predicted": (a or {}).get("at_predicted") or args.fallback_at,
                "isAt_predicted": (b or {}).get("isAt_predicted") or args.fallback_isAt,
                "at_gold": at_gold,
                "isAt_gold": isAt_gold,
                "at_explanation": (a or {}).get("at_explanation"),
                "isAt_explanation": (b or {}).get("isAt_explanation"),
                "raw_output_pa": (a or {}).get("raw_output"),
                "raw_output_pb": (b or {}).get("raw_output"),
                "latency_ms": (
                    (a.get("latency_ms", 0.0) if a else 0.0)
                    + (b.get("latency_ms", 0.0) if b else 0.0)
                ),
            }
        )

    with out_path.open("w", encoding="utf-8") as f:
        for r in new_rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"Wrote {out_path}")

    at_gold = [r["at_gold"] for r in new_rows]
    at_pred = [r["at_predicted"] for r in new_rows]
    isAt_gold = [r["isAt_gold"] for r in new_rows]
    isAt_pred = [r["isAt_predicted"] for r in new_rows]

    report = generate_evaluation_report(
        args.experiment_id, at_gold, at_pred, isAt_gold, isAt_pred,
        metadata={
            "source_pa": str(args.pa),
            "source_pb": str(args.pb),
            "n_pa": len(pa_rows),
            "n_pb": len(pb_rows),
            "n_overlap": n_overlap,
            "n_combined": len(new_rows),
        },
        print_summary=True,
    )
    report_path = log_dir / f"{args.experiment_id}_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
