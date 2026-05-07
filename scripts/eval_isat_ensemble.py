"""5-model isAt ensemble analysis on the v1 isAt-test split (n=188).

Models on the same 188 triplets:
  - mDeBERTa-v3 fine-tuned       (with confidence)
  - Gemma-4-31b PAB              (with conf_isAt parsed from raw_output)
  - Llama-3.3-70b PAB
  - RF handcrafted (T1.5)        (just trained via mask_same_split_eval.py)
  - C4 mask+e1+e2+temporal LR    (just trained via mask_same_split_eval.py)

Goal: find the best deployable isAt strategy on the only labelled split we
have. No k-fold available — this is single-split, so report the point + 95%
bootstrap CI for each candidate.

Confidence-aware where confidences exist (mDeBERTa, Gemma).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np

from hipe.evaluation.metrics import (
    ISAT_LABELS,
    compute_macro_recall,
    null_to_false,
)


REPO = Path(__file__).resolve().parent.parent

MD_ISAT = REPO / "runs/runs_mdeberta/runs/isAt_task_prediction_results.csv"
GEMMA_FULL = REPO / "logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl"
LLAMA_ISAT = REPO / "logs/ablations/T1_llm_zeroshot_PAB_openrouter_llama-33-70b-instruct_isAt-test_predictions.jsonl"
RF_ISAT = REPO / "logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_isAt_isAt-test_predictions.jsonl"
C4_ISAT = REPO / "logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_isAt-test_predictions.jsonl"


def _key(row: dict) -> tuple[str, str, str]:
    return (row["document_id"], row["pers_entity_id"], row["loc_entity_id"])


def load_md_isat(path: Path) -> dict[tuple, dict]:
    """Load mdeberta isAt predictions and compute ambiguity signals.

    margin   = |prob_TRUE - prob_FALSE|       (how confidently the top class wins)
    entropy  = -sum p log p                   (already in CSV)
    norm_ent = entropy / log(2)               (normalized to [0,1] for binary)
    ambig    = norm_ent * (1 - margin)        (combined score in [0,1])
    """
    import math
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            pT = float(r["prob_TRUE"])
            pF = float(r["prob_FALSE"])
            margin = abs(pT - pF)
            entropy = float(r.get("entropy", 0.0)) if r.get("entropy") else 0.0
            norm_ent = entropy / math.log(2) if entropy > 0 else 0.0
            ambig = norm_ent * (1.0 - margin)
            out[k] = {
                "pred": r["pred_label"],
                "true": r["true_label"],
                "conf": float(r["confidence"]),
                "margin": margin,
                "entropy": entropy,
                "norm_entropy": norm_ent,
                "ambiguity": ambig,
                "prob_TRUE": pT,
                "prob_FALSE": pF,
            }
    return out


def load_jsonl(path: Path, isat_field: str = "isAt_predicted",
               gold_field: str = "isAt_gold") -> dict[tuple, dict]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = _key(d)
            entry = {
                "pred": null_to_false(d.get(isat_field)),
                "gold": null_to_false(d.get(gold_field)),
            }
            ro = d.get("raw_output") or ""
            m = re.search(r"conf_isAt=([0-9.]+)", ro)
            if m:
                entry["conf"] = float(m.group(1))
            out[k] = entry
    return out


def macro_recall(gold: list[str], pred: list[str]) -> float:
    return compute_macro_recall(gold, pred, label_set=list(ISAT_LABELS))["macro_recall"]


def bootstrap_ci(gold: list[str], pred: list[str], n: int = 2000, seed: int = 42) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    n_obs = len(gold)
    point = macro_recall(gold, pred)
    samples = []
    for _ in range(n):
        idx = rng.integers(0, n_obs, n_obs)
        g = [gold[i] for i in idx]
        p = [pred[i] for i in idx]
        samples.append(macro_recall(g, p))
    samples.sort()
    lo = samples[int(0.025 * n)]
    hi = samples[int(0.975 * n)]
    return point, lo, hi


def _print_table(rows: list[tuple]) -> None:
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    md = load_md_isat(MD_ISAT)
    gemma = load_jsonl(GEMMA_FULL)
    llama = load_jsonl(LLAMA_ISAT)
    rf = load_jsonl(RF_ISAT)
    c4 = load_jsonl(C4_ISAT)

    keys = [k for k in md if k in gemma and k in llama and k in rf and k in c4]
    n_drop = len(md) - len(keys)
    print(f"Aligned n={len(keys)} (dropped {n_drop} for missing partner preds)")

    gold = [null_to_false(md[k]["true"]) for k in keys]
    md_pred = [null_to_false(md[k]["pred"]) for k in keys]
    md_conf = [md[k]["conf"] for k in keys]
    gm_pred = [gemma[k]["pred"] for k in keys]
    gm_conf = [gemma[k].get("conf") for k in keys]
    ll_pred = [llama[k]["pred"] for k in keys]
    rf_pred = [rf[k]["pred"] for k in keys]
    c4_pred = [c4[k]["pred"] for k in keys]

    print()
    print("=" * 78)
    print(f"Standalone MR(isAt) on v1 isAt-test (n={len(keys)}) with 95% bootstrap CI")
    print("=" * 78)
    rows = [("model", "MR", "95% CI")]
    for label, p in [("mDeBERTa", md_pred), ("Gemma", gm_pred), ("Llama", ll_pred),
                     ("RF (T1.5)", rf_pred), ("C4 (mask+e1+e2+temp)", c4_pred)]:
        pt, lo, hi = bootstrap_ci(gold, p, n=args.bootstrap)
        rows.append((label, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Pairwise disagreement matrix (% of items where the two models differ)")
    print("=" * 78)
    models = [("md", md_pred), ("gm", gm_pred), ("ll", ll_pred), ("rf", rf_pred), ("c4", c4_pred)]
    rows = [("",) + tuple(name for name, _ in models)]
    for n1, p1 in models:
        cells = [n1]
        for n2, p2 in models:
            if n1 == n2:
                cells.append("---")
            else:
                disagree = sum(1 for a, b in zip(p1, p2) if a != b) / len(keys)
                cells.append(f"{disagree:.3f}")
        rows.append(tuple(cells))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Ensemble strategies (no confidence — deployable when conf isn't available)")
    print("=" * 78)
    rows = [("strategy", "MR", "95% CI")]

    def majority_n(votes_per_item):
        out = []
        for vs in votes_per_item:
            t = sum(1 for v in vs if v == "TRUE")
            f = len(vs) - t
            out.append("TRUE" if t > f else ("FALSE" if f > t else "FALSE"))
        return out

    # 3-way LLM-ish (md, gm, ll)
    s = majority_n(list(zip(md_pred, gm_pred, ll_pred)))
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("majority(md, gm, ll)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 3-way classical (md, rf, c4)
    s = majority_n(list(zip(md_pred, rf_pred, c4_pred)))
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("majority(md, rf, c4)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 5-way majority
    s = majority_n(list(zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred)))
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("majority(md, gm, ll, rf, c4)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 5-way with Gemma weight=2 (Gemma alone is best single)
    def weighted_vote(weights_per_model, votes_per_item):
        out = []
        for vs in votes_per_item:
            t = sum(w for v, w in zip(vs, weights_per_model) if v == "TRUE")
            f = sum(w for v, w in zip(vs, weights_per_model) if v == "FALSE")
            out.append("TRUE" if t > f else "FALSE")
        return out

    s = weighted_vote([1, 2, 1, 1, 1], list(zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred)))
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("weighted(md=1, gm=2, ll=1, rf=1, c4=1)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # Drop the weakest (C4)
    s = majority_n(list(zip(md_pred, gm_pred, ll_pred, rf_pred)))
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("majority(md, gm, ll, rf)  [no C4]", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # Drop weakest two (Llama, C4)
    s = majority_n(list(zip(md_pred, gm_pred, rf_pred)))
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("majority(md, gm, rf)  [drop ll & c4]", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 5-way with weights tuned to standalone MR (gm 0.83 > md 0.78 > ll 0.77 > rf 0.72 > c4 0.68)
    s = weighted_vote([3, 4, 3, 2, 1], list(zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred)))
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("weighted by standalone-MR rank (4,3,3,2,1)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # union TRUE
    s = ["TRUE" if any(v == "TRUE" for v in vs) else "FALSE"
         for vs in zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred)]
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append(("any(5) says TRUE", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # at least 2 say TRUE
    s = ["TRUE" if sum(1 for v in vs if v == "TRUE") >= 2 else "FALSE"
         for vs in zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred)]
    pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
    rows.append((">=2 of 5 say TRUE", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    _print_table(rows)

    print()
    print("=" * 78)
    print("Confidence-aware strategies (use mDeBERTa + Gemma confidences)")
    print("=" * 78)
    rows = [("strategy", "MR", "95% CI", "n_routed")]

    # mDeBERTa high-conf else 5-way majority
    for T in (0.99, 0.98, 0.97):
        n_route = 0
        out = []
        for i, k in enumerate(keys):
            if md_conf[i] >= T:
                out.append(md_pred[i])
                n_route += 1
            else:
                vs = (md_pred[i], gm_pred[i], ll_pred[i], rf_pred[i], c4_pred[i])
                t = sum(1 for v in vs if v == "TRUE")
                out.append("TRUE" if t > 2 else "FALSE")
        pt, lo, hi = bootstrap_ci(gold, out, n=args.bootstrap)
        rows.append((f"md(conf>={T:.2f}) else 5-way majority", f"{pt:.4f}",
                     f"[{lo:.4f}, {hi:.4f}]", n_route))

    # md high-conf else (md+gm+rf majority — drop weak Llama/C4)
    for T in (0.99, 0.98):
        n_route = 0
        out = []
        for i in range(len(keys)):
            if md_conf[i] >= T:
                out.append(md_pred[i])
                n_route += 1
            else:
                t = sum(1 for v in (md_pred[i], gm_pred[i], rf_pred[i]) if v == "TRUE")
                out.append("TRUE" if t >= 2 else "FALSE")
        pt, lo, hi = bootstrap_ci(gold, out, n=args.bootstrap)
        rows.append((f"md(conf>={T:.2f}) else majority(md,gm,rf)",
                     f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]", n_route))

    # Use both mDeBERTa AND Gemma high-conf, fall back when disagreement
    for T_md, T_gm in ((0.99, 0.95), (0.98, 0.95)):
        out = []
        n_route_md = n_route_gm = 0
        for i in range(len(keys)):
            if md_pred[i] == gm_pred[i]:  # agree
                out.append(md_pred[i])
            elif md_conf[i] >= T_md:
                out.append(md_pred[i])
                n_route_md += 1
            elif gm_conf[i] is not None and gm_conf[i] >= T_gm:
                out.append(gm_pred[i])
                n_route_gm += 1
            else:
                t = sum(1 for v in (md_pred[i], gm_pred[i], ll_pred[i], rf_pred[i], c4_pred[i])
                        if v == "TRUE")
                out.append("TRUE" if t > 2 else "FALSE")
        pt, lo, hi = bootstrap_ci(gold, out, n=args.bootstrap)
        rows.append((f"agree | md(>={T_md:.2f}) | gm(>={T_gm:.2f}) | maj5",
                     f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]", f"md={n_route_md} gm={n_route_gm}"))

    _print_table(rows)

    print()
    print("=" * 78)
    print("Ambiguity-routed: keep mDeBERTa for low-ambiguity, route top X% to fallback")
    print("=" * 78)
    print("  Ambiguity scoring on v1 isAt-test:")
    margins = sorted(md[k]["margin"] for k in keys)
    ambigs = sorted((md[k]["ambiguity"] for k in keys), reverse=True)
    print(f"    margin     min/median/max = {margins[0]:.3f} / {margins[len(margins)//2]:.3f} / {margins[-1]:.3f}")
    print(f"    ambiguity  max/median/min = {ambigs[0]:.3f} / {ambigs[len(ambigs)//2]:.3f} / {ambigs[-1]:.3f}")
    print()

    # Sort items by ambiguity score descending; the top N are routed away from mDeBERTa.
    keys_by_ambig = sorted(range(len(keys)), key=lambda i: -md[keys[i]]["ambiguity"])

    rows = [("rule", "top X%", "n_routed", "fallback", "MR", "95% CI")]
    # RF dropped from official-test deployable strategies (degenerate due to feature drift)
    fallbacks = {
        "Gemma alone":           lambda i: gm_pred[i],
        "majority(gm, ll, c4)":  lambda i: "TRUE" if sum(1 for v in (gm_pred[i], ll_pred[i], c4_pred[i])
                                                          if v == "TRUE") >= 2 else "FALSE",
        "majority(gm, ll, rf)":  lambda i: "TRUE" if sum(1 for v in (gm_pred[i], ll_pred[i], rf_pred[i])
                                                          if v == "TRUE") >= 2 else "FALSE",
        "majority(gm, ll, c4, rf)":  lambda i: "TRUE" if sum(1 for v in (gm_pred[i], ll_pred[i],
                                                                           c4_pred[i], rf_pred[i])
                                                              if v == "TRUE") >= 2 else "FALSE",
        "4-way maj (md, gm, ll, c4)": lambda i: "TRUE" if sum(1 for v in (md_pred[i], gm_pred[i],
                                                                           ll_pred[i], c4_pred[i])
                                                              if v == "TRUE") >= 2 else "FALSE",
    }
    for X in (10, 20, 30, 40, 50):
        n_route = int(round(X / 100.0 * len(keys)))
        routed_set = set(keys_by_ambig[:n_route])
        for fb_name, fb_fn in fallbacks.items():
            out = []
            for i in range(len(keys)):
                if i in routed_set:
                    out.append(fb_fn(i))
                else:
                    out.append(md_pred[i])
            pt, lo, hi = bootstrap_ci(gold, out, n=args.bootstrap)
            rows.append(("ambig-route mDeBERTa -> fallback", f"{X}%", n_route,
                         fb_name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print_table(rows)

    # Margin-only routing (no entropy weighting)
    print()
    print("  Same sweep but routing by raw MARGIN only (smallest |pT-pF|):")
    keys_by_margin = sorted(range(len(keys)), key=lambda i: md[keys[i]]["margin"])
    rows = [("top X%", "fallback", "MR", "95% CI")]
    for X in (10, 20, 30):
        n_route = int(round(X / 100.0 * len(keys)))
        routed_set = set(keys_by_margin[:n_route])
        for fb_name, fb_fn in fallbacks.items():
            out = [fb_fn(i) if i in routed_set else md_pred[i] for i in range(len(keys))]
            pt, lo, hi = bootstrap_ci(gold, out, n=args.bootstrap)
            rows.append((f"{X}%", fb_name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Per-class breakdown of the best candidates")
    print("=" * 78)

    def per_class(name: str, pred: list[str]) -> None:
        from collections import Counter
        cm = {("TRUE", "TRUE"): 0, ("TRUE", "FALSE"): 0,
              ("FALSE", "TRUE"): 0, ("FALSE", "FALSE"): 0}
        for g, p in zip(gold, pred):
            cm[(g, p)] = cm.get((g, p), 0) + 1
        rec_T = cm[("TRUE", "TRUE")] / max(1, cm[("TRUE", "TRUE")] + cm[("TRUE", "FALSE")])
        rec_F = cm[("FALSE", "FALSE")] / max(1, cm[("FALSE", "FALSE")] + cm[("FALSE", "TRUE")])
        prec_T = cm[("TRUE", "TRUE")] / max(1, cm[("TRUE", "TRUE")] + cm[("FALSE", "TRUE")])
        n_pred_T = sum(1 for x in pred if x == "TRUE")
        print(f"  {name:<46}  rec_T={rec_T:.3f}  rec_F={rec_F:.3f}  prec_T={prec_T:.3f}  n_pred_TRUE={n_pred_T}")

    per_class("mDeBERTa alone", md_pred)
    per_class("Gemma alone", gm_pred)
    per_class("majority(md, gm, ll)", majority_n(list(zip(md_pred, gm_pred, ll_pred))))
    per_class(">=2 of 5 say TRUE",
              ["TRUE" if sum(1 for v in vs if v == "TRUE") >= 2 else "FALSE"
               for vs in zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred)])
    out = []
    for i in range(len(keys)):
        if md_pred[i] == gm_pred[i]:
            out.append(md_pred[i])
        elif md_conf[i] >= 0.99:
            out.append(md_pred[i])
        elif gm_conf[i] is not None and gm_conf[i] >= 0.95:
            out.append(gm_pred[i])
        else:
            t = sum(1 for v in (md_pred[i], gm_pred[i], ll_pred[i], rf_pred[i], c4_pred[i]) if v == "TRUE")
            out.append("TRUE" if t > 2 else "FALSE")
    per_class("agree | md(>=0.99) | gm(>=0.95) | maj5", out)

    # Sweep thresholds for the "k of 5 say TRUE" rule
    print()
    print("  k-of-5 sweep:")
    rows = [("rule", "MR", "rec_T", "rec_F", "n_pred_TRUE")]
    for k in (1, 2, 3, 4, 5):
        s = ["TRUE" if sum(1 for v in vs if v == "TRUE") >= k else "FALSE"
             for vs in zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred)]
        cm = {("TRUE","TRUE"):0,("TRUE","FALSE"):0,("FALSE","TRUE"):0,("FALSE","FALSE"):0}
        for g, p in zip(gold, s):
            cm[(g, p)] = cm.get((g, p), 0) + 1
        rec_T = cm[("TRUE", "TRUE")] / max(1, cm[("TRUE", "TRUE")] + cm[("TRUE", "FALSE")])
        rec_F = cm[("FALSE", "FALSE")] / max(1, cm[("FALSE", "FALSE")] + cm[("FALSE", "TRUE")])
        n_pred_T = sum(1 for x in s if x == "TRUE")
        mr = (rec_T + rec_F) / 2
        rows.append((f">={k}/5", f"{mr:.4f}", f"{rec_T:.3f}", f"{rec_F:.3f}", n_pred_T))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Oracle ceilings (informational)")
    print("=" * 78)
    # 3-way oracle
    for label, votes in [
        ("any of (md, gm, ll) right", list(zip(md_pred, gm_pred, ll_pred))),
        ("any of (md, gm, rf) right", list(zip(md_pred, gm_pred, rf_pred))),
        ("any of all 5 right",        list(zip(md_pred, gm_pred, ll_pred, rf_pred, c4_pred))),
    ]:
        out = [g if g in vs else vs[0] for vs, g in zip(votes, gold)]
        pt = macro_recall(gold, out)
        print(f"  Oracle ({label}): {pt:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
