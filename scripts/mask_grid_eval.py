"""Evaluate every MASK extraction cache and emit ablation-format artefacts.

For each ``runs/mask_*.npz`` cache, this script:
  1. Reads the cache and the official train/test split (sample_id-based).
  2. For each feature combo in ``--feature-sets``, trains an LR (or RF for
     handcrafted-only) on at-train and predicts on at-test.
  3. Writes ``logs/ablations/<exp_id>_predictions.jsonl`` and
     ``<exp_id>_report.json`` so the runs slot directly into the existing
     ``aggregate_results.py`` / ``disagreement_analysis.py`` pipelines.
  4. Aggregates a comparison table (CSV + JSON) under ``--summary-dir``.

Default feature sets (see Spec §6.1, classifiers C1–C4):
    mask        : mask_emb only                    (last layer, H-d)
    mask_layers : mask_emb_layers                  (multi-layer concat, L*H)
    concat      : mask + e1 + e2                   (3*H)
    concat_t    : mask + e1 + e2 + temporal        (3*H + 15)
    concat_l_t  : mask_layers + e1 + e2 + temporal (L*H + 2*H + 15)

Extra template-specific cells:
    mask_at     : the M4 dual-mask "at" slot       (H-d)  — only on M4 caches
    mask_isAt   : the M4 dual-mask "isAt" slot     (H-d)  — only on M4 caches
    mask_multi  : the M5 three-mask concat         (3*H)  — only on M5 caches

Usage:
    uv run python scripts/mask_grid_eval.py
    uv run python scripts/mask_grid_eval.py --task isAt
    uv run python scripts/mask_grid_eval.py --feature-sets mask concat_t \\
        --include-spectral
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.report import generate_evaluation_report

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Estimator factories
# ---------------------------------------------------------------------------


def make_lr_pipeline():
    return make_pipeline(
        StandardScaler(with_mean=True),
        LogisticRegression(max_iter=2000, class_weight="balanced", solver="lbfgs"),
    )


def make_rf():
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


# ---------------------------------------------------------------------------
# Feature assembly
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FeatureSpec:
    name: str
    builder: Callable[[dict[str, np.ndarray]], np.ndarray | None]
    estimator_factory: Callable[[], Any] = make_lr_pipeline
    requires: tuple[str, ...] = ()  # required cache keys


def _safe_concat(parts: list[np.ndarray]) -> np.ndarray:
    return np.concatenate(parts, axis=1).astype(np.float32, copy=False)


def _b_mask(z: dict) -> np.ndarray:
    return z["mask_emb"].astype(np.float32, copy=False)


def _b_mask_layers(z: dict) -> np.ndarray | None:
    if "mask_emb_layers" not in z:
        return None
    arr = z["mask_emb_layers"].astype(np.float32, copy=False)
    return arr if arr.shape[1] > z["mask_emb"].shape[1] else None  # else identical to mask


def _b_concat(z: dict) -> np.ndarray:
    return _safe_concat([z["mask_emb"], z["e1_emb"], z["e2_emb"]])


def _b_concat_t(z: dict) -> np.ndarray:
    return _safe_concat([z["mask_emb"], z["e1_emb"], z["e2_emb"], z["temporal"]])


def _b_concat_l_t(z: dict) -> np.ndarray | None:
    if "mask_emb_layers" not in z:
        return None
    arr = z["mask_emb_layers"].astype(np.float32, copy=False)
    if arr.shape[1] == z["mask_emb"].shape[1]:
        return None  # would just duplicate concat_t
    return _safe_concat([arr, z["e1_emb"], z["e2_emb"], z["temporal"]])


def _b_mask_at(z: dict) -> np.ndarray | None:
    return z["mask_at_emb"].astype(np.float32, copy=False) if "mask_at_emb" in z else None


def _b_mask_isAt(z: dict) -> np.ndarray | None:
    return z["mask_isAt_emb"].astype(np.float32, copy=False) if "mask_isAt_emb" in z else None


def _b_mask_multi(z: dict) -> np.ndarray | None:
    return z["mask_multi_emb"].astype(np.float32, copy=False) if "mask_multi_emb" in z else None


def _b_handcrafted(z: dict) -> np.ndarray:
    return z["handcrafted"].astype(np.float32, copy=False)


def _b_spectral(z: dict) -> np.ndarray | None:
    return z["spectral"].astype(np.float32, copy=False) if "spectral" in z else None


def _b_concat_spectral(z: dict) -> np.ndarray | None:
    if "spectral" not in z:
        return None
    return _safe_concat([z["mask_emb"], z["e1_emb"], z["e2_emb"], z["temporal"], z["spectral"]])


FEATURE_SETS: dict[str, FeatureSpec] = {
    "mask":        FeatureSpec("mask", _b_mask),
    "mask_layers": FeatureSpec("mask_layers", _b_mask_layers),
    "concat":      FeatureSpec("concat", _b_concat),
    "concat_t":    FeatureSpec("concat_t", _b_concat_t),
    "concat_l_t":  FeatureSpec("concat_l_t", _b_concat_l_t),
    "mask_at":     FeatureSpec("mask_at", _b_mask_at),
    "mask_isAt":   FeatureSpec("mask_isAt", _b_mask_isAt),
    "mask_multi":  FeatureSpec("mask_multi", _b_mask_multi),
    "handcrafted": FeatureSpec("handcrafted", _b_handcrafted, estimator_factory=make_rf),
    "spectral":    FeatureSpec("spectral", _b_spectral),
    "concat_spec": FeatureSpec("concat_spec", _b_concat_spectral),
}


# ---------------------------------------------------------------------------
# Cache discovery + loading
# ---------------------------------------------------------------------------


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


def _load_cache(npz_path: Path) -> dict[str, np.ndarray]:
    z = np.load(npz_path, allow_pickle=True)
    return {k: z[k] for k in z.files}


def _exp_id_for(npz_stem: str, feature_set: str, target: str, task: str) -> str:
    # Match the existing T1.4or5_mask_* naming convention so disagreement
    # analysis groups them with the legacy MASK runs.
    return f"T1.4or5_mask_grid_{npz_stem}_{feature_set}_{target}_{task}-test"


def _persist_predictions(
    log_dir: Path,
    exp_id: str,
    test_sids: list[str],
    languages: np.ndarray,
    target: str,
    gold: np.ndarray,
    pred: np.ndarray,
    other_gold: np.ndarray,
) -> None:
    pred_path = log_dir / f"{exp_id}_predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as f:
        for sid, lang, g, p, og in zip(test_sids, languages, gold, pred, other_gold):
            parts = sid.split(" | ")
            doc_id = parts[0] if parts else sid
            pers_id = parts[1] if len(parts) > 1 else ""
            loc_id = parts[2] if len(parts) > 2 else ""
            row = {
                "document_id": doc_id,
                "pers_entity_id": pers_id,
                "loc_entity_id": loc_id,
                "language": lang,
                "at_predicted": p if target == "at" else None,
                "isAt_predicted": p if target == "isAt" else None,
                "at_gold": g if target == "at" else og,
                "isAt_gold": g if target == "isAt" else og,
            }
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _eval_cell(
    log_dir: Path,
    exp_id: str,
    target: str,
    Xtr: np.ndarray,
    ytr: np.ndarray,
    Xte: np.ndarray,
    yte: np.ndarray,
    other_gold: np.ndarray,
    test_sids: list[str],
    languages: np.ndarray,
    estimator_factory: Callable[[], Any],
    extra_meta: dict[str, Any],
) -> dict[str, Any]:
    clf = estimator_factory()
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte).astype(str)

    _persist_predictions(
        log_dir, exp_id, test_sids, languages, target, yte, pred, other_gold
    )

    other_pred = ["FALSE"] * len(test_sids)
    if target == "at":
        report = generate_evaluation_report(
            exp_id,
            yte.tolist(), pred.tolist(),
            other_gold.tolist(), other_pred,
            metadata={**extra_meta, "target": target},
            print_summary=False,
        )
    else:
        report = generate_evaluation_report(
            exp_id,
            other_gold.tolist(), other_pred,
            yte.tolist(), pred.tolist(),
            metadata={**extra_meta, "target": target},
            print_summary=False,
        )
    (log_dir / f"{exp_id}_report.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--runs-dir", default=str(PROJECT_ROOT / "runs"))
    ap.add_argument("--task", choices=["at", "isAt"], default="at",
                    help="Holdout split to use (sample_id partition is identical "
                         "across tasks but the CSV has separate task rows).")
    ap.add_argument("--targets", nargs="+", default=["at", "isAt"],
                    help="Which target labels to train classifiers for.")
    ap.add_argument(
        "--feature-sets",
        nargs="+",
        default=["mask", "mask_layers", "concat_t", "concat_l_t",
                 "mask_at", "mask_isAt", "mask_multi"],
        help="Feature combinations to evaluate per cache.",
    )
    ap.add_argument("--include-handcrafted", action="store_true",
                    help="Also evaluate the handcrafted RF baseline once "
                         "(uses the first cache's handcrafted matrix).")
    ap.add_argument("--include-spectral", action="store_true",
                    help="Include the 'spectral' / 'concat_spec' cells "
                         "(requires caches augmented by extract_spectral_features.py).")
    ap.add_argument("--glob", default="mask_*.npz",
                    help="Glob pattern under runs-dir for cache discovery.")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="Skip caches whose stem matches any of these substrings.")
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    ap.add_argument("--summary-dir", default=str(PROJECT_ROOT / "runs" / "mask_grid_eval"))
    args = ap.parse_args()

    if args.include_spectral:
        for fs in ("spectral", "concat_spec"):
            if fs not in args.feature_sets:
                args.feature_sets.append(fs)

    # 1. Discover caches.
    runs_dir = Path(args.runs_dir)
    caches = sorted(runs_dir.glob(args.glob))
    caches = [p for p in caches if not any(ex in p.stem for ex in args.exclude)]
    if not caches:
        print(f"No caches found under {runs_dir} matching {args.glob!r}")
        return 1
    print(f"Discovered {len(caches)} caches:")
    for p in caches:
        print(f"  {p.name}  ({p.stat().st_size / 1e6:.1f} MB)")

    # 2. Resolve the train/test split once.
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    train_ids = {inst.sample_id for inst in sp.train}
    test_ids = {inst.sample_id for inst in sp.test}
    print(f"Split (task={args.task}): train={len(train_ids)} test={len(test_ids)}")

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    summary_dir = Path(args.summary_dir)
    summary_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    handcrafted_done = False

    t_start = time.perf_counter()
    for cache_path in caches:
        z = _load_cache(cache_path)
        sample_ids = z["sample_id"].astype(str)
        cache_meta = {
            "cache": cache_path.name,
            "model": str(z.get("_meta_model", "")),
            "template": str(z.get("_meta_template", "")),
            "field": str(z.get("_meta_field", "")),
            "layers": z.get("_meta_layers", np.asarray([-1])).tolist(),
        }

        # Common arrays
        all_arrays = {
            "at": z["at"].astype(str),
            "isAt": z["isAt"].astype(str),
            "language": z["language"].astype(str),
            "temporal": z["temporal"].astype(np.float32),
            "handcrafted": z["handcrafted"].astype(np.float32),
            "mask_emb": z["mask_emb"].astype(np.float32),
            "e1_emb": z["e1_emb"].astype(np.float32),
            "e2_emb": z["e2_emb"].astype(np.float32),
        }
        for opt in ("mask_emb_layers", "mask_at_emb", "mask_isAt_emb",
                    "mask_multi_emb", "spectral"):
            if opt in z:
                all_arrays[opt] = z[opt].astype(np.float32)

        train_a, test_a, train_sids, test_sids = _split_by_sample_ids(
            all_arrays, sample_ids, train_ids, test_ids
        )
        if not train_sids or not test_sids:
            print(f"  [skip] {cache_path.name}: empty train/test partition")
            continue
        n_train, n_test = len(train_sids), len(test_sids)

        for fs_name in args.feature_sets:
            spec = FEATURE_SETS.get(fs_name)
            if spec is None:
                print(f"  [warn] unknown feature set {fs_name!r}")
                continue
            Xtr = spec.builder(train_a)
            Xte = spec.builder(test_a)
            if Xtr is None or Xte is None:
                continue  # cache lacks the prerequisites for this combo (e.g. M4-only slot)

            for target in args.targets:
                ytr = train_a[target]
                yte = test_a[target]
                exp_id = _exp_id_for(cache_path.stem, spec.name, target, args.task)
                print(
                    f"\n{cache_path.stem}  fs={spec.name:11s}  target={target:5s}  "
                    f"X_train={Xtr.shape}"
                )
                t0 = time.perf_counter()
                report = _eval_cell(
                    log_dir,
                    exp_id,
                    target,
                    Xtr, ytr, Xte, yte,
                    test_a["isAt"] if target == "at" else test_a["at"],
                    test_sids,
                    test_a["language"],
                    spec.estimator_factory,
                    extra_meta={
                        **cache_meta,
                        "feature_set": spec.name,
                        "n_train": n_train,
                        "n_test": n_test,
                        "input_dim": int(Xtr.shape[1]),
                    },
                )
                fit_seconds = time.perf_counter() - t0
                row = {
                    "experiment_id": exp_id,
                    "cache": cache_path.name,
                    "model": cache_meta["model"],
                    "template": cache_meta["template"],
                    "feature_set": spec.name,
                    "target": target,
                    "input_dim": int(Xtr.shape[1]),
                    "global_score": report["scores"]["global_score"],
                    "macro_recall_at": report["scores"]["macro_recall_at"],
                    "macro_recall_isAt": report["scores"]["macro_recall_isAt"],
                    "fit_seconds": fit_seconds,
                }
                summary_rows.append(row)
                print(
                    f"    -> global={row['global_score']:.4f}  "
                    f"MR(at)={row['macro_recall_at']:.4f}  "
                    f"MR(isAt)={row['macro_recall_isAt']:.4f}  "
                    f"fit={fit_seconds:.1f}s"
                )

        # One-shot handcrafted RF baseline (independent of the encoder cache).
        if args.include_handcrafted and not handcrafted_done:
            handcrafted_done = True
            for target in args.targets:
                exp_id = _exp_id_for("handcrafted", "rf", target, args.task)
                ytr = train_a[target]
                yte = test_a[target]
                Xtr = train_a["handcrafted"]
                Xte = test_a["handcrafted"]
                report = _eval_cell(
                    log_dir, exp_id, target,
                    Xtr, ytr, Xte, yte,
                    test_a["isAt"] if target == "at" else test_a["at"],
                    test_sids, test_a["language"],
                    make_rf,
                    extra_meta={"feature_set": "handcrafted", "target": target,
                                "n_train": n_train, "n_test": n_test,
                                "input_dim": int(Xtr.shape[1])},
                )
                summary_rows.append({
                    "experiment_id": exp_id,
                    "cache": "(none)",
                    "model": "handcrafted-features",
                    "template": "—",
                    "feature_set": "handcrafted",
                    "target": target,
                    "input_dim": int(Xtr.shape[1]),
                    "global_score": report["scores"]["global_score"],
                    "macro_recall_at": report["scores"]["macro_recall_at"],
                    "macro_recall_isAt": report["scores"]["macro_recall_isAt"],
                    "fit_seconds": 0.0,
                })

    # 3. Write the aggregate table.
    summary_rows.sort(key=lambda r: (-r["global_score"], r["model"], r["template"]))
    csv_path = summary_dir / "summary.csv"
    json_path = summary_dir / "summary.json"
    if summary_rows:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
    json_path.write_text(
        json.dumps(
            {
                "task": args.task,
                "n_caches": len(caches),
                "n_cells": len(summary_rows),
                "feature_sets": args.feature_sets,
                "elapsed_seconds": time.perf_counter() - t_start,
                "rows": summary_rows,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 78)
    print(f"Top 15 cells by GlobalScore (task={args.task})")
    print("=" * 78)
    print(f"{'experiment_id':<60s} {'global':>8s} {'MR(at)':>8s} {'MR(isAt)':>9s}")
    for row in summary_rows[:15]:
        print(
            f"{row['experiment_id'][:60]:<60s} "
            f"{row['global_score']:>8.4f} "
            f"{row['macro_recall_at']:>8.4f} "
            f"{row['macro_recall_isAt']:>9.4f}"
        )
    print(f"\nCSV : {csv_path}")
    print(f"JSON: {json_path}")
    print(f"Per-cell predictions/reports under: {log_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
