"""Run an LLM over the FULL dataset (not just the at-test split).

Used to generate base-model predictions on every instance for nested-CV
evaluation of the disagreement stacker (see
``specs/HIPE2026_Disagreement_Stacker_Specs.md`` §6.2).

The LLM is training-free — predictions on any instance are honest regardless
of which CV fold that instance lands in — so a single full-dataset pass
suffices. For trainable base models, use ``scripts/run_kfold_cv.py`` with
``--emit-per-model-oof``.

Optional ``--skip-existing`` reads a previous JSONL and only predicts
instances missing from it; the existing rows are concatenated into the
output. Lets you reuse the at-test predictions (188 instances) and pay only
for the 1,063 train-side ones.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import orjson

from hipe.data import load_jsonl
from hipe.data.official import iter_official_instances
from hipe.llm import LLMPredictor, LLMPredictorConfig
from hipe.llm.prompts import UserMessageOptions

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_existing_keys(path: Path) -> tuple[set, list[dict]]:
    """Return (keys, full_rows) from a predictions JSONL."""
    keys: set = set()
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            keys.add((r["document_id"], r["pers_entity_id"], r["loc_entity_id"]))
            rows.append(r)
    return keys, rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--variant", choices=["A", "B", "AB", "R"], default="AB")
    ap.add_argument("--provider", choices=["deepinfra", "openai", "openrouter"], default="openrouter")
    ap.add_argument("--model", default="google/gemma-4-31b-it")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--text-field", choices=["text", "context"], default="text")
    ap.add_argument("--include-wikidata", action="store_true")
    ap.add_argument("--include-temporal", action="store_true")
    ap.add_argument("--rules-file", default=None)
    ap.add_argument(
        "--skip-existing", type=Path, default=None,
        help="Predictions JSONL whose rows are reused; only missing instances are predicted.",
    )
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "llm_full"), type=Path)
    ap.add_argument("--print-every", type=int, default=25)
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl}")
    # Auto-detect official nested format (top-level ``sampled_pairs``) vs the
    # flat dataset_reference.jsonl format.
    nested = False
    with Path(args.jsonl).open("rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            head = orjson.loads(raw)
            nested = "sampled_pairs" in head and "pers_entity_id" not in head
            break
    if nested:
        print("  detected official nested format (sampled_pairs); flattening to RelationInstance")
        instances = list(iter_official_instances(args.jsonl))
    else:
        instances = load_jsonl(args.jsonl)
    print(f"  n_instances total = {len(instances)}")

    skipped_rows: list[dict] = []
    existing_keys: set = set()
    if args.skip_existing:
        existing_keys, skipped_rows = _load_existing_keys(args.skip_existing)
        print(f"  reusing {len(skipped_rows)} existing rows from {args.skip_existing}")

    todo = [
        inst for inst in instances
        if (inst.document_id, inst.pers_entity_id, inst.loc_entity_id) not in existing_keys
    ]
    print(f"  to predict: {len(todo)}")

    domain_rules = None
    if args.rules_file:
        rules_path = Path(args.rules_file)
        if not rules_path.exists():
            ap.error(f"--rules-file does not exist: {rules_path}")
        domain_rules = rules_path.read_text(encoding="utf-8").strip()
        print(f"  loaded {len(domain_rules)} chars of domain rules from {rules_path}")

    user_opts = UserMessageOptions(
        zero_shot=not (args.include_wikidata or args.include_temporal),
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
    )
    predictor = LLMPredictor(cfg)
    print(f"Predictor: provider={predictor.client.provider} model={predictor.client.model} "
          f"variant={cfg.variant}")

    args.log_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = args.log_dir / f"{args.experiment_id}_predictions.jsonl"

    # Stream new predictions to disk so a crash doesn't lose them. Reused rows
    # are appended at the end so resuming is idempotent (re-reading the file
    # via --skip-existing would just re-skip everything).
    n_done = 0
    n_fail = 0
    with out_jsonl.open("w", encoding="utf-8") as f:
        for r in skipped_rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        for i, inst in enumerate(todo):
            try:
                pred = predictor.predict(inst)
            except Exception as exc:
                n_fail += 1
                print(f"  [{i}] FAIL on {inst.document_id} / {inst.pers_entity_id}: {exc!r}",
                      file=sys.stderr)
                continue
            row = {
                "document_id": inst.document_id,
                "pers_entity_id": inst.pers_entity_id,
                "loc_entity_id": inst.loc_entity_id,
                "language": inst.language,
                "at_predicted": pred.get("at"),
                "isAt_predicted": pred.get("isAt"),
                "at_gold": inst.at,
                "isAt_gold": inst.isAt,
                "at_explanation": pred.get("at_explanation"),
                "isAt_explanation": pred.get("isAt_explanation"),
                "raw_output": pred.get("raw_output"),
            }
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            f.flush()
            n_done += 1
            if (i + 1) % args.print_every == 0:
                stats = predictor.stats()
                print(f"  [{i+1}/{len(todo)}] ok={stats.get('parse_ok',0)} "
                      f"partial={stats.get('parse_partial',0)} fail={stats.get('parse_fail',0)} "
                      f"input_tokens={stats.get('prompt_tokens',0)}")

    print(f"\nDone: {n_done} new predictions, {n_fail} failures, {len(skipped_rows)} reused")
    print(f"Wrote {out_jsonl}")
    print(json.dumps(predictor.stats(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
