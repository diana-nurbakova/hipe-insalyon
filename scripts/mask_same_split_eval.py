"""Train MASK / handcrafted classifiers on at-train, evaluate on at-test.

The Phase 0 diagnostics scored MASK and handcrafted-RF baselines via
5-fold stratified CV on the full 1,251-instance dataset. The LLM zero-shot
results, on the other hand, were scored on the 188-instance at-task test
split. This script makes the comparison apples-to-apples by training on
the at-task train rows (1,063) and scoring the same 188 test rows the
LLMs saw.

Reuses the cached embeddings produced by
``scripts/extract_mask_embeddings.py`` so no GPU work is repeated.

Usage:
    uv run python scripts/mask_same_split_eval.py
    uv run python scripts/mask_same_split_eval.py \
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz \
        --task at
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.experiment import generate_evaluation_report

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_lr_pipeline():
    return make_pipeline(
        StandardScaler(with_mean=True),
        LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
        ),
    )


def make_rf():
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


def split_by_sample_ids(
    arrays: dict[str, np.ndarray],
    sample_ids: np.ndarray,
    train_ids: set[str],
    test_ids: set[str],
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], list[str], list[str]]:
    """Partition every array in ``arrays`` along axis 0 by sample_id membership.

    Returns (train_arrays, test_arrays, train_sample_ids, test_sample_ids).
    """
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


def feature_concat(*arrays: np.ndarray) -> np.ndarray:
    return np.concatenate(arrays, axis=1).astype(np.float32, copy=False)


def run_experiment(
    name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    estimator_factory,
) -> tuple[np.ndarray, dict]:
    clf = estimator_factory()
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    info = {"name": name, "n_train": len(X_train), "n_test": len(X_test), "input_dim": int(X_train.shape[1])}
    return pred.astype(str), info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--npz", default=str(
        PROJECT_ROOT / "runs" / "mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz"
    ))
    ap.add_argument("--task", choices=["at", "isAt"], default="at",
                    help="Which baseline split to use as the holdout.")
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    args = ap.parse_args()

    # 1. Load instances + baseline split → train/test sample_id sets.
    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    train_ids = {inst.sample_id for inst in sp.train}
    test_ids = {inst.sample_id for inst in sp.test}
    print(f"  task={args.task}: train={len(train_ids)}  test={len(test_ids)}")

    # 2. Load cached MASK + temporal + handcrafted arrays.
    print(f"Loading cached embeddings {args.npz}")
    Z = np.load(args.npz, allow_pickle=True)
    sample_ids = Z["sample_id"].astype(str)
    arrays = {
        "mask": Z["mask_emb"].astype(np.float32),
        "concat": Z["concat_emb"].astype(np.float32),
        "temporal": Z["temporal"].astype(np.float32),
        "handcrafted": Z["handcrafted"].astype(np.float32),
        "at": Z["at"].astype(str),
        "isAt": Z["isAt"].astype(str),
        "language": Z["language"].astype(str),
    }
    print(f"  cache size: {len(sample_ids)}")

    # 3. Partition arrays by sample_id.
    train_a, test_a, train_sids, test_sids = split_by_sample_ids(
        arrays, sample_ids, train_ids, test_ids
    )
    n_train = len(train_sids)
    n_test = len(test_sids)
    print(f"  matched train={n_train} / test={n_test}")
    if n_train == 0 or n_test == 0:
        raise SystemExit("Empty train or test partition — check that the npz "
                         "and split CSV reference the same sample_ids.")

    # Feature combinations to evaluate. Names mirror Phase 0 diagnostics.
    concat_temporal_train = feature_concat(train_a["concat"], train_a["temporal"])
    concat_temporal_test = feature_concat(test_a["concat"], test_a["temporal"])

    feature_sets = {
        "C1_mask_LR": (train_a["mask"], test_a["mask"], make_lr_pipeline),
        "C4_mask+e1+e2+temporal_LR": (concat_temporal_train, concat_temporal_test, make_lr_pipeline),
        "T1.4_temporal_only_LR": (train_a["temporal"], test_a["temporal"], make_lr_pipeline),
        "T1.5_handcrafted_RF": (train_a["handcrafted"], test_a["handcrafted"], make_rf),
    }

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []
    for name, (Xtr, Xte, factory) in feature_sets.items():
        for target in ("at", "isAt"):
            ytr = train_a[target]
            yte = test_a[target]
            print(f"\n>>> {name}  target={target}  X_train={Xtr.shape}")
            pred, info = run_experiment(name, Xtr, ytr, Xte, factory)
            # Persist a predictions JSONL in the same shape the LLM runner uses.
            exp_id = f"T1.4or5_mask_{name}_{target}_{args.task}-test"
            pred_path = log_dir / f"{exp_id}_predictions.jsonl"
            with pred_path.open("w", encoding="utf-8") as f:
                for sid, lang, gold, p in zip(test_sids, test_a["language"], yte, pred):
                    # Map sample_id back to (document_id, pers, loc) via the
                    # canonical "<doc> | <pers> | <loc>" format.
                    parts = sid.split(" | ")
                    document_id = parts[0] if parts else sid
                    pers_id = parts[1] if len(parts) > 1 else ""
                    loc_id = parts[2] if len(parts) > 2 else ""
                    f.write(json.dumps({
                        "document_id": document_id,
                        "pers_entity_id": pers_id,
                        "loc_entity_id": loc_id,
                        "language": lang,
                        "at_predicted": p if target == "at" else None,
                        "isAt_predicted": p if target == "isAt" else None,
                        "at_gold": gold if target == "at" else None,
                        "isAt_gold": gold if target == "isAt" else None,
                    }, ensure_ascii=False, default=str) + "\n")

            # Score via the same evaluator as the LLM runs. We need the
            # OTHER-target gold/pred too — fall back to FALSE for the
            # non-target so the report's macro-recall on the target is
            # still computed correctly.
            other = "isAt" if target == "at" else "at"
            other_gold = test_a[other].tolist()
            other_pred = ["FALSE"] * len(test_sids)  # placeholder; not the focus

            if target == "at":
                report = generate_evaluation_report(
                    exp_id,
                    yte.tolist(), pred.tolist(),
                    other_gold, other_pred,
                    metadata={**info, "target": target, "task": args.task},
                    print_summary=False,
                )
            else:
                report = generate_evaluation_report(
                    exp_id,
                    other_gold, other_pred,
                    yte.tolist(), pred.tolist(),
                    metadata={**info, "target": target, "task": args.task},
                    print_summary=False,
                )
            (log_dir / f"{exp_id}_report.json").write_text(
                json.dumps(report, indent=2, default=str), encoding="utf-8"
            )
            summary.append({
                "feature_set": name,
                "target": target,
                "macro_recall": (
                    report["scores"]["macro_recall_at"]
                    if target == "at"
                    else report["scores"]["macro_recall_isAt"]
                ),
                "input_dim": info["input_dim"],
            })

    # Pretty-print summary
    print("\n" + "=" * 80)
    print(f"Same-split eval (task={args.task}, n_test={n_test}) — macro-recall on target")
    print("=" * 80)
    print(f"{'feature_set':<32s} {'at':>10s} {'isAt':>10s} {'mean':>10s} {'dim':>8s}")
    by_set: dict[str, dict[str, float]] = {}
    for row in summary:
        by_set.setdefault(row["feature_set"], {})[row["target"]] = row["macro_recall"]
        by_set[row["feature_set"]]["dim"] = row["input_dim"]
    for name, scores in by_set.items():
        at_s = scores.get("at", float("nan"))
        is_s = scores.get("isAt", float("nan"))
        mean = (at_s + is_s) / 2 if at_s == at_s and is_s == is_s else float("nan")
        print(f"{name:<32s} {at_s:>10.4f} {is_s:>10.4f} {mean:>10.4f} {int(scores.get('dim', 0)):>8d}")

    # Persist summary.
    summary_path = log_dir / f"mask_same_split_summary_{args.task}-test.json"
    summary_path.write_text(json.dumps({
        "task": args.task,
        "n_train": n_train,
        "n_test": n_test,
        "by_feature_set": by_set,
        "rows": summary,
    }, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote summary to {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
