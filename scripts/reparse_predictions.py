"""Re-parse a predictions JSONL with the current parser.

Useful when you've improved the parser and want to know what scores you
WOULD have gotten without spending more API tokens. Reads
``<exp_id>_predictions.jsonl``, runs ``parse_output`` on every
``raw_output`` field, applies the configured fallbacks, and produces a
new report alongside the original (suffixed ``_reparsed``).

Usage:
    uv run python scripts/reparse_predictions.py \
        logs/ablations/T1.1_..._predictions.jsonl --variant A
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from hipe.evaluation.experiment import generate_evaluation_report
from hipe.llm.parser import parse_output


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("predictions_jsonl", type=Path)
    ap.add_argument("--variant", choices=["A", "B", "AB", "R"], required=True)
    ap.add_argument("--fallback-at", default="FALSE")
    ap.add_argument("--fallback-isAt", default="FALSE")
    ap.add_argument("--out-suffix", default="_reparsed")
    args = ap.parse_args()

    in_path: Path = args.predictions_jsonl
    rows: list[dict] = []
    with in_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    statuses = Counter()
    new_rows: list[dict] = []
    for r in rows:
        raw = r.get("raw_output") or ""
        pr = parse_output(raw, args.variant)
        statuses[pr.parse_status] += 1
        # P-A predicts only at; keep the original isAt prediction (which was
        # the FALSE-default). Same idea for P-B in reverse. P-AB / P-R
        # overwrite both.
        if args.variant == "A":
            new_at = pr.at or args.fallback_at
            new_isAt = r.get("isAt_predicted") or args.fallback_isAt
        elif args.variant == "B":
            new_at = r.get("at_predicted") or args.fallback_at
            new_isAt = pr.isAt or args.fallback_isAt
        else:
            new_at = pr.at or args.fallback_at
            new_isAt = pr.isAt or args.fallback_isAt
        nr = dict(r)
        nr["at_predicted"] = new_at
        nr["isAt_predicted"] = new_isAt
        nr["parse_status_reparsed"] = pr.parse_status
        new_rows.append(nr)

    print(f"Re-parsed {len(rows)} rows from {in_path}")
    print(f"  parse statuses: {dict(statuses)}")

    # Write new predictions
    stem = in_path.stem
    if stem.endswith("_predictions"):
        new_stem = stem.replace("_predictions", f"{args.out_suffix}_predictions")
    else:
        new_stem = stem + args.out_suffix
    new_pred_path = in_path.with_name(new_stem + ".jsonl")
    with new_pred_path.open("w", encoding="utf-8") as f:
        for r in new_rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"Wrote {new_pred_path}")

    # Score
    at_gold = [r["at_gold"] for r in new_rows]
    at_pred = [r["at_predicted"] for r in new_rows]
    isAt_gold = [r["isAt_gold"] for r in new_rows]
    isAt_pred = [r["isAt_predicted"] for r in new_rows]
    exp_id = stem.replace("_predictions", "") + args.out_suffix
    report = generate_evaluation_report(
        exp_id, at_gold, at_pred, isAt_gold, isAt_pred,
        metadata={"reparse_statuses": dict(statuses), "source": str(in_path), "variant": args.variant},
        print_summary=True,
    )
    report_path = in_path.with_name(exp_id + "_report.json")
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
