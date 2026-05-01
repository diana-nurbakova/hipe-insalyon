"""Generate HIPE-2026 submission files for a whole run, across languages.

Per Evaluation Specs §4.4 / §9.3, a submission window for Test A requires
de + fr + en JSONLs (and Test B adds the surprise fr literary set), each at
up to 3 runs (accuracy / efficiency / experimental). The single-input
``make_submission.py`` is fine for one (input × run) cell; this driver loops
over language inputs to keep the test-window choreography honest.

Inputs
------
``--input-glob`` (or ``--inputs``)
    The official-format JSONLs to merge into. Use the glob form (e.g.
    ``data/HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-*.jsonl``)
    to pick up all three test languages in one shot.
``--predictions-glob`` (or ``--predictions``)
    Per-language prediction JSONLs (the ablation log format produced by
    ``hipe.evaluation.run_ablation_experiment``). The driver pairs each
    input with the prediction file whose basename contains the matching
    language code -- so the predictions can either live in one merged
    file (single ``--predictions``) or one file per language.

Outputs
-------
``<out-dir>/<team>_<input-stem>_runN.jsonl`` for each (input, run) pair.

Usage::

    uv run python scripts/make_submission_batch.py \
        --input-glob 'data/HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-*.jsonl' \
        --predictions logs/ablations/T1.4or5_mask_contrastive_ordinal_m1_at-test_predictions.jsonl \
        --team OURTEAM --run 1 --validate --package
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from glob import glob
from pathlib import Path

from hipe.submission import (
    generate_submission_file,
    package_runs,
    predictions_from_records,
    submission_filename,
    validate_submission,
)


_LANG_RE = re.compile(r"-(de|fr|en|lb)(?:[-._]|$)")


def _detect_language(stem: str) -> str | None:
    """Pick the language code embedded in a HIPE-2026 filename, if any."""
    m = _LANG_RE.search(stem)
    return m.group(1) if m else None


def _resolve_paths(values: list[str], globs: list[str]) -> list[Path]:
    """Collect explicit paths and glob patterns into a sorted unique list."""
    out: list[Path] = []
    seen: set[str] = set()
    for v in values:
        p = Path(v)
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            out.append(p)
    for pattern in globs:
        for hit in sorted(glob(pattern)):
            p = Path(hit)
            key = str(p.resolve())
            if key not in seen:
                seen.add(key)
                out.append(p)
    return out


def _load_records(pred_path: Path) -> list[dict]:
    rows: list[dict] = []
    with pred_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _select_predictions_for_input(
    input_path: Path,
    pred_paths: list[Path],
) -> Path:
    """Pick the prediction file matching ``input_path``'s language.

    Falls back to the only prediction file when there is just one (treated
    as a merged predictions log covering all languages).
    """
    if len(pred_paths) == 1:
        return pred_paths[0]
    lang = _detect_language(input_path.stem)
    if lang is None:
        raise ValueError(
            f"Cannot detect language code in {input_path.name}; "
            "supply matching predictions via --predictions"
        )
    candidates = [p for p in pred_paths if _detect_language(p.stem) == lang]
    if not candidates:
        raise FileNotFoundError(
            f"No predictions file found for language {lang!r} matching {input_path.name}. "
            f"Available: {[p.name for p in pred_paths]}"
        )
    if len(candidates) > 1:
        raise ValueError(
            f"Ambiguous predictions for language {lang!r}: {[p.name for p in candidates]}"
        )
    return candidates[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--inputs", nargs="*", default=[],
        help="Explicit list of official-format JSONL inputs",
    )
    ap.add_argument(
        "--input-glob", default=None,
        help="Glob pattern matching official input JSONLs (e.g. test-*.jsonl)",
    )
    ap.add_argument(
        "--predictions", nargs="*", default=[],
        help="Explicit list of prediction JSONL logs",
    )
    ap.add_argument(
        "--predictions-glob", default=None,
        help="Glob pattern matching prediction JSONLs",
    )
    ap.add_argument("--team", required=True, help="Registered CLEF team name")
    ap.add_argument(
        "--run", type=int, required=True, choices=[1, 2, 3],
        help="Run number (1=accuracy, 2=efficiency, 3=experimental)",
    )
    ap.add_argument("--out-dir", default="submissions",
                    help="Where to write submission files (default: %(default)s)")
    ap.add_argument("--at-field", default="at_predicted")
    ap.add_argument("--isAt-field", default="isAt_predicted")
    ap.add_argument("--no-enforce-constraint", action="store_true")
    ap.add_argument("--validate", action="store_true",
                    help="Run check_jsonlschema.py on every output")
    ap.add_argument("--package", action="store_true",
                    help="After generation, zip outputs as <team>.zip")
    ap.add_argument("--zip-name", default=None,
                    help="Override the default <team>.zip name")
    ap.add_argument("--tools-dir", default=None,
                    help="Path to the cloned HIPE-2026-data repo (for --validate)")
    args = ap.parse_args()

    input_globs = [args.input_glob] if args.input_glob else []
    pred_globs = [args.predictions_glob] if args.predictions_glob else []
    inputs = _resolve_paths(args.inputs, input_globs)
    pred_paths = _resolve_paths(args.predictions, pred_globs)

    if not inputs:
        ap.error("Provide at least one --inputs or --input-glob")
    if not pred_paths:
        ap.error("Provide at least one --predictions or --predictions-glob")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for input_path in inputs:
        if not input_path.exists():
            print(f"[skip] missing input: {input_path}", file=sys.stderr)
            continue

        pred_path = _select_predictions_for_input(input_path, pred_paths)
        print(f"[{input_path.name}] predictions={pred_path.name}")

        records = _load_records(pred_path)
        predictions = predictions_from_records(
            records,
            at_field=args.at_field,
            isAt_field=args.isAt_field,
        )

        out_name = submission_filename(args.team, input_path, args.run)
        out_path = out_dir / out_name
        stats = generate_submission_file(
            input_path,
            predictions,
            out_path,
            enforce_constraint=not args.no_enforce_constraint,
        )
        if stats.n_missing_predictions:
            print(
                f"[warn] {stats.n_missing_predictions}/{stats.total_pairs} "
                f"pairs in {input_path.name} had no prediction "
                "(defaulted to FALSE/FALSE)"
            )

        if args.validate:
            try:
                res = validate_submission(out_path, tools_dir=args.tools_dir)
            except FileNotFoundError as e:
                print(f"[validate] {e}", file=sys.stderr)
                return 2
            if not res.ok:
                print(f"[validate] schema FAILED for {out_path}")
                print(res.stdout)
                print(res.stderr, file=sys.stderr)
                return res.returncode
            print(f"[validate] schema OK for {out_path.name}")

        written.append(out_path)

    if not written:
        print("No submission files were generated.", file=sys.stderr)
        return 1

    if args.package:
        zip_name = args.zip_name or f"{args.team}.zip"
        zip_path = package_runs(args.team, written, output_zip=out_dir / zip_name)
        print(f"Wrote {zip_path}")

    print(f"\nDone. {len(written)} submission file(s) in {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
