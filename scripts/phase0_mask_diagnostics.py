"""Phase 0 MASK diagnostics: viz + LR/RF baselines + go/no-go decision.

Loads cached MASK embeddings (from ``extract_mask_embeddings.py``) and:
  1. Plots PCA and UMAP projections coloured by ``at`` and ``isAt``.
  2. Computes silhouette scores per label.
  3. Evaluates 4 baselines under 5-fold stratified CV (macro-recall):
     - C1   LR on mask_emb (768-d)
     - C4   LR on mask + e1 + e2 + temporal (783-d)
     - T1.4 LR on temporal alone (15-d)
     - T1.5 RF on broader handcrafted features (~30-d)
  4. Applies the go/no-go gate from MASK Experiment Spec §0:
       MASK > handcrafted RF + 2%  -> GO
       within 2%                    -> CONDITIONAL (try contrastive)
       MASK < handcrafted RF        -> PIVOT (drop MASK as classifier)

Usage:
    uv run python scripts/phase0_mask_diagnostics.py \
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# IO + viz helpers
# ---------------------------------------------------------------------------


def load_npz(path: Path) -> dict[str, np.ndarray]:
    z = np.load(path, allow_pickle=True)
    return {k: z[k] for k in z.files}


def umap_project(emb: np.ndarray, n_neighbors: int = 15, min_dist: float = 0.1, seed: int = 42) -> np.ndarray:
    from umap import UMAP

    reducer = UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=2,
        metric="cosine",
        random_state=seed,
    )
    return reducer.fit_transform(emb)


def plot_projection(
    coords: np.ndarray,
    labels: np.ndarray,
    title: str,
    out_path: Path,
    palette: dict[str, str] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    unique = sorted(set(labels))
    palette = palette or {}
    default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for i, lbl in enumerate(unique):
        mask = labels == lbl
        ax.scatter(
            coords[mask, 0],
            coords[mask, 1],
            s=8,
            alpha=0.6,
            label=f"{lbl} (n={int(mask.sum())})",
            color=palette.get(str(lbl), default_colors[i % len(default_colors)]),
        )
    ax.set_title(title)
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Baselines + CV
# ---------------------------------------------------------------------------


def cv_macro_recall(
    X: np.ndarray,
    y: np.ndarray,
    *,
    estimator,
    n_splits: int = 5,
    seed: int = 42,
) -> tuple[float, float, np.ndarray, np.ndarray, list[str]]:
    """Stratified-K-fold CV. Returns (mean_macro_recall, std, y_true, y_pred, labels)."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores = []
    all_pred = np.empty_like(y)
    for train_idx, test_idx in skf.split(X, y):
        clf = estimator()
        clf.fit(X[train_idx], y[train_idx])
        pred = clf.predict(X[test_idx])
        scores.append(recall_score(y[test_idx], pred, average="macro", zero_division=0))
        all_pred[test_idx] = pred
    labels = sorted(set(y))
    return float(np.mean(scores)), float(np.std(scores)), y, all_pred, labels


def make_lr() -> LogisticRegression:
    return LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        solver="lbfgs",
        n_jobs=None,
    )


def make_lr_pipeline():
    def _factory():
        return make_pipeline(StandardScaler(with_mean=True), make_lr())
    return _factory


def make_rf_pipeline():
    def _factory():
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
    return _factory


def evaluate(
    name: str,
    X: np.ndarray,
    y: np.ndarray,
    estimator,
    n_splits: int = 5,
) -> dict:
    mean, std, y_true, y_pred, labels = cv_macro_recall(X, y, estimator=estimator, n_splits=n_splits)
    report = classification_report(y_true, y_pred, zero_division=0, output_dict=True)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    print(f"\n  {name}: macro-recall = {mean:.4f} ± {std:.4f}  (n={len(y)}, dim={X.shape[1]})")
    for cls in labels:
        rec = report.get(cls, {}).get("recall", float("nan"))
        prec = report.get(cls, {}).get("precision", float("nan"))
        sup = report.get(cls, {}).get("support", 0)
        print(f"      {cls!s:<12s}  prec={prec:.3f}  recall={rec:.3f}  n={sup}")
    return {
        "name": name,
        "macro_recall_mean": mean,
        "macro_recall_std": std,
        "input_dim": int(X.shape[1]),
        "labels": labels,
        "confusion_matrix": cm,
        "per_class": {
            cls: {
                "precision": report.get(cls, {}).get("precision"),
                "recall": report.get(cls, {}).get("recall"),
                "support": report.get(cls, {}).get("support"),
            }
            for cls in labels
        },
    }


# ---------------------------------------------------------------------------
# Go/no-go gate
# ---------------------------------------------------------------------------


def gate_decision(mask_score: float, handcrafted_score: float, *, tol: float = 0.02) -> str:
    delta = mask_score - handcrafted_score
    if delta > tol:
        return "GO"
    if delta < -tol:
        return "PIVOT"
    return "CONDITIONAL"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True, help="Output of extract_mask_embeddings.py")
    ap.add_argument("--out-dir", default=str(PROJECT_ROOT / "runs" / "phase0_mask_diag"))
    ap.add_argument("--n-splits", type=int, default=5)
    ap.add_argument("--skip-umap", action="store_true",
                    help="UMAP can be slow on CPU; skip when iterating.")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.npz}")
    Z = load_npz(Path(args.npz))
    mask = Z["mask_emb"].astype(np.float32)
    e1 = Z["e1_emb"].astype(np.float32)
    e2 = Z["e2_emb"].astype(np.float32)
    concat = Z["concat_emb"].astype(np.float32)
    temporal = Z["temporal"].astype(np.float32)
    hand = Z["handcrafted"].astype(np.float32)
    at = Z["at"].astype(str)
    isAt = Z["isAt"].astype(str)
    languages = Z["language"].astype(str)
    print(f"  mask_emb       : {mask.shape}")
    print(f"  e1_emb         : {e1.shape}")
    print(f"  e2_emb         : {e2.shape}")
    print(f"  concat_emb     : {concat.shape}")
    print(f"  temporal       : {temporal.shape}")
    print(f"  handcrafted    : {hand.shape}")
    print(f"  at unique      : {sorted(set(at))}")
    print(f"  isAt unique    : {sorted(set(isAt))}")
    print(f"  languages      : {sorted(set(languages))}")

    # -----------------------------------------------------------
    # Visualisations
    # -----------------------------------------------------------
    print("\n[1/3] Computing PCA(2) of mask_emb ...")
    pca = PCA(n_components=2, random_state=42)
    pca_coords = pca.fit_transform(mask)
    print(f"  explained variance: {pca.explained_variance_ratio_}")
    plot_projection(pca_coords, at, "PCA(2) — mask_emb coloured by `at`",
                    out_dir / "pca_at.png")
    plot_projection(pca_coords, isAt, "PCA(2) — mask_emb coloured by `isAt`",
                    out_dir / "pca_isAt.png")
    plot_projection(pca_coords, languages, "PCA(2) — mask_emb coloured by language",
                    out_dir / "pca_lang.png")

    if not args.skip_umap:
        print("[2/3] Computing UMAP(2) of mask_emb (may take 30-60 s) ...")
        umap_coords = umap_project(mask)
        plot_projection(umap_coords, at, "UMAP(2) — mask_emb coloured by `at`",
                        out_dir / "umap_at.png")
        plot_projection(umap_coords, isAt, "UMAP(2) — mask_emb coloured by `isAt`",
                        out_dir / "umap_isAt.png")
        plot_projection(umap_coords, languages, "UMAP(2) — mask_emb coloured by language",
                        out_dir / "umap_lang.png")
    else:
        print("[2/3] UMAP skipped (--skip-umap)")

    # Silhouette: do labels carve up the embedding space at all?
    print("[3/3] Silhouette scores")
    sil_at = silhouette_score(mask, at, metric="cosine") if len(set(at)) > 1 else float("nan")
    sil_isAt = silhouette_score(mask, isAt, metric="cosine") if len(set(isAt)) > 1 else float("nan")
    print(f"  silhouette(at)   = {sil_at:.4f}")
    print(f"  silhouette(isAt) = {sil_isAt:.4f}")

    # -----------------------------------------------------------
    # CV baselines
    # -----------------------------------------------------------
    print("\n" + "=" * 78)
    print("CV baselines (5-fold stratified, macro-recall)")
    print("=" * 78)

    results: dict = {
        "config": vars(args),
        "shapes": {
            "mask": list(mask.shape),
            "concat": list(concat.shape),
            "temporal": list(temporal.shape),
            "handcrafted": list(hand.shape),
        },
        "silhouette": {"at": sil_at, "isAt": sil_isAt},
        "experiments": {},
    }

    # Combined feature: concat (mask + e1 + e2) + temporal -> 783-d for C4
    concat_temporal = np.concatenate([concat, temporal], axis=1)

    feature_sets = {
        "C1_mask_LR": (mask, make_lr_pipeline()),
        "C4_mask+e1+e2+temporal_LR": (concat_temporal, make_lr_pipeline()),
        "T1.4_temporal_only_LR": (temporal, make_lr_pipeline()),
        "T1.5_handcrafted_RF": (hand, make_rf_pipeline()),
    }

    for label_name, y in (("at", at), ("isAt", isAt)):
        print(f"\n--- target: {label_name} ---")
        bucket: dict = {}
        for exp_name, (X, factory) in feature_sets.items():
            res = evaluate(f"{exp_name} [target={label_name}]", X, y, factory, n_splits=args.n_splits)
            bucket[exp_name] = res
        results["experiments"][label_name] = bucket

    # -----------------------------------------------------------
    # Go/no-go decision
    # -----------------------------------------------------------
    print("\n" + "=" * 78)
    print("Go/no-go decision (Spec §0 thresholds: at 0.59, isAt 0.68)")
    print("=" * 78)

    gate: dict = {}
    for label_name in ("at", "isAt"):
        bucket = results["experiments"][label_name]
        mask_score = bucket["C1_mask_LR"]["macro_recall_mean"]
        hand_score = bucket["T1.5_handcrafted_RF"]["macro_recall_mean"]
        decision = gate_decision(mask_score, hand_score, tol=0.02)
        spec_threshold = 0.59 if label_name == "at" else 0.68
        gate[label_name] = {
            "mask_score": mask_score,
            "handcrafted_score": hand_score,
            "delta": mask_score - hand_score,
            "decision": decision,
            "spec_floor": spec_threshold,
            "passes_spec_floor": mask_score >= spec_threshold,
        }
        print(
            f"  {label_name:5s}  MASK-LR={mask_score:.4f}  "
            f"handcrafted-RF={hand_score:.4f}  "
            f"Δ={mask_score - hand_score:+.4f}  "
            f"-> {decision}  (spec floor {spec_threshold:.2f}: "
            f"{'PASS' if mask_score >= spec_threshold else 'BELOW'})"
        )
    results["gate"] = gate

    # Persist results
    out_json = out_dir / "results.json"
    out_json.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults written to {out_json}")
    print(f"Plots written to {out_dir}/*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
