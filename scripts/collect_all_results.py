"""Aggregate every ablation / combination / CV result under ``logs/`` into one JSON.

Walks the repository's `logs/` tree and merges all JSON artefacts into a single
unified report at `reports/all_results.json`. The output is organised by
*kind* so a downstream consumer (paper, dashboard, model card) can pull the
slice it needs without re-discovering the file layout:

    {
      "generated_at":   ISO-8601 timestamp,
      "repo_root":      "<abs path>",
      "schema_version": "1.0",
      "ablations":  [ {experiment_id, scores, ...}, ... ],
      "agentic":    [ {experiment_id, scores, ...} ],
      "k_sweep":    [ {experiment_id, k, diversify, scores, ...}, ... ],
      "cv": {
        "kfold_per_feature_set": { ... feature_sets block ... },
        "kfold_oof":             { ... oof_summary block ... },
        "stacker_cv":            [ {run, candidates, MR_at_mean_pm_std, ...}, ... ],
        "bootstrap":             [ {run, global_score, MR_at, MR_isAt, ...}, ... ]
      },
      "llm_full_dataset": [ {experiment_id, n_instances, scores, ...} ],
      "disagreement":  { at: {...}, isAt: {...}, n_configurations, ... },
      "submissions": {
        "INSALyon_model_info": "<verbatim file>",
        "run_files": { "run1": [...], "run2": [...], "run3": [...] }
      },
      "index": {
        "by_global_score":       [ {experiment_id, global, kind}, ... ],   # sorted desc
        "by_experiment_id":      { experiment_id: {...} },                 # lookup table
        "n_total_experiments":   int,
        "n_by_kind":             { kind: count }
      }
    }

Usage::

    python scripts/collect_all_results.py --output reports/all_results.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def safe_load_json(path: Path) -> Any | None:
    try:
        return load_json(path)
    except Exception as exc:  # noqa: BLE001 — we want to skip and continue
        print(f"[warn] could not load {path.relative_to(REPO_ROOT)}: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Per-kind collectors
# ---------------------------------------------------------------------------


def _experiment_skeleton(report: dict, source_path: Path) -> dict:
    """Common per-experiment row built from a report-style JSON."""
    return {
        "experiment_id": report.get("experiment_id") or source_path.stem.removesuffix("_report"),
        "source_path": str(source_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "timestamp": report.get("timestamp"),
        "n_instances": report.get("n_instances"),
        "scores": report.get("scores"),
        "metadata": report.get("metadata"),
        "at_classification_report": report.get("at_classification_report"),
        "isAt_classification_report": report.get("isAt_classification_report"),
        "at_confusion_matrix": report.get("at_confusion_matrix"),
        "isAt_confusion_matrix": report.get("isAt_confusion_matrix"),
        "at_labels": report.get("at_labels"),
        "isAt_labels": report.get("isAt_labels"),
    }


def collect_ablations() -> list[dict]:
    """Walk logs/ablations/*.json and emit one row per experiment.

    Skips compound files (`compare_*`, `*_summary*`) — those are merged in by
    `collect_compare_summaries()` instead so the granularity stays uniform.
    """
    out: list[dict] = []
    ablations_dir = REPO_ROOT / "logs" / "ablations"
    if not ablations_dir.exists():
        return out
    for p in sorted(ablations_dir.glob("*.json")):
        name = p.name
        if name.startswith("compare_") or "_summary" in name or name.endswith(".bootstrap.json"):
            continue
        report = safe_load_json(p)
        if not report or "scores" not in report:
            continue
        out.append(_experiment_skeleton(report, p))
    return out


def collect_compare_summaries() -> list[dict]:
    """Expand `logs/ablations/compare_*.json` into per-variant rows."""
    out: list[dict] = []
    for p in sorted((REPO_ROOT / "logs" / "ablations").glob("compare_*.json")):
        data = safe_load_json(p)
        if not data:
            continue
        config = data.get("config", {})
        for r in data.get("results", []):
            out.append(
                {
                    "experiment_id": r.get("experiment_id"),
                    "source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "variant": r.get("variant"),
                    "model": r.get("model"),
                    "provider": r.get("provider"),
                    "scores": r.get("scores"),
                    "predictor_stats": r.get("predictor_stats"),
                    "compare_config": config,
                }
            )
    return out


def collect_mask_same_split_summaries() -> list[dict]:
    """Pick up `logs/ablations/mask_same_split_summary_*.json` aggregate runs."""
    out: list[dict] = []
    for p in sorted((REPO_ROOT / "logs" / "ablations").glob("mask_same_split_summary_*.json")):
        data = safe_load_json(p)
        if not data:
            continue
        out.append(
            {
                "summary_file": p.name,
                "source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                "task": data.get("task") or data.get("split"),
                "rows": data.get("rows") or data,
            }
        )
    return out


def collect_agentic() -> list[dict]:
    out: list[dict] = []
    d = REPO_ROOT / "logs" / "agentic"
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        report = safe_load_json(p)
        if not report:
            continue
        if "scores" in report:
            out.append(_experiment_skeleton(report, p))
        else:
            out.append({"source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"), "raw": report})
    return out


def collect_k_sweep() -> dict:
    """Aggregate the RAG K-sweep results (per-row + per-config summary)."""
    out: dict[str, Any] = {"per_run": [], "summaries": {}}
    d = REPO_ROOT / "logs" / "k_sweep"
    if not d.exists():
        return out

    for p in sorted(d.glob("*_report.json")):
        report = safe_load_json(p)
        if not report:
            continue
        out["per_run"].append(_experiment_skeleton(report, p))

    for summary in ("k_sweep_summary.json", "k_sweep_full188_summary.json"):
        sp = d / summary
        if not sp.exists():
            continue
        data = safe_load_json(sp)
        if data is None:
            continue
        out["summaries"][summary] = {
            "source_path": str(sp.relative_to(REPO_ROOT)).replace("\\", "/"),
            **data,
        }
    return out


def collect_cv() -> dict:
    """Aggregate CV-related artefacts (k-fold per feature set + nested stacker)."""
    cv_out: dict[str, Any] = {
        "kfold_per_feature_set": None,
        "kfold_oof": [],
        "stacker_cv": [],
        "bootstrap": [],
    }

    kfold_summary = REPO_ROOT / "logs" / "kfold" / "kfold_summary_seed42_n5.json"
    if kfold_summary.exists():
        cv_out["kfold_per_feature_set"] = {
            "source_path": str(kfold_summary.relative_to(REPO_ROOT)).replace("\\", "/"),
            **safe_load_json(kfold_summary),
        }

    for oof_summary in (
        REPO_ROOT / "logs" / "kfold_oof" / "oof_summary_seed42_n5.json",
        REPO_ROOT / "logs" / "kfold_oof_window14" / "oof_summary_seed42_n5.json",
    ):
        if oof_summary.exists():
            data = safe_load_json(oof_summary)
            if data is None:
                continue
            cv_out["kfold_oof"].append(
                {
                    "source_path": str(oof_summary.relative_to(REPO_ROOT)).replace("\\", "/"),
                    **data,
                }
            )

    # Nested-CV stacker summaries.
    cv_dir = REPO_ROOT / "logs" / "cv"
    if cv_dir.exists():
        for p in sorted(cv_dir.glob("*_summary.json")):
            data = safe_load_json(p)
            if data is None:
                continue
            cv_out["stacker_cv"].append(
                {
                    "run": p.stem.removesuffix("_summary"),
                    "source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                    **data,
                }
            )
        for p in sorted(cv_dir.glob("*.bootstrap.json")):
            data = safe_load_json(p)
            if data is None:
                continue
            cv_out["bootstrap"].append(
                {
                    "run": p.stem.removesuffix(".bootstrap"),
                    "source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                    **data,
                }
            )

    # Hybrid OOF bootstrap (in logs/kfold).
    extra_bs = REPO_ROOT / "logs" / "kfold" / "hybrid_kfold_oof_predictions.bootstrap.json"
    if extra_bs.exists():
        data = safe_load_json(extra_bs)
        if data is not None:
            cv_out["bootstrap"].append(
                {
                    "run": "hybrid_kfold_oof_predictions",
                    "source_path": str(extra_bs.relative_to(REPO_ROOT)).replace("\\", "/"),
                    **data,
                }
            )

    # Per-ablation bootstrap files (e.g. T1_hybrid_LookupStacker bootstraps).
    for p in sorted((REPO_ROOT / "logs" / "ablations").glob("*.bootstrap.json")):
        data = safe_load_json(p)
        if data is None:
            continue
        cv_out["bootstrap"].append(
            {
                "run": p.stem.removesuffix(".bootstrap"),
                "source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                **data,
            }
        )
    return cv_out


def collect_llm_full() -> list[dict]:
    out: list[dict] = []
    d = REPO_ROOT / "logs" / "llm_full"
    if not d.exists():
        return out
    for p in sorted(d.glob("*_report.json")):
        report = safe_load_json(p)
        if not report:
            continue
        out.append(_experiment_skeleton(report, p))
    return out


def collect_disagreement() -> dict | None:
    p = REPO_ROOT / "logs" / "final" / "disagreement" / "summary.json"
    if not p.exists():
        return None
    return {
        "source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
        **safe_load_json(p),
    }


def collect_final_results_index() -> dict | None:
    """The consolidated 224-experiment index `logs/final/results.json`."""
    p = REPO_ROOT / "logs" / "final" / "results.json"
    if not p.exists():
        return None
    data = safe_load_json(p)
    if data is None:
        return None
    # Strip the full body to a lean ranking — the per-experiment scores already
    # come from `collect_ablations()` so we just keep the ranking here.
    return {
        "source_path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
        "n_experiments": data.get("n_experiments"),
        "generated_at": data.get("generated_at"),
        "ranking_by_global_score": data.get("ranking_by_global_score"),
    }


def collect_submissions() -> dict:
    out: dict[str, Any] = {"INSALyon_model_info": None, "run_files": {}}
    info_path = REPO_ROOT / "submissions" / "INSALyon_model_info.txt"
    if info_path.exists():
        out["INSALyon_model_info"] = info_path.read_text(encoding="utf-8")

    for run in ("run1", "run2", "run3"):
        rd = REPO_ROOT / "submissions" / run
        if not rd.exists():
            continue
        files: list[dict] = []
        for jf in sorted(rd.glob("*.jsonl")):
            n_lines = sum(1 for _ in jf.open("r", encoding="utf-8"))
            files.append(
                {
                    "file": jf.name,
                    "source_path": str(jf.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "n_articles": n_lines,
                }
            )
        out["run_files"][run] = files
    return out


# ---------------------------------------------------------------------------
# Index / ranking
# ---------------------------------------------------------------------------


def _score_of(row: dict, key: str = "global_score") -> float | None:
    s = row.get("scores")
    if not isinstance(s, dict):
        return None
    return s.get(key)


def build_index(
    *,
    ablations: list[dict],
    agentic: list[dict],
    k_sweep_per_run: list[dict],
    llm_full: list[dict],
    compare_rows: list[dict],
) -> dict:
    """Build the cross-section lookup index."""
    everything: list[tuple[str, dict]] = []
    for r in ablations:
        everything.append(("ablation", r))
    for r in agentic:
        everything.append(("agentic", r))
    for r in k_sweep_per_run:
        everything.append(("k_sweep", r))
    for r in llm_full:
        everything.append(("llm_full", r))
    for r in compare_rows:
        everything.append(("compare", r))

    by_id: dict[str, dict] = {}
    n_by_kind: dict[str, int] = {}
    by_global: list[dict] = []
    for kind, row in everything:
        eid = row.get("experiment_id")
        n_by_kind[kind] = n_by_kind.get(kind, 0) + 1
        if not eid:
            continue
        if eid not in by_id:
            by_id[eid] = {"kind": kind, **row}
        gs = _score_of(row)
        if gs is not None:
            by_global.append(
                {
                    "experiment_id": eid,
                    "kind": kind,
                    "global_score": gs,
                    "macro_recall_at": _score_of(row, "macro_recall_at"),
                    "macro_recall_isAt": _score_of(row, "macro_recall_isAt"),
                    "n_instances": row.get("n_instances"),
                }
            )

    by_global.sort(key=lambda r: r["global_score"] or 0.0, reverse=True)
    return {
        "by_global_score": by_global,
        "by_experiment_id": by_id,
        "n_total_experiments": len(by_id),
        "n_by_kind": n_by_kind,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_unified_payload() -> dict:
    ablations = collect_ablations()
    compare_rows = collect_compare_summaries()
    mask_summaries = collect_mask_same_split_summaries()
    agentic = collect_agentic()
    k_sweep = collect_k_sweep()
    cv = collect_cv()
    llm_full = collect_llm_full()
    disagreement = collect_disagreement()
    final_index = collect_final_results_index()
    submissions = collect_submissions()

    index = build_index(
        ablations=ablations,
        agentic=agentic,
        k_sweep_per_run=k_sweep.get("per_run", []),
        llm_full=llm_full,
        compare_rows=compare_rows,
    )

    return {
        "schema_version": "1.0",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "ablations": ablations,
        "compare_runs": compare_rows,
        "mask_same_split_summaries": mask_summaries,
        "agentic": agentic,
        "k_sweep": k_sweep,
        "cv": cv,
        "llm_full_dataset": llm_full,
        "disagreement": disagreement,
        "final_results_index": final_index,
        "submissions": submissions,
        "index": index,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "reports" / "all_results.json",
        help="Path for the unified JSON file.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (set 0 for compact).",
    )
    args = parser.parse_args()

    out_path: Path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_unified_payload()

    indent = args.indent if args.indent > 0 else None
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=indent)

    n_total = payload["index"]["n_total_experiments"]
    n_by_kind = payload["index"]["n_by_kind"]
    print(
        f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)\n"
        f"  total experiments indexed: {n_total}\n"
        f"  by kind: {n_by_kind}\n"
        f"  ablations: {len(payload['ablations'])} rows\n"
        f"  agentic: {len(payload['agentic'])} rows\n"
        f"  k_sweep per-run: {len(payload['k_sweep'].get('per_run', []))} rows\n"
        f"  cv stacker_cv: {len(payload['cv']['stacker_cv'])} runs\n"
        f"  cv bootstrap: {len(payload['cv']['bootstrap'])} runs\n"
        f"  llm_full: {len(payload['llm_full_dataset'])} rows"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
