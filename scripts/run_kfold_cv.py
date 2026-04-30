"""Stratified 5-fold CV for MASK / RF / hybrid classifiers (Spec v0.9 §13.2.3).

Re-runs the four feature-set classifiers from
``scripts/mask_same_split_eval.py`` under stratified k-fold on the **full**
1,251-instance dataset, then assembles the hybrid prediction
(RF(at) + MASK-C4(isAt)) on each fold. Reports mean +/- std over folds plus
per-fold global / macro_recall_at / macro_recall_isAt — proper confidence
intervals for the zero-cost classifiers.

Folds are stratified on the combined ``at x isAt`` label so PROBABLE (the
rare class) lands in every fold.

Outputs
-------
``logs/kfold/{experiment}_kfold_summary.json`` — fold scores + aggregate
``logs/kfold/{experiment}_fold{i}_predictions.jsonl`` — predictions per fold

Usage::

    uv run python scripts/run_kfold_cv.py
    uv run python scripts/run_kfold_cv.py --n-folds 10 --seed 7
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from hipe.data import load_jsonl
from hipe.evaluation.metrics import compute_global_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_lr():
    return make_pipeline(
        StandardScaler(with_mean=True),
        LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs"),
    )


def make_rf():
    return RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


# Mapping mirrors mask_same_split_eval.py so results are directly comparable.
FEATURE_SETS = {
    # name -> (feature_key_in_npz, factory)
    "C1_mask_LR": ("mask", make_lr),
    "C4_mask+e1+e2+temporal_LR": (("concat", "temporal"), make_lr),
    "T1.4_temporal_only_LR": ("temporal", make_lr),
    "T1.5_handcrafted_RF": ("handcrafted", make_rf),
}


def _load_arrays(npz_path: Path) -> dict[str, np.ndarray]:
    Z = np.load(npz_path, allow_pickle=True)
    return {
        "sample_id": Z["sample_id"].astype(str),
        "mask": Z["mask_emb"].astype(np.float32),
        "concat": Z["concat_emb"].astype(np.float32),
        "temporal": Z["temporal"].astype(np.float32),
        "handcrafted": Z["handcrafted"].astype(np.float32),
        "at": Z["at"].astype(str),
        "isAt": Z["isAt"].astype(str),
        "language": Z["language"].astype(str),
    }


def _build_features(arrays: dict[str, np.ndarray], spec) -> np.ndarray:
    if isinstance(spec, str):
        return arrays[spec]
    return np.concatenate([arrays[k] for k in spec], axis=1).astype(np.float32, copy=False)


def _stratified_keys(at: np.ndarray, isAt: np.ndarray) -> np.ndarray:
    """Combined ``at_isAt`` keys for stratification.

    Using the cross-product preserves rare combinations (e.g. ``PROBABLE_TRUE``)
    in every fold so MR(at) doesn't swing wildly across folds.
    """
    return np.array([f"{a}_{i}" for a, i in zip(at, isAt)])


def _kfold_run(
    X: np.ndarray,
    y_at: np.ndarray,
    y_isAt: np.ndarray,
    factory_at,
    factory_isAt,
    n_folds: int,
    seed: int,
) -> tuple[list[dict], np.ndarray, np.ndarray, np.ndarray]:
    """Returns per-fold scores plus aggregated predictions over the union of test folds."""
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    keys = _stratified_keys(y_at, y_isAt)

    n = len(X)
    pred_at = np.empty(n, dtype=object)
    pred_isAt = np.empty(n, dtype=object)
    fold_assign = np.full(n, -1, dtype=np.int64)

    fold_scores: list[dict] = []
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, keys)):
        clf_at = factory_at()
        clf_at.fit(X[train_idx], y_at[train_idx])
        p_at = clf_at.predict(X[test_idx]).astype(str)

        clf_isAt = factory_isAt()
        clf_isAt.fit(X[train_idx], y_isAt[train_idx])
        p_isAt = clf_isAt.predict(X[test_idx]).astype(str)

        scores = compute_global_score(
            y_at[test_idx].tolist(), p_at.tolist(),
            y_isAt[test_idx].tolist(), p_isAt.tolist(),
        )
        fold_scores.append({
            "fold": fold_idx,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "global_score": scores["global_score"],
            "macro_recall_at": scores["macro_recall_at"],
            "macro_recall_isAt": scores["macro_recall_isAt"],
        })
        pred_at[test_idx] = p_at
        pred_isAt[test_idx] = p_isAt
        fold_assign[test_idx] = fold_idx

    return fold_scores, pred_at, pred_isAt, fold_assign


def _aggregate(fold_scores: list[dict]) -> dict:
    arr = lambda key: np.array([s[key] for s in fold_scores], dtype=float)
    return {
        "global_score": {
            "mean": float(arr("global_score").mean()),
            "std": float(arr("global_score").std(ddof=1)) if len(fold_scores) > 1 else 0.0,
            "per_fold": arr("global_score").tolist(),
        },
        "macro_recall_at": {
            "mean": float(arr("macro_recall_at").mean()),
            "std": float(arr("macro_recall_at").std(ddof=1)) if len(fold_scores) > 1 else 0.0,
            "per_fold": arr("macro_recall_at").tolist(),
        },
        "macro_recall_isAt": {
            "mean": float(arr("macro_recall_isAt").mean()),
            "std": float(arr("macro_recall_isAt").std(ddof=1)) if len(fold_scores) > 1 else 0.0,
            "per_fold": arr("macro_recall_isAt").tolist(),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--npz", default=str(
        PROJECT_ROOT / "runs" / "mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz"
    ))
    ap.add_argument("--n-folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "kfold"))
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    print(f"  n_instances = {len(instances)}")

    print(f"Loading cached embeddings {args.npz}")
    arrays = _load_arrays(Path(args.npz))
    n = len(arrays["sample_id"])
    print(f"  cache size: {n}")

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, dict] = {
        "n_folds": args.n_folds,
        "seed": args.seed,
        "n_instances": n,
        "feature_sets": {},
    }

    # --- Per-feature-set: train both targets, score per fold ---
    per_set_predictions: dict[str, dict[str, np.ndarray]] = {}
    for set_name, (feature_spec, factory) in FEATURE_SETS.items():
        X = _build_features(arrays, feature_spec)
        print(f"\n>>> {set_name}  X.shape={X.shape}")
        fold_scores, pred_at, pred_isAt, fold_assign = _kfold_run(
            X, arrays["at"], arrays["isAt"], factory, factory,
            args.n_folds, args.seed,
        )
        agg = _aggregate(fold_scores)
        summary["feature_sets"][set_name] = {
            "input_dim": int(X.shape[1]),
            "fold_scores": fold_scores,
            "aggregate": agg,
        }
        per_set_predictions[set_name] = {
            "at": pred_at,
            "isAt": pred_isAt,
            "fold_assign": fold_assign,
        }
        print(f"   global  = {agg['global_score']['mean']:.4f} +/- {agg['global_score']['std']:.4f}")
        print(f"   MR(at)  = {agg['macro_recall_at']['mean']:.4f} +/- {agg['macro_recall_at']['std']:.4f}")
        print(f"   MR(isAt)= {agg['macro_recall_isAt']['mean']:.4f} +/- {agg['macro_recall_isAt']['std']:.4f}")

    # --- Hybrid: RF(at) + MASK-C4(isAt) per fold ---
    # For each fold, predict at with handcrafted RF and isAt with MASK C4 LR
    # using the SAME train/test split, then score the merged predictions.
    print("\n>>> HYBRID  RF(at) + MASK-C4(isAt)  (per-fold same-split merge)")
    skf = StratifiedKFold(n_splits=args.n_folds, shuffle=True, random_state=args.seed)
    keys = _stratified_keys(arrays["at"], arrays["isAt"])
    X_rf = arrays["handcrafted"]
    X_mask = np.concatenate([arrays["concat"], arrays["temporal"]], axis=1)

    hybrid_pred_at = np.empty(n, dtype=object)
    hybrid_pred_isAt = np.empty(n, dtype=object)
    hybrid_fold_scores: list[dict] = []
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X_rf, keys)):
        rf = make_rf()
        rf.fit(X_rf[train_idx], arrays["at"][train_idx])
        p_at = rf.predict(X_rf[test_idx]).astype(str)

        lr = make_lr()
        lr.fit(X_mask[train_idx], arrays["isAt"][train_idx])
        p_isAt = lr.predict(X_mask[test_idx]).astype(str)

        scores = compute_global_score(
            arrays["at"][test_idx].tolist(), p_at.tolist(),
            arrays["isAt"][test_idx].tolist(), p_isAt.tolist(),
        )
        hybrid_fold_scores.append({
            "fold": fold_idx,
            "n_train": int(len(train_idx)),
            "n_test": int(len(test_idx)),
            "global_score": scores["global_score"],
            "macro_recall_at": scores["macro_recall_at"],
            "macro_recall_isAt": scores["macro_recall_isAt"],
        })
        hybrid_pred_at[test_idx] = p_at
        hybrid_pred_isAt[test_idx] = p_isAt

    hybrid_agg = _aggregate(hybrid_fold_scores)
    summary["hybrid_RF_at_plus_MASK_C4_isAt"] = {
        "fold_scores": hybrid_fold_scores,
        "aggregate": hybrid_agg,
    }
    print(f"   global  = {hybrid_agg['global_score']['mean']:.4f} +/- {hybrid_agg['global_score']['std']:.4f}")
    print(f"   MR(at)  = {hybrid_agg['macro_recall_at']['mean']:.4f} +/- {hybrid_agg['macro_recall_at']['std']:.4f}")
    print(f"   MR(isAt)= {hybrid_agg['macro_recall_isAt']['mean']:.4f} +/- {hybrid_agg['macro_recall_isAt']['std']:.4f}")

    # Persist hybrid out-of-fold predictions for downstream ensembling.
    out_predictions = log_dir / f"hybrid_kfold_oof_predictions.jsonl"
    with out_predictions.open("w", encoding="utf-8") as f:
        for sid, lang, gold_at, gold_isAt, p_at, p_isAt in zip(
            arrays["sample_id"], arrays["language"],
            arrays["at"], arrays["isAt"],
            hybrid_pred_at, hybrid_pred_isAt,
        ):
            parts = sid.split(" | ")
            f.write(json.dumps({
                "document_id": parts[0] if parts else sid,
                "pers_entity_id": parts[1] if len(parts) > 1 else "",
                "loc_entity_id": parts[2] if len(parts) > 2 else "",
                "language": lang,
                "at_predicted": p_at,
                "isAt_predicted": p_isAt,
                "at_gold": gold_at,
                "isAt_gold": gold_isAt,
            }, ensure_ascii=False) + "\n")
    print(f"\nWrote OOF hybrid predictions to {out_predictions}")

    summary_path = log_dir / f"kfold_summary_seed{args.seed}_n{args.n_folds}.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"Wrote summary to {summary_path}")

    print("\n" + "=" * 78)
    print(f"{args.n_folds}-fold CV (seed={args.seed}, n={n})")
    print("=" * 78)
    print(f"{'config':<42s} {'global':>15s} {'MR(at)':>15s} {'MR(isAt)':>15s}")
    for set_name, payload in summary["feature_sets"].items():
        a = payload["aggregate"]
        print(
            f"{set_name:<42s} "
            f"{a['global_score']['mean']:>7.4f}+/-{a['global_score']['std']:.3f}  "
            f"{a['macro_recall_at']['mean']:>7.4f}+/-{a['macro_recall_at']['std']:.3f}  "
            f"{a['macro_recall_isAt']['mean']:>7.4f}+/-{a['macro_recall_isAt']['std']:.3f}"
        )
    a = hybrid_agg
    print(
        f"{'HYBRID (RF at + MASK-C4 isAt)':<42s} "
        f"{a['global_score']['mean']:>7.4f}+/-{a['global_score']['std']:.3f}  "
        f"{a['macro_recall_at']['mean']:>7.4f}+/-{a['macro_recall_at']['std']:.3f}  "
        f"{a['macro_recall_isAt']['mean']:>7.4f}+/-{a['macro_recall_isAt']['std']:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
