"""Compare three feature stacks on the C4 (mask+e1+e2+temporal) baseline.

Same classifier (LR by default, RF on request) on three feature stacks:

  * ``base``      mask_emb ⊕ e1_emb ⊕ e2_emb ⊕ temporal   (current C4 baseline)
  * ``+evidence`` base ⊕ evidence(13) ⊕ verb_type(7) ⊕ hierarchy(3) ⊕ lang(4)
                  — the v2 handcrafted blocks from Subgroup Discovery Specs §4.1
  * ``+sd``       (+evidence) ⊕ subgroup-match indicators from one or more SD runs
                  — Option A from Subgroup Discovery Specs §6.1

Run all three in one go with ``--stacks base +evidence +sd``. Each stack
produces its own ``logs/ablations/<exp_id>_predictions.jsonl`` + report so
the aggregate / report scripts pick them up automatically.

Usage::

    # All three stacks, single SD run (same SD subgroups for at and isAt)
    uv run python scripts/rf_with_sd_features.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz \\
        --sd-run runs/sd/SD-H_<id> \\
        --stacks base +evidence +sd

    # RF instead of LR; only +evidence (skip SD indicators)
    uv run python scripts/rf_with_sd_features.py --classifier rf --stacks +evidence
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Iterable
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from hipe.data import load_baseline_split, load_jsonl
from hipe.evaluation.report import generate_evaluation_report
from hipe.subgroup_discovery import (
    Subgroup,
    add_subgroup_features,
    evidence_matrix,
    hierarchy_matrix,
    verb_type_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NPZ = PROJECT_ROOT / "runs" / "mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz"
DEFAULT_DATASET = PROJECT_ROOT / "data" / "dataset_reference.jsonl"


# ---------------------------------------------------------------- estimators

def make_lr():
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


def make_mlp():
    # Small MLP — comparable capacity to LR but with non-linear interactions.
    # We disable early_stopping because sklearn 1.7's MLPClassifier crashes
    # on string-labelled fits when computing the internal val score
    # (``np.isnan`` on a string array). 200 epochs converge well on ~1k rows.
    return make_pipeline(
        StandardScaler(with_mean=True),
        MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            alpha=1e-4,
            batch_size=64,
            max_iter=200,
            early_stopping=False,
            random_state=42,
        ),
    )


CLASSIFIER_FACTORIES = {"lr": make_lr, "rf": make_rf, "mlp": make_mlp}


# -------------------------------------------------------------- SD subgroups

def _load_subgroups(npz_path: Path) -> list[Subgroup]:
    z = np.load(npz_path, allow_pickle=True)
    target = str(z["target"])
    feature_names = [str(n) for n in z["feature_names"]]
    active = z["active"]
    bounds = z["bounds"]
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
                nwracc=float(z["nwracc"][k]),
                support=int(z["support"][k]),
                support_pos=int(z["support_pos"][k]),
                precision=float(z["precision"][k]),
                extent_indices=ext,
                target_class=target,
                feature_names=tuple(feature_names),
            )
        )
    return out


def _load_all_subgroups(sd_run: Path, targets: Iterable[str]) -> dict[str, list[Subgroup]]:
    out: dict[str, list[Subgroup]] = {}
    for t in targets:
        p = sd_run / f"subgroups_{t}.npz"
        if p.exists():
            out[t] = _load_subgroups(p)
            print(f"  loaded {len(out[t])} subgroups for {t} from {p.name}")
        else:
            print(f"  (no subgroups file for {t} in {sd_run.name})")
    return out


# -------------------------------------------------------- feature assembly

def _base_block(z: dict, idx: np.ndarray) -> np.ndarray:
    """C4: mask_emb ⊕ e1_emb ⊕ e2_emb ⊕ temporal, for ``idx`` rows of the cache."""
    parts = [z["mask_emb"][idx], z["e1_emb"][idx], z["e2_emb"][idx], z["temporal"][idx]]
    return np.concatenate(parts, axis=1).astype(np.float32, copy=False)


def _evidence_block(instances) -> np.ndarray:
    return np.hstack(
        [evidence_matrix(instances), verb_type_matrix(instances), hierarchy_matrix(instances)]
    ).astype(np.float32, copy=False)


def _language_block(instances) -> np.ndarray:
    codes = ("en", "fr", "de", "lb")
    out = np.zeros((len(instances), len(codes)), dtype=np.float32)
    for i, inst in enumerate(instances):
        lang = (inst.language or "").lower()
        if lang in codes:
            out[i, codes.index(lang)] = 1.0
    return out


def _sd_indicator_block(
    sd_feature_X: np.ndarray, subgroups_by_target: dict[str, list[Subgroup]]
) -> tuple[np.ndarray, list[str]]:
    """Concatenate match indicators across all SD targets."""
    if not subgroups_by_target:
        return np.zeros((sd_feature_X.shape[0], 0), dtype=np.float32), []
    blocks: list[np.ndarray] = []
    names: list[str] = []
    for target, subs in subgroups_by_target.items():
        if not subs:
            continue
        aug, sg_names = add_subgroup_features(sd_feature_X, subs)
        block = aug[:, sd_feature_X.shape[1] :]
        blocks.append(block)
        names.extend(sg_names)
    if not blocks:
        return np.zeros((sd_feature_X.shape[0], 0), dtype=np.float32), []
    return np.concatenate(blocks, axis=1).astype(np.float32, copy=False), names


# ---------------------------------------------------------------- pipeline

def _train_and_predict(estimator_factory, X_tr, y_tr, X_te):
    est = estimator_factory()
    est.fit(X_tr, y_tr)
    pred = est.predict(X_te).tolist()
    return pred


def _run_stack(
    stack_name: str,
    classifier: str,
    npz_stem: str,
    targets: list[str],
    X_tr_full: np.ndarray,
    X_te_full: np.ndarray,
    train_inst,
    test_inst,
    sample_ids_test,
    languages_test,
    log_dir: Path,
    sd_run_id: str | None,
) -> dict:
    factory = CLASSIFIER_FACTORIES[classifier]
    print(f"\n=== Stack '{stack_name}' (classifier={classifier})  X_tr={X_tr_full.shape}  X_te={X_te_full.shape} ===")

    rows: list[dict] = []
    at_pred: list[str] | None = None
    isAt_pred: list[str] | None = None
    for tgt in targets:
        y_tr = np.array([(inst.at if tgt == "at" else inst.isAt) for inst in train_inst])
        gold = [(inst.at if tgt == "at" else inst.isAt) for inst in test_inst]
        # Filter NaN labels at training time
        mask = np.array([y is not None for y in y_tr])
        y_tr_clean = np.array([y for y in y_tr if y is not None])
        X_tr_clean = X_tr_full[mask]
        preds = _train_and_predict(factory, X_tr_clean, y_tr_clean, X_te_full)
        if tgt == "at":
            at_pred = preds
            at_gold = gold
        else:
            isAt_pred = preds
            isAt_gold = gold

    # Assemble prediction rows (always include both fields for the harness)
    for i, inst in enumerate(test_inst):
        rows.append(
            {
                "document_id": inst.document_id,
                "pers_entity_id": inst.pers_entity_id,
                "loc_entity_id": inst.loc_entity_id,
                "language": inst.language,
                "at_predicted": at_pred[i] if at_pred else None,
                "isAt_predicted": isAt_pred[i] if isAt_pred else None,
                "at_gold": inst.at,
                "isAt_gold": inst.isAt,
            }
        )

    sd_tag = f"+{sd_run_id}" if (stack_name == "+sd" and sd_run_id) else ""
    exp_id = (
        f"T1.6_rf_sd_{npz_stem}_{classifier}_{stack_name.lstrip('+').replace('+','_')}{sd_tag}"
    )
    pred_path = log_dir / f"{exp_id}_predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print(f"  wrote {pred_path}")

    metadata = {
        "n_instances": len(rows),
        "stack": stack_name,
        "classifier": classifier,
        "n_features": int(X_tr_full.shape[1]),
        "sd_run": sd_run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    report = generate_evaluation_report(
        exp_id,
        [r["at_gold"] for r in rows], [r["at_predicted"] for r in rows],
        [r["isAt_gold"] for r in rows], [r["isAt_predicted"] for r in rows],
        metadata=metadata, print_summary=True,
    )
    report_path = log_dir / f"{exp_id}_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"  wrote {report_path}")
    return {
        "stack": stack_name,
        "exp_id": exp_id,
        "n_features": int(X_tr_full.shape[1]),
        "global_score": report["scores"]["global_score"],
        "macro_recall_at": report["scores"]["macro_recall_at"],
        "macro_recall_isAt": report["scores"]["macro_recall_isAt"],
    }


# ------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", default=str(DEFAULT_NPZ),
                    help="MASK cache (provides mask_emb/e1_emb/e2_emb/temporal/sample_id).")
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ap.add_argument("--sd-run", default=None,
                    help="SD run directory (subgroups_<TARGET>.npz files).")
    ap.add_argument("--sd-targets", nargs="+", default=["PROBABLE", "TRUE", "FALSE"],
                    help="Which SD subgroups to load as indicator features.")
    ap.add_argument("--classifiers", nargs="+", default=["lr"],
                    choices=["lr", "rf", "mlp"],
                    help="One or more classifiers to evaluate. Pass 'lr rf mlp' "
                         "to get the full classifier x stack matrix in one run.")
    ap.add_argument("--stacks", nargs="+", default=["base", "+evidence", "+sd"],
                    choices=["base", "+evidence", "+sd"])
    ap.add_argument("--targets", nargs="+", default=["at", "isAt"],
                    help="Which task slots to train classifiers for.")
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    args = ap.parse_args()

    npz_path = Path(args.npz)
    if not npz_path.exists():
        ap.error(f"--npz does not exist: {npz_path}")
    sd_run = Path(args.sd_run) if args.sd_run else None
    if "+sd" in args.stacks and sd_run is None:
        ap.error("stack '+sd' requires --sd-run")

    print(f"Loading MASK cache {npz_path}")
    z = np.load(npz_path, allow_pickle=True)
    cache = {k: z[k] for k in z.files}
    cache_ids = list(cache["sample_id"].astype(str))
    print(f"  rows in cache: {len(cache_ids)}")

    print(f"Loading dataset {args.dataset}")
    instances = load_jsonl(args.dataset)
    sp = load_baseline_split(instances, task="at")
    train_inst, test_inst = sp.train, sp.test
    print(f"  baseline split: train={len(train_inst)}  test={len(test_inst)}")

    # Align cache rows to train/test order
    idx_of = {sid: i for i, sid in enumerate(cache_ids)}
    train_idx = np.array([idx_of[i.sample_id] for i in train_inst])
    test_idx = np.array([idx_of[i.sample_id] for i in test_inst])

    base_tr = _base_block(cache, train_idx)
    base_te = _base_block(cache, test_idx)
    print(f"  base block (mask+e1+e2+temporal): {base_tr.shape[1]}-d")

    evidence_tr: np.ndarray | None = None
    evidence_te: np.ndarray | None = None
    if any(s in args.stacks for s in ("+evidence", "+sd")):
        print("  building evidence/verb/hierarchy/lang block ...")
        evidence_tr = np.hstack(
            [_evidence_block(train_inst), _language_block(train_inst)]
        ).astype(np.float32, copy=False)
        evidence_te = np.hstack(
            [_evidence_block(test_inst), _language_block(test_inst)]
        ).astype(np.float32, copy=False)
        print(f"  evidence block: {evidence_tr.shape[1]}-d")

    # Subgroup indicators are computed on the SAME feature space the SD was
    # discovered on. Today: SD-H = temporal(15) + evidence(13) + verb(7) +
    # hierarchy(3) + lang(4) = 42 dims, in that exact order.
    sd_block_tr: np.ndarray | None = None
    sd_block_te: np.ndarray | None = None
    sd_run_id: str | None = None
    if "+sd" in args.stacks:
        sd_run_id = sd_run.name
        print(f"\nLoading SD subgroups from {sd_run}")
        sg_by_target = _load_all_subgroups(sd_run, args.sd_targets)
        if not sg_by_target:
            print("  no subgroups found — skipping +sd stack")
            args.stacks = [s for s in args.stacks if s != "+sd"]
        else:
            # Recompute SD-H feature matrix (must match the order in
            # build_sd_feature_matrix: temporal ⊕ evidence ⊕ verb ⊕ hierarchy ⊕ lang).
            from hipe.features.temporal import temporal_matrix
            sd_h_tr = np.hstack([
                temporal_matrix(train_inst),
                evidence_matrix(train_inst),
                verb_type_matrix(train_inst),
                hierarchy_matrix(train_inst),
                _language_block(train_inst),
            ]).astype(np.float32, copy=False)
            sd_h_te = np.hstack([
                temporal_matrix(test_inst),
                evidence_matrix(test_inst),
                verb_type_matrix(test_inst),
                hierarchy_matrix(test_inst),
                _language_block(test_inst),
            ]).astype(np.float32, copy=False)
            sd_block_tr, names_tr = _sd_indicator_block(sd_h_tr, sg_by_target)
            sd_block_te, _names_te = _sd_indicator_block(sd_h_te, sg_by_target)
            print(f"  SD indicator block: {sd_block_tr.shape[1]} columns "
                  f"({sum(len(s) for s in sg_by_target.values())} subgroups across "
                  f"{len(sg_by_target)} targets)")

    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    npz_stem = npz_path.stem.replace("mask_", "")

    summary: list[dict] = []
    for stack in args.stacks:
        if stack == "base":
            X_tr, X_te = base_tr, base_te
        elif stack == "+evidence":
            X_tr = np.hstack([base_tr, evidence_tr]).astype(np.float32, copy=False)
            X_te = np.hstack([base_te, evidence_te]).astype(np.float32, copy=False)
        elif stack == "+sd":
            X_tr = np.hstack([base_tr, evidence_tr, sd_block_tr]).astype(np.float32, copy=False)
            X_te = np.hstack([base_te, evidence_te, sd_block_te]).astype(np.float32, copy=False)
        else:  # pragma: no cover - argparse choices guard this
            continue
        for clf in args.classifiers:
            result = _run_stack(
                stack, clf,
                npz_stem, args.targets,
                X_tr, X_te,
                train_inst, test_inst,
                [i.sample_id for i in test_inst],
                np.array([i.language for i in test_inst]),
                log_dir, sd_run_id,
            )
            result["classifier"] = clf
            summary.append(result)

    print("\n=== Classifier x stack comparison ===")
    print(
        f"{'classifier':<10} {'stack':<14} {'n_features':>11} "
        f"{'global':>9} {'mr_at':>9} {'mr_isAt':>9}"
    )
    for r in summary:
        print(
            f"{r['classifier']:<10} {r['stack']:<14} {r['n_features']:>11d} "
            f"{r['global_score']:>9.4f} {r['macro_recall_at']:>9.4f} {r['macro_recall_isAt']:>9.4f}"
        )

    summary_path = log_dir / f"rf_sd_summary_{int(time.time())}.json"
    summary_path.write_text(json.dumps({"runs": summary}, indent=2))
    print(f"\nWrote summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
