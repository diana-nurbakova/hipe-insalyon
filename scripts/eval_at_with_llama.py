"""Re-run at-task ensembles now that we have Llama predictions on the full v1 set.

Uses logs/llm_full/llama_33_70b_PAB_full_dataset_predictions.jsonl (1251 rows)
to evaluate strategies that include Llama on the 188-triplet val split (mDeBERTa's
at-test split).
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from hipe.evaluation.metrics import AT_LABELS, compute_macro_recall, null_to_false
from hipe.stacker import AT_ORDINAL_MAP, apply_lookup, build_lookup_table


REPO = Path(__file__).resolve().parent.parent
XLM_AT = REPO / "runs/materials/xml_roberta_at_result.csv"
MD_AT = REPO / "runs/runs_mdeberta/runs/at_task_prediction_result_updated.csv"
RF_OOF = REPO / "logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl"
C4_OOF = REPO / "logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl"
ORD_OOF = REPO / "logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl"
GEMMA_FULL = REPO / "logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl"
LLAMA_FULL = REPO / "logs/llm_full/llama_33_70b_PAB_full_dataset_predictions.jsonl"
V1_CSV = REPO / "data/v1_baseline_train_test_ids.csv"


def load_csv(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            out[k] = {"pred": r["pred_label"], "true": r["true_label"]}
    return out


def load_jsonl(path, field="at_predicted"):
    out = {}
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            k = (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])
            out[k] = d.get(field)
    return out


def macro_recall(g, p): return compute_macro_recall(g, p, label_set=list(AT_LABELS))["macro_recall"]


def bootstrap_ci(g, p, n=2000, seed=42):
    rng = np.random.default_rng(seed)
    pt = macro_recall(g, p)
    samples = []
    for _ in range(n):
        idx = rng.integers(0, len(g), len(g))
        samples.append(macro_recall([g[i] for i in idx], [p[i] for i in idx]))
    samples.sort()
    return pt, samples[int(0.025 * n)], samples[int(0.975 * n)]


def plurality_at(votes):
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


def _print(rows):
    if not rows: return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def main():
    xlm = load_csv(XLM_AT)
    md = load_csv(MD_AT)
    rf = load_jsonl(RF_OOF)
    c4 = load_jsonl(C4_OOF)
    ord_p = load_jsonl(ORD_OOF)
    gemma = load_jsonl(GEMMA_FULL)
    llama = load_jsonl(LLAMA_FULL)

    v1 = {}
    with open(V1_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["task"] == "at":
                v1[(r["document_id"], r["pers_entity_id"], r["loc_entity_id"])] = r["at_label"]

    test_keys = [k for k in xlm if k in md and k in rf and k in c4 and k in ord_p
                 and k in gemma and k in llama]
    train_keys = [k for k in v1 if k not in xlm and k in rf and k in c4 and k in ord_p
                  and k in gemma and k in llama]
    print(f"  test={len(test_keys)}  train={len(train_keys)}")

    gold = [xlm[k]["true"] for k in test_keys]
    xlm_p = [xlm[k]["pred"] for k in test_keys]
    md_p = [null_to_false(md[k]["pred"]) for k in test_keys]
    rf_p = [null_to_false(rf[k]) for k in test_keys]
    c4_p = [null_to_false(c4[k]) for k in test_keys]
    ord_pred = [null_to_false(ord_p[k]) for k in test_keys]
    gm_p = [null_to_false(gemma[k]) for k in test_keys]
    ll_p = [null_to_false(llama[k]) for k in test_keys]

    # Llama standalone
    print()
    print("=" * 78)
    print("Llama 3.3 70B PAB — standalone MR(at) on the 188 val split")
    print("=" * 78)
    pt, lo, hi = bootstrap_ci(gold, ll_p)
    print(f"  Llama standalone MR(at) = {pt:.4f}  CI=[{lo:.4f}, {hi:.4f}]")
    cnt = Counter(ll_p)
    print(f"  Llama predictions: {dict(cnt)}")
    # rec per class
    for lab in AT_LABELS:
        n_g = sum(1 for g in gold if g == lab)
        if n_g == 0: continue
        c = sum(1 for g, q in zip(gold, ll_p) if g == lab and q == lab)
        print(f"    rec_{lab}: {c}/{n_g} = {c / n_g:.3f}")

    # Build a 4-key stacker variant with Llama replacing Gemma
    print()
    print("=" * 78)
    print("4-key stacker variants (lookup tables on 1062-triplet train)")
    print("=" * 78)
    train_gold = [v1[k] for k in train_keys]
    rows = [("base models", "MR(at)", "95% CI", "lookup_size", "n_seen")]
    for name, models in [
        ("RF, C4, Ord, Gemma  [Run-1 baseline]", {"RF": rf, "C4": c4, "Ord": ord_p, "Gm": gemma}),
        ("RF, C4, Ord, Llama",                   {"RF": rf, "C4": c4, "Ord": ord_p, "Ll": llama}),
        ("RF, C4, Gemma, Llama",                 {"RF": rf, "C4": c4, "Gm": gemma, "Ll": llama}),
        ("RF, Ord, Gemma, Llama",                {"RF": rf, "Ord": ord_p, "Gm": gemma, "Ll": llama}),
    ]:
        train_v = {n: [null_to_false(s[k]) for k in train_keys] for n, s in models.items()}
        test_v = {n: [null_to_false(s[k]) for k in test_keys] for n, s in models.items()}
        lookup = build_lookup_table(train_v, train_gold, tiebreaker="alphabetical",
                                     ordinal_map=AT_ORDINAL_MAP)
        preds = apply_lookup(test_v, lookup, fallback="label", fallback_label="FALSE",
                              ordinal_map=AT_ORDINAL_MAP)
        pt, lo, hi = bootstrap_ci(gold, preds)
        n_seen = sum(1 for vt in zip(*test_v.values()) if vt in lookup)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]", len(lookup),
                     f"{n_seen}/{len(test_keys)}"))

    # 5-key stacker with both LLMs
    train_v = {"RF": [null_to_false(rf[k]) for k in train_keys],
               "C4": [null_to_false(c4[k]) for k in train_keys],
               "Ord": [null_to_false(ord_p[k]) for k in train_keys],
               "Gm": [null_to_false(gemma[k]) for k in train_keys],
               "Ll": [null_to_false(llama[k]) for k in train_keys]}
    test_v = {"RF": rf_p, "C4": c4_p, "Ord": ord_pred, "Gm": gm_p, "Ll": ll_p}
    lookup = build_lookup_table(train_v, train_gold, tiebreaker="alphabetical",
                                 ordinal_map=AT_ORDINAL_MAP)
    preds = apply_lookup(test_v, lookup, fallback="label", fallback_label="FALSE",
                          ordinal_map=AT_ORDINAL_MAP)
    pt, lo, hi = bootstrap_ci(gold, preds)
    n_seen = sum(1 for vt in zip(*test_v.values()) if vt in lookup)
    rows.append(("RF, C4, Ord, Gemma, Llama  [5-key]", f"{pt:.4f}",
                 f"[{lo:.4f}, {hi:.4f}]", len(lookup), f"{n_seen}/{len(test_keys)}"))

    _print(rows)

    # Plurality strategies including Llama
    print()
    print("=" * 78)
    print("Plurality strategies including Llama (no LLM-free row repeated)")
    print("=" * 78)
    rows = [("strategy", "MR(at)", "95% CI", "uses_LLM?")]

    # Build Run-1 baseline (4-key Gemma stacker + xlm + Gemma plurality)
    train_v_g = {"RF": [null_to_false(rf[k]) for k in train_keys],
                 "C4": [null_to_false(c4[k]) for k in train_keys],
                 "Ord": [null_to_false(ord_p[k]) for k in train_keys],
                 "Gm": [null_to_false(gemma[k]) for k in train_keys]}
    test_v_g = {"RF": rf_p, "C4": c4_p, "Ord": ord_pred, "Gm": gm_p}
    lookup_g = build_lookup_table(train_v_g, train_gold, tiebreaker="alphabetical",
                                   ordinal_map=AT_ORDINAL_MAP)
    stacker_gemma = apply_lookup(test_v_g, lookup_g, fallback="label",
                                  fallback_label="FALSE", ordinal_map=AT_ORDINAL_MAP)

    # Build Llama-replacing-Gemma stacker
    train_v_l = {"RF": [null_to_false(rf[k]) for k in train_keys],
                 "C4": [null_to_false(c4[k]) for k in train_keys],
                 "Ord": [null_to_false(ord_p[k]) for k in train_keys],
                 "Ll": [null_to_false(llama[k]) for k in train_keys]}
    test_v_l = {"RF": rf_p, "C4": c4_p, "Ord": ord_pred, "Ll": ll_p}
    lookup_l = build_lookup_table(train_v_l, train_gold, tiebreaker="alphabetical",
                                   ordinal_map=AT_ORDINAL_MAP)
    stacker_llama = apply_lookup(test_v_l, lookup_l, fallback="label",
                                  fallback_label="FALSE", ordinal_map=AT_ORDINAL_MAP)

    # Run-1 vs Llama-substituted variants
    cases = [
        ("plurality(xlm, 4-stacker[Gemma], Gemma)  RUN-1",
         [plurality_at([x, s, g]) for x, s, g in zip(xlm_p, stacker_gemma, gm_p)], "yes"),
        ("plurality(xlm, 4-stacker[Llama], Llama)  Llama-only-LLM",
         [plurality_at([x, s, l]) for x, s, l in zip(xlm_p, stacker_llama, ll_p)], "yes"),
        ("plurality(xlm, mDeBERTa, Llama)         no Gemma, no stacker",
         [plurality_at([x, m, l]) for x, m, l in zip(xlm_p, md_p, ll_p)], "yes"),
        ("plurality(xlm, mDeBERTa, Gemma)",
         [plurality_at([x, m, g]) for x, m, g in zip(xlm_p, md_p, gm_p)], "yes"),
        ("plurality(xlm, mDeBERTa, RF)            RUN-3 frugal",
         [plurality_at([x, m, r]) for x, m, r in zip(xlm_p, md_p, rf_p)], "no"),
        ("plurality(xlm, mDeBERTa, RF, Llama)",
         [plurality_at([x, m, r, l]) for x, m, r, l in zip(xlm_p, md_p, rf_p, ll_p)], "yes"),
        ("plurality(xlm, mDeBERTa, RF, Gemma)",
         [plurality_at([x, m, r, g]) for x, m, r, g in zip(xlm_p, md_p, rf_p, gm_p)], "yes"),
    ]
    for name, p, llm in cases:
        pt, lo, hi = bootstrap_ci(gold, p)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]", llm))
    _print(rows)

    # mDeBERTa (Run-2) with Llama
    print()
    print("=" * 78)
    print("Disagreement: Llama vs Gemma on the 188 (which LLM is more useful?)")
    print("=" * 78)
    n_agree = sum(1 for g_, l_ in zip(gm_p, ll_p) if g_ == l_)
    print(f"  Gemma == Llama on {n_agree}/{len(gold)} ({n_agree/len(gold):.1%})")
    # Where they disagree, who's right?
    gemma_right = llama_right = both_wrong = 0
    for g_, l_, gold_ in zip(gm_p, ll_p, gold):
        if g_ == l_: continue
        if g_ == gold_: gemma_right += 1
        elif l_ == gold_: llama_right += 1
        else: both_wrong += 1
    print(f"  on disagreements ({len(gold) - n_agree}):")
    print(f"    Gemma right, Llama wrong : {gemma_right}")
    print(f"    Llama right, Gemma wrong : {llama_right}")
    print(f"    both wrong               : {both_wrong}")


if __name__ == "__main__":
    raise SystemExit(main())
