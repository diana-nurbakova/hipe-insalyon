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
                    help="Fetch person birth/death via Wikidata SPARQL "
                         "(~20 req/s, ~1 min for 1,118 pairs).")
    ap.add_argument("--isat-window-days", type=int, default=14,
                    help="±N-day window for has_timex_in_isat_window (default 14, "
                         "matching dataset_reference.jsonl).")
    args = ap.parse_args()

    if not args.in_path.exists():
        raise SystemExit(f"--in not found: {args.in_path}")

    print(f"Enriching {args.in_path}")
    print(f"  use_heideltime  = {args.heideltime}")
    print(f"  use_wikidata    = {args.wikidata}")
    print(f"  isat_window     = {args.isat_window_days} days")

    t0 = time.perf_counter()
    n = enrich_official_jsonl(
        args.in_path,
        args.out_path,
        use_heideltime=args.heideltime,
        use_wikidata=args.wikidata,
        isat_window_days=args.isat_window_days,
    )
    elapsed = time.perf_counter() - t0
    print(f"\nDone: {n} pairs in {elapsed:.1f}s ({n/max(elapsed,1e-3):.1f}/s)")
    print(f"Wrote {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
