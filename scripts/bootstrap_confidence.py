"""Bootstrap 95% confidence interval over a predictions JSONL (Spec v0.9 §13.2.3).

Reads any predictions JSONL produced by the ablation harness — including the
hybrid file written by ``scripts/combine_split_predictions.py`` — and resamples
the (at_gold, at_pred, isAt_gold, isAt_pred) tuple ``n_bootstrap`` times to
estimate the sampling variability of the official global score.

Usage::

    uv run python scripts/bootstrap_confidence.py \
        --predictions logs/ablations/hybrid_RF_at_MASK_C4_isAt_at-test_predictions.jsonl

    uv run python scripts/bootstrap_confidence.py \
        --predictions logs/kfold/hybrid_kfold_oof_predictions.jsonl \
        --n-bootstrap 5000

Notes
-----
- ``null`` predictions are coerced to ``FALSE`` per the official rule.
- The bootstrap percentile method is reported (2.5% / 97.5% quantiles).
- This is much cheaper than k-fold for the LLM/agentic outputs because it
  doesn't require retraining; it only resamples the existing test predictions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from hipe.evaluation.metrics import compute_global_score, null_to_false


def _load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def bootstrap_global_score(
    at_gold: list[str],
    at_pred: list[str],
    isAt_gold: list[str],
    isAt_pred: list[str],
    *,
    n_bootstrap: int = 1000,
    seed: int = 42,
    ci: float = 0.95,
) -> dict:
    """Return point estimate + bootstrap 95% CI for global, MR(at), MR(isAt)."""
    rng = np.random.default_rng(seed)
    n = len(at_gold)
    assert n == len(at_pred) == len(isAt_gold) == len(isAt_pred)

    # Point estimate
    point = compute_global_score(at_gold, at_pred, isAt_gold, isAt_pred)

    g_samples = np.empty(n_bootstrap, dtype=np.float64)
    a_samples = np.empty(n_bootstrap, dtype=np.float64)
    i_samples = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        sub_at_g = [at_gold[j] for j in idx]
        sub_at_p = [at_pred[j] for j in idx]
        sub_is_g = [isAt_gold[j] for j in idx]
        sub_is_p = [isAt_pred[j] for j in idx]
        s = compute_global_score(sub_at_g, sub_at_p, sub_is_g, sub_is_p)
        g_samples[b] = s["global_score"]
        a_samples[b] = s["macro_recall_at"]
        i_samples[b] = s["macro_recall_isAt"]

    alpha = (1.0 - ci) / 2.0
    qlow, qhigh = 100.0 * alpha, 100.0 * (1.0 - alpha)
    return {
        "n_instances": n,
        "n_bootstrap": n_bootstrap,
        "ci": ci,
        "global_score": {
            "point": point["global_score"],
            "bootstrap_mean": float(g_samples.mean()),
            "bootstrap_std": float(g_samples.std(ddof=1)),
            "ci_lower": float(np.percentile(g_samples, qlow)),
            "ci_upper": float(np.percentile(g_samples, qhigh)),
        },
        "macro_recall_at": {
            "point": point["macro_recall_at"],
            "bootstrap_mean": float(a_samples.mean()),
            "bootstrap_std": float(a_samples.std(ddof=1)),
            "ci_lower": float(np.percentile(a_samples, qlow)),
            "ci_upper": float(np.percentile(a_samples, qhigh)),
        },
        "macro_recall_isAt": {
            "point": point["macro_recall_isAt"],
            "bootstrap_mean": float(i_samples.mean()),
            "bootstrap_std": float(i_samples.std(ddof=1)),
            "ci_lower": float(np.percentile(i_samples, qlow)),
            "ci_upper": float(np.percentile(i_samples, qhigh)),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--predictions", required=True, type=Path,
                    help="Predictions JSONL with at_gold/at_predicted/isAt_gold/isAt_predicted.")
    ap.add_argument("--n-bootstrap", type=int, default=1000)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=None,
                    help="Optional JSON output file. Defaults to <predictions>.bootstrap.json")
    args = ap.parse_args()

    rows = _load_rows(args.predictions)
    print(f"Loaded {len(rows)} rows from {args.predictions}")

    at_gold = [null_to_false(r.get("at_gold")) for r in rows]
    at_pred = [null_to_false(r.get("at_predicted")) for r in rows]
    isAt_gold = [null_to_false(r.get("isAt_gold")) for r in rows]
    isAt_pred = [null_to_false(r.get("isAt_predicted")) for r in rows]

    summary = bootstrap_global_score(
        at_gold, at_pred, isAt_gold, isAt_pred,
        n_bootstrap=args.n_bootstrap, seed=args.seed, ci=args.ci,
    )
    summary["source_file"] = str(args.predictions)

    out_path = args.out or args.predictions.with_suffix(".bootstrap.json")
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nBootstrap summary (n_bootstrap={args.n_bootstrap}, "
          f"CI={int(args.ci * 100)}%):")
    for key in ("global_score", "macro_recall_at", "macro_recall_isAt"):
        s = summary[key]
        print(f"  {key:<18s}: point={s['point']:.4f}  "
              f"bootstrap_mean={s['bootstrap_mean']:.4f}  "
              f"95% CI = [{s['ci_lower']:.4f}, {s['ci_upper']:.4f}]")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
