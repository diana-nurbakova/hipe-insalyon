"""Run an LLM baseline (T1.1: zero-shot, no RAG, no temporal features).

Drives ``hipe.evaluation.run_ablation_experiment`` with an
:class:`hipe.llm.LLMPredictor` so the run produces both the official
predictions JSONL and the evaluation report.

Examples:
    # P-AB on DeepInfra Llama 3.1 8B over the at-task test split
    uv run python scripts/run_llm_baseline.py --variant AB

    # Compare four variants on a small slice (smoke test)
    uv run python scripts/run_llm_baseline.py --variant A   --limit 20
    uv run python scripts/run_llm_baseline.py --variant B   --limit 20
    uv run python scripts/run_llm_baseline.py --variant AB  --limit 20
    uv run python scripts/run_llm_baseline.py --variant R   --limit 20

    # Use OpenAI gpt-4o-mini instead
    uv run python scripts/run_llm_baseline.py --variant AB --provider openai
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.experiment import run_ablation_experiment
from hipe.llm import LLMPredictor, LLMPredictorConfig
from hipe.llm.prompts import UserMessageOptions

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--task", choices=["at", "isAt"], default="at",
                    help="Which baseline split to use as the holdout.")
    ap.add_argument("--variant", choices=["A", "B", "AB", "R"], default="AB")
    ap.add_argument("--provider", choices=["deepinfra", "openai", "openrouter"],
                    default="deepinfra",
                    help="openrouter = Tier 0 free models (Spec v0.9 §1.3); "
                         "200 req/day shared across the OpenRouter account.")
    ap.add_argument("--model", default=None,
                    help="Override the provider's default model.")
    ap.add_argument("--fallback-provider",
                    choices=["deepinfra", "openai", "openrouter"], default=None,
                    help="Backup provider engaged once the primary's retries "
                         "are exhausted (e.g. openrouter primary → deepinfra "
                         "fallback if rate-limited).")
    ap.add_argument("--fallback-model", default=None,
                    help="Override the fallback provider's default model.")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--n-samples", type=int, default=1,
                    help="Self-consistency sampling: draw this many predictions "
                         "per instance and majority-vote (at, isAt). 1 = deterministic.")
    ap.add_argument("--sample-temperature", type=float, default=0.7,
                    help="Temperature used when --n-samples > 1.")
    ap.add_argument("--rules-file", default=None,
                    help="Path to a text file containing natural-language SD rules. "
                         "Injected into the user message as a [DOMAIN RULES] block "
                         "(Option C from Subgroup Discovery Specs §6.3).")
    ap.add_argument("--max-tokens", type=int, default=512,
                    help="Output token budget. P-R needs ~400+ for reasoning + classification.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Process only the first N test instances (smoke testing).")
    ap.add_argument("--text-field", choices=["text", "context"], default="text",
                    help="Which field to embed in the prompt's article block.")
    ap.add_argument("--include-wikidata", action="store_true",
                    help="Add the [ENTITY CONTEXT] block.")
    ap.add_argument("--include-temporal", action="store_true",
                    help="Add the [TEMPORAL SIGNALS] block.")
    ap.add_argument("--retriever-dir", default=None,
                    help="Path to a built retrieval index (e.g. runs/retriever_at_bgem3). "
                         "When set, RAG few-shot is enabled.")
    ap.add_argument("--k", "--k-retrieved", dest="k_retrieved", type=int, default=0,
                    help="Number of similar examples to retrieve. 0 disables retrieval.")
    ap.add_argument("--diversify-labels", action="store_true",
                    help="Diversify retrieved examples across (at, isAt) gold labels.")
    ap.add_argument("--retrieval-language", choices=["auto", "any", "en", "fr", "de"], default="auto",
                    help="Retrieval language preference. 'auto'=query language, 'any'=no filter.")
    ap.add_argument("--experiment-id", default=None,
                    help="Override the auto-generated experiment id.")
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    test = sp.test
    if args.limit is not None:
        test = test[: args.limit]
    if args.limit:
        print(f"  test split (task={args.task}): {len(test)} instances (limited to {args.limit})")
    else:
        print(f"  test split (task={args.task}): {len(test)} instances")

    retriever = None
    if args.retriever_dir and args.k_retrieved > 0:
        from hipe.retriever import Retriever
        print(f"Loading retriever from {args.retriever_dir}")
        retriever = Retriever.from_disk(args.retriever_dir)
        print(f"  index size = {len(retriever.index)}, dim = {retriever.index.dim}, "
              f"model = {retriever.encoder.config.model_name}")

    prefer_lang = None if args.retrieval_language == "any" else args.retrieval_language

    domain_rules = None
    if args.rules_file:
        rules_path = Path(args.rules_file)
        if not rules_path.exists():
            ap.error(f"--rules-file does not exist: {rules_path}")
        domain_rules = rules_path.read_text(encoding="utf-8").strip()
        print(f"  loaded {len(domain_rules)} chars of domain rules from {rules_path}")

    user_opts = UserMessageOptions(
        zero_shot=not (args.include_wikidata or args.include_temporal or args.k_retrieved),
        include_wikidata=args.include_wikidata,
        include_temporal=args.include_temporal,
        text_field=args.text_field,
        domain_rules=domain_rules,
    )
    cfg = LLMPredictorConfig(
        variant=args.variant,
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        user_message_options=user_opts,
        retriever=retriever,
        k_retrieved=args.k_retrieved,
        diversify_retrieved_labels=args.diversify_labels,
        retriever_prefer_language=prefer_lang,
        fallback_provider=args.fallback_provider,
        fallback_model=args.fallback_model,
        n_samples=args.n_samples,
        sample_temperature=args.sample_temperature,
    )
    predictor = LLMPredictor(cfg)
    print(f"Predictor: provider={predictor.client.provider} model={predictor.client.model} "
          f"variant={cfg.variant} text_field={user_opts.text_field} k={cfg.k_retrieved}")

    if args.experiment_id:
        exp_id = args.experiment_id
    else:
        tags = []
        tags.append("rag" + str(cfg.k_retrieved) if cfg.k_retrieved else "zeroshot")
        if user_opts.include_wikidata:
            tags.append("wd")
        if user_opts.include_temporal:
            tags.append("temp")
        if user_opts.domain_rules:
            tags.append("rules")
        if cfg.n_samples > 1:
            tags.append(f"sc{cfg.n_samples}")
        prov_tag = predictor.client.provider
        model_tag = predictor.client.model.split("/")[-1].replace(".", "")
        exp_id = f"T1_llm_{'_'.join(tags)}_P{cfg.variant}_{prov_tag}_{model_tag}_{args.task}-test"
    print(f"Experiment id: {exp_id}")

    extra_meta = {
        "predictor_config": {
            "variant": cfg.variant,
            "provider": cfg.provider,
            "model": predictor.client.model,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "text_field": user_opts.text_field,
            "include_wikidata": user_opts.include_wikidata,
            "include_temporal": user_opts.include_temporal,
            "k_retrieved": cfg.k_retrieved,
            "retriever_dir": args.retriever_dir,
            "retriever_prefer_language": prefer_lang,
            "diversify_retrieved_labels": cfg.diversify_retrieved_labels,
            "zero_shot": user_opts.zero_shot,
        },
        "data_split": {
            "task": args.task,
            "n_test": len(test),
            "limit": args.limit,
        },
    }

    report = run_ablation_experiment(
        experiment_id=exp_id,
        predict_fn=predictor.predict,
        dev_instances=test,
        log_dir=args.log_dir,
        extra_metadata=extra_meta,
    )

    stats = predictor.stats()
    print("\nPredictor stats:")
    print(json.dumps(stats, indent=2))
    # Append predictor stats to the report file for cost analysis later.
    report_path = Path(args.log_dir) / f"{exp_id}_report.json"
    if report_path.exists():
        existing = json.loads(report_path.read_text(encoding="utf-8"))
        existing.setdefault("metadata", {})["predictor_stats"] = stats
        report_path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")

    print(f"\nGlobalScore: {report['scores']['global_score']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
