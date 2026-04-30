"""Per-language ensemble routing (Spec v0.9 §13.2.2 Intervention 4).

The 28-experiment ablation showed that different approaches have different
per-language strengths. RAG **hurts** French (LLM P-R: 0.550 -> 0.467 with
RAG K=3) while it marginally helps English. This script lets us route each
language to its empirically-best predictor.

Each --route argument names a (language, predictions_file) pair. The script
reads all listed files, then for each row picks the prediction from the file
whose language tag matches the row's ``language`` field. A ``--default``
file is consulted for any language not explicitly routed.

Common routing pattern from the spec::

    uv run python scripts/build_per_language_ensemble.py \
        --route fr=logs/ablations/T1.1_llm_zeroshot_PR_<...>_at-test_predictions.jsonl \
        --route de=logs/ablations/T1_llm_rag3_PR_<...>_at-test_predictions.jsonl \
        --route en=logs/ablations/T1_llm_rag3_PR_<...>_at-test_predictions.jsonl \
        --experiment-id llm_PR_per_lang_routing_at-test

This routes French to zero-shot P-R (RAG hurts it) while keeping
RAG-augmented P-R for German and English.

Output: a single predictions JSONL + evaluation report, same format as the
ablation harness.
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


def _parse_route(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"--route expects 'lang=path', got {spec!r}"
        )
    lang, _, p = spec.partition("=")
    return lang.strip().lower(), Path(p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--route", action="append", default=[], type=_parse_route,
        help="Repeatable: lang=path/to/predictions.jsonl. "
             "lang in {en, fr, de, lb, ...} matches the row's language field.",
    )
    ap.add_argument("--default", type=Path, default=None,
                    help="Fallback predictions file for unrouted languages.")
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--log-dir", default="logs/ablations")
    args = ap.parse_args()

    if not args.route and not args.default:
        raise SystemExit("Provide at least --default or one --route lang=path.")

    routed: dict[str, dict[tuple[str, str, str], dict]] = {}
    for lang, path in args.route:
        rows = _load_rows(path)
        routed[lang] = {_key(r): r for r in rows}
        print(f"  route[{lang}] = {path}  rows={len(rows)}")

    default_idx: dict[tuple[str, str, str], dict] | None = None
    if args.default:
        default_rows = _load_rows(args.default)
        default_idx = {_key(r): r for r in default_rows}
        print(f"  default     = {args.default}  rows={len(default_rows)}")

    # Union of all keys across the routed sources + default.
    all_keys: set[tuple[str, str, str]] = set()
    for idx in routed.values():
        all_keys.update(idx)
    if default_idx is not None:
        all_keys.update(default_idx)
    keys = sorted(all_keys)
    if not keys:
        raise SystemExit("No rows in any input file.")

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    out_path = log_dir / f"{args.experiment_id}_predictions.jsonl"

    counts: dict[str, int] = {}
    rows_out: list[dict] = []
    for k in keys:
        # Determine language from any source that has the row.
        lang = None
        for idx in (default_idx, *routed.values()):
            if idx is None:
                continue
            r = idx.get(k)
            if r and r.get("language"):
                lang = r["language"].lower()
                break

        # Pick the right source: language-specific route, else default.
        source = routed.get(lang) if lang else None
        if source is None or k not in source:
            source = default_idx
        if source is None or k not in source:
            counts["MISSING"] = counts.get("MISSING", 0) + 1
            continue

        r = source[k]
        counts[lang or "UNKNOWN"] = counts.get(lang or "UNKNOWN", 0) + 1
        rows_out.append({
            "document_id": k[0],
            "pers_entity_id": k[1],
            "loc_entity_id": k[2],
            "language": r.get("language"),
            "at_predicted": r.get("at_predicted"),
            "isAt_predicted": r.get("isAt_predicted"),
            "at_gold": r.get("at_gold"),
            "isAt_gold": r.get("isAt_gold"),
            "at_explanation": r.get("at_explanation"),
            "isAt_explanation": r.get("isAt_explanation"),
        })

    with out_path.open("w", encoding="utf-8") as f:
        for r in rows_out:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"Routing counts: {counts}  total={len(rows_out)}")
    print(f"Wrote predictions to {out_path}")

    at_gold = [r["at_gold"] for r in rows_out]
    at_pred = [r["at_predicted"] for r in rows_out]
    isAt_gold = [r["isAt_gold"] for r in rows_out]
    isAt_pred = [r["isAt_predicted"] for r in rows_out]
    report = generate_evaluation_report(
        args.experiment_id, at_gold, at_pred, isAt_gold, isAt_pred,
        metadata={
            "routes": {lang: str(p) for lang, p in args.route},
            "default": str(args.default) if args.default else None,
            "counts": counts,
        },
        print_summary=True,
    )
    (log_dir / f"{args.experiment_id}_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
