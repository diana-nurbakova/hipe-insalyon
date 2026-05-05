"""Stratified 5-fold OOF predictions for the ordinal contrastive MLP (Colab-side).

Run this on Google Colab (with GPU) to produce
``logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl`` — the 4th base model
for the disagreement stacker (see
``specs/HIPE2026_Disagreement_Stacker_Specs.md`` §4.3).

Local CPU is too slow for the contrastive trainer; this script duplicates
the training-loop hyperparameters from
``scripts/train_mask_contrastive.py`` (which produces the test-split
predictions) but wraps them in a ``StratifiedKFold(seed=42, n_splits=5)``
loop that matches ``scripts/run_kfold_per_model_oof.py`` so all four
base-model OOF JSONLs slot together cleanly.

Colab quick-start::

    !git clone https://github.com/<you>/HIPE.git
    %cd HIPE
    !pip install -q uv && uv sync
    # upload runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz
    !uv run python scripts/run_kfold_contrastive_oof.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz
    # download logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.model_selection import StratifiedKFold

from hipe.mask.contrastive import (
    AT_LABELS,
    AT_TO_IDX,
    ISAT_LABELS,
    ISAT_TO_IDX,
    ContrastiveModelConfig,
    TrainConfig,
    encode_labels,
    predict,
    train_contrastive,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_features(cache: dict, name: str) -> np.ndarray:
    if name == "concat_t":
        return np.concatenate(
            [cache["mask_emb"], cache["e1_emb"], cache["e2_emb"], cache["temporal"]],
            axis=1,
        )
    if name == "concat":
        return np.concatenate(
            [cache["mask_emb"], cache["e1_emb"], cache["e2_emb"]], axis=1
        )
    if name == "mask":
        return cache["mask_emb"]
    raise ValueError(f"unsupported feature set: {name}")


def _split_sample_id(sid: str) -> tuple[str, str, str]:
    parts = sid.split(" | ")
    return (
        parts[0] if parts else sid,
        parts[1] if len(parts) > 1 else "",
        parts[2] if len(parts) > 2 else "",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True,
                    help="Cache produced by extract_mask_embeddings.py")
    ap.add_argument("--feature-set", default="concat_t",
                    choices=["mask", "concat", "concat_t"])
    ap.add_argument("--n-folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    # Trainer hyperparameters — match the test-split run that produced
    # T1.4or5_mask_contrastive_ordinal_m1_at-test (MR(at)=0.6723).
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--alpha", type=float, default=0.7,
                    help="CE loss weight (1-alpha is contrastive).")
    ap.add_argument("--contrastive-at", choices=["ordinal", "supcon", "none"], default="ordinal")
    ap.add_argument("--contrastive-isAt", choices=["supcon", "none"], default="supcon")
    ap.add_argument("--base-margin", type=float, default=0.5)
    ap.add_argument("--temperature", type=float, default=0.07)
    ap.add_argument("--k-per-class", type=int, default=16)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--hidden-dim", type=int, default=256)
    ap.add_argument("--bottleneck-dim", type=int, default=512)
    ap.add_argument("--projection-dim", type=int, default=128)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--val-fraction", type=float, default=0.10,
                    help="Stratified val slice carved INSIDE each train fold.")
    ap.add_argument("--device", default=None)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "kfold_oof"), type=Path)
    ap.add_argument("--out-name", default="OrdContM1_at_oof_predictions.jsonl")
    args = ap.parse_args()

    print(f"Loading cache {args.npz}")
    z = np.load(args.npz, allow_pickle=True)
    cache = {k: z[k] for k in z.files}

    X = _build_features(cache, args.feature_set).astype(np.float32, copy=False)
    sample_ids = cache["sample_id"].astype(str)
    languages = cache["language"].astype(str)
    at_raw = cache["at"].astype(str)
    isAt_raw = cache["isAt"].astype(str)
    n = len(X)
    print(f"  X.shape = {X.shape}, feature_set={args.feature_set}")

    # Stratify on at_isAt cross-product to keep PROBABLE balanced across folds.
    strat_keys = np.array([f"{a}_{i}" for a, i in zip(at_raw, isAt_raw)])
    skf = StratifiedKFold(n_splits=args.n_folds, shuffle=True, random_state=args.seed)

    oof_at = np.empty(n, dtype=object)
    oof_fold = np.full(n, -1, dtype=np.int64)

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  device = {device}")

    rng = np.random.default_rng(args.seed)
    for fold_idx, (train_idx, test_idx) in enumerate(
        skf.split(np.arange(n), strat_keys)
    ):
        print(f"\n>>> fold {fold_idx+1}/{args.n_folds} "
              f"train={len(train_idx)} test={len(test_idx)}")
        t0 = time.perf_counter()

        # Stratified val slice carved off train fold (mirrors train_mask_contrastive.py).
        at_train = encode_labels(at_raw[train_idx], AT_TO_IDX)
        isAt_train = encode_labels(isAt_raw[train_idx], ISAT_TO_IDX)
        at_test = encode_labels(at_raw[test_idx], AT_TO_IDX)
        isAt_test = encode_labels(isAt_raw[test_idx], ISAT_TO_IDX)

        val_X = val_at = val_isAt = None
        if args.val_fraction > 0:
            val_picks: list[int] = []
            for cls in np.unique(at_train):
                cls_idx = np.where(at_train == cls)[0]
                k_val = max(1, round(len(cls_idx) * args.val_fraction)) if len(cls_idx) >= 4 else 0
                if k_val > 0:
                    val_picks.extend(rng.choice(cls_idx, size=k_val, replace=False).tolist())
            val_picks = np.array(sorted(val_picks), dtype=np.int64)
            keep = np.ones(len(at_train), dtype=bool)
            keep[val_picks] = False
            val_X = X[train_idx][~keep]
            val_at = at_train[~keep]
            val_isAt = isAt_train[~keep]
            X_train = X[train_idx][keep]
            at_train = at_train[keep]
            isAt_train = isAt_train[keep]
        else:
            X_train = X[train_idx]

        model_cfg = ContrastiveModelConfig(
            input_dim=int(X_train.shape[1]),
            hidden_dim=args.hidden_dim,
            bottleneck_dim=args.bottleneck_dim,
            projection_dim=args.projection_dim,
            dropout=args.dropout,
            n_at_classes=len(AT_LABELS),
            n_isAt_classes=len(ISAT_LABELS),
        )
        train_cfg = TrainConfig(
            epochs=args.epochs,
            lr=args.lr,
            weight_decay=args.weight_decay,
            alpha=args.alpha,
            contrastive_at=args.contrastive_at,
            contrastive_isAt=args.contrastive_isAt,
            base_margin=args.base_margin,
            temperature=args.temperature,
            k_per_class_at=args.k_per_class,
            early_stopping_patience=args.patience,
            seed=args.seed + fold_idx,  # fresh init per fold
            device=device,
        )
        result = train_contrastive(
            X_train, at_train, isAt_train,
            X_val=val_X, at_val=val_at, isAt_val=val_isAt,
            model_cfg=model_cfg, train_cfg=train_cfg,
        )
        # Predict on this fold's test instances. Pass the train-fold's mean/std
        # so the test rows go through the same standardisation the model was
        # trained on (avoids feature-scale mismatch).
        at_pred_idx, _isAt_pred_idx, _at_proba = predict(
            result.model, X[test_idx],
            feature_mean=result.feature_mean,
            feature_std=result.feature_std,
            device=device,
        )
        at_pred = [AT_LABELS[i] for i in at_pred_idx]
        oof_at[test_idx] = at_pred
        oof_fold[test_idx] = fold_idx

        # Per-fold MR(at) sanity check.
        n_per_class = {c: 0 for c in AT_LABELS}
        n_correct = {c: 0 for c in AT_LABELS}
        for ti, p in zip(test_idx, at_pred):
            g = at_raw[ti]
            n_per_class[g] += 1
            if g == p:
                n_correct[g] += 1
        recalls = [n_correct[c] / n_per_class[c] for c in AT_LABELS if n_per_class[c] > 0]
        mr = sum(recalls) / len(recalls)
        print(f"   fold MR(at) = {mr:.4f}   "
              f"recalls = {[(c, n_correct[c], n_per_class[c]) for c in AT_LABELS]}")
        print(f"   elapsed: {time.perf_counter() - t0:.1f}s")

    # Pool MR(at) over OOF.
    n_per_class = {c: 0 for c in AT_LABELS}
    n_correct = {c: 0 for c in AT_LABELS}
    for g, p in zip(at_raw, oof_at):
        n_per_class[g] += 1
        if g == p:
            n_correct[g] += 1
    recalls = [n_correct[c] / n_per_class[c] for c in AT_LABELS if n_per_class[c] > 0]
    pooled_mr = sum(recalls) / len(recalls)

    args.log_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.log_dir / args.out_name
    with out_path.open("w", encoding="utf-8") as f:
        for sid, lang, ag, ig, ap_, fold in zip(
            sample_ids, languages, at_raw, isAt_raw, oof_at, oof_fold
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
    print(f"\n  pooled OOF MR(at) = {pooled_mr:.4f}")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
