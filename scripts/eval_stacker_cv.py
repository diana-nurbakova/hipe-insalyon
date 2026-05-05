"""Nested CV evaluation of the disagreement stacker.

Implements ``specs/HIPE2026_Disagreement_Stacker_Specs.md`` §6.2 and §4.4
on top of the lookup-table stacker (:mod:`hipe.stacker`).

Inputs
------
K base-model OOF prediction JSONLs, each covering all dataset instances
(typically 1,251). Each row provides ``at_predicted`` for one instance under
the same model — for trainable models, generated via cross-validation so
the prediction for instance ``i`` came from a model that did NOT train on
``i``; for training-free models (LLMs), any prediction is honest.

Protocol
--------
- **Outer CV** (``--n-folds``, default 5): stratified split on ``at_isAt``
  cross-product. For each outer fold, evaluate the stacker on the held-out
  fold using a lookup table built only on the train fold.
- **Greedy model selection** (``--max-models``): inside each outer fold,
  forward-select base models using ``--inner-folds`` CV on the train fold.
  The selected subset for fold ``f`` is the one that maximises mean inner-CV
  MR(at). At each greedy step, we add the candidate giving the largest mean
  inner-CV gain (no improvement → stop).

Outputs
-------
- ``logs/cv/<exp>_summary.json`` — per-outer-fold scores, selected models,
  inner-CV traces, and aggregated mean ± std.
- ``logs/cv/<exp>_oof_predictions.jsonl`` — per-instance stacker predictions
  using the model selected for that instance's outer-test fold (so the file
  is itself leakage-free).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold

from hipe.evaluation.metrics import compute_macro_recall, null_to_false
from hipe.stacker import (
    AT_ORDINAL_MAP,
    apply_lookup,
    build_lookup_table,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parse_base_source(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"--base-source expects NAME=path, got {spec!r}"
        )
    name, _, p = spec.partition("=")
    return name.strip(), Path(p.strip())


def _load_rows(path: Path) -> dict[tuple[str, str, str], dict]:
    out: dict[tuple[str, str, str], dict] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out[(r["document_id"], r["pers_entity_id"], r["loc_entity_id"])] = r
    return out


def _stratified_keys(at: list[str], isAt: list[str]) -> np.ndarray:
    return np.array([f"{a}_{i}" for a, i in zip(at, isAt)])


def _evaluate_subset(
    selected: list[str],
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    base_predictions: dict[str, list[str]],
    at_gold: list[str],
    *,
    tiebreaker: str = "ordinal_median",
    fallback: str = "ordinal",
    fallback_label: str = "FALSE",
) -> tuple[float, dict[str, float]]:
    """Build a lookup on train_idx using ``selected`` models, evaluate on test_idx.

    Returns (MR(at), per-class recall).
    """
    train_pred = {m: [base_predictions[m][i] for i in train_idx] for m in selected}
    train_gold = [at_gold[i] for i in train_idx]
    lookup = build_lookup_table(
        train_pred, train_gold,
        tiebreaker=tiebreaker, ordinal_map=AT_ORDINAL_MAP,
    )
    test_pred = {m: [base_predictions[m][i] for i in test_idx] for m in selected}
    stacker_pred = apply_lookup(
        test_pred, lookup,
        fallback=fallback, fallback_label=fallback_label, ordinal_map=AT_ORDINAL_MAP,
    )
    test_gold = [at_gold[i] for i in test_idx]
    rep = compute_macro_recall(
        test_gold, stacker_pred, label_set=("TRUE", "PROBABLE", "FALSE"),
    )
    per_class = {k.replace("recall_", ""): v for k, v in rep.items() if k.startswith("recall_")}
    return rep["macro_recall"], per_class


def _greedy_select(
    candidates: list[str],
    train_idx: np.ndarray,
    base_predictions: dict[str, list[str]],
    at_gold: list[str],
    keys_for_strat: np.ndarray,
    *,
    max_models: int,
    inner_folds: int,
    tiebreaker: str,
    fallback: str,
    seed: int,
) -> tuple[list[str], list[dict]]:
    """Forward-select up to ``max_models`` candidates by inner-CV mean MR(at).

    Returns (final_selected, per-step trace). Stops if no candidate improves.
    """
    selected: list[str] = []
    remaining = list(candidates)
    trace: list[dict] = []
    skf = StratifiedKFold(
        n_splits=inner_folds, shuffle=True, random_state=seed,
    )
    last_best = -1.0
    while remaining and len(selected) < max_models:
        step_results: list[tuple[str, float, list[float]]] = []
        for cand in remaining:
            trial = selected + [cand]
            fold_scores: list[float] = []
            inner_keys = keys_for_strat[train_idx]
            for inner_train, inner_val in skf.split(train_idx, inner_keys):
                inner_train_idx = train_idx[inner_train]
                inner_val_idx = train_idx[inner_val]
                mr, _ = _evaluate_subset(
                    trial, inner_train_idx, inner_val_idx,
                    base_predictions, at_gold,
                    tiebreaker=tiebreaker, fallback=fallback,
                )
                fold_scores.append(mr)
            mean_mr = float(np.mean(fold_scores))
            step_results.append((cand, mean_mr, fold_scores))
        # Pick best candidate; stop if no gain over last step (ε > 1e-6).
        step_results.sort(key=lambda x: -x[1])
        best_cand, best_mean, best_scores = step_results[0]
        improved = best_mean > last_best + 1e-6
        trace.append({
            "step": len(selected) + 1,
            "candidates_evaluated": [
                {"model": c, "inner_cv_mean_MR": m, "per_inner_fold": s}
                for c, m, s in step_results
            ],
            "selected_this_step": best_cand if improved else None,
            "best_mean": best_mean,
            "improved": improved,
        })
        if not improved:
            break
        selected.append(best_cand)
        remaining.remove(best_cand)
        last_best = best_mean
    return selected, trace


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--base-source", action="append", required=True, type=_parse_base_source,
        metavar="NAME=PATH",
        help="Repeat for each candidate base model. PATH is the OOF predictions "
             "JSONL covering ALL dataset instances (typically 1,251).",
    )
    ap.add_argument("--experiment-id", required=True)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "cv"), type=Path)
    ap.add_argument("--n-folds", type=int, default=5,
                    help="Outer CV fold count.")
    ap.add_argument("--inner-folds", type=int, default=3,
                    help="Inner CV fold count for greedy model selection.")
    ap.add_argument("--max-models", type=int, default=4,
                    help="Cap on the number of base models the greedy step picks.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--tiebreaker", choices=("alphabetical", "ordinal_median", "last_model"),
        default="ordinal_median",
    )
    ap.add_argument(
        "--fallback", choices=("majority", "ordinal", "label"), default="ordinal",
        help="Resolution for vote tuples not seen in the train fold.",
    )
    ap.add_argument(
        "--no-greedy", action="store_true",
        help="Skip greedy selection; use all candidate models in every outer fold.",
    )
    args = ap.parse_args()

    # --- load and align all OOF sources by (doc, pers, loc) key ------------
    candidates: list[str] = []
    by_model: dict[str, dict[tuple[str, str, str], dict]] = {}
    for name, path in args.base_source:
        rows = _load_rows(path)
        candidates.append(name)
        by_model[name] = rows
        print(f"  {name:<20s}: {len(rows):4d} rows from {path}")
    if not candidates:
        ap.error("provide at least one --base-source")

    # Inner-join across candidates by key. Drop instances not present in every
    # source (LLM run might be incomplete during background-fill).
    keys_set = set.intersection(*[set(d.keys()) for d in by_model.values()])
    keys = sorted(keys_set)
    print(f"  shared keys across all sources: {len(keys)}")

    base_predictions: dict[str, list[str]] = {
        name: [null_to_false(by_model[name][k]["at_predicted"]) for k in keys]
        for name in candidates
    }
    # Pull at_gold from whichever source has it; fall back across sources for
    # robustness against single-target prediction files.
    at_gold: list[str] = []
    isAt_gold: list[str | None] = []
    for k in keys:
        ag = None
        ig = None
        for name in candidates:
            r = by_model[name][k]
            if ag is None and r.get("at_gold") is not None:
                ag = r["at_gold"]
            if ig is None and r.get("isAt_gold") is not None:
                ig = r["isAt_gold"]
        at_gold.append(null_to_false(ag))
        isAt_gold.append(ig)
    strat_keys = _stratified_keys(at_gold, [null_to_false(g) for g in isAt_gold])

    # --- outer CV ----------------------------------------------------------
    outer = StratifiedKFold(
        n_splits=args.n_folds, shuffle=True, random_state=args.seed,
    )
    per_fold: list[dict] = []
    oof_pred = [None] * len(keys)
    oof_fold = [-1] * len(keys)
    oof_selected: list[list[str] | None] = [None] * len(keys)

    for fold_idx, (train_idx, test_idx) in enumerate(
        outer.split(np.arange(len(keys)), strat_keys)
    ):
        print(f"\n>>> outer fold {fold_idx+1}/{args.n_folds} "
              f"(train={len(train_idx)}, test={len(test_idx)})")
        if args.no_greedy:
            selected = list(candidates)
            trace = []
        else:
            selected, trace = _greedy_select(
                candidates, train_idx, base_predictions, at_gold, strat_keys,
                max_models=args.max_models, inner_folds=args.inner_folds,
                tiebreaker=args.tiebreaker, fallback=args.fallback, seed=args.seed,
            )
        print(f"   selected: {selected}")

        # Build lookup on full train fold; evaluate on test fold.
        mr_test, per_class_test = _evaluate_subset(
            selected, train_idx, test_idx, base_predictions, at_gold,
            tiebreaker=args.tiebreaker, fallback=args.fallback,
        )
        # Re-derive the lookup once more so we can store stacker predictions.
        train_pred = {m: [base_predictions[m][i] for i in train_idx] for m in selected}
        train_gold_fold = [at_gold[i] for i in train_idx]
        lookup = build_lookup_table(
            train_pred, train_gold_fold,
            tiebreaker=args.tiebreaker, ordinal_map=AT_ORDINAL_MAP,
        )
        test_pred_dict = {m: [base_predictions[m][i] for i in test_idx] for m in selected}
        stacker_pred = apply_lookup(
            test_pred_dict, lookup,
            fallback=args.fallback, fallback_label="FALSE", ordinal_map=AT_ORDINAL_MAP,
        )
        for j, ti in enumerate(test_idx):
            oof_pred[ti] = stacker_pred[j]
            oof_fold[ti] = fold_idx
            oof_selected[ti] = list(selected)

        per_fold.append({
            "fold": fold_idx,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "selected_models": list(selected),
            "MR_at": mr_test,
            "per_class_recall": per_class_test,
            "greedy_trace": trace,
        })
        print(f"   test MR(at) = {mr_test:.4f}   per-class={per_class_test}")

    # --- aggregate ---------------------------------------------------------
    fold_scores = np.array([f["MR_at"] for f in per_fold], dtype=float)
    pooled_mr = compute_macro_recall(
        at_gold, oof_pred, label_set=("TRUE", "PROBABLE", "FALSE"),
    )
    pooled_per_class = {
        k.replace("recall_", ""): v for k, v in pooled_mr.items() if k.startswith("recall_")
    }
    summary = {
        "n_instances": len(keys),
        "n_outer_folds": args.n_folds,
        "n_inner_folds": args.inner_folds,
        "max_models": args.max_models,
        "seed": args.seed,
        "tiebreaker": args.tiebreaker,
        "fallback": args.fallback,
        "candidates": candidates,
        "per_fold": per_fold,
        "MR_at_mean_pm_std": {
            "mean": float(fold_scores.mean()),
            "std": float(fold_scores.std(ddof=1)),
            "per_fold": fold_scores.tolist(),
        },
        "MR_at_pooled_OOF": {
            "macro_recall": pooled_mr["macro_recall"],
            "per_class": pooled_per_class,
        },
        "selected_models_per_fold": [f["selected_models"] for f in per_fold],
    }

    args.log_dir.mkdir(parents=True, exist_ok=True)
    out_summary = args.log_dir / f"{args.experiment_id}_summary.json"
    out_summary.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    out_oof = args.log_dir / f"{args.experiment_id}_oof_predictions.jsonl"
    with out_oof.open("w", encoding="utf-8") as f:
        for k, gold_at, gold_is, pred, fold, sel in zip(
            keys, at_gold, isAt_gold, oof_pred, oof_fold, oof_selected
        ):
            f.write(json.dumps({
                "document_id": k[0],
                "pers_entity_id": k[1],
                "loc_entity_id": k[2],
                "at_predicted": pred,
                "at_gold": gold_at,
                "isAt_gold": gold_is,
                "fold": int(fold),
                "stacker_models": sel,
            }, ensure_ascii=False, default=str) + "\n")

    print("\n" + "=" * 72)
    print(f"Stacker nested CV ({args.n_folds}-fold, candidates={candidates})")
    print("=" * 72)
    print(f"MR(at) per outer fold: {[f'{s:.4f}' for s in fold_scores]}")
    print(f"MR(at) mean +- std:    {fold_scores.mean():.4f} +- {fold_scores.std(ddof=1):.4f}")
    print(f"MR(at) OOF pooled:     {pooled_mr['macro_recall']:.4f}")
    print(f"OOF per-class recall:  {pooled_per_class}")
    print(f"\nWrote {out_summary}")
    print(f"Wrote {out_oof}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
