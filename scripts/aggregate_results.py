"""Aggregate every experiment in ``logs/ablations/`` into a single JSON.

Walks every ``<exp_id>_report.json`` in the log directory, joins it with
its companion ``<exp_id>_predictions.jsonl`` (when available), computes
extra per-language and per-class breakdowns, and writes a unified
``results.json`` shaped for downstream reporting and plotting.

Usage:
    uv run python scripts/aggregate_results.py
    uv run python scripts/aggregate_results.py --out logs/final/results.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from hipe.evaluation.metrics import (
    AT_LABELS,
    ISAT_LABELS,
    classification_report,
    compute_global_score,
    confusion_matrix,
    null_to_false,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_predictions(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _per_language(rows: list[dict]) -> dict[str, dict[str, Any]]:
    by_lang: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_lang[str(r.get("language") or "unknown")].append(r)
    out: dict[str, dict[str, Any]] = {}
    for lang, bucket in sorted(by_lang.items()):
        if not bucket:
            continue
        at_g = [null_to_false(r.get("at_gold")) for r in bucket]
        at_p = [null_to_false(r.get("at_predicted")) for r in bucket]
        is_g = [null_to_false(r.get("isAt_gold")) for r in bucket]
        is_p = [null_to_false(r.get("isAt_predicted")) for r in bucket]
        try:
            scores = compute_global_score(at_g, at_p, is_g, is_p)
        except ValueError:
            # Skip languages where predictions contain unexpected labels.
            continue
        out[lang] = {
            "n_instances": len(bucket),
            "global_score": scores["global_score"],
            "macro_recall_at": scores["macro_recall_at"],
            "macro_recall_isAt": scores["macro_recall_isAt"],
            "at_details": scores["at_details"],
            "isAt_details": scores["isAt_details"],
            "confusion_matrix_at": confusion_matrix(at_g, at_p, AT_LABELS),
            "confusion_matrix_isAt": confusion_matrix(is_g, is_p, ISAT_LABELS),
        }
    return out


def _label_distribution(rows: list[dict]) -> dict[str, dict[str, dict[str, int]]]:
    """Per-target prediction vs gold label-count distribution."""
    out = {"at": {"gold": defaultdict(int), "pred": defaultdict(int)},
           "isAt": {"gold": defaultdict(int), "pred": defaultdict(int)}}
    for r in rows:
        out["at"]["gold"][str(null_to_false(r.get("at_gold")))] += 1
        out["at"]["pred"][str(null_to_false(r.get("at_predicted")))] += 1
        out["isAt"]["gold"][str(null_to_false(r.get("isAt_gold")))] += 1
        out["isAt"]["pred"][str(null_to_false(r.get("isAt_predicted")))] += 1
    return {
        target: {k: dict(v) for k, v in side.items()}
        for target, side in out.items()
    }


def _accuracy_summary(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"n": 0}
    at_correct = sum(
        1 for r in rows if null_to_false(r.get("at_predicted")) == null_to_false(r.get("at_gold"))
    )
    is_correct = sum(
        1 for r in rows if null_to_false(r.get("isAt_predicted")) == null_to_false(r.get("isAt_gold"))
    )
    both = sum(
        1 for r in rows
        if null_to_false(r.get("at_predicted")) == null_to_false(r.get("at_gold"))
        and null_to_false(r.get("isAt_predicted")) == null_to_false(r.get("isAt_gold"))
    )
    return {
        "n": n,
        "at_accuracy": at_correct / n,
        "isAt_accuracy": is_correct / n,
        "both_accuracy": both / n,
        "at_correct": at_correct,
        "isAt_correct": is_correct,
        "both_correct": both,
    }


def _enrich(report: dict, predictions: list[dict]) -> dict:
    if not predictions:
        return report
    enriched = dict(report)
    enriched["per_language"] = _per_language(predictions)
    enriched["label_distribution"] = _label_distribution(predictions)
    enriched["accuracy"] = _accuracy_summary(predictions)
    return enriched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--log-dir",
        action="append",
        default=None,
        help="Directory of per-experiment reports. Repeatable. Defaults to "
             "logs/ablations + logs/agentic + logs/k_sweep when omitted.",
    )
    ap.add_argument("--out", default=str(PROJECT_ROOT / "logs" / "final" / "results.json"))
    args = ap.parse_args()

    log_dirs = [Path(p) for p in (args.log_dir or [
        PROJECT_ROOT / "logs" / "ablations",
        PROJECT_ROOT / "logs" / "agentic",
        PROJECT_ROOT / "logs" / "k_sweep",
    ])]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    reports: dict[str, dict] = {}
    report_paths = sorted(
        p for log_dir in log_dirs if log_dir.exists()
        for p in log_dir.glob("*_report.json")
    )
    for report_path in report_paths:
        log_dir = report_path.parent
        exp_id = report_path.stem.replace("_report", "")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"  skipping {report_path.name}: invalid JSON")
            continue
        pred_path = log_dir / f"{exp_id}_predictions.jsonl"
        predictions = _load_predictions(pred_path)
        reports[exp_id] = _enrich(report, predictions)
        print(f"  {exp_id}: n={len(predictions)}  global={report.get('scores',{}).get('global_score', 'NA'):.4f}"
              if isinstance(report.get('scores',{}).get('global_score'), float) else f"  {exp_id} (no score)")

    # Build a flat ranking table across all reports for quick consumption.
    ranking: list[dict] = []
    for exp_id, r in reports.items():
        s = r.get("scores", {})
        if not s:
            continue
        md = r.get("metadata", {})
        pred_stats = (md.get("predictor_stats") or {})
        ranking.append({
            "experiment_id": exp_id,
            "global_score": s.get("global_score"),
            "macro_recall_at": s.get("macro_recall_at"),
            "macro_recall_isAt": s.get("macro_recall_isAt"),
            "n_instances": r.get("n_instances"),
            "model": pred_stats.get("model") or md.get("predictor_config", {}).get("model"),
            "provider": pred_stats.get("provider"),
            "variant": pred_stats.get("variant"),
            "k_retrieved": pred_stats.get("k_retrieved", 0),
            "include_wikidata": md.get("predictor_config", {}).get("include_wikidata"),
            "include_temporal": md.get("predictor_config", {}).get("include_temporal"),
            "prompt_tokens": pred_stats.get("prompt_tokens"),
            "completion_tokens": pred_stats.get("completion_tokens"),
            "parse_ok": pred_stats.get("parse_ok"),
            "parse_partial": pred_stats.get("parse_partial"),
            "parse_fail": pred_stats.get("parse_fail"),
            "avg_latency_ms": md.get("avg_latency_ms"),
        })
    ranking.sort(key=lambda r: r.get("global_score") or 0, reverse=True)

    bundle = {
        "n_experiments": len(reports),
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "ranking_by_global_score": ranking,
        "experiments": reports,
    }
    out_path.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    print(f"\nAggregated {len(reports)} experiments -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
