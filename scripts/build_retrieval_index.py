"""Build a RAG retrieval index over the baseline train split.

The index stores entity-aware sentence embeddings of training instances so
the classifier agent can fetch similar examples at inference time.

Per HIPE-2026 Pipeline Spec §3 and §13.1, the validation/test partition
must NEVER be indexed. This script honours that by reading the baseline
split CSV and indexing only rows assigned to ``split == 'train'``.

Usage:
    uv run python scripts/build_retrieval_index.py
    uv run python scripts/build_retrieval_index.py --model BAAI/bge-m3
    uv run python scripts/build_retrieval_index.py --model intfloat/multilingual-e5-small
    uv run python scripts/build_retrieval_index.py --task isAt --out-dir runs/retriever_isAt
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from hipe.data import load_baseline_split, load_jsonl
from hipe.retriever import EntityAwareEncoder, FaissIndex
from hipe.retriever.embed import EncoderConfig, DEFAULT_MODEL
from hipe.retriever.retrieve import instance_to_metadata

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--task", choices=["at", "isAt"], default="at",
                    help="Which baseline split to use (the train partition is task-specific).")
    ap.add_argument("--field", choices=["context", "text"], default="context",
                    help="Which text field to embed (default: context).")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--max-seq-length", type=int, default=None,
                    help="Override the model's default max_seq_length.")
    ap.add_argument("--device", default=None, help="cuda / cpu / mps. Default: auto.")
    ap.add_argument("--out-dir", default=str(PROJECT_ROOT / "runs" / "retriever_at"),
                    help="Directory to write index.faiss + metadata.jsonl")
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl} ...")
    instances = load_jsonl(args.jsonl)
    print(f"  {len(instances)} instances loaded")

    sp = load_baseline_split(instances, task=args.task)
    print(f"  baseline split (task={args.task}): train={len(sp.train)} test={len(sp.test)}")

    print(f"Loading encoder {args.model} (this can take a few minutes on first run) ...")
    cfg = EncoderConfig(
        model_name=args.model,
        field=args.field,
        batch_size=args.batch_size,
        max_seq_length=args.max_seq_length,
        device=args.device,
    )
    t0 = time.perf_counter()
    encoder = EntityAwareEncoder(cfg)
    print(f"  loaded in {time.perf_counter() - t0:.1f}s; embedding dim = {encoder.dim}")

    print(f"Embedding {len(sp.train)} training instances ...")
    t0 = time.perf_counter()
    embeddings = encoder.encode_instances(sp.train, show_progress_bar=True)
    elapsed = time.perf_counter() - t0
    print(f"  embeddings shape = {embeddings.shape}, took {elapsed:.1f}s "
          f"({1000*elapsed/len(sp.train):.0f} ms / instance)")

    print("Building FAISS index ...")
    metadata = [instance_to_metadata(inst) for inst in sp.train]
    index = FaissIndex.build(embeddings, metadata)
    print(f"  index size = {len(index)}, dim = {index.dim}")

    out_dir = Path(args.out_dir)
    print(f"Saving index to {out_dir} ...")
    index.save(out_dir)
    config_path = out_dir / "build_config.json"
    import json
    config_path.write_text(json.dumps({
        "model": args.model,
        "field": args.field,
        "task": args.task,
        "n_instances": len(sp.train),
        "dim": index.dim,
        "max_seq_length": args.max_seq_length,
        "batch_size": args.batch_size,
    }, indent=2))
    print(f"  wrote build config -> {config_path}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
