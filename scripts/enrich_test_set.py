"""Enrich an official-format test JSONL with Block-1 derived features.

See ``hipe.preprocessing.enrich`` and
``specs/HIPE2026_Pipeline_Specs_v4.md`` §2.3 for the derivation rules. The
output is a flat ``RelationInstance``-shaped JSONL ready for
``scripts/extract_mask_embeddings.py`` (so the feature blocks the RF / C4 LR
classifiers consume become non-zero).

Examples
--------
Default — fast Python-only path (regex signals + spaCy verbs + sentence
position). No Wikidata, no HeidelTime::

    uv run python scripts/enrich_test_set.py \\
        --in data/newspapers/v1.0/HIPE-2026-v1.0-test-all.jsonl \\
        --out data/newspapers/v1.0/HIPE-2026-v1.0-test-all_enriched.jsonl

Add Wikidata-derived person status (slow due to SPARQL rate-limiting,
~20 req/s; ~1 minute for the 1,118-pair test set)::

    uv run python scripts/enrich_test_set.py \\
        --in data/newspapers/v1.0/HIPE-2026-v1.0-test-all.jsonl \\
        --out data/newspapers/v1.0/HIPE-2026-v1.0-test-all_enriched.jsonl \\
        --wikidata

Add HeidelTime TIMEX3 extraction (requires Java + py-heideltime)::

    uv run python scripts/enrich_test_set.py \\
        --in data/newspapers/v1.0/HIPE-2026-v1.0-test-all.jsonl \\
        --out data/newspapers/v1.0/HIPE-2026-v1.0-test-all_enriched.jsonl \\
        --heideltime --wikidata
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from hipe.preprocessing import enrich_official_jsonl

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="in_path", required=True, type=Path,
                    help="Official nested JSONL (test or train).")
    ap.add_argument("--out", dest="out_path", required=True, type=Path,
                    help="Flat enriched JSONL output path.")
    ap.add_argument("--heideltime", action="store_true",
                    help="Run HeidelTime TIMEX3 extraction (needs Java + py-heideltime).")
    ap.add_argument("--wikidata", action="store_true",
                    help="Block-1 Wikidata: person birth/death -> temporal_person_status. "
                         "~1 SPARQL per unique person QID; SPARQL endpoint averages "
                         "0.5–2 req/s in practice.")
    ap.add_argument("--wikidata-full", action="store_true",
                    help="Block-2 Wikidata: also populate person_context, "
                         "location_context, known_person_location_relations, "
                         "person_location_match. Adds 1 SPARQL per unique location QID.")
    ap.add_argument("--retriever-dir", default=None,
                    help="Block-3 RAG: path to a built retrieval index "
                         "(e.g. runs/retriever_at_bgem3) for similar_examples.")
    ap.add_argument("--k-retrieved", type=int, default=5,
                    help="How many similar examples to retrieve per pair "
                         "when --retriever-dir is set.")
    ap.add_argument("--isat-window-days", type=int, default=14,
                    help="±N-day window for has_timex_in_isat_window (default 14, "
                         "matching dataset_reference.jsonl).")
    args = ap.parse_args()

    if not args.in_path.exists():
        raise SystemExit(f"--in not found: {args.in_path}")

    print(f"Enriching {args.in_path}")
    print(f"  use_heideltime    = {args.heideltime}")
    print(f"  use_wikidata      = {args.wikidata}  (Block-1 person status)")
    print(f"  use_wikidata_full = {args.wikidata_full}  (Block-2 person/location context)")
    print(f"  retriever_dir     = {args.retriever_dir}  (Block-3 similar_examples, k={args.k_retrieved})")
    print(f"  isat_window       = {args.isat_window_days} days")

    t0 = time.perf_counter()
    n = enrich_official_jsonl(
        args.in_path,
        args.out_path,
        use_heideltime=args.heideltime,
        use_wikidata=args.wikidata,
        use_wikidata_full=args.wikidata_full,
        isat_window_days=args.isat_window_days,
        retriever_dir=args.retriever_dir,
        k_retrieved=args.k_retrieved,
    )
    elapsed = time.perf_counter() - t0
    print(f"\nDone: {n} pairs in {elapsed:.1f}s ({n/max(elapsed,1e-3):.1f}/s)")
    print(f"Wrote {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
