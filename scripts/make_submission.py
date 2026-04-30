"""Generate a HIPE-2026 submission JSONL.

Reads an experiment-log JSONL (one row per pair, produced by
``hipe.evaluation.run_ablation_experiment``) and merges its predictions back
into the official input file's nested structure. Optionally validates the
result against the official schema.

Usage::

    uv run python scripts/make_submission.py \
        --input data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-de.jsonl \
        --predictions logs/ablations/T1.2_llm_fewshot_predictions.jsonl \
        --team OURTEAM --run 1 \
        --out-dir submissions/ \
        --validate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from hipe.submission import (
    generate_submission_file,
    predictions_from_records,
    submission_filename,
    validate_submission,
)


def _load_records(pred_log: Path) -> list[dict]:
    records: list[dict] = []
    with pred_log.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True,
                    help="Official input JSONL (test or dev) to merge into")
    ap.add_argument("--predictions", required=True,
                    help="Predictions JSONL produced by run_ablation_experiment")
    ap.add_argument("--team", required=True, help="Registered CLEF team name")
    ap.add_argument("--run", type=int, required=True, choices=[1, 2, 3],
                    help="Run number (1=accuracy, 2=efficiency, 3=experimental)")
    ap.add_argument("--out-dir", default="submissions",
                    help="Directory to write the submission file (default: %(default)s)")
    ap.add_argument("--out-name", default=None,
                    help="Override the auto-generated filename")
    ap.add_argument("--at-field", default="at_predicted",
                    help="Key of the `at` prediction in the log (default: %(default)s)")
    ap.add_argument("--isAt-field", default="isAt_predicted",
                    help="Key of the `isAt` prediction in the log (default: %(default)s)")
    ap.add_argument("--no-enforce-constraint", action="store_true",
                    help="Do NOT force isAt=FALSE when at=FALSE")
    ap.add_argument("--validate", action="store_true",
                    help="Run check_jsonlschema.py on the output")
    ap.add_argument("--tools-dir", default=None,
                    help="Path to the cloned HIPE-2026-data repo")
    args = ap.parse_args()

    input_path = Path(args.input)
    pred_log = Path(args.predictions)
    if not input_path.exists():
        ap.error(f"--input does not exist: {input_path}")
    if not pred_log.exists():
        ap.error(f"--predictions does not exist: {pred_log}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = args.out_name or submission_filename(args.team, input_path, args.run)
    out_path = out_dir / out_name

    records = _load_records(pred_log)
    predictions = predictions_from_records(
        records,
        at_field=args.at_field,
        isAt_field=args.isAt_field,
    )

    stats = generate_submission_file(
        input_path,
        predictions,
        out_path,
        enforce_constraint=not args.no_enforce_constraint,
    )

    if stats.n_missing_predictions:
        print(
            f"[warn] {stats.n_missing_predictions}/{stats.total_pairs} pairs "
            f"had no prediction and were defaulted to FALSE/FALSE"
        )

    if args.validate:
        try:
            res = validate_submission(out_path, tools_dir=args.tools_dir)
        except FileNotFoundError as e:
            print(f"[validate] {e}", file=sys.stderr)
            return 0
        if res.ok:
            print(f"[validate] schema OK for {out_path}")
        else:
            print(f"[validate] schema FAILED for {out_path}")
            print(res.stdout)
            print(res.stderr, file=sys.stderr)
            return res.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
