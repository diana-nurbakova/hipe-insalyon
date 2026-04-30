"""Sweep MASK extraction across (template × encoder) cells.

Wraps :mod:`scripts.extract_mask_embeddings` so each cell produces a
self-contained ``runs/mask_<encoder>_<template>[_L...].npz`` cache. Reuses
existing caches by default (skip when ``--force`` is not set), so the script
is safe to re-run after a partial failure.

Examples:
    # Default: all 5 templates on hmBERT, last layer only
    uv run python scripts/run_mask_template_encoder_grid.py

    # Multi-layer extraction on hmBERT for all templates (spec §8.7)
    uv run python scripts/run_mask_template_encoder_grid.py \\
        --layers -1 -4 -7

    # Two encoders × M2 only (apples-to-apples encoder comparison)
    uv run python scripts/run_mask_template_encoder_grid.py \\
        --templates M2 \\
        --encoders dbmdz/bert-base-historic-multilingual-cased xlm-roberta-base

    # Spec §7.2 Phase-1 grid: all templates × hmBERT, plus M2 × {XLM-R-base, mGTE}
    uv run python scripts/run_mask_template_encoder_grid.py \\
        --templates M1 M2 M3 M4 M5 \\
        --encoders dbmdz/bert-base-historic-multilingual-cased
    uv run python scripts/run_mask_template_encoder_grid.py \\
        --templates M2 \\
        --encoders xlm-roberta-base Alibaba-NLP/gte-multilingual-base
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def _slugify(model_name: str) -> str:
    return model_name.replace("/", "_").replace("-", "_")


def _cache_path(model: str, template: str, layers: tuple[int, ...]) -> Path:
    layer_tag = "L" + "_".join(str(l) for l in layers) if layers != (-1,) else ""
    suffix = f"_{layer_tag}" if layer_tag else ""
    return PROJECT_ROOT / "runs" / f"mask_{_slugify(model)}_{template}{suffix}.npz"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument(
        "--templates",
        nargs="+",
        default=["M1", "M2", "M3", "M4", "M5"],
        help="Templates to extract (default: all five).",
    )
    ap.add_argument(
        "--encoders",
        nargs="+",
        default=["dbmdz/bert-base-historic-multilingual-cased"],
        help=("Encoder model names (HuggingFace IDs). Pass multiple to compare. "
              "Heavy options: 'xlm-roberta-large', 'Alibaba-NLP/gte-multilingual-base'."),
    )
    ap.add_argument("--field", choices=["context", "text"], default="context")
    ap.add_argument("--max-seq-length", type=int, default=256)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--device", default=None)
    ap.add_argument(
        "--layers",
        type=int,
        nargs="+",
        default=[-1],
        help="Hidden-layer indices to extract from (default: -1 = last layer only).",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Re-extract even if the .npz cache already exists.",
    )
    ap.add_argument(
        "--summary-out",
        default=str(PROJECT_ROOT / "runs" / "mask_grid_extraction_summary.json"),
    )
    args = ap.parse_args()

    layers = tuple(args.layers)
    cells: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []

    # Import here so --help works without torch installed.
    from hipe.data import load_jsonl
    from hipe.features import handcrafted_matrix, temporal_matrix
    from hipe.mask import MASKEncoder, MASKEncoderConfig
    from hipe.mask.encoder import stack_embeddings
    import numpy as np

    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    print(f"  {len(instances)} instances")

    # Pre-compute the feature matrices once: they don't depend on the encoder.
    print("Pre-computing handcrafted + temporal feature matrices ...")
    temp_matrix = temporal_matrix(instances)
    hand_matrix = handcrafted_matrix(instances)

    grid = [(enc, tpl) for enc in args.encoders for tpl in args.templates]
    print(f"\nGrid: {len(grid)} cells "
          f"({len(args.encoders)} encoder(s) × {len(args.templates)} template(s))")

    t_start = time.perf_counter()
    for cell_idx, (encoder_name, template) in enumerate(grid, start=1):
        out_path = _cache_path(encoder_name, template, layers)
        cell_meta = {
            "encoder": encoder_name,
            "template": template,
            "layers": list(layers),
            "out": str(out_path),
        }
        if out_path.exists() and not args.force:
            size_mb = out_path.stat().st_size / 1e6
            print(f"\n[{cell_idx}/{len(grid)}] SKIP {encoder_name} × {template}  "
                  f"(cache exists, {size_mb:.1f} MB)")
            cell_meta["status"] = "skipped"
            cell_meta["size_mb"] = size_mb
            skipped.append(cell_meta)
            continue

        print(
            f"\n[{cell_idx}/{len(grid)}] EXTRACT  encoder={encoder_name}  "
            f"template={template}  layers={layers}"
        )
        cfg = MASKEncoderConfig(
            model_name=encoder_name,
            template=template,
            field=args.field,
            max_seq_length=args.max_seq_length,
            batch_size=args.batch_size,
            device=args.device,
            layers=layers,
        )
        try:
            t0 = time.perf_counter()
            encoder = MASKEncoder(cfg)
            print(f"  loaded encoder in {time.perf_counter() - t0:.1f}s; "
                  f"hidden_size={encoder.hidden_size}; device={encoder.device}")
            t0 = time.perf_counter()
            batches = encoder.encode_instances(instances, progress=True)
            extract_seconds = time.perf_counter() - t0
            print(f"  extraction took {extract_seconds:.1f}s "
                  f"({1000*extract_seconds/len(instances):.0f} ms/instance)")

            arr = stack_embeddings(batches)
            save_kwargs = {
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
                "temporal": temp_matrix,
                "handcrafted": hand_matrix,
                "_meta_model": np.asarray(encoder_name),
                "_meta_template": np.asarray(template),
                "_meta_field": np.asarray(args.field),
                "_meta_layers": np.asarray(layers),
            }
            if "mask_at_emb" in arr:
                save_kwargs["mask_at_emb"] = arr["mask_at_emb"]
                save_kwargs["mask_isAt_emb"] = arr["mask_isAt_emb"]
            if "mask_multi_emb" in arr:
                save_kwargs["mask_multi_emb"] = arr["mask_multi_emb"]

            out_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez(out_path, **save_kwargs)
            size_mb = out_path.stat().st_size / 1e6
            print(f"  wrote {out_path}  ({size_mb:.1f} MB)")

            cell_meta.update({
                "status": "ok",
                "extract_seconds": extract_seconds,
                "hidden_size": encoder.hidden_size,
                "size_mb": size_mb,
                "n_instances": len(instances),
                "has_dual_mask": "mask_at_emb" in arr,
                "has_multi_mask": "mask_multi_emb" in arr,
            })
            cells.append(cell_meta)

            # Free the encoder so multi-cell sweeps don't OOM.
            del encoder, batches, arr
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

        except Exception as exc:  # noqa: BLE001 — sweep should keep going on a single failure
            print(f"  FAILED on {encoder_name} × {template}: {exc!r}")
            cell_meta["status"] = "failed"
            cell_meta["error"] = repr(exc)
            failed.append(cell_meta)

    elapsed = time.perf_counter() - t_start
    summary = {
        "elapsed_seconds": elapsed,
        "n_total": len(grid),
        "n_ok": len(cells),
        "n_skipped": len(skipped),
        "n_failed": len(failed),
        "args": vars(args),
        "ok": cells,
        "skipped": skipped,
        "failed": failed,
    }
    out_summary = Path(args.summary_out)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(f"\nGrid done in {elapsed/60:.1f} min — "
          f"ok={len(cells)} skipped={len(skipped)} failed={len(failed)}")
    print(f"Summary: {out_summary}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
