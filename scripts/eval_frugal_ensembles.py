"""Frugal ensemble analysis — drop the large LLMs (Gemma, Llama) and see how
much score we keep with smaller models only.

Frugality tiers (BF16 weights):
  - Encoder/RF tier (~1 GB):     RF (1 MB), C4 (1 MB), OrdContM1 (8 MB),
                                  hmBERT (424 MB), mDeBERTa (1,061 MB),
                                  xlm-roberta-large (2,136 MB)
  - LLM tier (~tens of GB):      Gemma 4 31B (58.5 GB), Llama 3.3 70B (134.6 GB)

This script reports:

  AT task (mDeBERTa's 188-triplet val split, all base-model preds are OOF):
    - 3-model stacker (RF, C4, Ord) — no LLMs
    - 4-model stacker w/ Gemma replaced by xlm-roberta (note: xlm OOF not
      available, so we use xlm's val predictions; mild data-leak but
      diagnostic)
    - Plurality combinations:
        plurality(xlm, mDeBERTa)
        plurality(xlm, mDeBERTa, RF)
        plurality(xlm, RF, C4, Ord)
        plurality(xlm, 3-model-stacker)
        plurality(xlm, 3-model-stacker, mDeBERTa)
    Compare to Run-6 baseline: plurality(xlm, 4-model-stacker, Gemma) = 0.7765

  ISAT task (v1 isAt-test n=187):
    - majority(xlm, mDeBERTa, RF) — purely frugal
    - majority(xlm, RF, C4)
    - majority(xlm, mDeBERTa, RF, C4)
    - majority(xlm, mDeBERTa, Llama)        — adds Llama back
    - ambig-route xlm -> majority(mDeBERTa, RF) etc.
    Compare to Run-4/5/6 isAt: majority(xlm, Gemma, Llama) = 0.8411
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from hipe.evaluation.metrics import (
    AT_LABELS, ISAT_LABELS, compute_macro_recall, null_to_false,
)
from hipe.stacker import AT_ORDINAL_MAP, apply_lookup, build_lookup_table


REPO = Path(__file__).resolve().parent.parent

# at task inputs
XLM_AT = REPO / "runs/materials/xml_roberta_at_result.csv"
MD_AT = REPO / "runs/runs_mdeberta/runs/at_task_prediction_result_updated.csv"
V1_CSV = REPO / "data/v1_baseline_train_test_ids.csv"
RF_OOF = REPO / "logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl"
C4_OOF = REPO / "logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl"
ORD_OOF = REPO / "logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl"
GEMMA_FULL = REPO / "logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl"

# isAt task inputs
XLM_ISAT = REPO / "runs/materials/xml_roberta_isAt_result.csv"
MD_ISAT = REPO / "runs/runs_mdeberta/runs/isAt_task_prediction_results.csv"
LLAMA_ISAT = REPO / "logs/ablations/T1_llm_zeroshot_PAB_openrouter_llama-33-70b-instruct_isAt-test_predictions.jsonl"
RF_V1_ISAT = REPO / "logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_isAt_isAt-test_predictions.jsonl"
C4_V1_ISAT = REPO / "logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_isAt-test_predictions.jsonl"


def _norm_isat(s):
    s = (s or "").strip()
    if s.lower() == "true":  return "TRUE"
    if s.lower() == "false": return "FALSE"
    return s


def _key(d):
    return (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])


def load_csv_preds(path: Path, normalize: bool = False) -> dict[tuple, dict]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            pred = _norm_isat(r["pred_label"]) if normalize else r["pred_label"]
            true = _norm_isat(r["true_label"]) if normalize else r["true_label"]
            out[k] = {"pred": pred, "true": true,
                      "conf": float(r.get("confidence", 0))}
    return out


def load_jsonl_preds(path: Path, field: str = "at_predicted") -> dict[tuple, str | None]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            out[_key(d)] = d.get(field)
    return out


def load_v1_at_golds() -> dict[tuple, str]:
    out = {}
    with V1_CSV.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["task"] != "at": continue
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            out[k] = r["at_label"]
    return out


def macro_recall(gold, pred, labels):
    return compute_macro_recall(gold, pred, label_set=list(labels))["macro_recall"]


def bootstrap_ci(gold, pred, labels, n=2000, seed=42):
    rng = np.random.default_rng(seed)
    n_obs = len(gold)
    point = macro_recall(gold, pred, labels)
    samples = []
    for _ in range(n):
        idx = rng.integers(0, n_obs, n_obs)
        g = [gold[i] for i in idx]; p = [pred[i] for i in idx]
        samples.append(macro_recall(g, p, labels))
    samples.sort()
    return point, samples[int(0.025 * n)], samples[int(0.975 * n)]


def plurality_at(votes: list[str]) -> str:
    cnt = Counter(votes)
    top = max(cnt.values())
    winners = [l for l, n in cnt.items() if n == top]
    if len(winners) == 1: return winners[0]
    ords = sorted(AT_ORDINAL_MAP[v] for v in votes if v in AT_ORDINAL_MAP)
    if not ords: return "FALSE"
    med = ords[len(ords) // 2]
    inv = {v: k for k, v in AT_ORDINAL_MAP.items()}
    cand = inv.get(med)
    return cand if cand in winners else sorted(winners)[0]


def majority_isat(votes: list[str]) -> str:
    n_t = sum(1 for v in votes if v == "TRUE")
    return "TRUE" if n_t * 2 > len(votes) else "FALSE"


def _print(rows):
    if not rows: return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def at_analysis(args):
    print("=" * 78)
    print("AT — frugal ensembles on the 188-triplet val split (mDeBERTa-test)")
    print("=" * 78)

    xlm = load_csv_preds(XLM_AT)
    md = load_csv_preds(MD_AT)
    rf = load_jsonl_preds(RF_OOF)
    c4 = load_jsonl_preds(C4_OOF)
    ord_p = load_jsonl_preds(ORD_OOF)
    gemma = load_jsonl_preds(GEMMA_FULL)
    v1 = load_v1_at_golds()

    test_keys = [k for k in xlm if k in md and k in rf and k in c4 and k in ord_p and k in gemma]
    train_keys = [k for k in v1 if k not in xlm and k in rf and k in c4 and k in ord_p and k in gemma]
    print(f"  test={len(test_keys)}  train_for_stacker={len(train_keys)}")

    gold = [xlm[k]["true"] for k in test_keys]
    xlm_p = [xlm[k]["pred"] for k in test_keys]
    md_p = [null_to_false(md[k]["pred"]) for k in test_keys]
    rf_p = [null_to_false(rf[k]) for k in test_keys]
    c4_p = [null_to_false(c4[k]) for k in test_keys]
    ord_pred = [null_to_false(ord_p[k]) for k in test_keys]
    gm_p = [null_to_false(gemma[k]) for k in test_keys]

    # ----- Build stacker variants on train --------------------------------
    train_gold = [v1[k] for k in train_keys]

    def build(stacker_models: dict[str, dict]) -> tuple[dict, dict]:
        train_votes = {n: [null_to_false(s[k]) for k in train_keys]
                       for n, s in stacker_models.items()}
        test_votes = {n: [null_to_false(s[k]) for k in test_keys]
                      for n, s in stacker_models.items()}
        return train_votes, test_votes

    # 4-model stacker (baseline, with Gemma)
    train4, test4 = build({"RF": rf, "C4": c4, "Ord": ord_p, "Gm": gemma})
    lookup4 = build_lookup_table(train4, train_gold,
                                  tiebreaker="alphabetical",
                                  ordinal_map=AT_ORDINAL_MAP)
    stacker4 = apply_lookup(test4, lookup4, fallback="label",
                             fallback_label="FALSE",
                             ordinal_map=AT_ORDINAL_MAP)
    # 3-model stacker (no Gemma): RF + C4 + Ord
    train3, test3 = build({"RF": rf, "C4": c4, "Ord": ord_p})
    lookup3 = build_lookup_table(train3, train_gold,
                                  tiebreaker="alphabetical",
                                  ordinal_map=AT_ORDINAL_MAP)
    stacker3 = apply_lookup(test3, lookup3, fallback="label",
                             fallback_label="FALSE",
                             ordinal_map=AT_ORDINAL_MAP)
    # 2-model stacker: RF + C4 (no Gemma, no Ord)
    train2, test2 = build({"RF": rf, "C4": c4})
    lookup2 = build_lookup_table(train2, train_gold,
                                  tiebreaker="alphabetical",
                                  ordinal_map=AT_ORDINAL_MAP)
    stacker2 = apply_lookup(test2, lookup2, fallback="label",
                             fallback_label="FALSE",
                             ordinal_map=AT_ORDINAL_MAP)

    print()
    print("  Standalone reference points:")
    rows = [("model", "MR(at)", "95% CI")]
    for name, p in [("xlm-roberta", xlm_p), ("mDeBERTa", md_p),
                    ("RF (OOF)", rf_p), ("C4 (OOF)", c4_p),
                    ("OrdContM1 (OOF)", ord_pred), ("Gemma", gm_p)]:
        pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    print()
    print("  Stacker variants (lookup tables built on 1062-triplet train):")
    rows = [("strategy", "MR(at)", "95% CI")]
    for name, p in [
        ("4-model stacker (RF, C4, Ord, Gemma)  — has LLM",         stacker4),
        ("3-model stacker (RF, C4, Ord)         — no LLM",          stacker3),
        ("2-model stacker (RF, C4)              — no LLM, no MASK contrastive", stacker2),
    ]:
        pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    print()
    print("  Plurality / mixed strategies (no Gemma / no LLM at all):")
    rows = [("strategy", "MR(at)", "95% CI", "uses_LLM?")]
    cases = [
        ("xlm alone",                                    xlm_p, False),
        ("mDeBERTa alone",                               md_p, False),
        ("plurality(xlm, mDeBERTa)",                     [plurality_at([x, m]) for x, m in zip(xlm_p, md_p)], False),
        ("plurality(xlm, mDeBERTa, RF)",                 [plurality_at([x, m, r]) for x, m, r in zip(xlm_p, md_p, rf_p)], False),
        ("plurality(xlm, RF, C4, Ord)",                  [plurality_at([x, r, c, o]) for x, r, c, o in zip(xlm_p, rf_p, c4_p, ord_pred)], False),
        ("plurality(xlm, 3-model-stacker)",              [plurality_at([x, s]) for x, s in zip(xlm_p, stacker3)], False),
        ("plurality(xlm, 3-model-stacker, mDeBERTa)",    [plurality_at([x, s, m]) for x, s, m in zip(xlm_p, stacker3, md_p)], False),
        ("plurality(xlm, 3-model-stacker, RF)",          [plurality_at([x, s, r]) for x, s, r in zip(xlm_p, stacker3, rf_p)], False),
        ("plurality(xlm, 4-model-stacker, Gemma)  RUN-6", [plurality_at([x, s, g]) for x, s, g in zip(xlm_p, stacker4, gm_p)], True),
        ("plurality(xlm, 4-model-stacker)",              [plurality_at([x, s]) for x, s in zip(xlm_p, stacker4)], True),  # stacker has Gemma inside
        ("plurality(xlm, 3-model-stacker, Gemma)",       [plurality_at([x, s, g]) for x, s, g in zip(xlm_p, stacker3, gm_p)], True),
    ]
    for name, p, uses_llm in cases:
        pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]",
                     "yes" if uses_llm else "no"))
    _print(rows)


def isat_analysis(args):
    print()
    print("=" * 78)
    print("ISAT — frugal ensembles on v1 isAt-test (n=187)")
    print("=" * 78)

    xlm = load_csv_preds(XLM_ISAT, normalize=True)
    md = {}
    with MD_ISAT.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            md[k] = {"pred": r["pred_label"], "true": r["true_label"]}
    gemma = load_jsonl_preds(GEMMA_FULL, field="isAt_predicted")
    llama = load_jsonl_preds(LLAMA_ISAT, field="isAt_predicted")
    rf = load_jsonl_preds(RF_V1_ISAT, field="isAt_predicted")
    c4 = load_jsonl_preds(C4_V1_ISAT, field="isAt_predicted")

    keys = [k for k in xlm if k in md and k in gemma and k in llama and k in rf and k in c4]
    print(f"  aligned n={len(keys)}")

    gold = [xlm[k]["true"] for k in keys]
    xlm_p = [xlm[k]["pred"] for k in keys]
    md_p = [null_to_false(md[k]["pred"]) for k in keys]
    gm_p = [null_to_false(gemma[k]) for k in keys]
    ll_p = [null_to_false(llama[k]) for k in keys]
    rf_p = [null_to_false(rf[k]) for k in keys]
    c4_p = [null_to_false(c4[k]) for k in keys]

    print()
    print("  Standalone reference points:")
    rows = [("model", "MR(isAt)", "95% CI")]
    for name, p in [("xlm-roberta", xlm_p), ("mDeBERTa", md_p),
                    ("RF (T1.5)", rf_p), ("C4 LR", c4_p),
                    ("Gemma", gm_p), ("Llama", ll_p)]:
        pt, lo, hi = bootstrap_ci(gold, p, ISAT_LABELS, n=args.bootstrap)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    print()
    print("  Frugal ensembles (no Gemma / no LLM at all):")
    rows = [("strategy", "MR(isAt)", "95% CI", "uses_LLM?")]

    cases = [
        # No LLM at all
        ("xlm alone",                                  xlm_p, "no"),
        ("mDeBERTa alone",                             md_p, "no"),
        ("majority(xlm, mDeBERTa, RF)",                [majority_isat([x, m, r]) for x, m, r in zip(xlm_p, md_p, rf_p)], "no"),
        ("majority(xlm, mDeBERTa, C4)",                [majority_isat([x, m, c]) for x, m, c in zip(xlm_p, md_p, c4_p)], "no"),
        ("majority(xlm, RF, C4)",                      [majority_isat([x, r, c]) for x, r, c in zip(xlm_p, rf_p, c4_p)], "no"),
        ("majority(xlm, mDeBERTa, RF, C4)",            [majority_isat([x, m, r, c]) for x, m, r, c in zip(xlm_p, md_p, rf_p, c4_p)], "no"),
        ("xlm OR mDeBERTa says TRUE (any-true)",       ["TRUE" if (x == "TRUE" or m == "TRUE") else "FALSE" for x, m in zip(xlm_p, md_p)], "no"),
        ("xlm AND mDeBERTa say TRUE (both-true)",      ["TRUE" if (x == "TRUE" and m == "TRUE") else "FALSE" for x, m in zip(xlm_p, md_p)], "no"),
        # No Gemma but Llama OK (mid-tier — Llama 70B is bigger than Gemma 31B though)
        ("majority(xlm, mDeBERTa, Llama)               — has LLM", [majority_isat([x, m, l]) for x, m, l in zip(xlm_p, md_p, ll_p)], "yes"),
        ("majority(xlm, RF, Llama)",                   [majority_isat([x, r, l]) for x, r, l in zip(xlm_p, rf_p, ll_p)], "yes"),
        ("majority(xlm, mDeBERTa, RF, Llama)",         [majority_isat([x, m, r, l]) for x, m, r, l in zip(xlm_p, md_p, rf_p, ll_p)], "yes"),
        # No Llama but Gemma OK (smaller LLM)
        ("majority(xlm, mDeBERTa, Gemma)               — has LLM", [majority_isat([x, m, g]) for x, m, g in zip(xlm_p, md_p, gm_p)], "yes"),
        ("majority(xlm, RF, Gemma)",                   [majority_isat([x, r, g]) for x, r, g in zip(xlm_p, rf_p, gm_p)], "yes"),
        # baseline Run-6 isAt
        ("majority(xlm, Gemma, Llama)            RUN-6", [majority_isat([x, g, l]) for x, g, l in zip(xlm_p, gm_p, ll_p)], "yes"),
    ]
    for name, p, llm in cases:
        pt, lo, hi = bootstrap_ci(gold, p, ISAT_LABELS, n=args.bootstrap)
        rec_T = sum(1 for g, q in zip(gold, p) if g == "TRUE" and q == "TRUE") / max(1, sum(1 for g in gold if g == "TRUE"))
        rec_F = sum(1 for g, q in zip(gold, p) if g == "FALSE" and q == "FALSE") / max(1, sum(1 for g in gold if g == "FALSE"))
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]", llm))
    _print(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()
    at_analysis(args)
    isat_analysis(args)

    print()
    print("=" * 78)
    print("Footprint reference (BF16 weights)")
    print("=" * 78)
    print("  Component                   Params         Disk MB")
    print("  RF (handcrafted)              842,545          20")
    print("  C4 (StandardScaler+LR)         11,598           1")
    print("  OrdContM1 (contrastive MLP) 2,156,293           8")
    print("  hmBERT encoder            110,617,344         424")
    print("  mDeBERTa-v3 base          278,043,651       1,061")
    print("  xlm-roberta-large         559,892,482       2,136")
    print("  Gemma 4 31B            30,700,000,000      58,556")
    print("  Llama 3.3 70B          70,553,706,496     134,600")
    print()
    print("  Frugal-tier ensemble (no LLM): RF + C4 + OrdContM1 + hmBERT + xlm + mDeBERTa")
    print("    => 953.6 MP, 3,650 MB total — runs on a single 8-GB GPU.")
    print("  +Gemma adds 30.7 GP, 58 GB.")
    print("  +Llama adds 70.5 GP, 134 GB.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
