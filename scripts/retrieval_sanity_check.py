"""Sanity-check the retrieval index by querying random test instances.

For each query, prints the gold (at, isAt) labels and the top-K nearest
neighbors from the train pool with their labels and contexts. Eyeball
whether the retrieved examples look semantically related.

Usage:
    uv run python scripts/retrieval_sanity_check.py
    uv run python scripts/retrieval_sanity_check.py --index-dir runs/retriever_at_bgem3
    uv run python scripts/retrieval_sanity_check.py --k 5 --n-queries 5 --diversify
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from hipe.data import load_baseline_split, load_jsonl
from hipe.retriever import Retriever

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"))
    ap.add_argument("--index-dir", default=str(PROJECT_ROOT / "runs" / "retriever_at_bgem3"))
    ap.add_argument("--task", choices=["at", "isAt"], default="at")
    ap.add_argument("--n-queries", type=int, default=3)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--diversify", action="store_true",
                    help="Diversify retrieved examples across (at, isAt) labels.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    print(f"Loading dataset {args.jsonl}")
    instances = load_jsonl(args.jsonl)
    sp = load_baseline_split(instances, task=args.task)
    print(f"  test pool size: {len(sp.test)}")

    print(f"Loading retriever from {args.index_dir}")
    retriever = Retriever.from_disk(args.index_dir, device=args.device)
    print(f"  index size = {len(retriever.index)}, dim = {retriever.index.dim}")
    print(f"  encoder model = {retriever.encoder.config.model_name}")

    rng = random.Random(args.seed)
    queries = rng.sample(sp.test, k=min(args.n_queries, len(sp.test)))

    for qi, q in enumerate(queries):
        print("\n" + "=" * 80)
        print(f"QUERY {qi+1}/{len(queries)}  sample_id={q.sample_id}")
        print(f"  language    : {q.language}")
        print(f"  date        : {q.date}")
        print(f"  person      : {(q.pers_mentions_list or [''])[0]!r}  qid={q.pers_wikidata_QID}")
        print(f"  location    : {(q.loc_mentions_list or [''])[0]!r}  qid={q.loc_wikidata_QID}")
        print(f"  GOLD at     : {q.at}")
        print(f"  GOLD isAt   : {q.isAt}")
        ctx = (q.context or "").replace("\n", " ")
        print(f"  context     : {ctx[:240]}{'...' if len(ctx) > 240 else ''}")

        results = retriever.search(
            q,
            k=args.k,
            prefer_language="auto",
            diversify_labels=args.diversify,
        )
        print(f"\n  top-{args.k} neighbours (lang preference: {q.language}):")
        for r in results:
            ctx = (r.metadata.get("context", "") or "").replace("\n", " ")
            print(f"    score={r.score:.3f}  rank={r.rank}  lang={r.language:2s}  "
                  f"at={str(r.at):<8s} isAt={str(r.isAt):<5s}")
            print(f"      {(r.metadata.get('pers_mention') or '?')!r} <-> "
                  f"{(r.metadata.get('loc_mention') or '?')!r}")
            print(f"      ctx: {ctx[:180]}{'...' if len(ctx) > 180 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
