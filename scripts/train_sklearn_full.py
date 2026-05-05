"""Train RF + C4 LR on the FULL labeled set; optionally predict on the test set.

Companion to ``scripts/train_contrastive_full.py`` (the GPU contrastive model).
Sklearn-only, no GPU needed; ~1 minute total for both models.

Per ``HIPE2026_Stacked_Approach.md`` §8, the final-submission base models
train on all 1,251 labeled instances (no held-out split). The test
predictions can be produced now (pass ``--test-npz``) or later (just
``--save-models``, then load the .joblib files separately).

Usage::

    # Train + save models only (use later for test prediction)
    uv run python scripts/train_sklearn_full.py \\
        --train-npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7.npz \\
        --save-models models/final/

    # Train + predict on test in one shot
    uv run python scripts/train_sklearn_full.py \\
        --train-npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7.npz \\
        --test-npz runs/mask_test_M2_L-1_-4_-7.npz \\
        --save-models models/final/ \\
        --out-dir logs/official_test
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

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
    return {k: Z[k] for k in Z.files}


def _build_features(arrays: dict[str, np.ndarray], spec) -> np.ndarray:
    if isinstance(spec, str):
        return arrays[spec].astype(np.float32, copy=False)
    return np.concatenate(
        [arrays[k] for k in spec], axis=1
    ).astype(np.float32, copy=False)


def _split_sample_id(sid: str) -> tuple[str, str, str]:
    parts = sid.split(" | ")
    return (
        parts[0] if parts else sid,
        parts[1] if len(parts) > 1 else "",
        parts[2] if len(parts) > 2 else "",
    )


def _train_one(
    name: str,
    X_spec,
    factory,
    train_arrays: dict[str, np.ndarray],
):
    print(f"\n>>> {name}")
    X_train = _build_features(train_arrays, X_spec)
    print(f"   X_train.shape = {X_train.shape}")
    y_at = train_arrays["at"].astype(str)
    t0 = time.perf_counter()
    clf = factory()
    clf.fit(X_train, y_at)
    print(f"   trained on {len(y_at)} instances in {time.perf_counter() - t0:.1f}s")
    print(f"   train class counts: " + ", ".join(
        f"{c}={int((y_at == c).sum())}" for c in ("TRUE", "PROBABLE", "FALSE")
    ))
    return clf, X_train.shape


def _predict_and_write(
    name: str,
    X_spec,
    clf,
    test_arrays: dict[str, np.ndarray],
    out_path: Path,
    train_dim: int,
) -> None:
    X_test = _build_features(test_arrays, X_spec)
    print(f"\n   predicting with {name}: X_test.shape = {X_test.shape}")
    if X_test.shape[1] != train_dim:
        raise SystemExit(
            f"   feature-dim mismatch: train={train_dim} vs test={X_test.shape[1]}; "
            f"check both npz files were extracted with the same --layers config."
        )
    pred = clf.predict(X_test).astype(str)
    sample_ids = test_arrays["sample_id"].astype(str)
    languages = test_arrays["language"].astype(str)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for sid, lang, p in zip(sample_ids, languages, pred):
            doc, pers, loc = _split_sample_id(sid)
            f.write(json.dumps({
                "document_id": doc,
                "pers_entity_id": pers,
                "loc_entity_id": loc,
                "language": lang,
                "at_predicted": p,
                "isAt_predicted": None,
                "at_gold": None,
                "isAt_gold": None,
            }, ensure_ascii=False) + "\n")
    print(f"   wrote {out_path} ({len(pred)} predictions)")
    print(f"   pred class counts: " + ", ".join(
        f"{c}={int((pred == c).sum())}" for c in ("TRUE", "PROBABLE", "FALSE")
    ))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--train-npz", required=True, type=Path,
        help="MASK embeddings cache for the LABELED set (1,251 instances).",
    )
    ap.add_argument(
        "--test-npz", type=Path, default=None,
        help="Optional: cache for the OFFICIAL test set. If set, the script "
             "also predicts on it and writes JSONLs to --out-dir. Must be "
             "extracted with the same --layers config as --train-npz.",
    )
    ap.add_argument(
        "--save-models", type=Path, default=None,
        help="Directory to save the trained classifiers (RF.joblib, C4_LR.joblib). "
             "Loadable later with joblib.load() for separate test inference.",
    )
    ap.add_argument(
        "--out-dir", type=Path,
        default=PROJECT_ROOT / "logs" / "official_test",
        help="Where to write the predictions JSONLs (only used with --test-npz).",
    )
    ap.add_argument("--rf-out-name", default="RF_official_test_at_predictions.jsonl")
    ap.add_argument("--c4-out-name", default="C4_official_test_at_predictions.jsonl")
    args = ap.parse_args()

    print(f"Loading train cache {args.train_npz}")
    train_arrays = _load_arrays(args.train_npz)
    print(f"  train n = {len(train_arrays['sample_id'])}")
    if "at" not in train_arrays:
        raise SystemExit(
            f"  train cache missing 'at' labels — was this built from "
            f"dataset_reference.jsonl?"
        )

    test_arrays = None
    if args.test_npz is not None:
        if not args.test_npz.exists():
            raise SystemExit(f"  --test-npz does not exist: {args.test_npz}")
        print(f"Loading test cache  {args.test_npz}")
        test_arrays = _load_arrays(args.test_npz)
        print(f"  test n = {len(test_arrays['sample_id'])}")

    # --- train both classifiers on the full labeled set --------------------
    rf, rf_shape = _train_one(
        "RF_handcrafted", "handcrafted", make_rf, train_arrays,
    )
    c4, c4_shape = _train_one(
        "C4_mask_e1e2_temp", ("concat", "temporal"), make_lr, train_arrays,
    )

    # --- save trained models if requested ----------------------------------
    if args.save_models is not None:
        args.save_models.mkdir(parents=True, exist_ok=True)
        rf_path = args.save_models / "RF_handcrafted.joblib"
        c4_path = args.save_models / "C4_mask_e1e2_temp.joblib"
        joblib.dump({"clf": rf, "feature_spec": "handcrafted",
                     "input_dim": rf_shape[1]}, rf_path)
        joblib.dump({"clf": c4, "feature_spec": ("concat", "temporal"),
                     "input_dim": c4_shape[1]}, c4_path)
        print(f"\nSaved models:")
        print(f"  {rf_path}")
        print(f"  {c4_path}")

    # --- optional: predict on the test set ---------------------------------
    if test_arrays is not None:
        _predict_and_write(
            "RF_handcrafted", "handcrafted", rf,
            test_arrays, args.out_dir / args.rf_out_name, rf_shape[1],
        )
        _predict_and_write(
            "C4_mask_e1e2_temp", ("concat", "temporal"), c4,
            test_arrays, args.out_dir / args.c4_out_name, c4_shape[1],
        )

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
