"""Run multiple prompt variants on the same holdout and tabulate scores.

For each requested variant (default: A, B, AB, R) this runs the LLM
zero-shot baseline through ``run_ablation_experiment`` and then prints a
comparison table. Variant P-A targets only ``at`` (so its ``isAt`` column
will be FALSE-by-default) and P-B vice versa; the comparison flags this
so the table is interpretable.

Reports land in ``logs/ablations/`` exactly like ``run_llm_baseline.py``,
plus a combined ``compare_<task>_<provider>_<model>.json`` with the
side-by-side numbers.

Usage:
    uv run python scripts/compare_prompt_variants.py
    uv run python scripts/compare_prompt_variants.py --variants AB R
    uv run python scripts/compare_prompt_variants.py --provider openai --model gpt-4o-mini --limit 30
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.experiment import run_ablation_experiment
from hipe.llm import LLMPredictor, LLMPredictorConfig
from hipe.llm.prompts import UserMessageOptions

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _experiment_id(variant: str, provider: str, model: str, task: str, *, with_ctx: bool, limit: int | None) -> str:
    tag = "withctx" if with_ctx else "zeroshot"
    model_tag = model.split("/")[-1].replace(".", "")
    suffix = f"_lim{limit}" if limit else ""
    return f"T1.1_llm_{tag}_P{variant}_{provider}_{model_tag}_{task}-test{suffix}"


def run_variant(
    variant: str,
    *,
    test_instances,
    config: dict[str, Any],
) -> dict[str, Any]:
    user_opts = UserMessageOptions(
        zero_shot=not (config["include_wikidata"] or config["include_temporal"]),
        include_wikidata=config["include_wikidata"],
        include_temporal=config["include_temporal"],
        text_field=config["text_field"],
    )
    cfg = LLMPredictorConfig(
        variant=variant,
        provider=config["provider"],
        model=config["model"],
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        user_message_options=user_opts,
    )
    predictor = LLMPredictor(cfg)

    exp_id = _experiment_id(
        variant,
        provider=predictor.client.provider,
        model=predictor.client.model,
        task=config["task"],
        with_ctx=config["include_wikidata"] or config["include_temporal"],
        limit=config["limit"],
    )
    print(f"\n>>> Variant P-{variant}  (exp_id={exp_id})")

    extra_meta = {
        "predictor_config": {
            "variant": variant,
            "provider": cfg.provider,
            "model": predictor.client.model,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "text_field": user_opts.text_field,
            "include_wikidata": user_opts.include_wikidata,
            "include_temporal": user_opts.include_temporal,
            "zero_shot": user_opts.zero_shot,
        },
        "data_split": {
            "task": config["task"],
            "n_test": len(test_instances),
            "limit": config["limit"],
        },
    }

    report = run_ablation_experiment(
        experiment_id=exp_id,
        predict_fn=predictor.predict,
        dev_instances=test_instances,
        log_dir=config["log_dir"],
        extra_metadata=extra_meta,
        print_summary=False,
    )

    stats = predictor.stats()
    # Persist predictor stats into the report file.
    report_path = Path(config["log_dir"]) / f"{exp_id}_report.json"
    if report_path.exists():
        existing = json.loads(report_path.read_text(encoding="utf-8"))
        existing.setdefault("metadata", {})["predictor_stats"] = stats
        report_path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")

    scores = report["scores"]
    print(
        f"    Global={scores['global_score']:.4f}  "
        f"MR(at)={scores['macro_recall_at']:.4f}  "
        f"MR(isAt)={scores['macro_recall_isAt']:.4f}  "
        f"parse_ok={stats['parse_ok']}/{stats['n_calls']}"
    )

    return {
        "variant": variant,
        "experiment_id": exp_id,
        "model": predictor.client.model,
        "provider": predictor.client.provider,
        "scores": scores,
        "predictor_stats": stats,
        "report_path": str(report_path),
    }


def print_table(results: list[dict[str, Any]]) -> None:
    print("\n" + "=" * 96)
    print("Prompt-variant comparison")
    print("=" * 96)
    header = (
        f"{'variant':<8s}{'global':>10s}{'MR(at)':>10s}{'MR(isAt)':>11s}"
        f"{'parse_ok':>11s}{'tok_in':>10s}{'tok_out':>10s}"
    )
    print(header)
    print("-" * 96)
    for r in results:
        s = r["scores"]
        st = r["predictor_stats"]
        ok_frac = f"{st['parse_ok']}/{st['n_calls']}"
        print(
            f"P-{r['variant']:<6s}"
            f"{s['global_score']:>10.4f}"
            f"{s['macro_recall_at']:>10.4f}"
            f"{s['macro_recall_isAt']:>11.4f}"
            f"{ok_frac:>11s}"
            f"{st['prompt_tokens']:>10d}"
            f"{st['completion_tokens']:>10d}"
        )
    print("=" * 96)
    if results:
        best = max(results, key=lambda r: r["scores"]["global_score"])
        print(f"Best by global score: P-{best['variant']} "
              f"({best['scores']['global_score']:.4f})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--task", choices=["at", "isAt"], default="at")
    ap.add_argument("--variants", nargs="+", default=["A", "B", "AB", "R"],
                    choices=["A", "B", "AB", "R"])
    ap.add_argument("--provider", choices=["deepinfra", "openai"], default="deepinfra")
    ap.add_argument("--model", default=None)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--text-field", choices=["text", "context"], default="text")
    ap.add_argument("--include-wikidata", action="store_true")
    ap.add_argument("--include-temporal", action="store_true")
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    test = sp.test
    if args.limit is not None:
        test = test[: args.limit]
    print(f"Holdout: task={args.task}, n_test={len(test)}")

    config = {
        "provider": args.provider,
        "model": args.model,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "text_field": args.text_field,
        "include_wikidata": args.include_wikidata,
        "include_temporal": args.include_temporal,
        "task": args.task,
        "limit": args.limit,
        "log_dir": args.log_dir,
    }

    results: list[dict[str, Any]] = []
    for variant in args.variants:
        results.append(run_variant(variant, test_instances=test, config=config))

    print_table(results)

    out_path = Path(args.log_dir) / (
        f"compare_P{'-'.join(args.variants)}_{args.provider}_{args.task}-test"
        f"{'_lim' + str(args.limit) if args.limit else ''}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"config": config, "results": results}, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nCombined comparison written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
