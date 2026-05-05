"""Train the ordinal-contrastive MLP on the FULL labeled set (no val/test split).

For the official-submission flow per ``HIPE2026_Stacked_Approach.md`` §8:
once architecture choices are locked from dev, the final model uses all
1,251 labeled instances for maximum signal — no hold-out validation split.

Modes
-----
- ``--save-model PATH``     save the trained model (state_dict + feature
                             statistics) for later test-set inference.
- ``--test-npz PATH``       additionally extract test predictions in the
                             same call. Optional; pair with ``--out-pred``.

Carves a small stratified val slice (default 10%) ONLY for early stopping
on the contrastive loss; the slice is reused as part of training data after
early stop. Set ``--val-fraction 0`` to disable early stopping and train for
the full ``--epochs`` (deterministic at the cost of mild overfitting risk).

Hyperparameters mirror ``scripts/train_mask_contrastive.py`` (the dev
configuration that produced ``T1.4or5_mask_contrastive_ordinal_m1_at-test``
with MR(at)=0.6723) and ``scripts/run_kfold_contrastive_oof.py`` (the
nested-CV companion).

Colab usage::

    !uv run python scripts/train_contrastive_full.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz \\
        --feature-set concat_t \\
        --val-fraction 0.10 \\
        --save-model models/final/OrdContM1_full.pt \\
        --test-npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_test.npz \\
        --out-pred logs/official_test/OrdContM1_official_test_at_predictions.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

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
    if name == "concat_l_t":
        if "mask_emb_layers" not in cache:
            raise ValueError(
                "concat_l_t requires mask_emb_layers in the npz; "
                "extract with `--layers -1 -4 -7`"
            )
        return np.concatenate(
            [cache["mask_emb_layers"], cache["e1_emb"], cache["e2_emb"], cache["temporal"]],
            axis=1,
        )
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


def _carve_val(at_train: np.ndarray, val_fraction: float, seed: int) -> np.ndarray:
    """Stratified val slice, mirrors scripts/train_mask_contrastive.py."""
    rng = np.random.default_rng(seed)
    val_idx: list[int] = []
    for cls in np.unique(at_train):
        cls_idx = np.where(at_train == cls)[0]
        n_val = max(1, round(len(cls_idx) * val_fraction)) if len(cls_idx) >= 4 else 0
        if n_val == 0:
            continue
        picks = rng.choice(cls_idx, size=n_val, replace=False)
        val_idx.extend(picks.tolist())
    return np.array(sorted(val_idx), dtype=np.int64)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True,
                    help="Cache produced by extract_mask_embeddings.py over the LABELED set.")
    ap.add_argument("--feature-set", default="concat_l_t",
                    choices=["mask", "concat", "concat_t", "concat_l_t"],
                    help="Default matches the dev OrdContM1 winner (MR(at)=0.6723).")
    ap.add_argument("--val-fraction", type=float, default=0.10,
                    help="Stratified val slice for early stopping. Set 0 to disable.")
    ap.add_argument("--seed", type=int, default=42)
    # Trainer hyperparameters — same as test-split + OOF runs.
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--alpha", type=float, default=0.7)
    ap.add_argument("--contrastive-at", choices=["ordinal", "supcon", "none"], default="ordinal")
    ap.add_argument("--contrastive-isAt", choices=["supcon", "none"], default="supcon")
    ap.add_argument("--base-margin", type=float, default=1.0,
                    help="Default 1.0 matches the dev OrdContM1 winner (the trainer's library default is 0.5).")
    ap.add_argument("--temperature", type=float, default=0.07)
    ap.add_argument("--k-per-class", type=int, default=16)
    ap.add_argument("--patience", type=int, default=5)
    ap.add_argument("--hidden-dim", type=int, default=256)
    ap.add_argument("--bottleneck-dim", type=int, default=512)
    ap.add_argument("--projection-dim", type=int, default=128)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--device", default=None)
    # Save / inference outputs.
    ap.add_argument(
        "--save-model", type=Path, default=None,
        help="Path to save the trained model + feature mean/std (a single .pt file).",
    )
    ap.add_argument(
        "--test-npz", type=Path, default=None,
        help="Optional: cache produced by extract_mask_embeddings.py over the "
             "OFFICIAL test set. If set, the script also predicts on those "
             "instances and writes a predictions JSONL.",
    )
    ap.add_argument(
        "--out-pred", type=Path, default=None,
        help="Where to write test-set predictions JSONL when --test-npz is set. "
             "Defaults to logs/official_test/OrdContM1_official_test_at_predictions.jsonl.",
    )
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
    print(f"  n labeled instances = {n}")

    at_all = encode_labels(at_raw, AT_TO_IDX)
    isAt_all = encode_labels(isAt_raw, ISAT_TO_IDX)

    # Optional stratified val slice for early stopping. Note: the val slice
    # is pulled OUT of training before the trainer sees it, so it acts purely
    # as an early-stopping signal — no leakage in this single-shot training
    # run, since there is no test fold against which "leakage" would matter
    # (we predict only on the official UNLABELED test set).
    val_X = val_at = val_isAt = None
    if args.val_fraction > 0:
        val_idx = _carve_val(at_all, args.val_fraction, seed=args.seed)
        if len(val_idx) > 0:
            keep = np.ones(n, dtype=bool)
            keep[val_idx] = False
            val_X = X[~keep]
            val_at = at_all[~keep]
            val_isAt = isAt_all[~keep]
            X_train = X[keep]
            at_train = at_all[keep]
            isAt_train = isAt_all[keep]
            print(f"  carved val slice: {len(val_idx)}; train remainder: {len(at_train)}")
        else:
            X_train, at_train, isAt_train = X, at_all, isAt_all
    else:
        X_train, at_train, isAt_train = X, at_all, isAt_all
        print(f"  --val-fraction 0: training for full {args.epochs} epochs (no early stop)")

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  device = {device}")

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
        seed=args.seed,
        device=device,
    )

    print("\nTraining on full labeled set (no fold, no held-out test) ...")
    t0 = time.perf_counter()
    result = train_contrastive(
        X_train, at_train, isAt_train,
        X_val=val_X, at_val=val_at, isAt_val=val_isAt,
        model_cfg=model_cfg, train_cfg=train_cfg,
    )
    print(f"  trained in {time.perf_counter() - t0:.1f}s; "
          f"best epoch = {result.best_epoch}, best val score = {result.best_val_score:.4f}")

    # --- Optional: save model state_dict + feature stats -------------------
    if args.save_model is not None:
        args.save_model.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "state_dict": result.model.state_dict(),
            "feature_mean": result.feature_mean,
            "feature_std": result.feature_std,
            "model_cfg": {
                "input_dim": model_cfg.input_dim,
                "hidden_dim": model_cfg.hidden_dim,
                "bottleneck_dim": model_cfg.bottleneck_dim,
                "projection_dim": model_cfg.projection_dim,
                "dropout": model_cfg.dropout,
                "n_at_classes": model_cfg.n_at_classes,
                "n_isAt_classes": model_cfg.n_isAt_classes,
            },
            "train_cfg": {
                "feature_set": args.feature_set,
                "alpha": args.alpha,
                "contrastive_at": args.contrastive_at,
                "contrastive_isAt": args.contrastive_isAt,
                "base_margin": args.base_margin,
                "temperature": args.temperature,
                "k_per_class": args.k_per_class,
                "epochs": args.epochs,
                "best_epoch": result.best_epoch,
                "best_val_score": result.best_val_score,
                "seed": args.seed,
            },
        }
        torch.save(payload, args.save_model)
        print(f"  saved model -> {args.save_model}")

    # --- Optional: predict on the official test set ------------------------
    if args.test_npz is not None:
        if not args.test_npz.exists():
            raise SystemExit(f"--test-npz does not exist: {args.test_npz}")
        print(f"\nPredicting on official test set: {args.test_npz}")
        zt = np.load(args.test_npz, allow_pickle=True)
        test_cache = {k: zt[k] for k in zt.files}
        Xt = _build_features(test_cache, args.feature_set).astype(np.float32, copy=False)
        test_sample_ids = test_cache["sample_id"].astype(str)
        test_languages = test_cache["language"].astype(str)
        if Xt.shape[1] != X.shape[1]:
            raise SystemExit(
                f"feature-dim mismatch: train npz has {X.shape[1]}, "
                f"test npz has {Xt.shape[1]} (different --feature-set?)"
            )
        at_pred_idx, isAt_pred_idx, at_proba = predict(
            result.model, Xt,
            feature_mean=result.feature_mean,
            feature_std=result.feature_std,
            device=device,
        )
        out_pred = args.out_pred or (
            PROJECT_ROOT / "logs" / "official_test" /
            "OrdContM1_official_test_at_predictions.jsonl"
        )
        out_pred.parent.mkdir(parents=True, exist_ok=True)
        with out_pred.open("w", encoding="utf-8") as f:
            for sid, lang, ai, ii, prob in zip(
                test_sample_ids, test_languages, at_pred_idx, isAt_pred_idx, at_proba
            ):
                doc, pers, loc = _split_sample_id(sid)
                f.write(json.dumps({
                    "document_id": doc,
                    "pers_entity_id": pers,
                    "loc_entity_id": loc,
                    "language": lang,
                    "at_predicted": AT_LABELS[ai],
                    "isAt_predicted": ISAT_LABELS[ii],
                    "at_proba": [float(p) for p in prob],
                    "at_gold": None,
                    "isAt_gold": None,
                }, ensure_ascii=False) + "\n")
        print(f"  wrote {out_pred} ({len(test_sample_ids)} predictions)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
