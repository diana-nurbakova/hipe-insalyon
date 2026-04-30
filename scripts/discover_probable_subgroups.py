"""End-to-end MCMC-COTP subgroup discovery for the PROBABLE class.

Implements HIPE2026_Subgroup_Discovery_Specs v2 §3-§7. Builds the SD feature
matrix from ``data/dataset_reference.jsonl`` (with optional MASK embedding
cache for spectral / PCA blocks), runs MCMC subgroup discovery for ``--target``
(default ``PROBABLE``), and writes:

  - ``runs/sd/<run_id>/subgroups_<TARGET>.json``  summary of the top-k patterns
  - ``runs/sd/<run_id>/subgroups_<TARGET>.npz``   bounds/active/extents (replayable)
  - ``runs/sd/<run_id>/cv_stability_<TARGET>.json`` optional 5-fold CV report
  - ``runs/sd/<run_id>/summary.json``              run-level metadata

Feature configurations (Specs v2 §4.3):

  SD-H    handcrafted only (~42 dims) — interpretable baseline, no MASK needed
  SD-HS   handcrafted + spectral eigenvectors (recommended primary)
  SD-HSP  handcrafted + spectral + PCA-MASK
  SD-P    backward-compat: handcrafted_matrix ⊕ PCA-MASK (v1)

Usage::

    # Recommended primary config (v2 §4.3)
    uv run python scripts/discover_probable_subgroups.py \\
        --config SD-HS \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz

    # Handcrafted-only — no MASK cache needed
    uv run python scripts/discover_probable_subgroups.py --config SD-H

    # All three classes + 5-fold CV stability check
    uv run python scripts/discover_probable_subgroups.py \\
        --config SD-HS --target PROBABLE TRUE FALSE --cv

    # v1 hybrid (handcrafted ⊕ PCA-MASK) for comparison
    uv run python scripts/discover_probable_subgroups.py --config SD-P
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from hipe.data import load_jsonl
from hipe.features import HANDCRAFTED_FEATURE_NAMES, handcrafted_matrix
from hipe.subgroup_discovery import (
    MCMCSubgroupDiscovery,
    build_hybrid_features,
    build_sd_feature_matrix,
    cv_stability,
    load_hierarchy_cache,
)
from hipe.subgroup_discovery.integration import summarize

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "data" / "dataset_reference.jsonl"
DEFAULT_NPZ = PROJECT_ROOT / "runs" / "mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz"
DEFAULT_SPLIT_CSV = PROJECT_ROOT / "data" / "v1_baseline_train_test_ids.csv"


def _load_split_ids(csv_path: Path, task: str = "at") -> dict[str, str]:
    import pandas as pd
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    df = df[df["task"] == task]
    return dict(zip(df["sample_id"], df["split"]))


def _filter_train(items, sample_ids, split_csv: Path):
    sample_to_split = _load_split_ids(split_csv, task="at")
    keep = np.array(
        [sample_to_split.get(s, "?") == "train" for s in sample_ids], dtype=bool
    )
    if not keep.any():
        raise SystemExit(
            f"No rows of {split_csv} matched the dataset. "
            "Pass --no-train-only to use all rows."
        )
    return keep


def _persist_subgroups(out_dir: Path, target: str, subgroups, feature_names):
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = summarize(subgroups, feature_names=feature_names)
    json_path = out_dir / f"subgroups_{target}.json"
    json_path.write_text(json.dumps({"target": target, "subgroups": rows}, indent=2))
    print(f"  wrote {json_path}")
    if subgroups:
        npz_path = out_dir / f"subgroups_{target}.npz"
        active = np.stack([s.active for s in subgroups], axis=0)
        bounds = np.stack([s.bounds for s in subgroups], axis=0)
        extent_lens = np.array([len(s.extent_indices) for s in subgroups])
        flat_extents = np.concatenate([s.extent_indices for s in subgroups])
        np.savez(
            npz_path,
            target=np.asarray(target),
            feature_names=np.asarray(feature_names),
            active=active,
            bounds=bounds,
            nwracc=np.array([s.nwracc for s in subgroups], dtype=np.float32),
            precision=np.array([s.precision for s in subgroups], dtype=np.float32),
            support=np.array([s.support for s in subgroups], dtype=np.int32),
            support_pos=np.array([s.support_pos for s in subgroups], dtype=np.int32),
            extent_lens=extent_lens,
            extent_indices=flat_extents,
        )
        print(f"  wrote {npz_path}")
    return rows


def _build_features(
    instances,
    *,
    config: str,
    mask_embeddings,
    n_pca: int,
    spectral_components: int,
    spectral_neighbors: int,
    hierarchy_cache,
    random_state: int,
):
    if config == "SD-P":
        # v1 backward-compat: handcrafted_matrix ⊕ PCA-MASK
        if mask_embeddings is None:
            raise SystemExit("config SD-P requires --npz with mask_emb")
        hand = handcrafted_matrix(instances)
        return build_hybrid_features(
            hand, mask_embeddings,
            n_pca=n_pca, handcrafted_names=HANDCRAFTED_FEATURE_NAMES,
            random_state=random_state, verbose=True,
        ) + ({"spectral": None, "pca_full": None},)  # extra slot to match return

    X, names, meta = build_sd_feature_matrix(
        instances,
        mask_embeddings=mask_embeddings,
        config=config,
        hierarchy_cache=hierarchy_cache,
        spectral_n_components=spectral_components,
        spectral_n_neighbors=spectral_neighbors,
        pca_n_components=n_pca,
        random_state=random_state,
        verbose=True,
    )
    return X, names, None, meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET),
                    help="dataset_reference.jsonl with full RelationInstance fields")
    ap.add_argument("--npz", default=str(DEFAULT_NPZ),
                    help="MASK cache (used for spectral / PCA blocks)")
    ap.add_argument("--split-csv", default=str(DEFAULT_SPLIT_CSV))
    ap.add_argument("--config", default="SD-HS",
                    choices=("SD-H", "SD-HS", "SD-HSP", "SD-P"),
                    help="Feature configuration (Specs v2 §4.3)")
    ap.add_argument("--target", nargs="+", default=["PROBABLE"])
    ap.add_argument("--train-only", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--hierarchy-cache", default=None,
                    help="Optional JSON file with the Wikidata P131 hierarchy cache")
    ap.add_argument("--n-pca", type=int, default=10,
                    help="MASK PCA components (used by SD-HSP and SD-P)")
    ap.add_argument("--spectral-components", type=int, default=10)
    ap.add_argument("--spectral-neighbors", type=int, default=15)
    ap.add_argument("--n-chains", type=int, default=10)
    ap.add_argument("--n-steps", type=int, default=10000)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--annealing", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--nwracc-threshold", type=float, default=0.3)
    ap.add_argument("--redundancy-theta", type=float, default=0.5)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--min-support", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--cv", action=argparse.BooleanOptionalAction, default=False)
    ap.add_argument("--cv-folds", type=int, default=5)
    ap.add_argument("--cv-min-precision", type=float, default=0.3)
    ap.add_argument("--cv-min-folds", type=int, default=3)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out-dir", default=None,
                    help="Run output directory. Default: runs/sd/<run_id>")
    args = ap.parse_args()

    print(f"Loading dataset {args.dataset}")
    instances = load_jsonl(args.dataset)
    sample_ids = [inst.sample_id for inst in instances]
    print(f"  rows: {len(instances)}")

    if args.train_only:
        keep = _filter_train(instances, sample_ids, Path(args.split_csv))
        instances = [inst for inst, k in zip(instances, keep) if k]
        sample_ids = [s for s, k in zip(sample_ids, keep) if k]
        print(f"  restricting to baseline train split: {len(instances)}")

    mask_embeddings = None
    if args.config in ("SD-HS", "SD-HSP", "SD-P"):
        npz_path = Path(args.npz)
        if not npz_path.exists():
            raise SystemExit(f"config {args.config} requires --npz that exists: {npz_path}")
        print(f"Loading MASK cache {npz_path}")
        z = np.load(npz_path, allow_pickle=True)
        cache_ids = list(z["sample_id"].astype(str))
        cache_emb = np.asarray(z["mask_emb"], dtype=np.float32)
        # Align cache rows with the (possibly filtered) instance order.
        idx = {sid: i for i, sid in enumerate(cache_ids)}
        rows = [idx.get(sid) for sid in sample_ids]
        if any(r is None for r in rows):
            missing = [sid for sid, r in zip(sample_ids, rows) if r is None]
            raise SystemExit(
                f"{len(missing)} instances are absent from the MASK cache "
                f"(first: {missing[:2]}). Re-run extract_mask_embeddings.py first."
            )
        mask_embeddings = cache_emb[rows]
        print(f"  mask_emb (aligned): {mask_embeddings.shape}")

    hierarchy_cache = None
    if args.hierarchy_cache:
        hierarchy_cache = load_hierarchy_cache(args.hierarchy_cache)
        print(f"  loaded hierarchy cache: {len(hierarchy_cache)} target QIDs")

    X, feature_names, _legacy_pca, meta = _build_features(
        instances,
        config=args.config,
        mask_embeddings=mask_embeddings,
        n_pca=args.n_pca,
        spectral_components=args.spectral_components,
        spectral_neighbors=args.spectral_neighbors,
        hierarchy_cache=hierarchy_cache,
        random_state=args.seed,
    )
    print(f"Feature matrix: {X.shape}")

    y_at = np.array([inst.at for inst in instances])

    run_id = args.run_id or f"{args.config}_{time.strftime('%Y%m%d_%H%M%S')}"
    out_dir = Path(args.out_dir) if args.out_dir else PROJECT_ROOT / "runs" / "sd" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run directory: {out_dir}")

    common_kwargs = dict(
        n_chains=args.n_chains,
        n_steps=args.n_steps,
        temperature=args.temperature,
        annealing=args.annealing,
        nwracc_threshold=args.nwracc_threshold,
        redundancy_theta=args.redundancy_theta,
        top_k=args.top_k,
        min_support=args.min_support,
        random_state=args.seed,
    )

    all_results: dict = {
        "run_id": run_id,
        "config": args.config,
        "dataset": str(args.dataset),
        "npz": str(args.npz) if mask_embeddings is not None else None,
        "train_only": bool(args.train_only),
        "n_features": int(X.shape[1]),
        "n_rows": int(X.shape[0]),
        "feature_names": list(feature_names),
        "mcmc": dict(common_kwargs),
        "targets": {},
    }

    for target in args.target:
        n_pos = int((y_at == target).sum())
        print(f"\n=== Target: {target}  (positives = {n_pos}) ===")
        if n_pos < 2:
            print("  skipping: too few positives in this slice")
            continue
        sd = MCMCSubgroupDiscovery(
            feature_names=feature_names, target_class=target, **common_kwargs
        )
        t0 = time.perf_counter()
        subgroups = sd.fit(X, y_at)
        elapsed = time.perf_counter() - t0
        if subgroups:
            print(
                f"  discovered {len(subgroups)} subgroups in {elapsed:.1f}s "
                f"(top NWRAcc = {subgroups[0].nwracc:.3f})"
            )
            for k, sg in enumerate(subgroups[:5]):
                print(
                    f"    [{k+1}] NWRAcc={sg.nwracc:.3f}  prec={sg.precision:.2f}  "
                    f"sup={sg.support_pos}/{sg.support}  |active|={sg.n_active()}"
                )
                print(f"        {sg.pattern_desc}")
        else:
            print(f"  no subgroups crossed threshold (elapsed {elapsed:.1f}s)")

        rows = _persist_subgroups(out_dir, target, subgroups, feature_names)
        all_results["targets"][target] = {
            "n_positives": n_pos,
            "n_subgroups": len(subgroups),
            "discovery_seconds": round(elapsed, 2),
            "subgroups": rows,
        }

        if args.cv:
            print(f"  running {args.cv_folds}-fold stability ...")
            t0 = time.perf_counter()
            try:
                report = cv_stability(
                    X, y_at, feature_names,
                    target_class=target,
                    n_folds=args.cv_folds,
                    min_precision=args.cv_min_precision,
                    min_folds=args.cv_min_folds,
                    sd_kwargs={
                        **{k: v for k, v in common_kwargs.items() if k != "random_state"},
                        "n_chains": max(2, common_kwargs["n_chains"] // 2),
                        "n_steps": max(1000, common_kwargs["n_steps"] // 2),
                    },
                    random_state=args.seed,
                    verbose=True,
                )
            except Exception as exc:
                print(f"  CV failed for {target}: {exc!r} — continuing with next target")
                all_results["targets"][target]["cv_error"] = repr(exc)
                continue
            elapsed = time.perf_counter() - t0
            cv_path = out_dir / f"cv_stability_{target}.json"
            cv_path.write_text(
                json.dumps({
                    "target": target,
                    "n_folds": args.cv_folds,
                    "min_precision": args.cv_min_precision,
                    "min_folds": args.cv_min_folds,
                    "elapsed_seconds": round(elapsed, 2),
                    "stable_patterns": report.stable_patterns,
                    "n_stable": report.n_stable(),
                }, indent=2)
            )
            print(
                f"  stable patterns: {report.n_stable()}  "
                f"(precision >= {args.cv_min_precision} on >= "
                f"{args.cv_min_folds}/{args.cv_folds})  -> {cv_path}"
            )
            all_results["targets"][target]["cv_n_stable"] = report.n_stable()
            all_results["targets"][target]["cv_seconds"] = round(elapsed, 2)

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\nWrote summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
