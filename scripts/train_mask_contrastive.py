"""Train the MASK + MLP + contrastive head and emit ablation-format artefacts.

Loads a single ``runs/mask_*.npz`` cache, partitions by the official train/test
split (sample_id-based), optionally carves a stratified validation slice off
the training pool, then trains :class:`ContrastiveRelationClassifier` on the
chosen feature combo.

Outputs (under ``--log-dir``):
  ``<exp_id>_predictions.jsonl`` — per-instance pred/gold rows
  ``<exp_id>_report.json``       — official-scorer report + training history

Examples:
    # Joint head, ordinal contrastive on `at` + SupCon on `isAt`
    uv run python scripts/train_mask_contrastive.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz

    # CE-only baseline on the same features (ablation: contrastive contribution)
    uv run python scripts/train_mask_contrastive.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz \\
        --contrastive-at none --contrastive-isAt none --alpha 1.0

    # Multi-layer MASK + entity + temporal features
    uv run python scripts/train_mask_contrastive.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L_1__4__7.npz \\
        --feature-set concat_l_t
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import time
from pathlib import Path

import numpy as np

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.report import generate_evaluation_report
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


# Available feature combos. Mirrors mask_grid_eval.FEATURE_SETS conceptually
# but inlined so we can keep the scripts independent.
def build_features(z: dict, name: str) -> np.ndarray | None:
    if name == "mask":
        return z["mask_emb"]
    if name == "mask_layers":
        return z.get("mask_emb_layers")
    if name == "concat":
        return np.concatenate([z["mask_emb"], z["e1_emb"], z["e2_emb"]], axis=1)
    if name == "concat_t":
        return np.concatenate(
            [z["mask_emb"], z["e1_emb"], z["e2_emb"], z["temporal"]], axis=1
        )
    if name == "concat_l_t":
        if "mask_emb_layers" not in z:
            return None
        return np.concatenate(
            [z["mask_emb_layers"], z["e1_emb"], z["e2_emb"], z["temporal"]], axis=1
        )
    if name == "mask_at":
        return z.get("mask_at_emb")
    if name == "mask_isAt":
        return z.get("mask_isAt_emb")
    if name == "mask_multi":
        return z.get("mask_multi_emb")
    raise ValueError(f"Unknown feature set: {name!r}")


def _split_by_sample_ids(
    arrays: dict[str, np.ndarray],
    sample_ids: np.ndarray,
    train_ids: set[str],
    test_ids: set[str],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], list[str], list[str]]:
    train_mask = np.array([sid in train_ids for sid in sample_ids], dtype=bool)
    test_mask = np.array([sid in test_ids for sid in sample_ids], dtype=bool)
    train_a = {k: v[train_mask] for k, v in arrays.items()}
    test_a = {k: v[test_mask] for k, v in arrays.items()}
    return (
        train_a,
        test_a,
        [str(s) for s in sample_ids[train_mask]],
        [str(s) for s in sample_ids[test_mask]],
    )


def _carve_val(at_train: np.ndarray, val_fraction: float, seed: int) -> np.ndarray:
    """Stratified validation indices on the training set, by `at` class."""
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
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--npz", required=True, help="Cache produced by extract_mask_embeddings.py")
    ap.add_argument("--task", choices=["at", "isAt"], default="at")
    ap.add_argument(
        "--feature-set",
        default="concat_t",
        choices=["mask", "mask_layers", "concat", "concat_t", "concat_l_t",
                 "mask_at", "mask_isAt", "mask_multi"],
    )
    ap.add_argument("--val-fraction", type=float, default=0.10,
                    help="Stratified validation slice carved off the training set "
                         "(0 disables early stopping).")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--alpha", type=float, default=0.7,
                    help="CE loss weight (1-alpha is contrastive).")
    ap.add_argument("--contrastive-at", choices=["ordinal", "supcon", "none"], default="ordinal")
    ap.add_argument("--contrastive-isAt", choices=["supcon", "none"], default="supcon")
    ap.add_argument("--base-margin", type=float, default=0.5,
                    help="Margin scalar for OrdinalContrastiveLoss.")
    ap.add_argument("--temperature", type=float, default=0.07,
                    help="SupConLoss temperature.")
    ap.add_argument("--k-per-class", type=int, default=16,
                    help="Examples per `at` class per batch (batch_size = k * 3).")
    ap.add_argument("--patience", type=int, default=5,
                    help="Early-stopping patience on val global score.")
    ap.add_argument("--hidden-dim", type=int, default=256)
    ap.add_argument("--bottleneck-dim", type=int, default=512)
    ap.add_argument("--projection-dim", type=int, default=128)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    ap.add_argument("--experiment-id", default=None)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    args = ap.parse_args()

    npz_path = Path(args.npz)
    print(f"Loading cache {npz_path}")
    z = np.load(npz_path, allow_pickle=True)
    cache = {k: z[k] for k in z.files}

    # Resolve features.
    X = build_features(cache, args.feature_set)
    if X is None:
        raise SystemExit(
            f"Cache {npz_path.name} does not support feature set "
            f"{args.feature_set!r} (missing required arrays)."
        )
    X = X.astype(np.float32, copy=False)
    sample_ids = cache["sample_id"].astype(str)
    languages = cache["language"].astype(str)
    at_labels_raw = cache["at"].astype(str)
    isAt_labels_raw = cache["isAt"].astype(str)

    print(f"  X shape           : {X.shape}")
    print(f"  feature set       : {args.feature_set}")
    print(f"  template / model  : {cache.get('_meta_template', '?')!s} / "
          f"{cache.get('_meta_model', '?')!s}")

    # Split.
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    train_ids = {inst.sample_id for inst in sp.train}
    test_ids = {inst.sample_id for inst in sp.test}
    arrays = {
        "X": X,
        "at": at_labels_raw,
        "isAt": isAt_labels_raw,
        "language": languages,
    }
    train_a, test_a, train_sids, test_sids = _split_by_sample_ids(
        arrays, sample_ids, train_ids, test_ids
    )
    print(f"  train (matched)   : {len(train_sids)}")
    print(f"  test  (matched)   : {len(test_sids)}")

    at_train = encode_labels(train_a["at"], AT_TO_IDX)
    isAt_train = encode_labels(train_a["isAt"], ISAT_TO_IDX)
    at_test = encode_labels(test_a["at"], AT_TO_IDX)
    isAt_test = encode_labels(test_a["isAt"], ISAT_TO_IDX)

    # Optional stratified validation split.
    val_X = val_at = val_isAt = None
    if args.val_fraction > 0:
        val_idx = _carve_val(at_train, args.val_fraction, seed=args.seed)
        if len(val_idx) > 0:
            keep_mask = np.ones(len(at_train), dtype=bool)
            keep_mask[val_idx] = False
            val_X = train_a["X"][~keep_mask]
            val_at = at_train[~keep_mask]
            val_isAt = isAt_train[~keep_mask]
            train_a["X"] = train_a["X"][keep_mask]
            at_train = at_train[keep_mask]
            isAt_train = isAt_train[keep_mask]
            print(f"  val carved        : {len(val_idx)}")
            print(f"  train (after val) : {len(at_train)}")

    # Model + train.
    model_cfg = ContrastiveModelConfig(
        input_dim=int(train_a["X"].shape[1]),
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
        device=args.device,
    )

    print(
        f"\nTraining: epochs={train_cfg.epochs} alpha={train_cfg.alpha} "
        f"contrastive(at)={train_cfg.contrastive_at} "
        f"contrastive(isAt)={train_cfg.contrastive_isAt} "
        f"k_per_class={train_cfg.k_per_class_at}"
    )
    t0 = time.perf_counter()
    result = train_contrastive(
        train_a["X"],
        at_train,
        isAt_train,
        X_val=val_X,
        at_val=val_at,
        isAt_val=val_isAt,
        model_cfg=model_cfg,
        train_cfg=train_cfg,
    )
    train_seconds = time.perf_counter() - t0
    print(f"\nTrained in {train_seconds:.1f}s; best epoch={result.best_epoch} "
          f"val_global={result.best_val_score:.4f}")

    # Predict on test.
    at_pred, isAt_pred, at_proba = predict(
        result.model,
        test_a["X"],
        feature_mean=result.feature_mean,
        feature_std=result.feature_std,
    )

    # Decode and persist predictions.
    at_pred_str = [AT_LABELS[i] for i in at_pred]
    isAt_pred_str = [ISAT_LABELS[i] for i in isAt_pred]

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    if args.experiment_id:
        exp_id = args.experiment_id
    else:
        tags = ["T1.4or5_mask_contrastive", npz_path.stem,
                args.feature_set, f"a{int(args.alpha*100):03d}"]
        if args.contrastive_at != "none":
            tags.append(f"at-{args.contrastive_at}")
        if args.contrastive_isAt != "none":
            tags.append(f"isAt-{args.contrastive_isAt}")
        exp_id = "_".join(tags) + f"_{args.task}-test"
    print(f"Experiment id: {exp_id}")

    pred_path = log_dir / f"{exp_id}_predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as f:
        for sid, lang, gold_at, gold_isAt, p_at, p_isAt in zip(
            test_sids, test_a["language"], test_a["at"], test_a["isAt"],
            at_pred_str, isAt_pred_str,
        ):
            parts = sid.split(" | ")
            doc_id = parts[0] if parts else sid
            pers_id = parts[1] if len(parts) > 1 else ""
            loc_id = parts[2] if len(parts) > 2 else ""
            row = {
                "document_id": doc_id,
                "pers_entity_id": pers_id,
                "loc_entity_id": loc_id,
                "language": lang,
                "at_predicted": p_at,
                "isAt_predicted": p_isAt,
                "at_gold": gold_at,
                "isAt_gold": gold_isAt,
            }
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    metadata = {
        "experiment_id": exp_id,
        "feature_set": args.feature_set,
        "input_dim": int(train_a["X"].shape[1]),
        "n_train": int(len(at_train)),
        "n_val": int(0 if val_at is None else len(val_at)),
        "n_test": int(len(at_test)),
        "best_epoch": result.best_epoch,
        "best_val_global": result.best_val_score,
        "train_seconds": train_seconds,
        "history": result.history,
        "cache": str(npz_path),
        "model_meta": {
            "model": str(cache.get("_meta_model", "")),
            "template": str(cache.get("_meta_template", "")),
            "field": str(cache.get("_meta_field", "")),
            "layers": cache.get("_meta_layers", np.asarray([-1])).tolist(),
        },
        # ContrastiveModelConfig / TrainConfig use slots=True, so vars() doesn't
        # work; asdict() walks the dataclass fields and serialises cleanly.
        "model_config": dataclasses.asdict(model_cfg),
        "train_config": dataclasses.asdict(train_cfg),
    }
    report = generate_evaluation_report(
        exp_id,
        list(test_a["at"]), at_pred_str,
        list(test_a["isAt"]), isAt_pred_str,
        metadata=metadata,
        print_summary=True,
    )
    (log_dir / f"{exp_id}_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )

    print(f"\nGlobalScore: {report['scores']['global_score']:.4f}")
    print(f"Wrote {pred_path}")
    print(f"Wrote {log_dir / f'{exp_id}_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
