"""Emit per-model OOF predictions for nested-CV stacker evaluation.

Companion to ``scripts/run_kfold_cv.py``: that script reports per-classifier
fold scores and writes only the hybrid OOF JSONL. For nested-CV evaluation
of the disagreement stacker (see
``specs/HIPE2026_Disagreement_Stacker_Specs.md`` §6.2) we need a separate
OOF JSONL per candidate base model so the stacker can replay them per fold.

Models emitted (each as ``logs/kfold_oof/<name>_at_oof_predictions.jsonl``):
- ``RF_handcrafted``      handcrafted features + RandomForest (matches T1.5 test-split run)
- ``C4_mask_e1e2_temp``   MASK + e1 + e2 + temporal features + LogisticRegression

Folds are stratified on the ``at_isAt`` cross-product to keep PROBABLE
balanced. Folds match ``run_kfold_cv.py`` for the same ``--seed`` / ``--n-folds``
so the OOF rows align across base-model emitters and the SDov overlay (if/when
that gets CV-aware later).
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


def _stratified_keys(at: np.ndarray, isAt: np.ndarray) -> np.ndarray:
    return np.array([f"{a}_{i}" for a, i in zip(at, isAt)])


def _split_sample_id(sid: str) -> tuple[str, str, str]:
    parts = sid.split(" | ")
    return (
        parts[0] if parts else sid,
        parts[1] if len(parts) > 1 else "",
        parts[2] if len(parts) > 2 else "",
    )


def cross_val_predict_at(
    X: np.ndarray,
    y_at: np.ndarray,
    keys: np.ndarray,
    factory,
    n_folds: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Run K-fold CV, return (OOF at_pred, fold_assign, per-fold MR(at))."""
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    n = len(X)
    pred = np.empty(n, dtype=object)
    fold_assign = np.full(n, -1, dtype=np.int64)
    per_fold: list[dict] = []
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, keys)):
        clf = factory()
        clf.fit(X[train_idx], y_at[train_idx])
        p = clf.predict(X[test_idx]).astype(str)
        pred[test_idx] = p
        fold_assign[test_idx] = fold_idx
        # Per-fold MR(at) only — isAt is intentionally left null on these rows.
        scores = compute_global_score(
            y_at[test_idx].tolist(), p.tolist(),
            ["FALSE"] * len(test_idx), ["FALSE"] * len(test_idx),
        )
        per_fold.append({
            "fold": fold_idx,
            "n_test": int(len(test_idx)),
            "macro_recall_at": scores["macro_recall_at"],
        })
    return pred, fold_assign, per_fold


def write_oof_jsonl(
    out_path: Path,
    sample_ids: np.ndarray,
    languages: np.ndarray,
    at_gold: np.ndarray,
    isAt_gold: np.ndarray,
    at_pred: np.ndarray,
    fold_assign: np.ndarray,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for sid, lang, ag, ig, ap_, fold in zip(
            sample_ids, languages, at_gold, isAt_gold, at_pred, fold_assign
        ):
            doc, pers, loc = _split_sample_id(sid)
            f.write(json.dumps({
                "document_id": doc,
                "pers_entity_id": pers,
                "loc_entity_id": loc,
                "language": lang,
                "at_predicted": ap_,
                "isAt_predicted": None,
                "at_gold": ag,
                "isAt_gold": ig,
                "fold": int(fold),
            }, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", default=str(
        PROJECT_ROOT / "runs" / "mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz"
    ))
    ap.add_argument("--n-folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "kfold_oof"), type=Path)
    args = ap.parse_args()

    print(f"Loading cached embeddings {args.npz}")
    arrays = _load_arrays(Path(args.npz))
    n = len(arrays["sample_id"])
    print(f"  cache size: {n}")

    keys = _stratified_keys(arrays["at"], arrays["isAt"])
    log_dir = Path(args.log_dir)

    summary = {"n_folds": args.n_folds, "seed": args.seed, "n_instances": n, "models": {}}

    for name, X_spec, factory in [
        ("RF_handcrafted", "handcrafted", make_rf),
        ("C4_mask_e1e2_temp", ("concat", "temporal"), make_lr),
    ]:
        if isinstance(X_spec, str):
            X = arrays[X_spec]
        else:
            X = np.concatenate([arrays[k] for k in X_spec], axis=1).astype(np.float32, copy=False)
        print(f"\n>>> {name}  X.shape={X.shape}")

        pred, fold_assign, per_fold = cross_val_predict_at(
            X, arrays["at"], keys, factory, args.n_folds, args.seed,
        )
        out_path = log_dir / f"{name}_at_oof_predictions.jsonl"
        write_oof_jsonl(
            out_path,
            arrays["sample_id"], arrays["language"], arrays["at"], arrays["isAt"],
            pred, fold_assign,
        )
        # Aggregate score across folds — each row has gold + pred so a single-pass
        # MR(at) over the union is a sensible CV summary too.
        agg_scores = compute_global_score(
            arrays["at"].tolist(), pred.tolist(),
            ["FALSE"] * n, ["FALSE"] * n,
        )
        summary["models"][name] = {
            "X_shape": list(X.shape),
            "OOF_path": str(out_path),
            "per_fold_MR_at": [s["macro_recall_at"] for s in per_fold],
            "OOF_pooled_MR_at": agg_scores["macro_recall_at"],
        }
        per_fold_mr = [s["macro_recall_at"] for s in per_fold]
        print(f"   OOF pooled MR(at) = {agg_scores['macro_recall_at']:.4f}")
        print(f"   per-fold MR(at) = "
              f"{np.mean(per_fold_mr):.4f} +/- {np.std(per_fold_mr, ddof=1):.4f}")
        print(f"   wrote {out_path}")

    summary_path = log_dir / f"oof_summary_seed{args.seed}_n{args.n_folds}.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote summary to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
