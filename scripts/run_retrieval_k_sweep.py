"""K-sweep + diversify-labels ablation for the RAG retriever (Spec §3.3).

Runs ``LLMPredictor`` over the dev/test split for a grid of
``(k, diversify_labels)`` settings and writes:

    logs/ablations/<experiment_id>_predictions.jsonl  (one per cell)
    logs/ablations/<experiment_id>_report.json        (one per cell)
    <log-dir>/k_sweep_summary.csv                     (aggregate)
    <log-dir>/k_sweep_summary.json                    (aggregate)

The aggregate is the artefact this script exists for: it lets us pick the
best (k, diversify) combo for the production run by eyeballing one table.

Examples:
    # Full sweep on the at-task baseline
    uv run python scripts/run_retrieval_k_sweep.py \\
        --retriever-dir runs/retriever_at_bgem3 \\
        --variant AB --provider deepinfra --task at \\
        --k-values 1 3 5 8 --limit 100

    # Smoke test with both diversify settings
    uv run python scripts/run_retrieval_k_sweep.py \\
        --retriever-dir runs/retriever_at_bgem3 \\
        --variant AB --task at --k-values 3 5 \\
        --diversify-modes off on --limit 30
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.experiment import run_ablation_experiment
from hipe.llm import LLMPredictor, LLMPredictorConfig
from hipe.llm.prompts import UserMessageOptions

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _format_summary(rows: list[dict[str, Any]]) -> str:
    """Render the sweep table as a fixed-width string for stdout."""
    if not rows:
        return "(empty)"
    headers = [
        "k", "diversify", "global", "macro_at", "macro_isAt",
        "n_calls", "parse_ok", "avg_lat_ms", "avg_retrieved",
    ]
    widths = {h: len(h) for h in headers}
    formatted: list[dict[str, str]] = []
    for r in rows:
        cells = {
            "k": str(r["k"]),
            "diversify": "yes" if r["diversify_labels"] else "no",
            "global": f"{r['global_score']:.4f}",
            "macro_at": f"{r['macro_recall_at']:.4f}",
            "macro_isAt": f"{r['macro_recall_isAt']:.4f}",
            "n_calls": str(r["n_calls"]),
            "parse_ok": str(r["parse_ok"]),
            "avg_lat_ms": f"{r['avg_latency_ms']:.0f}",
            "avg_retrieved": f"{r['avg_retrieved_per_call']:.2f}",
        }
        for h, v in cells.items():
            widths[h] = max(widths[h], len(v))
        formatted.append(cells)
    sep = "  "
    lines = [sep.join(h.ljust(widths[h]) for h in headers)]
    lines.append(sep.join("-" * widths[h] for h in headers))
    for cells in formatted:
        lines.append(sep.join(cells[h].ljust(widths[h]) for h in headers))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--task", choices=["at", "isAt"], default="at",
                    help="Which baseline split to use as the holdout.")
    ap.add_argument("--variant", choices=["A", "B", "AB", "R"], default="AB")
    ap.add_argument("--provider", choices=["deepinfra", "openai"], default="deepinfra")
    ap.add_argument("--model", default=None,
                    help="Override the provider's default model.")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--retriever-dir", required=True,
                    help="Path to a built retrieval index (e.g. runs/retriever_at_bgem3).")
    ap.add_argument("--k-values", type=int, nargs="+", default=[1, 3, 5, 8],
                    help="K values to sweep.")
    ap.add_argument("--diversify-modes", nargs="+", choices=["off", "on", "both"],
                    default=["both"],
                    help="Whether to diversify across (at, isAt) gold buckets. "
                         "Pass 'both' (default) to run each k twice.")
    ap.add_argument("--retrieval-language", choices=["auto", "any", "en", "fr", "de"],
                    default="auto")
    ap.add_argument("--limit", type=int, default=None,
                    help="Process only the first N test instances per cell (smoke testing).")
    ap.add_argument("--text-field", choices=["text", "context"], default="text")
    ap.add_argument("--include-wikidata", action="store_true")
    ap.add_argument("--include-temporal", action="store_true")
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "k_sweep"))
    ap.add_argument("--summary-name", default="k_sweep_summary",
                    help="Basename of the aggregate CSV/JSON files.")
    ap.add_argument("--experiment-prefix", default="T2_ksweep",
                    help="Prefix for per-cell experiment ids.")
    args = ap.parse_args()

    # Resolve diversify modes to a concrete list of booleans.
    diversify_settings: list[bool] = []
    for m in args.diversify_modes:
        if m == "both":
            diversify_settings.extend([False, True])
        elif m == "on":
            diversify_settings.append(True)
        else:
            diversify_settings.append(False)
    # Deduplicate while preserving order.
    seen: set[bool] = set()
    diversify_settings = [d for d in diversify_settings if not (d in seen or seen.add(d))]

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    test = sp.test
    if args.limit is not None:
        test = test[: args.limit]
    print(f"  test split (task={args.task}): {len(test)} instances "
          f"(limited to {args.limit})" if args.limit else f"  test split (task={args.task}): {len(test)} instances")

    from hipe.retriever import Retriever

    print(f"Loading retriever from {args.retriever_dir}")
    retriever = Retriever.from_disk(args.retriever_dir)
    print(f"  index size = {len(retriever.index)}, dim = {retriever.index.dim}, "
          f"model = {retriever.encoder.config.model_name}")

    prefer_lang = None if args.retrieval_language == "any" else args.retrieval_language
    user_opts = UserMessageOptions(
        zero_shot=False,
        include_wikidata=args.include_wikidata,
        include_temporal=args.include_temporal,
        text_field=args.text_field,
    )

    summary_rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    for k in args.k_values:
        for diversify in diversify_settings:
            cfg = LLMPredictorConfig(
                variant=args.variant,
                provider=args.provider,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                user_message_options=user_opts,
                retriever=retriever,
                k_retrieved=k,
                diversify_retrieved_labels=diversify,
                retriever_prefer_language=prefer_lang,
            )
            predictor = LLMPredictor(cfg)
            div_tag = "div" if diversify else "nodiv"
            model_tag = predictor.client.model.split("/")[-1].replace(".", "")
            exp_id = (
                f"{args.experiment_prefix}_k{k}_{div_tag}_P{cfg.variant}"
                f"_{predictor.client.provider}_{model_tag}_{args.task}-test"
            )
            print(f"\n>>> Cell: k={k}, diversify={diversify}  exp_id={exp_id}")

            extra_meta = {
                "predictor_config": {
                    "variant": cfg.variant,
                    "provider": cfg.provider,
                    "model": predictor.client.model,
                    "temperature": cfg.temperature,
                    "k_retrieved": cfg.k_retrieved,
                    "diversify_retrieved_labels": cfg.diversify_retrieved_labels,
                    "retriever_dir": args.retriever_dir,
                    "retriever_prefer_language": prefer_lang,
                    "include_wikidata": user_opts.include_wikidata,
                    "include_temporal": user_opts.include_temporal,
                },
                "data_split": {"task": args.task, "n_test": len(test), "limit": args.limit},
            }

            report = run_ablation_experiment(
                experiment_id=exp_id,
                predict_fn=predictor.predict,
                dev_instances=test,
                log_dir=log_dir,
                extra_metadata=extra_meta,
                print_summary=False,
            )
            stats = predictor.stats()
            scores = report["scores"]

            row = {
                "experiment_id": exp_id,
                "k": k,
                "diversify_labels": diversify,
                "global_score": scores["global_score"],
                "macro_recall_at": scores["macro_recall_at"],
                "macro_recall_isAt": scores["macro_recall_isAt"],
                "n_calls": stats["n_calls"],
                "parse_ok": stats["parse_ok"],
                "parse_partial": stats["parse_partial"],
                "parse_fail": stats["parse_fail"],
                "avg_latency_ms": report["metadata"]["avg_latency_ms"],
                "avg_retrieved_per_call": stats["avg_retrieved_per_call"],
                "model": predictor.client.model,
                "provider": predictor.client.provider,
            }
            summary_rows.append(row)

            print(
                f"    global={row['global_score']:.4f}  "
                f"macro_at={row['macro_recall_at']:.4f}  "
                f"macro_isAt={row['macro_recall_isAt']:.4f}  "
                f"parse_ok={stats['parse_ok']}/{stats['n_calls']}"
            )

            # Append per-cell stats to the report for downstream tooling.
            report_path = log_dir / f"{exp_id}_report.json"
            if report_path.exists():
                existing = json.loads(report_path.read_text(encoding="utf-8"))
                existing.setdefault("metadata", {})["predictor_stats"] = stats
                report_path.write_text(
                    json.dumps(existing, indent=2, default=str), encoding="utf-8"
                )

    # Sort: global score desc, then k asc.
    summary_rows.sort(key=lambda r: (-r["global_score"], r["k"]))

    csv_path = log_dir / f"{args.summary_name}.csv"
    json_path = log_dir / f"{args.summary_name}.json"
    if summary_rows:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
    json_path.write_text(
        json.dumps(
            {
                "task": args.task,
                "variant": args.variant,
                "n_test": len(test),
                "limit": args.limit,
                "k_values": args.k_values,
                "diversify_settings": diversify_settings,
                "rows": summary_rows,
                "elapsed_seconds": time.perf_counter() - t0,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print(f"K-sweep summary  ({len(summary_rows)} cells, sorted by global score):")
    print(_format_summary(summary_rows))
    print(f"\nWrote {csv_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
