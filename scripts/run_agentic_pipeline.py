"""Run the full agentic pipeline (Classifier -> Justification -> Validator [-> escalation]).

Implements Spec v0.7 sec. 5-6 in a runnable form. The classifier and (optional)
escalation predictor are both ``LLMPredictor`` instances; pass different
``--escalate-model`` (e.g. GPT-5-mini) to enable the Tier-3 escalation path.

Examples:
    # Full agentic run on the at-task baseline with RAG few-shot
    uv run python scripts/run_agentic_pipeline.py \\
        --retriever-dir runs/retriever_at_bgem3 \\
        --variant AB --provider deepinfra --task at \\
        --k-retrieved 5 --diversify-labels

    # Add Tier-3 escalation to OpenAI gpt-4o-mini
    uv run python scripts/run_agentic_pipeline.py \\
        --retriever-dir runs/retriever_at_bgem3 \\
        --variant AB --provider deepinfra --k-retrieved 3 \\
        --escalate-provider openai --escalate-model gpt-4o-mini

    # Disable Justification (matches efficiency profile, sec. 9.2)
    uv run python scripts/run_agentic_pipeline.py \\
        --retriever-dir runs/retriever_at_bgem3 \\
        --variant AB --task at --no-justification --hard-only
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.experiment import run_ablation_experiment
from hipe.llm import (
    AgenticPredictor,
    AgenticPredictorConfig,
    JustificationAgent,
    JustificationAgentConfig,
    LLMPredictor,
    LLMPredictorConfig,
    ValidatorConfig,
)
from hipe.llm.prompts import UserMessageOptions

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_classifier(args: argparse.Namespace, retriever) -> LLMPredictor:
    user_opts = UserMessageOptions(
        zero_shot=not (args.include_wikidata or args.include_temporal or args.k_retrieved),
        include_wikidata=args.include_wikidata,
        include_temporal=args.include_temporal,
        text_field=args.text_field,
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
        retriever_prefer_language=(None if args.retrieval_language == "any"
                                   else args.retrieval_language),
    )
    return LLMPredictor(cfg)


def _build_escalator(args: argparse.Namespace, retriever) -> LLMPredictor | None:
    if not args.escalate_model and not args.escalate_provider:
        return None
    user_opts = UserMessageOptions(
        zero_shot=not (args.include_wikidata or args.include_temporal or args.k_retrieved),
        include_wikidata=args.include_wikidata,
        include_temporal=args.include_temporal,
        text_field=args.text_field,
    )
    cfg = LLMPredictorConfig(
        variant=args.variant,
        provider=args.escalate_provider or args.provider,
        model=args.escalate_model,
        # Spec §4.2 suggests temperature 0.3 for the stronger model so
        # escalation can recover from a deterministic Tier-2 mistake; expose
        # as a CLI knob with a slightly higher default than the classifier.
        temperature=args.escalate_temperature,
        max_tokens=args.max_tokens,
        user_message_options=user_opts,
        retriever=retriever,
        k_retrieved=args.k_retrieved,
        diversify_retrieved_labels=args.diversify_labels,
        retriever_prefer_language=(None if args.retrieval_language == "any"
                                   else args.retrieval_language),
    )
    return LLMPredictor(cfg)


def _build_justifier(args: argparse.Namespace) -> JustificationAgent | None:
    if args.no_justification:
        return None
    cfg = JustificationAgentConfig(
        provider=args.justify_provider or args.provider,
        model=args.justify_model or args.model,
        temperature=args.justify_temperature,
        max_tokens=args.justify_max_tokens,
    )
    return JustificationAgent(cfg)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--task", choices=["at", "isAt"], default="at")
    ap.add_argument("--variant", choices=["A", "B", "AB", "R"], default="AB")
    ap.add_argument("--provider", choices=["deepinfra", "openai"], default="deepinfra")
    ap.add_argument("--model", default=None)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--text-field", choices=["text", "context"], default="text")
    ap.add_argument("--include-wikidata", action="store_true")
    ap.add_argument("--include-temporal", action="store_true")

    # Retriever
    ap.add_argument("--retriever-dir", default=None)
    ap.add_argument("--k-retrieved", type=int, default=0)
    ap.add_argument("--diversify-labels", action="store_true")
    ap.add_argument("--retrieval-language", choices=["auto", "any", "en", "fr", "de"],
                    default="auto")

    # Justification agent
    ap.add_argument("--no-justification", action="store_true",
                    help="Disable the Justification agent (efficiency profile, sec. 9.2).")
    ap.add_argument("--justify-provider", default=None,
                    help="Override provider for the Justification agent.")
    ap.add_argument("--justify-model", default=None,
                    help="Override model for the Justification agent.")
    ap.add_argument("--justify-temperature", type=float, default=0.0)
    ap.add_argument("--justify-max-tokens", type=int, default=768)

    # Validator
    ap.add_argument("--no-validator", action="store_true",
                    help="Disable the Validator entirely.")
    ap.add_argument("--hard-only", action="store_true",
                    help="Validator runs only the hard logical checks "
                         "(efficiency profile, sec. 6.5).")
    ap.add_argument("--at-conf-threshold", type=float, default=0.7)
    ap.add_argument("--isAt-conf-threshold", type=float, default=0.6)
    ap.add_argument("--soft-flag-threshold", type=int, default=2)

    # Escalation
    ap.add_argument("--escalate-provider", choices=["deepinfra", "openai"], default=None,
                    help="Provider for the Tier-3 escalation predictor (sec. 6.4).")
    ap.add_argument("--escalate-model", default=None,
                    help="Model for Tier-3 escalation (e.g. gpt-4o-mini).")
    ap.add_argument("--escalate-temperature", type=float, default=0.3)
    ap.add_argument("--no-escalation", action="store_true",
                    help="Disable escalation in the Validator (logs flags only).")

    ap.add_argument("--experiment-id", default=None)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "agentic"))
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    test = sp.test
    if args.limit is not None:
        test = test[: args.limit]
    print(f"  test split (task={args.task}): {len(test)} instances"
          f"{f' (limited to {args.limit})' if args.limit else ''}")

    retriever = None
    if args.retriever_dir and args.k_retrieved > 0:
        from hipe.retriever import Retriever
        print(f"Loading retriever from {args.retriever_dir}")
        retriever = Retriever.from_disk(args.retriever_dir)
        print(f"  index size = {len(retriever.index)}, dim = {retriever.index.dim}")

    classifier = _build_classifier(args, retriever)
    justifier = _build_justifier(args)
    escalator = _build_escalator(args, retriever)

    val_cfg = ValidatorConfig(
        hard_only=args.hard_only,
        at_conf_threshold=args.at_conf_threshold,
        isAt_conf_threshold=args.isAt_conf_threshold,
        soft_flag_threshold=args.soft_flag_threshold,
        enable_escalation=(not args.no_escalation),
    )
    pipeline_cfg = AgenticPredictorConfig(
        enable_justification=not args.no_justification,
        enable_validator=not args.no_validator,
        validator=val_cfg,
    )
    predictor = AgenticPredictor(
        classifier=classifier,
        justifier=justifier,
        escalator=escalator,
        config=pipeline_cfg,
    )

    print(f"Pipeline: classifier={classifier.client.provider}/{classifier.client.model} "
          f"variant={args.variant} k={args.k_retrieved} "
          f"justifier={'on' if justifier else 'off'} "
          f"validator={'on' if pipeline_cfg.enable_validator else 'off'} "
          f"escalator={escalator.client.model if escalator else 'off'}")

    if args.experiment_id:
        exp_id = args.experiment_id
    else:
        tags = [f"agentic", f"P{args.variant}"]
        if args.k_retrieved:
            tags.append(f"rag{args.k_retrieved}")
            if args.diversify_labels:
                tags.append("div")
        if args.no_justification:
            tags.append("nojust")
        if args.hard_only:
            tags.append("hardonly")
        if escalator is not None:
            tags.append(f"esc-{escalator.client.model.split('/')[-1].replace('.', '')}")
        prov_tag = classifier.client.provider
        model_tag = classifier.client.model.split("/")[-1].replace(".", "")
        exp_id = f"{'_'.join(tags)}_{prov_tag}_{model_tag}_{args.task}-test"
    print(f"Experiment id: {exp_id}")

    extra_meta = {
        "predictor": "AgenticPredictor",
        "classifier_config": {
            "variant": args.variant,
            "provider": classifier.client.provider,
            "model": classifier.client.model,
            "k_retrieved": args.k_retrieved,
            "diversify_labels": args.diversify_labels,
        },
        "justifier_config": (
            {
                "provider": justifier.client.provider,
                "model": justifier.client.model,
            }
            if justifier is not None else None
        ),
        "escalator_config": (
            {
                "provider": escalator.client.provider,
                "model": escalator.client.model,
            }
            if escalator is not None else None
        ),
        "validator_config": {
            "hard_only": val_cfg.hard_only,
            "at_conf_threshold": val_cfg.at_conf_threshold,
            "isAt_conf_threshold": val_cfg.isAt_conf_threshold,
            "soft_flag_threshold": val_cfg.soft_flag_threshold,
            "enable_escalation": val_cfg.enable_escalation,
        },
        "data_split": {"task": args.task, "n_test": len(test), "limit": args.limit},
    }

    report = run_ablation_experiment(
        experiment_id=exp_id,
        predict_fn=predictor.predict,
        dev_instances=test,
        log_dir=args.log_dir,
        extra_metadata=extra_meta,
    )

    stats = predictor.stats()
    print("\nAgentic predictor stats:")
    print(json.dumps(stats, indent=2, default=str))

    report_path = Path(args.log_dir) / f"{exp_id}_report.json"
    if report_path.exists():
        existing = json.loads(report_path.read_text(encoding="utf-8"))
        existing.setdefault("metadata", {})["predictor_stats"] = stats
        report_path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")

    print(f"\nGlobalScore: {report['scores']['global_score']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
