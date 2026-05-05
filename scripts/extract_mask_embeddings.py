"""Extract MASK embeddings (mask + e1 + e2) over the full dataset.

Caches a single ``.npz`` containing the concatenated embedding matrices and
parallel metadata arrays so subsequent diagnostic / training runs don't pay
the encoding cost again. The cache schema includes:

  - ``mask_emb``         (N, H)        last-layer MASK mean (back-compat)
  - ``mask_emb_layers``  (N, L*H)      multi-layer concat per ``--layers``
  - ``e1_emb``, ``e2_emb`` (N, H)      last-layer span means
  - ``concat_emb``       (N, 3*H)      mask + e1 + e2 concatenation
  - ``temporal``         (N, 15)       handcrafted temporal vector
  - ``handcrafted``      (N, 36)       broader handcrafted feature vector
  - ``mask_at_emb`` / ``mask_isAt_emb`` (N, H)  — only for template M4
  - ``mask_multi_emb``   (N, 3*H)      — only for template M5

Usage:
    uv run python scripts/extract_mask_embeddings.py
    uv run python scripts/extract_mask_embeddings.py --template M2 --field context
    uv run python scripts/extract_mask_embeddings.py --template M3 --layers -1 -4 -7
    uv run python scripts/extract_mask_embeddings.py --model xlm-roberta-base \
        --max-seq-length 256 --batch-size 8
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

import orjson

from hipe.data import load_jsonl
from hipe.data.official import iter_official_instances
from hipe.features import handcrafted_matrix, temporal_matrix
from hipe.mask import MASKEncoder, MASKEncoderConfig
from hipe.mask.encoder import DEFAULT_MODEL, stack_embeddings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _slugify(model_name: str) -> str:
    return model_name.replace("/", "_").replace("-", "_")


def _default_out_path(model_name: str, template: str, layers: tuple[int, ...]) -> Path:
    slug = _slugify(model_name)
    layer_tag = "L" + "_".join(str(l) for l in layers) if layers != (-1,) else ""
    suffix = f"_{layer_tag}" if layer_tag else ""
    return PROJECT_ROOT / "runs" / f"mask_{slug}_{template}{suffix}.npz"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--template", choices=["M1", "M2", "M3", "M4", "M5"], default="M2")
    ap.add_argument("--field", choices=["context", "text"], default="context")
    ap.add_argument("--max-seq-length", type=int, default=256)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--device", default=None, help="cuda / cpu / mps. Default: auto.")
    ap.add_argument(
        "--layers",
        type=int,
        nargs="+",
        default=[-1],
        help=("Hidden-layer indices to extract MASK embeddings from (negative "
              "values index from the end). Pass e.g. '-1 -4 -7' for the spec's "
              "12/9/6 multi-layer setup."),
    )
    ap.add_argument("--out", default=None,
                    help="Output .npz path. Default: runs/mask_<model>_<template>[_L...].npz")
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl}")
    # Auto-detect official nested format vs the flat dataset_reference.jsonl
    # by peeking at the first non-empty line. Nested official files carry a
    # top-level ``sampled_pairs`` array; the flat format is one row per pair.
    nested = False
    with Path(args.jsonl).open("rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            head = orjson.loads(raw)
            nested = "sampled_pairs" in head and "pers_entity_id" not in head
            break
    if nested:
        print("  detected official nested format (sampled_pairs); flattening to RelationInstance")
        instances = list(iter_official_instances(args.jsonl))
    else:
        instances = load_jsonl(args.jsonl)
    print(f"  {len(instances)} instances")

    layers_tuple = tuple(args.layers)
    print(
        f"Loading encoder {args.model} (template={args.template}, "
        f"field={args.field}, layers={layers_tuple})"
    )
    cfg = MASKEncoderConfig(
        model_name=args.model,
        template=args.template,
        field=args.field,
        max_seq_length=args.max_seq_length,
        batch_size=args.batch_size,
        device=args.device,
        layers=layers_tuple,
    )
    t0 = time.perf_counter()
    encoder = MASKEncoder(cfg)
    print(f"  loaded in {time.perf_counter() - t0:.1f}s; "
          f"hidden_size={encoder.hidden_size}; n_layers={encoder.n_layers_total}; "
          f"device={encoder.device}")

    print(f"Encoding {len(instances)} instances ...")
    t0 = time.perf_counter()
    batches = encoder.encode_instances(instances, progress=True)
    elapsed = time.perf_counter() - t0
    print(f"  done in {elapsed:.1f}s ({1000*elapsed/len(instances):.0f} ms/instance)")

    arr = stack_embeddings(batches)
    pers_in = int(arr["pers_in_context"].sum())
    loc_in = int(arr["loc_in_context"].sum())
    print(f"  pers_in_context: {pers_in}/{len(instances)} ({100*pers_in/len(instances):.1f}%)")
    print(f"  loc_in_context : {loc_in}/{len(instances)} ({100*loc_in/len(instances):.1f}%)")
    print(f"  mask_emb shape          : {arr['mask_emb'].shape}")
    print(f"  mask_emb_layers shape   : {arr['mask_emb_layers'].shape}")
    if "mask_at_emb" in arr:
        print(f"  mask_at_emb shape       : {arr['mask_at_emb'].shape}")
        print(f"  mask_isAt_emb shape     : {arr['mask_isAt_emb'].shape}")
    if "mask_multi_emb" in arr:
        print(f"  mask_multi_emb shape    : {arr['mask_multi_emb'].shape}")

    print("Computing handcrafted feature matrices ...")
    temp = temporal_matrix(instances)
    hand = handcrafted_matrix(instances)
    print(f"  temporal feature shape    : {temp.shape}")
    print(f"  handcrafted feature shape : {hand.shape}")

    if args.out is None:
        out = _default_out_path(args.model, args.template, layers_tuple)
    else:
        out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    save_kwargs: dict = {
        "mask_emb": arr["mask_emb"],
        "mask_emb_layers": arr["mask_emb_layers"],
        "e1_emb": arr["e1_emb"],
        "e2_emb": arr["e2_emb"],
        "concat_emb": arr["concat_emb"],
        "sample_id": np.asarray(arr["sample_id"]),
        "language": np.asarray(arr["language"]),
        "at": np.asarray(arr["at"]),
        "isAt": np.asarray(arr["isAt"]),
        "pers_in_context": arr["pers_in_context"],
        "loc_in_context": arr["loc_in_context"],
        "temporal": temp,
        "handcrafted": hand,
        # Pin the recipe so the eval grid can introspect each cache.
        "_meta_model": np.asarray(args.model),
        "_meta_template": np.asarray(args.template),
        "_meta_field": np.asarray(args.field),
        "_meta_layers": np.asarray(layers_tuple),
    }
    if "mask_at_emb" in arr:
        save_kwargs["mask_at_emb"] = arr["mask_at_emb"]
        save_kwargs["mask_isAt_emb"] = arr["mask_isAt_emb"]
    if "mask_multi_emb" in arr:
        save_kwargs["mask_multi_emb"] = arr["mask_multi_emb"]

    np.savez(out, **save_kwargs)
    print(f"Saved to {out}  ({out.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
