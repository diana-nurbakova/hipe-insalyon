"""Re-run isAt and at ensemble analyses with xlm-roberta as primary.

xlm-roberta uses the same train/val splits as mDeBERTa:
  - at-task split: 188 mDeBERTa-test triplets (118 v1-test + 70 v1-train)
  - isAt-task split: v1 isAt-test (188 triplets)

Two analyses:
  A. isAt: ambiguity-routed xlm-roberta + (Gemma, Llama, C4) fallback
  B. at:   (a) standalone vs disagreement stacker, (b) post-hoc combinations

Compares head-to-head with the previously analyzed mDeBERTa configuration.
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
    AT_LABELS,
    ISAT_LABELS,
    compute_macro_recall,
    null_to_false,
)
from hipe.stacker import (
    AT_ORDINAL_MAP,
    apply_lookup,
    build_lookup_table,
)


REPO = Path(__file__).resolve().parent.parent

XLM_AT = REPO / "runs/materials/xml_roberta_at_result.csv"
XLM_ISAT = REPO / "runs/materials/xml_roberta_isAt_result.csv"
MD_AT = REPO / "runs/runs_mdeberta/runs/at_task_prediction_result_updated.csv"
MD_ISAT = REPO / "runs/runs_mdeberta/runs/isAt_task_prediction_results.csv"
V1_CSV = REPO / "data/v1_baseline_train_test_ids.csv"
RF_OOF = REPO / "logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl"
C4_OOF = REPO / "logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl"
ORD_OOF = REPO / "logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl"
GEMMA_FULL = REPO / "logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl"
LLAMA_ISAT = REPO / "logs/ablations/T1_llm_zeroshot_PAB_openrouter_llama-33-70b-instruct_isAt-test_predictions.jsonl"
RF_V1_ISAT = REPO / "logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_isAt_isAt-test_predictions.jsonl"
C4_V1_ISAT = REPO / "logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_isAt-test_predictions.jsonl"


def _norm_isat(s: str) -> str:
    s = (s or "").strip()
    if s.lower() == "true": return "TRUE"
    if s.lower() == "false": return "FALSE"
    return s


def load_xlm_isat() -> dict[tuple, dict]:
    """xlm-roberta isAt has only 2 probabilities; we reconstruct margin/entropy."""
    out = {}
    with XLM_ISAT.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            pred = _norm_isat(r["pred_label"])
            true = _norm_isat(r["true_label"])
            conf = float(r["confidence"])
            # Binary: p_top = conf, p_other = 1 - conf
            p_top = conf
            p_other = 1.0 - conf
            margin = p_top - p_other
            entropy = 0.0
            for p in (p_top, p_other):
                if p > 1e-9:
                    entropy -= p * math.log(p)
            norm_ent = entropy / math.log(2)
            ambig = norm_ent * (1.0 - margin)
            out[k] = {
                "pred": pred, "true": true, "conf": conf,
                "margin": margin, "norm_entropy": norm_ent, "ambiguity": ambig,
            }
    return out


def load_xlm_at() -> dict[tuple, dict]:
    """xlm-roberta at CSV has only `confidence` (no per-class probs).

    Use confidence directly as a proxy for ambiguity: ambig = 1 - conf.
    Without per-class probs we can't compute proper margin/entropy.
    """
    out = {}
    with XLM_AT.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            conf = float(r["confidence"])
            out[k] = {
                "pred": r["pred_label"],
                "true": r["true_label"],
                "conf": conf,
                "ambiguity": 1.0 - conf,
            }
    return out


def load_md_isat() -> dict[tuple, dict]:
    out = {}
    with MD_ISAT.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            pT = float(r["prob_TRUE"])
            pF = float(r["prob_FALSE"])
            margin = abs(pT - pF)
            entropy = 0.0
            for p in (pT, pF):
                if p > 1e-9:
                    entropy -= p * math.log(p)
            norm_ent = entropy / math.log(2)
            out[k] = {
                "pred": r["pred_label"], "true": r["true_label"],
                "conf": float(r["confidence"]),
                "margin": margin, "norm_entropy": norm_ent,
                "ambiguity": norm_ent * (1.0 - margin),
            }
    return out


def load_md_at() -> dict[tuple, dict]:
    out = {}
    with MD_AT.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            out[k] = {"pred": r["pred_label"], "true": r["true_label"],
                      "conf": float(r["confidence"])}
    return out


def load_jsonl(path: Path, field: str = "isAt_predicted") -> dict[tuple, str | None]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])
            out[k] = d.get(field)
    return out


def load_v1_at_golds() -> dict[tuple, str]:
    out = {}
    with V1_CSV.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["task"] != "at":
                continue
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
        g = [gold[i] for i in idx]
        p = [pred[i] for i in idx]
        samples.append(macro_recall(g, p, labels))
    samples.sort()
    return point, samples[int(0.025 * n)], samples[int(0.975 * n)]


def _print(rows):
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def isat_analysis(args):
    print("=" * 78)
    print("ISAT — xlm-roberta vs mDeBERTa primary, on v1 isAt-test (n=187)")
    print("=" * 78)

    xlm = load_xlm_isat()
    md = load_md_isat()
    gemma = load_jsonl(GEMMA_FULL)
    llama = load_jsonl(LLAMA_ISAT)
    rf = load_jsonl(RF_V1_ISAT)
    c4 = load_jsonl(C4_V1_ISAT)

    keys = [k for k in xlm if k in md and k in gemma and k in llama and k in rf and k in c4]
    print(f"  aligned n={len(keys)} (dropped {len(xlm) - len(keys)} for missing partner preds)")

    gold = [xlm[k]["true"] for k in keys]
    xlm_pred = [xlm[k]["pred"] for k in keys]
    md_pred = [null_to_false(md[k]["pred"]) for k in keys]
    gm_pred = [null_to_false(gemma[k]) for k in keys]
    ll_pred = [null_to_false(llama[k]) for k in keys]
    rf_pred = [null_to_false(rf[k]) for k in keys]
    c4_pred = [null_to_false(c4[k]) for k in keys]

    print()
    print("  Standalone MR(isAt):")
    rows = [("model", "MR", "95% CI")]
    for label, p in [("xlm-roberta", xlm_pred), ("mDeBERTa", md_pred),
                     ("Gemma", gm_pred), ("Llama", ll_pred),
                     ("RF (T1.5)", rf_pred), ("C4 (mask+e1e2+temp)", c4_pred)]:
        pt, lo, hi = bootstrap_ci(gold, p, ISAT_LABELS, n=args.bootstrap)
        rows.append((label, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    print()
    print("  Pairwise disagreement w/ xlm-roberta:")
    for nm, p in [("mDeBERTa", md_pred), ("Gemma", gm_pred), ("Llama", ll_pred),
                  ("RF", rf_pred), ("C4", c4_pred)]:
        d = sum(1 for a, b in zip(xlm_pred, p) if a != b) / len(keys)
        print(f"    xlm vs {nm:<10s}: {d:.3f}")

    # Routing strategies with xlm-roberta as primary
    print()
    print("  Ambig-routed: keep xlm for low-amb, route top X% to fallback")
    print("    (xlm confidence range is narrower than mDeBERTa, so X% threshold "
          "lands on different absolute confidence values)")
    keys_by_ambig = sorted(range(len(keys)), key=lambda i: -xlm[keys[i]]["ambiguity"])
    fallbacks = {
        "Gemma alone": lambda i: gm_pred[i],
        "majority(gm, ll, c4)": lambda i: "TRUE" if sum(1 for v in (gm_pred[i], ll_pred[i], c4_pred[i])
                                                          if v == "TRUE") >= 2 else "FALSE",
        "majority(md, gm, ll)": lambda i: "TRUE" if sum(1 for v in (md_pred[i], gm_pred[i], ll_pred[i])
                                                          if v == "TRUE") >= 2 else "FALSE",
        "5-way maj (md, gm, ll, c4, rf)": lambda i: "TRUE" if sum(1 for v in (md_pred[i], gm_pred[i],
                                                                                ll_pred[i], c4_pred[i],
                                                                                rf_pred[i])
                                                                    if v == "TRUE") >= 3 else "FALSE",
    }
    rows = [("top X%", "n_routed", "fallback", "MR", "95% CI")]
    for X in (10, 20, 30, 40, 50):
        n_route = int(round(X / 100.0 * len(keys)))
        routed_set = set(keys_by_ambig[:n_route])
        for fb_name, fb_fn in fallbacks.items():
            out = [fb_fn(i) if i in routed_set else xlm_pred[i] for i in range(len(keys))]
            pt, lo, hi = bootstrap_ci(gold, out, ISAT_LABELS, n=args.bootstrap)
            rows.append((f"{X}%", n_route, fb_name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    # Confidence-free voting strategies with xlm in the mix
    print()
    print("  Confidence-free voting strategies:")
    rows = [("strategy", "MR", "95% CI", "rec_T", "rec_F", "n_pred_T")]
    for name, votes in [
        ("majority(xlm, gm, ll)",
         list(zip(xlm_pred, gm_pred, ll_pred))),
        ("majority(xlm, md, gm)",
         list(zip(xlm_pred, md_pred, gm_pred))),
        ("majority(xlm, gm, ll, c4)",  # 4 voters
         list(zip(xlm_pred, gm_pred, ll_pred, c4_pred))),
        ("majority(xlm, md, gm, ll)",
         list(zip(xlm_pred, md_pred, gm_pred, ll_pred))),
        ("majority(xlm, md, gm, ll, c4)",  # 5 voters
         list(zip(xlm_pred, md_pred, gm_pred, ll_pred, c4_pred))),
        (">=2 of 5 (xlm, md, gm, ll, c4) say TRUE",
         list(zip(xlm_pred, md_pred, gm_pred, ll_pred, c4_pred))),
    ]:
        if name.startswith(">="):
            preds = ["TRUE" if sum(1 for v in vs if v == "TRUE") >= 2 else "FALSE" for vs in votes]
        else:
            # Simple majority: TRUE if majority of votes are TRUE
            preds = []
            for vs in votes:
                t = sum(1 for v in vs if v == "TRUE")
                preds.append("TRUE" if t * 2 > len(vs) else "FALSE")
        pt, lo, hi = bootstrap_ci(gold, preds, ISAT_LABELS, n=args.bootstrap)
        rec_T = sum(1 for g, p in zip(gold, preds) if g == "TRUE" and p == "TRUE") / max(1, sum(1 for g in gold if g == "TRUE"))
        rec_F = sum(1 for g, p in zip(gold, preds) if g == "FALSE" and p == "FALSE") / max(1, sum(1 for g in gold if g == "FALSE"))
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]",
                     f"{rec_T:.3f}", f"{rec_F:.3f}", sum(1 for p in preds if p == "TRUE")))
    _print(rows)


def at_analysis(args):
    print()
    print("=" * 78)
    print("AT — xlm-roberta vs mDeBERTa, on shared 188-triplet val split")
    print("=" * 78)

    xlm = load_xlm_at()
    md = load_md_at()
    rf = load_jsonl(RF_OOF, field="at_predicted")
    c4 = load_jsonl(C4_OOF, field="at_predicted")
    ord_p = load_jsonl(ORD_OOF, field="at_predicted")
    gemma = load_jsonl(GEMMA_FULL, field="at_predicted")
    v1_golds = load_v1_at_golds()

    test_keys = [k for k in xlm if k in md and k in rf and k in c4 and k in ord_p and k in gemma]
    train_keys = [k for k in v1_golds
                  if k not in xlm and k in rf and k in c4 and k in ord_p and k in gemma]
    print(f"  test  set: n={len(test_keys)}")
    print(f"  train set (v1 - xlm-test): n={len(train_keys)}")

    gold = [xlm[k]["true"] for k in test_keys]
    xlm_pred = [xlm[k]["pred"] for k in test_keys]
    md_pred = [null_to_false(md[k]["pred"]) for k in test_keys]
    rf_pred = [null_to_false(rf[k]) for k in test_keys]
    c4_pred = [null_to_false(c4[k]) for k in test_keys]
    ord_pred = [null_to_false(ord_p[k]) for k in test_keys]
    gm_pred = [null_to_false(gemma[k]) for k in test_keys]

    print()
    print("  Standalone MR(at):")
    rows = [("model", "MR(at)", "95% CI", "rec_T", "rec_P", "rec_F")]
    for label, p in [("xlm-roberta", xlm_pred), ("mDeBERTa", md_pred),
                     ("RF (OOF)", rf_pred), ("C4 (OOF)", c4_pred),
                     ("OrdContM1 (OOF)", ord_pred), ("Gemma", gm_pred)]:
        pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
        details = compute_macro_recall(gold, p, label_set=list(AT_LABELS))
        rt = details.get("recall_TRUE")
        rp = details.get("recall_PROBABLE")
        rf_r = details.get("recall_FALSE")
        rows.append((label, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]",
                     f"{rt:.3f}" if rt else "n/a",
                     f"{rp:.3f}" if rp else "n/a",
                     f"{rf_r:.3f}" if rf_r else "n/a"))
    _print(rows)

    # 4-key stacker (RF, C4, Ord, Gemma) on this split
    train_votes = {
        "RF":  [null_to_false(rf[k]) for k in train_keys],
        "C4":  [null_to_false(c4[k]) for k in train_keys],
        "Ord": [null_to_false(ord_p[k]) for k in train_keys],
        "Gm":  [null_to_false(gemma[k]) for k in train_keys],
    }
    test_votes = {
        "RF":  rf_pred, "C4":  c4_pred, "Ord": ord_pred, "Gm":  gm_pred,
    }
    train_gold = [v1_golds[k] for k in train_keys]
    lookup = build_lookup_table(train_votes, train_gold,
                                 tiebreaker="alphabetical",
                                 ordinal_map=AT_ORDINAL_MAP)
    stacker_preds = apply_lookup(test_votes, lookup, fallback="label",
                                  fallback_label="FALSE",
                                  ordinal_map=AT_ORDINAL_MAP)

    print()
    print("  Stacker + xlm-roberta combinations:")
    rows = [("strategy", "MR(at)", "95% CI")]
    pt, lo, hi = bootstrap_ci(gold, stacker_preds, AT_LABELS, n=args.bootstrap)
    rows.append(("4-key stacker (RF,C4,Ord,Gm) tb=alpha+fb=label",
                 f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # xlm overrides stacker on disagreement
    p = [x if x != s else s for x, s in zip(xlm_pred, stacker_preds)]
    pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
    rows.append(("xlm overrides stacker (always)",
                 f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # Plurality(xlm, stacker, gemma)
    def plurality_3(a, b, c, ordinal_map):
        cnt = Counter([a, b, c])
        top = max(cnt.values())
        winners = [l for l, n in cnt.items() if n == top]
        if len(winners) == 1: return winners[0]
        ords = sorted(ordinal_map[v] for v in (a, b, c))
        med = ords[len(ords) // 2]
        inv = {v: k for k, v in ordinal_map.items()}
        cand = inv[med]
        return cand if cand in winners else sorted(winners)[0]

    p = [plurality_3(x, s, g, AT_ORDINAL_MAP)
         for x, s, g in zip(xlm_pred, stacker_preds, gm_pred)]
    pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
    rows.append(("plurality(xlm, stacker, gemma)",
                 f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 5-way plurality(xlm, rf, c4, ord, gm)
    def plurality_n(votes, ordinal_map):
        cnt = Counter(votes)
        top = max(cnt.values())
        winners = [l for l, n in cnt.items() if n == top]
        if len(winners) == 1: return winners[0]
        ords = sorted(ordinal_map[v] for v in votes)
        med = ords[len(ords) // 2]
        inv = {v: k for k, v in ordinal_map.items()}
        cand = inv[med]
        return cand if cand in winners else sorted(winners)[0]

    p = [plurality_n([x, r, c, o, g], AT_ORDINAL_MAP)
         for x, r, c, o, g in zip(xlm_pred, rf_pred, c4_pred, ord_pred, gm_pred)]
    pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
    rows.append(("plurality(xlm, rf, c4, ord, gm)",
                 f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 5-way plurality(xlm, md, rf, c4, gm) — without OrdContM1, with both BERT-style
    p = [plurality_n([x, m, r, c, g], AT_ORDINAL_MAP)
         for x, m, r, c, g in zip(xlm_pred, md_pred, rf_pred, c4_pred, gm_pred)]
    pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
    rows.append(("plurality(xlm, md, rf, c4, gm)",
                 f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 6-way plurality(xlm, md, rf, c4, ord, gm)
    p = [plurality_n([x, m, r, c, o, g], AT_ORDINAL_MAP)
         for x, m, r, c, o, g in zip(xlm_pred, md_pred, rf_pred, c4_pred, ord_pred, gm_pred)]
    pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS, n=args.bootstrap)
    rows.append(("plurality(xlm, md, rf, c4, ord, gm)",
                 f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    _print(rows)

    # Disagreement breakdown
    n_agree = 0
    xlm_right = stacker_right = both_wrong = 0
    for x, s, g in zip(xlm_pred, stacker_preds, gold):
        if x == s:
            n_agree += 1
            continue
        if x == g and s != g: xlm_right += 1
        elif s == g and x != g: stacker_right += 1
        else: both_wrong += 1
    print()
    print(f"  xlm vs 4-key stacker disagreement on n={len(test_keys)}:")
    print(f"    agree: {n_agree}  disagree: {len(test_keys) - n_agree}")
    print(f"    xlm right    : {xlm_right}")
    print(f"    stacker right: {stacker_right}")
    print(f"    both wrong   : {both_wrong}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    isat_analysis(args)
    at_analysis(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
