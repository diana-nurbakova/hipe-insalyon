"""Write an isAt-only submission using ambiguity-routed mDeBERTa + ensemble.

For each official-test pair we have isAt predictions from:
  - mDeBERTa-v3 fine-tuned (with margin/entropy from predict_confidence.csv)
  - Gemma-4-31b PAB
  - Llama-3.3-70b PAB
  - C4 LR (mask + e1 + e2 + temporal)
  - OrdContM1 contrastive (optional 5th model)

Strategy validated on v1 isAt-test (n=187):
  - Compute mDeBERTa ambiguity = norm_entropy * (1 - margin); margin = |p_T - p_F|.
  - Sort by ambiguity descending; route the top X% (default 30%) to a fallback
    majority vote over the other models. Below-threshold items keep mDeBERTa.

Default fallback: majority(Gemma, Llama, C4). Optionally include OrdContM1.

The output preserves the input mDeBERTa submission JSONLs verbatim except the
`isAt` field on each pair (and `isAt_explanation` is set to a routing tag so we
can audit which prediction came from where).

Usage::

    uv run python scripts/write_isat_ambig_submission.py \\
        --top-pct 0.30 \\
        --include-ord \\
        --out-dir submissions/ambig-route-isAt
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LANG_FILES = [
    "HIPE-2026-v1.0-impresso-test-de.jsonl",
    "HIPE-2026-v1.0-impresso-test-en.jsonl",
    "HIPE-2026-v1.0-impresso-test-fr.jsonl",
    "HIPE-2026-v1.0-surprise-test-fr.jsonl",
]

MD_SUBMISSION_DIR = REPO / "runs/runs_mdeberta/runs/run_2_test_submission"
MD_OUTPUTS_DIR = REPO / "runs/test_outputs_mdeberta"
GEMMA_OFFICIAL = REPO / "logs/official_test/gemma4_31b_PAB_official_test_predictions.jsonl"
LLAMA_OFFICIAL = REPO / "logs/official_test/llama_33_70b_PAB_official_test_predictions.jsonl"
C4_OFFICIAL = REPO / "logs/official_test/C4_official_test_isAt_predictions.jsonl"
ORD_OFFICIAL = REPO / "logs/official_test/OrdContM1_official_test_at_predictions.jsonl"


def _md_outputs_subdir(jsonl_name: str) -> str:
    if "surprise-test-fr" in jsonl_name:
        return "output_surprise_test_fr"
    if "test-de" in jsonl_name:
        return "output_test_de"
    if "test-en" in jsonl_name:
        return "output_test_en"
    if "test-fr" in jsonl_name:
        return "output_test_fr"
    raise ValueError(f"unknown jsonl name {jsonl_name}")


def load_md_confidence(jsonl_name: str) -> dict[tuple, dict]:
    """Load mDeBERTa isAt predict_confidence.csv for one language file."""
    sub = _md_outputs_subdir(jsonl_name)
    path = MD_OUTPUTS_DIR / sub / "isAt" / "predict_confidence.csv"
    out: dict[tuple, dict] = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            pT = float(r["prob_TRUE"])
            pF = float(r["prob_FALSE"])
            margin = abs(pT - pF)
            # entropy of binary distribution (in nats)
            entropy = 0.0
            for p in (pT, pF):
                if p > 1e-9:
                    entropy -= p * math.log(p)
            norm_ent = entropy / math.log(2)
            ambig = norm_ent * (1.0 - margin)
            out[k] = {
                "pred": r["pred_label"],
                "conf": float(r["confidence"]),
                "margin": margin,
                "norm_entropy": norm_ent,
                "ambiguity": ambig,
                "prob_TRUE": pT,
                "prob_FALSE": pF,
            }
    return out


def load_jsonl_isat(path: Path, field: str = "isAt_predicted") -> dict[tuple, str | None]:
    out: dict[tuple, str | None] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])
            out[k] = d.get(field)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top-pct", type=float, default=0.30,
                    help="Fraction of most-ambiguous mDeBERTa items to route. Default 0.30.")
    ap.add_argument("--include-ord", action="store_true",
                    help="Add OrdContM1 to the fallback majority (4-way: gm, ll, c4, ord).")
    ap.add_argument("--out-dir", type=Path,
                    default=REPO / "submissions" / "ambig-route-isAt",
                    help="Where to write the per-language submission JSONLs.")
    ap.add_argument("--rule-tag", default="amb30",
                    help="Tag written into isAt_explanation for routed items.")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Load partner predictions (cover all 1118 official test pairs)
    print(f"Loading partner predictions...")
    gemma = load_jsonl_isat(GEMMA_OFFICIAL)
    llama = load_jsonl_isat(LLAMA_OFFICIAL)
    c4 = load_jsonl_isat(C4_OFFICIAL)
    ord_preds = load_jsonl_isat(ORD_OFFICIAL) if args.include_ord else {}
    print(f"  Gemma: {len(gemma)}  Llama: {len(llama)}  C4: {len(c4)}  Ord: {len(ord_preds)}")

    # Pass 1: gather ALL mDeBERTa isAt predictions to compute global ambiguity threshold
    all_md: dict[tuple, dict] = {}
    pair_to_lang_file: dict[tuple, str] = {}
    for jsonl_name in LANG_FILES:
        md = load_md_confidence(jsonl_name)
        for k, v in md.items():
            all_md[k] = v
            pair_to_lang_file[k] = jsonl_name
    print(f"  mDeBERTa: {len(all_md)} predictions")

    # Compute global threshold for top X% by ambiguity
    keys_by_ambig = sorted(all_md.keys(), key=lambda k: -all_md[k]["ambiguity"])
    n_route = int(round(args.top_pct * len(keys_by_ambig)))
    routed_set = set(keys_by_ambig[:n_route])
    threshold = all_md[keys_by_ambig[n_route - 1]]["ambiguity"] if n_route > 0 else 1.0
    print(f"  routing top {args.top_pct:.0%} = {n_route} pairs (ambiguity >= {threshold:.4f})")

    def fallback(k: tuple) -> str:
        votes = []
        for src in (gemma, llama, c4):
            v = src.get(k)
            if v is None or v not in ("TRUE", "FALSE"):
                continue
            votes.append(v)
        if args.include_ord:
            v = ord_preds.get(k)
            if v in ("TRUE", "FALSE"):
                votes.append(v)
        if not votes:
            return "FALSE"
        n_T = sum(1 for v in votes if v == "TRUE")
        # majority threshold = strictly more than half
        return "TRUE" if n_T * 2 > len(votes) else "FALSE"

    # Pass 2: rewrite each language file
    n_kept = 0
    n_routed = 0
    n_disagree_routed = 0
    for jsonl_name in LANG_FILES:
        in_path = MD_SUBMISSION_DIR / jsonl_name
        out_path = args.out_dir / jsonl_name
        with in_path.open("r", encoding="utf-8") as fin, \
             out_path.open("w", encoding="utf-8") as fout:
            for line in fin:
                doc = json.loads(line)
                doc_id = doc["document_id"]
                for pair in doc.get("sampled_pairs", []):
                    k = (doc_id, pair["pers_entity_id"], pair["loc_entity_id"])
                    md_entry = all_md.get(k)
                    if md_entry is None:
                        # mDeBERTa missing — fall back unconditionally
                        new_isat = fallback(k)
                        pair["isAt_explanation"] = f"{args.rule_tag}_md_missing_fb"
                        n_routed += 1
                        n_disagree_routed += int(new_isat != pair.get("isAt"))
                    elif k in routed_set:
                        new_isat = fallback(k)
                        was = pair.get("isAt") or md_entry["pred"]
                        if new_isat != was:
                            n_disagree_routed += 1
                        pair["isAt_explanation"] = (
                            f"{args.rule_tag}_route_amb={md_entry['ambiguity']:.3f}"
                        )
                        n_routed += 1
                    else:
                        new_isat = md_entry["pred"]
                        pair["isAt_explanation"] = f"{args.rule_tag}_keep_md_amb={md_entry['ambiguity']:.3f}"
                        n_kept += 1
                    pair["isAt"] = new_isat
                fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
        print(f"  wrote {out_path}")

    print(f"\nDone. kept_md={n_kept}  routed={n_routed}  routed_overrides_md={n_disagree_routed}")

    # Per-language vote distribution sanity
    print("\nPer-language isAt distribution in the new submission:")
    for jsonl_name in LANG_FILES:
        c = Counter()
        with (args.out_dir / jsonl_name).open("r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                for pair in doc.get("sampled_pairs", []):
                    c[pair.get("isAt")] += 1
        print(f"  {jsonl_name}: {dict(c)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
