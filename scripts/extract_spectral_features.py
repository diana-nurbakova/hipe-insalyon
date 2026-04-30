"""Augment a MASK cache with Laplacian-eigenmap spectral features.

Reads ``runs/mask_*.npz``, computes spectral features from the chosen base
embedding (``mask_emb`` by default), and writes a sibling ``*_spec<k>.npz``
that includes a new ``spectral`` array (N × n_components). The grid evaluator
picks these up automatically via the ``--include-spectral`` flag.

The fit is **transductive** — Laplacian eigenmaps don't admit a clean
closed-form out-of-sample extension, and our train/test split is a fixed
known partition. The spectral features therefore reflect the entire
1,251-instance manifold, which is appropriate when the same instances are
both training and held out.

For an inductive variant (fit-on-train, Nyström-extend), use
:class:`hipe.mask.spectral.SpectralFeatureExtractor` directly.

Examples:
    uv run python scripts/extract_spectral_features.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz

    # Use the multi-layer concat as the base embedding instead
    uv run python scripts/extract_spectral_features.py \\
        --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L_1__4__7.npz \\
        --base mask_emb_layers --n-components 16 --n-neighbors 30
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from hipe.mask.spectral import (
    compute_spectral_features_full,
    eigenvector_label_nmi,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True, help="Input MASK cache.")
    ap.add_argument(
        "--base",
        default="mask_emb",
        choices=["mask_emb", "mask_emb_layers", "concat_emb"],
        help="Which array in the cache to compute spectral features from.",
    )
    ap.add_argument("--n-components", type=int, default=10)
    ap.add_argument("--n-neighbors", type=int, default=20)
    ap.add_argument("--metric", default="cosine")
    ap.add_argument("--sigma", type=float, default=None,
                    help="Heat-kernel bandwidth; defaults to median k-NN distance.")
    ap.add_argument("--out", default=None,
                    help="Override output path. Default: <input>_spec<k>.npz")
    args = ap.parse_args()

    in_path = Path(args.npz)
    if not in_path.exists():
        raise SystemExit(f"--npz does not exist: {in_path}")

    print(f"Loading {in_path}")
    z = np.load(in_path, allow_pickle=True)
    cache = {k: z[k] for k in z.files}
    if args.base not in cache:
        raise SystemExit(
            f"Cache lacks base array {args.base!r}. Available: "
            f"{sorted(k for k in cache.keys() if not k.startswith('_'))}"
        )

    base = cache[args.base].astype(np.float32, copy=False)
    print(f"  base shape: {base.shape}  metric={args.metric}  k={args.n_neighbors}")

    print("Computing spectral features ...")
    feats, eigvals = compute_spectral_features_full(
        base,
        n_components=args.n_components,
        n_neighbors=args.n_neighbors,
        metric=args.metric,
        sigma=args.sigma,
    )
    print(f"  features shape: {feats.shape}")
    print(f"  eigenvalues  : {np.array2string(eigvals, precision=4)}")

    # Diagnostic: eigenvector ↔ label NMI.
    if "at" in cache and "isAt" in cache:
        from hipe.mask.contrastive import AT_TO_IDX, ISAT_TO_IDX, encode_labels

        at_int = encode_labels(cache["at"].astype(str), AT_TO_IDX)
        isAt_int = encode_labels(cache["isAt"].astype(str), ISAT_TO_IDX)
        nmi_at = eigenvector_label_nmi(feats, at_int, n_bins=3)
        nmi_isAt = eigenvector_label_nmi(feats, isAt_int, n_bins=2)
        print("  NMI(at)  per eigenvector :", [f"{v:.3f}" for v in nmi_at])
        print("  NMI(isAt) per eigenvector:", [f"{v:.3f}" for v in nmi_isAt])
    else:
        nmi_at, nmi_isAt = [], []

    # Persist alongside originals.
    out_path = Path(args.out) if args.out else in_path.with_name(
        f"{in_path.stem}_spec{args.n_components}.npz"
    )
    out_kwargs = dict(cache)
    out_kwargs["spectral"] = feats
    out_kwargs["_meta_spectral"] = np.asarray(json.dumps({
        "base": args.base,
        "n_components": args.n_components,
        "n_neighbors": args.n_neighbors,
        "metric": args.metric,
        "sigma": args.sigma,
        "eigenvalues": eigvals.tolist(),
        "nmi_at": nmi_at,
        "nmi_isAt": nmi_isAt,
    }))
    np.savez(out_path, **out_kwargs)
    size_mb = out_path.stat().st_size / 1e6
    print(f"Wrote {out_path}  ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
