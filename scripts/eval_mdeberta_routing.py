"""Evaluate fine-tuned mDeBERTa predictions and explore confidence-routed
hybrids with Gemma / 4-model stacker.

Inputs:
  - runs/runs_mdeberta/runs/at_task_prediction_results.csv  (at, no IDs)
  - runs/runs_mdeberta/runs/isAt_task_prediction_results.csv  (isAt, with IDs)
  - logs/ablations/* JSONL prediction files for the comparison models

Note on alignment:
  - mdeberta isAt CSV has document_id / pers_entity_id / loc_entity_id columns,
    so we can join it with any other isAt-test JSONL (same 188 triplets).
  - mdeberta at CSV exposes only sample_idx (0..187) and lacks ID columns.
    The label distribution matches the v1_baseline at-test split (104 F / 18 P
    / 66 T) but the linear order does NOT match. So we evaluate at standalone
    and flag that confidence-routing for the at task needs the upstream script
    to emit document_id columns (or an explicit sample_idx -> order_index map)
    before we can align with RF / C4 / OrdContM1 / Gemma at-test predictions.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from hipe.evaluation.metrics import (
    AT_LABELS,
    ISAT_LABELS,
    classification_report,
    compute_global_score,
    compute_macro_recall,
    confusion_matrix,
    null_to_false,
)


REPO = Path(__file__).resolve().parent.parent
MD_AT = REPO / "runs/runs_mdeberta/runs/at_task_prediction_results.csv"
MD_ISAT = REPO / "runs/runs_mdeberta/runs/isAt_task_prediction_results.csv"

# Comparison models on the project's at-test split (188 instances; isAt golds
# are populated for these triplets too even though they're a different sample
# than the v1 isAt-test split).
ABL = REPO / "logs/ablations"
GEMMA_AT_TEST = ABL / "T1_llm_zeroshot_PAB_openrouter_gemma-4-31b-it_at-test_predictions.jsonl"
STACKER4_AT_TEST = ABL / "T1_hybrid_DisStacker4_RF_C4SDov_OrdContM1_Gemma_at_GemmaIsAt_predictions.jsonl"
RF_AT_TEST = ABL / "T1.4or5_mask_T1.5_handcrafted_RF_at_at-test_predictions.jsonl"
C4_AT_TEST = ABL / "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test+SDov_PROBABLE_from_FALSE_nw0.05_predictions.jsonl"
ORD_AT_TEST = ABL / "T1.4or5_mask_contrastive_ordinal_m1_at-test_predictions.jsonl"

# Llama on the v1 isAt-test split — same 188 triplets that mdeberta isAt used.
LLAMA_ISAT_TEST = ABL / "T1_llm_zeroshot_PAB_openrouter_llama-33-70b-instruct_isAt-test_predictions.jsonl"
# Gemma full-dataset (1,250 keys, covers 187/188 isAt-test triplets).
GEMMA_FULL = REPO / "logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl"


def load_md_at(path: Path) -> list[dict]:
    """Read mdeberta at CSV (no IDs)."""
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "sample_idx": int(r["sample_idx"]),
                "true": r["true_label"],
                "pred": r["pred_label"],
                "confidence": float(r["confidence"]),
                "prob_FALSE": float(r["prob_FALSE"]),
                "prob_TRUE": float(r["prob_TRUE"]),
                "prob_PROBABLE": float(r["prob_PROBABLE"]),
            })
    rows.sort(key=lambda d: d["sample_idx"])
    return rows


def load_md_isat(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "sample_idx": int(r["sample_idx"]),
                "key": (r["document_id"], r["pers_entity_id"], r["loc_entity_id"]),
                "true": r["true_label"],
                "pred": r["pred_label"],
                "confidence": float(r["confidence"]),
                "prob_FALSE": float(r["prob_FALSE"]),
                "prob_TRUE": float(r["prob_TRUE"]),
            })
    rows.sort(key=lambda d: d["sample_idx"])
    return rows


def load_jsonl_preds(path: Path) -> dict[tuple, dict]:
    """Index a model's JSONL predictions by (doc, pers, loc)."""
    out: dict[tuple, dict] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            key = (d["document_id"], d["pers_entity_id"], d["loc_entity_id"])
            out[key] = d
    return out


def _print_table(rows: list[tuple]) -> None:
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def _eval_block(name: str, gold: list[str], pred: list[str], labels: tuple[str, ...]) -> dict:
    mr = compute_macro_recall(gold, pred, label_set=list(labels))
    cm = confusion_matrix(gold, pred, list(labels))
    cr = classification_report(gold, pred, list(labels))
    print(f"\n[{name}]  n={len(gold)}  macro_recall={mr['macro_recall']:.4f}")
    rows = [("label", "recall", "precision", "f1", "support")]
    for lab in labels:
        rec = mr[f"recall_{lab}"]
        cri = cr.get(lab, {})
        rows.append((
            lab,
            f"{rec:.3f}" if rec is not None else "n/a",
            f"{cri.get('precision', 0):.3f}",
            f"{cri.get('f1-score', 0):.3f}",
            cri.get("support", 0),
        ))
    _print_table(rows)
    print("  confusion (rows=gold, cols=pred):")
    print("    " + " ".join(f"{l:>9}" for l in labels))
    for i, lab in enumerate(labels):
        print(f"    {lab:>9} " + " ".join(f"{cm[i][j]:>9}" for j in range(len(labels))))
    return {"macro_recall": mr["macro_recall"], "per_label": mr, "confusion": cm}


def evaluate_standalone(md_at: list[dict], md_isat: list[dict]) -> None:
    print("=" * 78)
    print("mDeBERTa standalone — val/test split from v1_baseline")
    print("=" * 78)
    at_gold = [null_to_false(r["true"]) for r in md_at]
    at_pred = [null_to_false(r["pred"]) for r in md_at]
    isat_gold = [null_to_false(r["true"]) for r in md_isat]
    isat_pred = [null_to_false(r["pred"]) for r in md_isat]

    _eval_block("at  (n=188 v1 at-test split)", at_gold, at_pred, AT_LABELS)
    _eval_block("isAt (n=188 v1 isAt-test split)", isat_gold, isat_pred, ISAT_LABELS)

    # We CANNOT compute the official "global" combining mdeberta at + mdeberta
    # isAt as-is because the two splits cover different triplets. We report the
    # arithmetic mean for orientation only.
    g = compute_global_score(at_gold, at_pred, isat_gold, isat_pred)
    print(f"\n[unofficial — different splits] mean(MR_at, MR_isAt) = {g['global_score']:.4f}")


def evaluate_at_comparison(md_at: list[dict]) -> None:
    """For the at task, we have mdeberta predictions on at-test (no IDs) and
    JSONL preds for RF / C4 / OrdContM1 / Gemma / 4-model stacker on the same
    188 at-test triplets. Compute MR(at) for each on the at-test split.
    """
    print()
    print("=" * 78)
    print("at task — comparison on the v1 at-test split (n=188)")
    print("=" * 78)

    md_gold = [null_to_false(r["true"]) for r in md_at]
    md_pred = [null_to_false(r["pred"]) for r in md_at]
    md_mr = compute_macro_recall(md_gold, md_pred, label_set=list(AT_LABELS))["macro_recall"]

    rows = [("model", "MR(at)")]
    rows.append(("mDeBERTa-v3 fine-tuned", f"{md_mr:.4f}"))
    for label, path in [
        ("RF (handcrafted)", RF_AT_TEST),
        ("C4-SDov (mask+e1+e2+temp)", C4_AT_TEST),
        ("OrdContM1 (contrastive)", ORD_AT_TEST),
        ("Gemma-4-31b PAB", GEMMA_AT_TEST),
        ("4-model disagreement stacker", STACKER4_AT_TEST),
    ]:
        if not path.exists():
            rows.append((label, "missing"))
            continue
        gold, pred = [], []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                g = null_to_false(d.get("at_gold"))
                p = null_to_false(d.get("at_predicted"))
                if g in AT_LABELS and p in AT_LABELS:
                    gold.append(g)
                    pred.append(p)
        mr = compute_macro_recall(gold, pred, label_set=list(AT_LABELS))["macro_recall"]
        rows.append((label, f"{mr:.4f}  (n={len(gold)})"))
    _print_table(rows)


def evaluate_isat_comparison(md_isat: list[dict]) -> None:
    """For isAt, mdeberta covers 188 v1 isAt-test triplets. Gemma full-dataset
    covers 187/188; Llama-PAB covers all 188. Compare on the aligned subsets."""
    print()
    print("=" * 78)
    print("isAt task — comparison on the v1 isAt-test split (n=188)")
    print("=" * 78)

    md_by_key = {r["key"]: r for r in md_isat}
    keys = [r["key"] for r in md_isat]

    md_gold = [null_to_false(md_by_key[k]["true"]) for k in keys]
    md_pred = [null_to_false(md_by_key[k]["pred"]) for k in keys]
    md_mr = compute_macro_recall(md_gold, md_pred, label_set=list(ISAT_LABELS))["macro_recall"]

    rows = [("model", "MR(isAt)", "n_aligned")]
    rows.append(("mDeBERTa-v3 fine-tuned", f"{md_mr:.4f}", str(len(keys))))

    if GEMMA_FULL.exists():
        gemma = load_jsonl_preds(GEMMA_FULL)
        gold, pred = [], []
        for k in keys:
            d = gemma.get(k)
            if d is None:
                continue
            gold.append(null_to_false(d.get("isAt_gold")))
            pred.append(null_to_false(d.get("isAt_predicted")))
        mr = compute_macro_recall(gold, pred, label_set=list(ISAT_LABELS))["macro_recall"]
        rows.append(("Gemma-4-31b PAB (full-dataset)", f"{mr:.4f}", str(len(gold))))

    if LLAMA_ISAT_TEST.exists():
        llama = load_jsonl_preds(LLAMA_ISAT_TEST)
        gold, pred = [], []
        for k in keys:
            d = llama.get(k)
            if d is None:
                continue
            gold.append(null_to_false(d.get("isAt_gold")))
            pred.append(null_to_false(d.get("isAt_predicted")))
        mr = compute_macro_recall(gold, pred, label_set=list(ISAT_LABELS))["macro_recall"]
        rows.append(("Llama-3.3-70b PAB", f"{mr:.4f}", str(len(gold))))
    _print_table(rows)


def routing_isat(md_isat: list[dict], thresholds: list[float]) -> None:
    """Confidence-routed hybrid: keep mdeberta where confidence >= T, else use Llama."""
    print()
    print("=" * 78)
    print("Confidence-routed hybrid for isAt (mDeBERTa keep >= T, else Gemma-PAB)")
    print("=" * 78)
    if not GEMMA_FULL.exists():
        print(f"  [skip] Gemma full-dataset JSONL not found at {GEMMA_FULL}")
        return

    partner = load_jsonl_preds(GEMMA_FULL)
    keys = [r["key"] for r in md_isat if r["key"] in partner]
    n_skipped = sum(1 for r in md_isat if r["key"] not in partner)
    if n_skipped:
        print(f"  [warn] {n_skipped} mdeberta keys missing from Gemma; restricted to n={len(keys)}")
    md_by_key = {r["key"]: r for r in md_isat}
    gold = [null_to_false(md_by_key[k]["true"]) for k in keys]

    # baselines on the aligned subset
    md_pred = [null_to_false(md_by_key[k]["pred"]) for k in keys]
    p_pred = [null_to_false(partner[k]["isAt_predicted"]) for k in keys]
    md_mr = compute_macro_recall(gold, md_pred, label_set=list(ISAT_LABELS))["macro_recall"]
    p_mr = compute_macro_recall(gold, p_pred, label_set=list(ISAT_LABELS))["macro_recall"]
    print(f"  baseline mDeBERTa MR(isAt) = {md_mr:.4f}")
    print(f"  baseline Gemma    MR(isAt) = {p_mr:.4f}")

    rows = [("threshold", "kept_md", "fallback_gemma", "MR(isAt)")]
    for T in thresholds:
        hybrid = []
        n_kept = 0
        for k in keys:
            mr = md_by_key[k]
            if mr["confidence"] >= T:
                hybrid.append(null_to_false(mr["pred"]))
                n_kept += 1
            else:
                hybrid.append(null_to_false(partner[k]["isAt_predicted"]))
        mr_score = compute_macro_recall(gold, hybrid, label_set=list(ISAT_LABELS))["macro_recall"]
        rows.append((f"{T:.2f}", n_kept, len(keys) - n_kept, f"{mr_score:.4f}"))
    _print_table(rows)

    print("\n  Mirrored — agreement-or-X:")
    for label, when_disagree in [("keep mDeBERTa", "md"), ("keep Gemma", "gemma")]:
        hybrid = []
        for k in keys:
            mr = md_by_key[k]
            l = null_to_false(partner[k]["isAt_predicted"])
            m = null_to_false(mr["pred"])
            if m == l:
                hybrid.append(m)
            else:
                hybrid.append(m if when_disagree == "md" else l)
        mr_score = compute_macro_recall(gold, hybrid, label_set=list(ISAT_LABELS))["macro_recall"]
        print(f"    {label} on disagreement: MR(isAt) = {mr_score:.4f}")


def disagreement_isat(md_isat: list[dict], partner: str = "gemma") -> None:
    """Anatomy of mDeBERTa vs <partner> disagreement on isAt-test (n=188).

    Tells us where each model is right/wrong when they disagree, and whether
    confidence (mdeberta) or class-conditional routing can pick the winner.
    """
    print()
    print("=" * 78)
    if partner == "gemma":
        print("Disagreement analysis: mDeBERTa vs Gemma-4-31b PAB on v1 isAt-test")
        print("=" * 78)
        if not GEMMA_FULL.exists():
            print(f"  [skip] Gemma full-dataset JSONL not found at {GEMMA_FULL}")
            return
        partner_preds = load_jsonl_preds(GEMMA_FULL)
        partner_label = "Gemma"
    else:
        print(f"Disagreement analysis: mDeBERTa vs Llama-PAB on v1 isAt-test")
        print("=" * 78)
        if not LLAMA_ISAT_TEST.exists():
            return
        partner_preds = load_jsonl_preds(LLAMA_ISAT_TEST)
        partner_label = "Llama"

    keys = [r["key"] for r in md_isat if r["key"] in partner_preds]
    n_skipped = sum(1 for r in md_isat if r["key"] not in partner_preds)
    if n_skipped:
        print(f"  [warn] {n_skipped} mdeberta keys missing from {partner_label} predictions; skipped")
    md_by_key = {r["key"]: r for r in md_isat}

    n = len(keys)
    agree = 0
    md_right_dis = 0
    llama_right_dis = 0
    both_wrong_dis = 0
    by_class_dis: dict[tuple[str, str], int] = {}
    by_lang_dis: dict[str, dict[str, int]] = {}
    by_lang_total: dict[str, int] = {}
    md_disagree_winrate_by_conf: dict[str, list[int]] = {}
    md_disagree_rows: list[dict] = []

    for k in keys:
        m_row = md_by_key[k]
        m = null_to_false(m_row["pred"])
        g = null_to_false(m_row["true"])
        l = null_to_false(partner_preds[k]["isAt_predicted"])
        lang = partner_preds[k].get("language", "?")
        by_lang_total[lang] = by_lang_total.get(lang, 0) + 1
        if m == l:
            agree += 1
            continue
        # disagreement
        bucket = by_lang_dis.setdefault(lang, {"total": 0, "md_right": 0, "llama_right": 0, "both_wrong": 0})
        bucket["total"] += 1
        cell = (m, l)
        by_class_dis[cell] = by_class_dis.get(cell, 0) + 1
        if m == g and l != g:
            md_right_dis += 1
            bucket["md_right"] += 1
        elif l == g and m != g:
            llama_right_dis += 1
            bucket["llama_right"] += 1
        else:
            both_wrong_dis += 1
            bucket["both_wrong"] += 1
        # bin mdeberta confidence on disagreements
        c = m_row["confidence"]
        if c >= 0.99:
            cb = ">=0.99"
        elif c >= 0.97:
            cb = "0.97-0.99"
        elif c >= 0.95:
            cb = "0.95-0.97"
        elif c >= 0.90:
            cb = "0.90-0.95"
        else:
            cb = "<0.90"
        md_disagree_winrate_by_conf.setdefault(cb, []).append(1 if m == g else 0)
        md_disagree_rows.append({
            "key": k, "lang": lang, "gold": g, "md": m, "llama": l, "conf": c,
        })

    print(f"  total n={n}  agree={agree}  disagree={n-agree}  ({(n-agree)/n:.1%})")
    print(f"  on disagreements ({n-agree}):")
    print(f"    mDeBERTa right, {partner_label} wrong : {md_right_dis}")
    print(f"    {partner_label} right, mDeBERTa wrong : {llama_right_dis}")
    print(f"    both wrong                  : {both_wrong_dis}")
    print()
    print(f"  disagreement cells (mDeBERTa, {partner_label}) -> count:")
    for cell, c in sorted(by_class_dis.items(), key=lambda x: -x[1]):
        print(f"    md={cell[0]:<6}  llama={cell[1]:<6}  n={c}")

    print()
    print("  per-language breakdown of disagreement:")
    rows = [("lang", "n_total", "n_disagree", "md_right", "llama_right", "both_wrong")]
    for lang in sorted(by_lang_dis):
        b = by_lang_dis[lang]
        rows.append((lang, by_lang_total[lang], b["total"], b["md_right"], b["llama_right"], b["both_wrong"]))
    _print_table(rows)

    print()
    print("  mDeBERTa win-rate on disagreement, by mDeBERTa confidence:")
    rows = [("conf bin", "n_disagree", "md_winrate", f"{partner_label.lower()}_winrate", "both_wrong")]
    for cb in [">=0.99", "0.97-0.99", "0.95-0.97", "0.90-0.95", "<0.90"]:
        wins = md_disagree_winrate_by_conf.get(cb, [])
        if not wins:
            continue
        # Also need Llama win count and both-wrong count for the bin — recompute
        md_w = sum(wins)
        # Llama wins where md is wrong AND llama right (we recorded only md right above)
        # easier to recompute from md_disagree_rows
        rows_in_bin = [r for r in md_disagree_rows
                       if (r["conf"] >= 0.99 and cb == ">=0.99")
                       or (0.97 <= r["conf"] < 0.99 and cb == "0.97-0.99")
                       or (0.95 <= r["conf"] < 0.97 and cb == "0.95-0.97")
                       or (0.90 <= r["conf"] < 0.95 and cb == "0.90-0.95")
                       or (r["conf"] < 0.90 and cb == "<0.90")]
        n_b = len(rows_in_bin)
        l_w = sum(1 for r in rows_in_bin if r["llama"] == r["gold"] and r["md"] != r["gold"])
        bw = sum(1 for r in rows_in_bin if r["md"] != r["gold"] and r["llama"] != r["gold"])
        md_rate = md_w / n_b if n_b else 0.0
        l_rate = l_w / n_b if n_b else 0.0
        rows.append((cb, n_b, f"{md_rate:.3f}", f"{l_rate:.3f}", bw))
    _print_table(rows)


def disagreement_isat_3way(md_isat: list[dict]) -> None:
    """3-way disagreement table on isAt-test: mDeBERTa, Gemma full-dataset, Llama-PAB."""
    print()
    print("=" * 78)
    print("3-way comparison on v1 isAt-test: mDeBERTa, Gemma, Llama (n=187)")
    print("=" * 78)
    if not (GEMMA_FULL.exists() and LLAMA_ISAT_TEST.exists()):
        print("  [skip] missing one of Gemma full-dataset / Llama isAt-test")
        return
    gemma = load_jsonl_preds(GEMMA_FULL)
    llama = load_jsonl_preds(LLAMA_ISAT_TEST)
    keys = [r["key"] for r in md_isat if r["key"] in gemma and r["key"] in llama]
    md_by_key = {r["key"]: r for r in md_isat}

    # tally agreement patterns
    pattern_counts: dict[str, int] = {}
    pattern_correct: dict[str, int] = {}
    by_lang: dict[str, dict[str, int]] = {}
    for k in keys:
        m = null_to_false(md_by_key[k]["pred"])
        gm = null_to_false(gemma[k]["isAt_predicted"])
        ll = null_to_false(llama[k]["isAt_predicted"])
        g = null_to_false(md_by_key[k]["true"])
        lang = gemma[k].get("language", "?")

        # which models agree with each other?
        agree_md_gm = (m == gm)
        agree_md_ll = (m == ll)
        agree_gm_ll = (gm == ll)
        if agree_md_gm and agree_md_ll:
            pattern = "all_agree"
        elif agree_md_gm:
            pattern = "md=gm vs ll"
        elif agree_md_ll:
            pattern = "md=ll vs gm"
        elif agree_gm_ll:
            pattern = "gm=ll vs md"
        else:
            pattern = "all_differ_2vs1"  # impossible w/ 2-class isAt

        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        # count which label is correct under each pattern
        pattern_correct.setdefault(pattern, 0)
        # who wins?
        winners = []
        if m == g: winners.append("md")
        if gm == g: winners.append("gm")
        if ll == g: winners.append("ll")
        bucket = by_lang.setdefault(lang, {})
        bucket[pattern] = bucket.get(pattern, 0) + 1

    rows = [("pattern", "n", "fraction")]
    for p, c in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        rows.append((p, c, f"{c/len(keys):.3f}"))
    _print_table(rows)

    # MR for each disagreement pattern when each model is right
    print()
    print("  Per-pattern: which model is correct?")
    rows2 = [("pattern", "n", "md_right", "gm_right", "ll_right", "all_right", "all_wrong")]
    for p in sorted(pattern_counts):
        n_p = 0
        md_r = gm_r = ll_r = all_r = all_w = 0
        for k in keys:
            m = null_to_false(md_by_key[k]["pred"])
            gm = null_to_false(gemma[k]["isAt_predicted"])
            ll = null_to_false(llama[k]["isAt_predicted"])
            g = null_to_false(md_by_key[k]["true"])
            agree_md_gm = (m == gm)
            agree_md_ll = (m == ll)
            agree_gm_ll = (gm == ll)
            if agree_md_gm and agree_md_ll:
                pat = "all_agree"
            elif agree_md_gm:
                pat = "md=gm vs ll"
            elif agree_md_ll:
                pat = "md=ll vs gm"
            elif agree_gm_ll:
                pat = "gm=ll vs md"
            else:
                pat = "all_differ_2vs1"
            if pat != p:
                continue
            n_p += 1
            mc, gc, lc = (m == g), (gm == g), (ll == g)
            if mc: md_r += 1
            if gc: gm_r += 1
            if lc: ll_r += 1
            if mc and gc and lc: all_r += 1
            if not (mc or gc or lc): all_w += 1
        rows2.append((p, n_p, md_r, gm_r, ll_r, all_r, all_w))
    _print_table(rows2)

    # 3-way ensembles
    print()
    print("  Ensemble strategies on n={}:".format(len(keys)))
    gold = [null_to_false(md_by_key[k]["true"]) for k in keys]
    md_p = [null_to_false(md_by_key[k]["pred"]) for k in keys]
    gm_p = [null_to_false(gemma[k]["isAt_predicted"]) for k in keys]
    ll_p = [null_to_false(llama[k]["isAt_predicted"]) for k in keys]

    # majority vote (with isAt 2-class, ties broken by Gemma since strongest standalone)
    def maj(votes):
        c = sum(1 for v in votes if v == "TRUE")
        if c >= 2: return "TRUE"
        return "FALSE"

    rows3 = [("strategy", "MR(isAt)")]
    s = [maj([m, g, l]) for m, g, l in zip(md_p, gm_p, ll_p)]
    rows3.append(("majority vote (md,gm,ll)",
                  f"{compute_macro_recall(gold, s, label_set=list(ISAT_LABELS))['macro_recall']:.4f}"))

    # union TRUE
    s = ["TRUE" if any(v == "TRUE" for v in (m, g, l)) else "FALSE" for m, g, l in zip(md_p, gm_p, ll_p)]
    rows3.append(("TRUE if ANY says TRUE",
                  f"{compute_macro_recall(gold, s, label_set=list(ISAT_LABELS))['macro_recall']:.4f}"))

    # intersection TRUE
    s = ["TRUE" if all(v == "TRUE" for v in (m, g, l)) else "FALSE" for m, g, l in zip(md_p, gm_p, ll_p)]
    rows3.append(("TRUE if ALL say TRUE",
                  f"{compute_macro_recall(gold, s, label_set=list(ISAT_LABELS))['macro_recall']:.4f}"))

    # mDeBERTa high-conf else majority
    for T in (0.99, 0.98, 0.97, 0.95):
        s = []
        for k, m, gm, ll in zip(keys, md_p, gm_p, ll_p):
            if md_by_key[k]["confidence"] >= T:
                s.append(m)
            else:
                s.append(maj([m, gm, ll]))
        rows3.append((f"md (conf>={T:.2f}) else majority(md,gm,ll)",
                      f"{compute_macro_recall(gold, s, label_set=list(ISAT_LABELS))['macro_recall']:.4f}"))
    # md hi-conf else gemma alone
    for T in (0.99, 0.98):
        s = []
        for k, m, gm in zip(keys, md_p, gm_p):
            s.append(m if md_by_key[k]["confidence"] >= T else gm)
        rows3.append((f"md (conf>={T:.2f}) else Gemma",
                      f"{compute_macro_recall(gold, s, label_set=list(ISAT_LABELS))['macro_recall']:.4f}"))

    # oracle 3-way
    s = []
    for m, gm, ll, g in zip(md_p, gm_p, ll_p, gold):
        if g in (m, gm, ll):
            s.append(g)
        else:
            s.append(m)
    rows3.append(("Oracle (any of 3 right)",
                  f"{compute_macro_recall(gold, s, label_set=list(ISAT_LABELS))['macro_recall']:.4f}"))
    _print_table(rows3)


def routing_isat_per_class(md_isat: list[dict]) -> None:
    """Class-conditional routing: keep mdeberta only when its predicted class
    has good precision (FALSE), else fall back to Gemma. Plus oracle ceiling.
    """
    print()
    print("=" * 78)
    print("Per-class routing for isAt (mDeBERTa where pred-class is reliable)")
    print("=" * 78)
    if not GEMMA_FULL.exists():
        return
    partner = load_jsonl_preds(GEMMA_FULL)
    keys = [r["key"] for r in md_isat if r["key"] in partner]
    md_by_key = {r["key"]: r for r in md_isat}
    gold = [null_to_false(md_by_key[k]["true"]) for k in keys]
    md_pred = [null_to_false(md_by_key[k]["pred"]) for k in keys]
    p_pred = [null_to_false(partner[k]["isAt_predicted"]) for k in keys]

    s1 = [m if m == "FALSE" else l for m, l in zip(md_pred, p_pred)]
    mr1 = compute_macro_recall(gold, s1, label_set=list(ISAT_LABELS))["macro_recall"]
    s2 = [l if l == "FALSE" else m for m, l in zip(md_pred, p_pred)]
    mr2 = compute_macro_recall(gold, s2, label_set=list(ISAT_LABELS))["macro_recall"]
    s3 = ["TRUE" if (m == "TRUE" or l == "TRUE") else "FALSE" for m, l in zip(md_pred, p_pred)]
    mr3 = compute_macro_recall(gold, s3, label_set=list(ISAT_LABELS))["macro_recall"]
    s4 = ["TRUE" if (m == "TRUE" and l == "TRUE") else "FALSE" for m, l in zip(md_pred, p_pred)]
    mr4 = compute_macro_recall(gold, s4, label_set=list(ISAT_LABELS))["macro_recall"]

    rows = [("strategy", "MR(isAt)")]
    rows.append(("S1: mDeBERTa where it says FALSE, else Gemma", f"{mr1:.4f}"))
    rows.append(("S2: Gemma where it says FALSE, else mDeBERTa", f"{mr2:.4f}"))
    rows.append(("S3: TRUE if ANY says TRUE (union)",             f"{mr3:.4f}"))
    rows.append(("S4: TRUE only if BOTH say TRUE (intersection)", f"{mr4:.4f}"))
    s_oracle = [m if m == g else (l if l == g else m) for m, l, g in zip(md_pred, p_pred, gold)]
    mr_o = compute_macro_recall(gold, s_oracle, label_set=list(ISAT_LABELS))["macro_recall"]
    rows.append(("Oracle (pick winner per item)", f"{mr_o:.4f}"))
    _print_table(rows)


def confidence_distribution(md_at: list[dict], md_isat: list[dict]) -> None:
    print()
    print("=" * 78)
    print("Confidence distribution (where the model is right vs. wrong)")
    print("=" * 78)
    for name, rows, labels in [
        ("at",   md_at,   AT_LABELS),
        ("isAt", md_isat, ISAT_LABELS),
    ]:
        bins = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 1.01]
        print(f"  task={name}")
        print("    conf-bin              n   acc")
        for lo, hi in zip(bins[:-1], bins[1:]):
            n = sum(1 for r in rows if lo <= r["confidence"] < hi)
            if n == 0:
                continue
            correct = sum(1 for r in rows if lo <= r["confidence"] < hi
                          and null_to_false(r["true"]) == null_to_false(r["pred"]))
            print(f"    [{lo:.2f}, {hi:.2f})    {n:4d}   {correct/n:.3f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md-at", default=str(MD_AT))
    ap.add_argument("--md-isat", default=str(MD_ISAT))
    ap.add_argument("--thresholds", type=float, nargs="*",
                    default=[0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99])
    args = ap.parse_args()

    md_at = load_md_at(Path(args.md_at))
    md_isat = load_md_isat(Path(args.md_isat))

    evaluate_standalone(md_at, md_isat)
    evaluate_at_comparison(md_at)
    evaluate_isat_comparison(md_isat)
    confidence_distribution(md_at, md_isat)
    disagreement_isat(md_isat, partner="gemma")
    disagreement_isat(md_isat, partner="llama")
    disagreement_isat_3way(md_isat)
    routing_isat(md_isat, args.thresholds)
    routing_isat_per_class(md_isat)

    print()
    print("=" * 78)
    print("Notes on at-task confidence routing")
    print("=" * 78)
    print("  mdeberta at CSV exposes only sample_idx (0..187), not the ")
    print("  (document_id, pers_entity_id, loc_entity_id) triplet. Linear ")
    print("  mapping sample_idx+1 -> order_index doesn't reproduce the at-test ")
    print("  label sequence, so we cannot deterministically join with RF / C4 / ")
    print("  OrdContM1 / Gemma at-test predictions. To unblock the at-task ")
    print("  routing experiment, re-emit the at predictions CSV with the same ")
    print("  ID columns as the isAt CSV (or write a sample_idx -> order_index ")
    print("  map alongside).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
