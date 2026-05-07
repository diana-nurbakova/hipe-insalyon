"""Write Run-3 official-test submission — frugal-with-encoders, no LLM at inference.

Strategy:
  - at task: plurality(xlm-roberta, mDeBERTa, RF) per pair, ordinal_median
             tiebreaker. Validated MR(at)=0.7198 on the 188-triplet dev split.
  - isAt task: xlm-roberta alone. Validated MR(isAt)=0.7854 on v1 isAt-test
             (effectively equivalent within bootstrap CI to
             majority(xlm, mDeBERTa, RF)=0.7869, while avoiding the
             feature-drift collapse RF exhibits on the official test —
             RF isAt predicts all-FALSE there due to handcrafted feature
             distribution shift).

Footprint:
  - xlm-roberta-large 2,136 MB + mDeBERTa-v3 1,061 MB + RF 20 MB ≈ 3.2 GB.
  - Run-3 is ~60x smaller on disk than Run-1 (which carries Gemma 31B + Llama 70B).

Inputs (all 1118 pairs aligned by (doc, pers, loc)):
  - xlm-roberta at + isAt: runs/submission_xmlroberta_at_isAt/submission_roberta_at_isAt
  - mDeBERTa at: runs/materials/submission_2_official_test_mdeberta_only
  - RF at: logs/official_test/RF_official_test_at_predictions.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LANG_FILES = [
    "HIPE-2026-v1.0-impresso-test-de",
    "HIPE-2026-v1.0-impresso-test-en",
    "HIPE-2026-v1.0-impresso-test-fr",
    "HIPE-2026-v1.0-surprise-test-fr",
]

XLM_DIR = REPO / "runs/submission_xmlroberta_at_isAt/submission_roberta_at_isAt"
MD_DIR = REPO / "runs/materials/submission_2_official_test_mdeberta_only"
RF_AT = REPO / "logs/official_test/RF_official_test_at_predictions.jsonl"

AT_ORDINAL_MAP = {"FALSE": 0, "PROBABLE": 1, "TRUE": 2}


def load_official_at(folder: Path) -> dict[tuple, str]:
    out = {}
    for base in LANG_FILES:
        p = folder / f"{base}.jsonl"
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                for pair in d.get("sampled_pairs", []):
                    k = (d["document_id"], pair["pers_entity_id"], pair["loc_entity_id"])
                    out[k] = pair.get("at")
    return out


def load_official_isat(folder: Path) -> dict[tuple, str]:
    out = {}
    for base in LANG_FILES:
        p = folder / f"{base}.jsonl"
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                for pair in d.get("sampled_pairs", []):
                    k = (d["document_id"], pair["pers_entity_id"], pair["loc_entity_id"])
                    out[k] = pair.get("isAt")
    return out


def load_rf_at(path: Path) -> dict[tuple, str]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])
            v = d.get("at_predicted")
            if v in ("TRUE", "PROBABLE", "FALSE"):
                out[k] = v
    return out


def plurality_at(votes: list[str]) -> str:
    cnt = Counter(votes)
    top = max(cnt.values())
    winners = [l for l, n in cnt.items() if n == top]
    if len(winners) == 1:
        return winners[0]
    ords = sorted(AT_ORDINAL_MAP[v] for v in votes if v in AT_ORDINAL_MAP)
    if not ords:
        return "FALSE"
    med = ords[len(ords) // 2]
    inv = {v: k for k, v in AT_ORDINAL_MAP.items()}
    cand = inv.get(med)
    return cand if cand in winners else sorted(winners)[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=REPO / "submissions" / "run3")
    ap.add_argument("--name-prefix", default="INSALyon")
    ap.add_argument("--run-tag", default="run3")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading model predictions on official test...")
    xlm_at = load_official_at(XLM_DIR)
    xlm_isat = load_official_isat(XLM_DIR)
    md_at = load_official_at(MD_DIR)
    rf_at = load_rf_at(RF_AT)
    print(f"  xlm-roberta: {len(xlm_at)} at + {len(xlm_isat)} isAt")
    print(f"  mDeBERTa:    {len(md_at)} at")
    print(f"  RF:          {len(rf_at)} at")
    print()

    # at provenance counter
    at_provenance = Counter()
    n_pairs = 0
    n_at_changed_vs_xlm = 0

    for base in LANG_FILES:
        in_path = XLM_DIR / f"{base}.jsonl"
        out_path = args.out_dir / f"{args.name_prefix}_{base}_{args.run_tag}.jsonl"
        cnt_at = Counter()
        cnt_isat = Counter()
        with in_path.open("r", encoding="utf-8") as fin, \
             out_path.open("w", encoding="utf-8") as fout:
            for line in fin:
                doc = json.loads(line)
                doc_id = doc["document_id"]
                for pair in doc.get("sampled_pairs", []):
                    k = (doc_id, pair["pers_entity_id"], pair["loc_entity_id"])
                    votes = []
                    for v in (xlm_at.get(k), md_at.get(k), rf_at.get(k)):
                        if v in ("TRUE", "PROBABLE", "FALSE"):
                            votes.append(v)
                    new_at = plurality_at(votes) if votes else "FALSE"
                    if new_at != xlm_at.get(k):
                        n_at_changed_vs_xlm += 1
                    pair["at"] = new_at
                    pair["at_explanation"] = "plurality(xlm-roberta, mDeBERTa, RF) tb=ordinal_median"
                    pair["isAt"] = xlm_isat.get(k, "FALSE")
                    pair["isAt_explanation"] = "xlm-roberta alone"
                    cnt_at[new_at] += 1
                    cnt_isat[pair["isAt"]] += 1
                    n_pairs += 1
                    at_provenance[
                        ("xlm" if xlm_at.get(k) == new_at else "")
                        + ("md" if md_at.get(k) == new_at else "")
                        + ("rf" if rf_at.get(k) == new_at else "")
                    ] += 1
                fout.write(json.dumps(doc, ensure_ascii=False) + "\n")
        print(f"  wrote {out_path}")
        print(f"    at:   {dict(cnt_at)}")
        print(f"    isAt: {dict(cnt_isat)}")

    print()
    print(f"Total pairs written: {n_pairs}")
    print(f"at vote provenance (which model(s) voted for the winner):")
    for prov, n in at_provenance.most_common():
        print(f"  {prov!r}: {n}")
    print(f"at changes vs xlm-roberta-alone baseline: {n_at_changed_vs_xlm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
