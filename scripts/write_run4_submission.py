"""Write Run-4 (and optional Run-5) official-test submissions.

Run-4: at = mDeBERTa, isAt = majority(xlm-roberta, Gemma, Llama-3.3-70b)
  - The at predictions come from the user's mDeBERTa fine-tune (submission_3).
    Validated MR(at) on the 188-triplet val split: 0.6189.
  - The isAt vote uses the existing xlm-roberta isAt (submission_3) plus Gemma
    full-dataset and Llama-3.3-70b PAB on the official test. Validated on v1
    isAt-test: MR(isAt)=0.8411 vs Gemma alone 0.8273 (+0.014).

Run-5 (optional, --include-run5): at = existing 4-model-stacker, isAt = same.
  - On the dev set the 4-model-stacker scores MR(at)~0.73 vs mDeBERTa~0.62.
    Run-5 prioritises score; Run-4 prioritises team-narrative coherence.

Inputs (all 1118-pair aligned by (doc, pers, loc)):
  - mDeBERTa at + xlm-roberta isAt: runs/materials/submission_3_*/HIPE-2026-v1.0-*.jsonl
  - 4-model stacker at + Gemma isAt: submissions/4-model-stacker/INSALyon_*_run1.jsonl
  - Gemma isAt: logs/official_test/gemma4_31b_PAB_official_test_predictions.jsonl
  - Llama isAt: logs/official_test/llama_33_70b_PAB_official_test_predictions.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LANG_FILES = [
    ("de", "HIPE-2026-v1.0-impresso-test-de"),
    ("en", "HIPE-2026-v1.0-impresso-test-en"),
    ("fr", "HIPE-2026-v1.0-impresso-test-fr"),
    ("surprise-fr", "HIPE-2026-v1.0-surprise-test-fr"),
]

STACKER_DIR = REPO / "submissions/4-model-stacker"
XLM_DIR = REPO / "runs/materials/submission_3_official_test_mdeberta_at_roberta_isAt"
XLM_AT_DIR = REPO / "runs/submission_xmlroberta_at_isAt/submission_roberta_at_isAt"
GEMMA = REPO / "logs/official_test/gemma4_31b_PAB_official_test_predictions.jsonl"
LLAMA = REPO / "logs/official_test/llama_33_70b_PAB_official_test_predictions.jsonl"


# ordinal map for at-task plurality tiebreaker (FALSE < PROBABLE < TRUE)
AT_ORDINAL_MAP = {"FALSE": 0, "PROBABLE": 1, "TRUE": 2}


def load_xlm_at_official() -> dict[tuple, str]:
    """Load xlm-roberta at predictions from the official-test submission folder."""
    out = {}
    for _, base in LANG_FILES:
        path = XLM_AT_DIR / f"{base}.jsonl"
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                for p in d.get("sampled_pairs", []):
                    k = (d["document_id"], p["pers_entity_id"], p["loc_entity_id"])
                    out[k] = p.get("at")
    return out


def load_stacker_at() -> dict[tuple, str]:
    """Load 4-model-stacker at predictions from the existing submission folder."""
    out = {}
    for _, base in LANG_FILES:
        path = STACKER_DIR / f"INSALyon_{base}_run1.jsonl"
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                for p in d.get("sampled_pairs", []):
                    k = (d["document_id"], p["pers_entity_id"], p["loc_entity_id"])
                    out[k] = p.get("at")
    return out


def load_gemma_at() -> dict[tuple, str]:
    out = {}
    with GEMMA.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])
            v = d.get("at_predicted")
            if v in ("TRUE", "PROBABLE", "FALSE"):
                out[k] = v
    return out


def plurality_at(votes: list[str]) -> str:
    """3-class plurality with ordinal_median tiebreaker."""
    cnt = Counter(votes)
    top = max(cnt.values())
    winners = [l for l, n in cnt.items() if n == top]
    if len(winners) == 1:
        return winners[0]
    ords = sorted(AT_ORDINAL_MAP[v] for v in votes if v in AT_ORDINAL_MAP)
    if not ords:
        return "FALSE"
    median_ord = ords[len(ords) // 2]
    inv = {v: k for k, v in AT_ORDINAL_MAP.items()}
    cand = inv.get(median_ord)
    if cand in winners:
        return cand
    return sorted(winners)[0]


def load_partner_isat(path: Path) -> dict[tuple, str]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])
            v = d.get("isAt_predicted")
            if v in ("TRUE", "FALSE"):
                out[k] = v
    return out


def load_xlm_isat() -> dict[tuple, str]:
    out = {}
    for _, base in LANG_FILES:
        path = XLM_DIR / f"{base}.jsonl"
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                for p in d.get("sampled_pairs", []):
                    k = (d["document_id"], p["pers_entity_id"], p["loc_entity_id"])
                    out[k] = p.get("isAt")
    return out


def majority_isat(votes: list[str]) -> str:
    """3-way binary majority — TRUE iff strictly more than half are TRUE."""
    n_t = sum(1 for v in votes if v == "TRUE")
    return "TRUE" if n_t * 2 > len(votes) else "FALSE"


def write_one_run(*, out_dir: Path, name_prefix: str, run_tag: str,
                   at_source_dir: Path, at_source_pattern: str,
                   new_isat: dict[tuple, str]) -> dict:
    """Walk each language file from `at_source_dir`, replace isAt, write to out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {"per_file_at": {}, "per_file_isat": {}, "n_pairs": 0,
               "n_isat_changed": 0}
    for tag, base in LANG_FILES:
        in_path = at_source_dir / at_source_pattern.format(base=base)
        if not in_path.exists():
            raise SystemExit(f"  missing input file: {in_path}")
        out_path = out_dir / f"{name_prefix}_{base}_{run_tag}.jsonl"
        cnt_at = Counter()
        cnt_isat = Counter()
        with in_path.open("r", encoding="utf-8") as fin, \
             out_path.open("w", encoding="utf-8") as fout:
            for line in fin:
                doc = json.loads(line)
                doc_id = doc["document_id"]
                for pair in doc.get("sampled_pairs", []):
                    k = (doc_id, pair["pers_entity_id"], pair["loc_entity_id"])
                    old = pair.get("isAt")
                    new = new_isat.get(k, "FALSE")
                    if new != old:
                        summary["n_isat_changed"] += 1
                    pair["isAt"] = new
                    pair["isAt_explanation"] = "majority(xlm-roberta, Gemma, Llama-3.3-70b)"
                    cnt_at[pair.get("at")] += 1
                    cnt_isat[new] += 1
                    summary["n_pairs"] += 1
                fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
        summary["per_file_at"][base] = dict(cnt_at)
        summary["per_file_isat"][base] = dict(cnt_isat)
        print(f"  wrote {out_path}")
    return summary


def write_run6(*, out_dir: Path, name_prefix: str, run_tag: str,
                xlm_at: dict[tuple, str], stacker_at: dict[tuple, str],
                gemma_at: dict[tuple, str], new_isat: dict[tuple, str]) -> dict:
    """Run-6: at = plurality(xlm, stacker, gemma); isAt = majority isAt.

    Walks the structure of submission_3 (mDeBERTa at + xlm isAt) but replaces
    BOTH the at field (with the 3-way plurality) and the isAt field (with the
    3-way majority).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {"per_file_at": {}, "per_file_isat": {}, "n_pairs": 0,
               "n_at_changed": 0, "n_isat_changed": 0,
               "at_provenance": Counter()}
    for tag, base in LANG_FILES:
        in_path = XLM_DIR / f"{base}.jsonl"
        out_path = out_dir / f"{name_prefix}_{base}_{run_tag}.jsonl"
        cnt_at = Counter()
        cnt_isat = Counter()
        with in_path.open("r", encoding="utf-8") as fin, \
             out_path.open("w", encoding="utf-8") as fout:
            for line in fin:
                doc = json.loads(line)
                doc_id = doc["document_id"]
                for pair in doc.get("sampled_pairs", []):
                    k = (doc_id, pair["pers_entity_id"], pair["loc_entity_id"])
                    old_at = pair.get("at")
                    votes = []
                    for v in (xlm_at.get(k), stacker_at.get(k), gemma_at.get(k)):
                        if v in ("TRUE", "PROBABLE", "FALSE"):
                            votes.append(v)
                    new_at = plurality_at(votes) if votes else "FALSE"
                    if new_at != old_at:
                        summary["n_at_changed"] += 1
                    pair["at"] = new_at
                    pair["at_explanation"] = "plurality(xlm-roberta, 4-model-stacker, Gemma) tb=ordinal_median"
                    new_isat_v = new_isat.get(k, "FALSE")
                    if new_isat_v != pair.get("isAt"):
                        summary["n_isat_changed"] += 1
                    pair["isAt"] = new_isat_v
                    pair["isAt_explanation"] = "majority(xlm-roberta, Gemma, Llama-3.3-70b)"
                    cnt_at[new_at] += 1
                    cnt_isat[new_isat_v] += 1
                    summary["n_pairs"] += 1
                    # Track which model the at vote came from for provenance.
                    summary["at_provenance"][
                        ("xlm" if xlm_at.get(k) == new_at else "")
                        + ("st" if stacker_at.get(k) == new_at else "")
                        + ("gm" if gemma_at.get(k) == new_at else "")
                    ] += 1
                fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
        summary["per_file_at"][base] = dict(cnt_at)
        summary["per_file_isat"][base] = dict(cnt_isat)
        print(f"  wrote {out_path}")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=REPO / "submissions")
    ap.add_argument("--name-prefix", default="INSALyon")
    ap.add_argument("--include-run5", action="store_true",
                    help="Also produce Run-5 = 4-model-stacker at + majority isAt.")
    ap.add_argument("--include-run6", action="store_true",
                    help="Also produce Run-6 = plurality(xlm, stacker, gemma) at + majority isAt.")
    args = ap.parse_args()

    print("Loading partner isAt predictions...")
    xlm = load_xlm_isat()
    gemma = load_partner_isat(GEMMA)
    llama = load_partner_isat(LLAMA)
    print(f"  xlm-roberta:  {len(xlm)} pairs ({dict(Counter(xlm.values()))})")
    print(f"  Gemma:        {len(gemma)} pairs ({dict(Counter(gemma.values()))})")
    print(f"  Llama-3.3-70b: {len(llama)} pairs ({dict(Counter(llama.values()))})")

    # Per-pair isAt majority over (xlm, gemma, llama)
    new_isat: dict[tuple, str] = {}
    n_overrides_xlm = 0
    n_overrides_gemma = 0
    keys = set(xlm) | set(gemma) | set(llama)
    for k in keys:
        votes = []
        for src in (xlm, gemma, llama):
            v = src.get(k)
            if v is not None:
                votes.append(v)
        if not votes:
            new_isat[k] = "FALSE"
            continue
        new_isat[k] = majority_isat(votes)
        if k in xlm and xlm[k] != new_isat[k]:
            n_overrides_xlm += 1
        if k in gemma and gemma[k] != new_isat[k]:
            n_overrides_gemma += 1
    print(f"  majority flips xlm vote on  {n_overrides_xlm} pairs")
    print(f"  majority flips gemma vote on {n_overrides_gemma} pairs")
    print()

    # ----- Run-4: mDeBERTa at + majority isAt -----------------------------
    print("=" * 78)
    print("Run-4: at = mDeBERTa, isAt = majority(xlm-roberta, Gemma, Llama)")
    print("=" * 78)
    s4 = write_one_run(
        out_dir=args.out_dir / "run4",
        name_prefix=args.name_prefix,
        run_tag="run4",
        at_source_dir=XLM_DIR,  # submission_3 — has mDeBERTa at + xlm isAt
        at_source_pattern="{base}.jsonl",
        new_isat=new_isat,
    )
    print(f"\n  Total pairs: {s4['n_pairs']}")
    print(f"  isAt changes vs xlm-only baseline: {s4['n_isat_changed']}")
    print(f"  Per-file at distribution (mDeBERTa, unchanged):")
    for base, cnt in s4["per_file_at"].items():
        print(f"    {base}: {cnt}")
    print(f"  Per-file isAt distribution (majority):")
    for base, cnt in s4["per_file_isat"].items():
        print(f"    {base}: {cnt}")

    # ----- Optional Run-6: plurality(xlm, stacker, gemma) at + majority isAt
    if args.include_run6:
        print()
        print("=" * 78)
        print("Run-6: at = plurality(xlm-roberta, 4-model-stacker, Gemma)")
        print("       isAt = majority(xlm-roberta, Gemma, Llama-3.3-70b)")
        print("=" * 78)
        xlm_at = load_xlm_at_official()
        stacker_at = load_stacker_at()
        gemma_at = load_gemma_at()
        print(f"  xlm-roberta at:    {len(xlm_at)} pairs ({dict(Counter(xlm_at.values()))})")
        print(f"  4-model-stacker at: {len(stacker_at)} pairs ({dict(Counter(stacker_at.values()))})")
        print(f"  Gemma at:          {len(gemma_at)} pairs ({dict(Counter(gemma_at.values()))})")
        s6 = write_run6(
            out_dir=args.out_dir / "run6",
            name_prefix=args.name_prefix, run_tag="run6",
            xlm_at=xlm_at, stacker_at=stacker_at, gemma_at=gemma_at,
            new_isat=new_isat,
        )
        print(f"\n  Total pairs: {s6['n_pairs']}")
        print(f"  at changes vs xlm-only baseline:   {s6['n_at_changed']}")
        print(f"  isAt changes vs xlm-only baseline: {s6['n_isat_changed']}")
        print(f"  Per-file at distribution (3-way plurality):")
        for base, cnt in s6["per_file_at"].items():
            print(f"    {base}: {cnt}")
        print(f"  at provenance (which models' votes survive):")
        for prov, n in s6["at_provenance"].most_common():
            print(f"    {prov!r}: {n}")

    # ----- Optional Run-5: 4-model-stacker at + majority isAt -------------
    if args.include_run5:
        print()
        print("=" * 78)
        print("Run-5: at = 4-model-stacker, isAt = majority(xlm-roberta, Gemma, Llama)")
        print("=" * 78)
        s5 = write_one_run(
            out_dir=args.out_dir / "run5",
            name_prefix=args.name_prefix,
            run_tag="run5",
            at_source_dir=STACKER_DIR,
            at_source_pattern=f"{args.name_prefix}_{{base}}_run1.jsonl",
            new_isat=new_isat,
        )
        print(f"\n  Total pairs: {s5['n_pairs']}")
        print(f"  isAt changes vs 4-model-stacker baseline: {s5['n_isat_changed']}")
        print(f"  Per-file at distribution (4-model-stacker, unchanged):")
        for base, cnt in s5["per_file_at"].items():
            print(f"    {base}: {cnt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
