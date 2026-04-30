"""Apply SD-discovered subgroups as post-processing overrides (Option B).

Reads an existing predictions JSONL (from any classifier), recomputes the SD
feature matrix on the matching test instances, fires each subgroup that meets
the quality gates, and flips eligible predictions toward the subgroup's
target class. Writes a new predictions file plus a fresh evaluation report
under ``logs/ablations/``.

Usage::

    # Override FALSE→PROBABLE on the C4 baseline using SD-H subgroups
    uv run python scripts/apply_sd_overrides.py \\
        --predictions logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test_predictions.jsonl \\
        --sd-run runs/sd/SD-H_20260430_175226 \\
        --target PROBABLE --only-from FALSE --min-nwracc 0.05

    # Layer multiple targets (PROBABLE then TRUE rescue) by chaining runs:
    uv run python scripts/apply_sd_overrides.py \\
        --predictions <previous-pass>.jsonl \\
        --sd-run runs/sd/<run> --target TRUE --only-from FALSE --min-nwracc 0.1
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from hipe.data import RelationInstance, load_jsonl
from hipe.evaluation.report import generate_evaluation_report
from hipe.subgroup_discovery import (
    Subgroup,
    apply_overrides,
    build_sd_feature_matrix,
)
from hipe.subgroup_discovery.features import build_hybrid_features
from hipe.features import HANDCRAFTED_FEATURE_NAMES, handcrafted_matrix

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = PROJECT_ROOT / "data" / "dataset_reference.jsonl"


def _load_subgroups(npz_path: Path) -> list[Subgroup]:
    z = np.load(npz_path, allow_pickle=True)
    target = str(z["target"])
    feature_names = [str(n) for n in z["feature_names"]]
    active = z["active"]            # (k, d)
    bounds = z["bounds"]            # (k, d, 2)
    nwracc = z["nwracc"]
    precision = z["precision"]
    support = z["support"]
    support_pos = z["support_pos"]
    extent_lens = z["extent_lens"]
    flat = z["extent_indices"]
    out: list[Subgroup] = []
    cursor = 0
    for k in range(active.shape[0]):
        n_ext = int(extent_lens[k])
        ext = flat[cursor : cursor + n_ext]
        cursor += n_ext
        out.append(
            Subgroup(
                pattern_desc=f"<sg#{k}>",
                active=active[k],
                bounds=bounds[k],
                nwracc=float(nwracc[k]),
                support=int(support[k]),
                support_pos=int(support_pos[k]),
                precision=float(precision[k]),
                extent_indices=ext,
                target_class=target,
                feature_names=tuple(feature_names),
            )
        )
    return out


def _index_by_keys(rows: list[dict]) -> dict[tuple[str, str, str], dict]:
    return {
        (r["document_id"], r["pers_entity_id"], r["loc_entity_id"]): r
        for r in rows
    }


def _key(inst: RelationInstance) -> tuple[str, str, str]:
    return (inst.document_id, inst.pers_entity_id, inst.loc_entity_id)


def _build_test_features(instances, summary: dict, mask_embeddings):
    """Recompute the SD feature matrix on ``instances`` matching the run's config."""
    config = summary.get("config", "SD-H")
    if config == "SD-P":
        # v1 hybrid: handcrafted_matrix ⊕ PCA-MASK fitted on the test pool
        # — caller is responsible for keeping the test pool matched. Note:
        # PCA fit on test alone is not identical to the train-fit PCA the
        # subgroups were discovered on, so SD-P + Option B is a best-effort
        # reuse of the bounds.
        if mask_embeddings is None:
            raise SystemExit("config SD-P needs --npz with mask_emb")
        n_pca = int(summary.get("mcmc", {}).get("n_pca", 20)) or 20
        hand = handcrafted_matrix(instances)
        X, names, _pca = build_hybrid_features(
            hand, mask_embeddings,
            n_pca=n_pca, handcrafted_names=HANDCRAFTED_FEATURE_NAMES,
            verbose=False,
        )
        return X, names

    return build_sd_feature_matrix(
        instances,
        mask_embeddings=mask_embeddings,
        config=config,
        spectral_n_components=int(summary.get("config_spectral_components", 10)),
        spectral_n_neighbors=int(summary.get("config_spectral_neighbors", 15)),
        pca_n_components=int(summary.get("config_pca_components", 10)),
        verbose=False,
    )[:2]


def _aligned_mask_embeddings(npz_path: Path, sample_ids: list[str]) -> np.ndarray:
    z = np.load(npz_path, allow_pickle=True)
    cache_ids = list(z["sample_id"].astype(str))
    cache_emb = np.asarray(z["mask_emb"], dtype=np.float32)
    idx = {sid: i for i, sid in enumerate(cache_ids)}
    rows = [idx.get(sid) for sid in sample_ids]
    missing = [sid for sid, r in zip(sample_ids, rows) if r is None]
    if missing:
        raise SystemExit(
            f"{len(missing)} instances missing from MASK cache (first: {missing[:2]})"
        )
    return cache_emb[rows]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--predictions", required=True,
                    help="Existing *_predictions.jsonl to override.")
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ap.add_argument("--sd-run", required=True,
                    help="SD run directory (containing summary.json + subgroups_*.npz).")
    ap.add_argument("--target", default="PROBABLE",
                    help="Subgroup target class (must match a subgroups_<TARGET>.npz file).")
    ap.add_argument("--only-from", nargs="+", default=["FALSE"],
                    help="Predictions in this set are eligible for override.")
    ap.add_argument("--min-nwracc", type=float, default=0.05)
    ap.add_argument("--min-precision", type=float, default=0.0)
    ap.add_argument("--task", choices=["at", "isAt"], default="at",
                    help="Which task slot to override.")
    ap.add_argument("--mask-npz", default=None,
                    help="MASK cache to align test rows for SD-HS/SD-HSP/SD-P configs.")
    ap.add_argument("--experiment-id", default=None)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    args = ap.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.exists():
        ap.error(f"--predictions does not exist: {pred_path}")
    sd_dir = Path(args.sd_run)
    if not sd_dir.exists():
        ap.error(f"--sd-run does not exist: {sd_dir}")
    sg_path = sd_dir / f"subgroups_{args.target}.npz"
    if not sg_path.exists():
        ap.error(f"no subgroups file: {sg_path}")

    summary_path = sd_dir / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    else:
        # Run is mid-flight — infer config from the subgroup feature_names.
        z_first = np.load(sg_path, allow_pickle=True)
        n_feats = len(z_first["feature_names"])
        inferred = "SD-H" if n_feats == 42 else f"unknown({n_feats}d)"
        print(f"  summary.json missing — inferred config = {inferred}")
        summary = {"config": inferred}
    config = summary.get("config", "SD-H")
    print(f"Loading SD subgroups for target={args.target}  (config={config})")
    subgroups = _load_subgroups(sg_path)
    eligible_subgroups = [
        s for s in subgroups
        if s.nwracc >= args.min_nwracc and s.precision >= args.min_precision
    ]
    print(
        f"  loaded {len(subgroups)} subgroups; "
        f"{len(eligible_subgroups)} pass NWRAcc>={args.min_nwracc} & "
        f"precision>={args.min_precision}"
    )
    if not eligible_subgroups:
        print("  no subgroups eligible — exiting without changes")
        return 0

    print(f"Loading predictions: {pred_path}")
    rows = [json.loads(l) for l in pred_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_key = _index_by_keys(rows)
    print(f"  rows: {len(rows)}")

    print(f"Loading dataset: {args.dataset}")
    all_inst = load_jsonl(args.dataset)
    inst_by_key = {_key(i): i for i in all_inst}

    aligned_inst: list[RelationInstance] = []
    aligned_rows: list[dict] = []
    for r in rows:
        k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
        if k in inst_by_key:
            aligned_inst.append(inst_by_key[k])
            aligned_rows.append(r)
        else:
            print(f"  warning: missing dataset row for {k}")
    print(f"  aligned: {len(aligned_inst)}/{len(rows)} rows")

    mask_embeddings = None
    if config in ("SD-HS", "SD-HSP", "SD-P"):
        if not args.mask_npz:
            raise SystemExit(f"config {config} needs --mask-npz")
        sample_ids = [i.sample_id for i in aligned_inst]
        mask_embeddings = _aligned_mask_embeddings(Path(args.mask_npz), sample_ids)
        print(f"  mask_emb (aligned): {mask_embeddings.shape}")

    X_test, feature_names = _build_test_features(aligned_inst, summary, mask_embeddings)
    print(f"  test feature matrix: {X_test.shape}")
    expected_d = subgroups[0].active.shape[0]
    if X_test.shape[1] != expected_d:
        raise SystemExit(
            f"Feature dimensionality mismatch: SD has {expected_d}, test built {X_test.shape[1]}. "
            f"Check that SD config '{config}' is reproduced exactly on the test pool."
        )

    pred_field = "at_predicted" if args.task == "at" else "isAt_predicted"
    gold_field = "at_gold" if args.task == "at" else "isAt_gold"
    preds_old = [r.get(pred_field) for r in aligned_rows]
    new_preds, n_over = apply_overrides(
        preds_old, X_test, eligible_subgroups,
        target=args.target, only_from=tuple(args.only_from),
        min_nwracc=args.min_nwracc, min_precision=args.min_precision,
        verbose=False,
    )
    delta_indices = [i for i, (a, b) in enumerate(zip(preds_old, new_preds)) if a != b]
    print(f"Applied {n_over} overrides ({args.task})")

    # Write new predictions file
    out_rows: list[dict] = []
    for r, new in zip(aligned_rows, new_preds):
        rr = dict(r)
        rr[pred_field] = new
        rr.setdefault("override_history", []).append(
            {
                "from": r.get(pred_field),
                "to": new,
                "target": args.target,
                "sd_run": str(sd_dir.name),
                "min_nwracc": args.min_nwracc,
                "min_precision": args.min_precision,
            }
        )
        out_rows.append(rr)

    base = pred_path.stem.replace("_predictions", "")
    if args.experiment_id:
        exp_id = args.experiment_id
    else:
        from_tag = "+".join(sorted(args.only_from))
        exp_id = f"{base}+SDov_{args.target}_from_{from_tag}_nw{args.min_nwracc}"

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    new_pred_path = log_dir / f"{exp_id}_predictions.jsonl"
    with new_pred_path.open("w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"Wrote {new_pred_path}")

    # Generate report
    at_gold = [r["at_gold"] for r in out_rows]
    at_pred = [r["at_predicted"] for r in out_rows]
    isAt_gold = [r["isAt_gold"] for r in out_rows]
    isAt_pred = [r["isAt_predicted"] for r in out_rows]
    metadata = {
        "n_instances": len(out_rows),
        "source_predictions": str(pred_path),
        "sd_run": str(sd_dir),
        "sd_config": config,
        "target": args.target,
        "only_from": list(args.only_from),
        "min_nwracc": args.min_nwracc,
        "min_precision": args.min_precision,
        "n_overrides": n_over,
        "n_eligible_subgroups": len(eligible_subgroups),
        "task": args.task,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    report = generate_evaluation_report(
        exp_id, at_gold, at_pred, isAt_gold, isAt_pred,
        metadata=metadata, print_summary=True,
    )
    report_path = log_dir / f"{exp_id}_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {report_path}")

    # Diff vs baseline summary line for quick scanning
    baseline_report_path = pred_path.parent / pred_path.name.replace(
        "_predictions.jsonl", "_report.json"
    )
    if baseline_report_path.exists():
        base_report = json.loads(baseline_report_path.read_text(encoding="utf-8"))
        scores_b = base_report.get("scores", {}) or {}
        scores_n = report["scores"]
        # Compare the relevant per-task metric — global is contaminated when
        # the input predictions only cover one slot (at OR isAt).
        metric = "macro_recall_at" if args.task == "at" else "macro_recall_isAt"
        if metric in scores_b:
            b = float(scores_b[metric])
            n = float(scores_n[metric])
            print(
                f"\n{metric}: baseline={b:.4f}  with_overrides={n:.4f}  "
                f"delta={n - b:+.4f}  (n_overrides={n_over})"
            )
        if "global_score" in scores_b:
            print(
                f"global_score: baseline={float(scores_b['global_score']):.4f}  "
                f"with_overrides={float(scores_n['global_score']):.4f} "
                f"(global counts both tasks; only meaningful when both slots are predicted)"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
