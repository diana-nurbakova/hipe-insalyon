"""Rebuild the disagreement-stacker on mDeBERTa's at-task train/test split.

mDeBERTa used a different 80/20 split (1063/188) than v1_baseline. To compare
ensembling on its 188 test triplets fairly, we:

  1. Identify mDeBERTa's train (1063 triplets) and test (188 triplets) by
     reading the IDs from at_task_prediction_result_updated.csv vs. the
     v1_baseline-labelled pool.
  2. Build a lookup table on the 1063-triplet train set using OOF predictions
     of {RF, C4, OrdContM1, Gemma} (leakage-free, since OOF) + the gold labels.
  3. Apply the lookup to the 188 mDeBERTa-test triplets (also using OOF) and
     compute MR(at) with bootstrap CI.
  4. Compare to plain plurality and to mDeBERTa standalone.
  5. Try a 5-key variant that also uses mDeBERTa's train predictions (note: not
     OOF, mild leakage; included for diagnostics).

The 4-key OOF-only stacker is the principled number — that's what we'd deploy
in this regime. The 5-key result tells us whether adding mDeBERTa would help
at all, motivating whether it's worth k-fold-OOF'ing mDeBERTa later.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from hipe.evaluation.metrics import (
    AT_LABELS,
    compute_macro_recall,
    null_to_false,
)
from hipe.stacker import (
    AT_ORDINAL_MAP,
    apply_lookup,
    build_lookup_table,
    cell_summary,
    loo_lookup_predictions,
)


REPO = Path(__file__).resolve().parent.parent
MD_AT = REPO / "runs/runs_mdeberta/runs/at_task_prediction_result_updated.csv"
V1_CSV = REPO / "data/v1_baseline_train_test_ids.csv"
RF_OOF = REPO / "logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl"
C4_OOF = REPO / "logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl"
ORD_OOF = REPO / "logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl"
GEMMA_FULL = REPO / "logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl"


def _key(row: dict) -> tuple[str, str, str]:
    return (row["document_id"], row["pers_entity_id"], row["loc_entity_id"])


def load_md_at(path: Path) -> dict[tuple, dict]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            out[k] = {"pred": r["pred_label"], "true": r["true_label"]}
    return out


def load_jsonl_preds(path: Path, field: str = "at_predicted") -> dict[tuple, str | None]:
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = _key(d)
            out[k] = d.get(field)
    return out


def load_v1_at_golds() -> dict[tuple, str]:
    """Gold at_label per triplet for all 1251 v1-labelled at instances."""
    out = {}
    with V1_CSV.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["task"] != "at":
                continue
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            out[k] = r["at_label"]
    return out


def macro_recall(gold, pred):
    return compute_macro_recall(gold, pred, label_set=list(AT_LABELS))["macro_recall"]


def bootstrap_ci(gold, pred, n=2000, seed=42):
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
    return point, samples[int(0.025 * n)], samples[int(0.975 * n)]


def _print_table(rows):
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bootstrap", type=int, default=2000)
    ap.add_argument("--print-cells", action="store_true",
                    help="Print the stacker's cell summary on the train side.")
    args = ap.parse_args()

    md = load_md_at(MD_AT)
    v1_golds = load_v1_at_golds()
    rf = load_jsonl_preds(RF_OOF)
    c4 = load_jsonl_preds(C4_OOF)
    ord_p = load_jsonl_preds(ORD_OOF)
    gemma = load_jsonl_preds(GEMMA_FULL)

    test_keys = [k for k in md if k in rf and k in c4 and k in ord_p and k in gemma]
    train_keys = [k for k in v1_golds
                  if k not in md  # exclude mDeBERTa's test set
                  and k in rf and k in c4 and k in ord_p and k in gemma]
    print(f"  test  set (mDeBERTa-test): n={len(test_keys)} (drop={len(md) - len(test_keys)})")
    print(f"  train set (v1 - mdeberta-test): n={len(train_keys)}")

    # Build the 4-model preds for train and test sides
    def build_votes(keys):
        return {
            "RF":   [null_to_false(rf[k]) for k in keys],
            "C4":   [null_to_false(c4[k]) for k in keys],
            "Ord":  [null_to_false(ord_p[k]) for k in keys],
            "Gemma": [null_to_false(gemma[k]) for k in keys],
        }

    train_votes = build_votes(train_keys)
    test_votes = build_votes(test_keys)
    train_gold = [v1_golds[k] for k in train_keys]
    test_gold = [null_to_false(md[k]["true"]) for k in test_keys]

    # ----- 4-key disagreement stacker (no mDeBERTa) ------------------------
    print()
    print("=" * 78)
    print("4-key disagreement stacker (RF, C4, Ord, Gemma) — OOF on both sides")
    print("=" * 78)
    for tb in ("ordinal_median", "alphabetical", "last_model"):
        for fb in ("majority", "ordinal", "label"):
            lookup = build_lookup_table(train_votes, train_gold,
                                         tiebreaker=tb,
                                         ordinal_map=AT_ORDINAL_MAP)
            preds = apply_lookup(test_votes, lookup,
                                 fallback=fb,
                                 fallback_label="FALSE",
                                 ordinal_map=AT_ORDINAL_MAP)
            pt, lo, hi = bootstrap_ci(test_gold, preds, n=args.bootstrap)
            n_seen = sum(1 for v_tuple in zip(*test_votes.values())
                         if v_tuple in lookup)
            print(f"  tb={tb:<16s} fb={fb:<10s}  MR(at)={pt:.4f}  CI=[{lo:.4f}, {hi:.4f}]  "
                  f"n_seen_cells={n_seen}/{len(test_keys)}  lookup_size={len(lookup)}")

    # ----- 5-key stacker WITH mDeBERTa (uses non-OOF md preds — mild leak) -
    print()
    print("=" * 78)
    print("5-key stacker INCLUDING mDeBERTa (md preds are NOT OOF — mild leak)")
    print("=" * 78)
    md_train_pred = []
    md_train_gold = []
    md_train_keys_real = []
    # Use the 70 v1-test triplets in mDeBERTa's training as md train side:
    # those have md predictions in some artifact? No — md only emits preds for
    # its 188 test triplets. So for 5-key, we'd need md preds on its 1063
    # training set, which we do NOT have. Skip 5-key for now; report this.
    print("  [skipped] mDeBERTa only has predictions on its 188 test triplets — "
          "we don't have its 1063 train-side preds, so the 5-key lookup table "
          "can't be populated. Worth re-emitting if mDeBERTa is k-fold OOF'd.")

    # ----- baselines for context ------------------------------------------
    print()
    print("=" * 78)
    print("Baselines on the same 188 mDeBERTa-test triplets")
    print("=" * 78)
    rows = [("strategy", "MR(at)", "95% CI")]
    for label, p in [
        ("mDeBERTa standalone",  [null_to_false(md[k]["pred"]) for k in test_keys]),
        ("RF (OOF) standalone",  test_votes["RF"]),
        ("Gemma standalone",     test_votes["Gemma"]),
    ]:
        pt, lo, hi = bootstrap_ci(test_gold, p, n=args.bootstrap)
        rows.append((label, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print_table(rows)

    # ----- mDeBERTa + 4-key stacker post-hoc combinations ------------------
    print()
    print("=" * 78)
    print("Post-hoc: combine 4-key stacker with mDeBERTa")
    print("=" * 78)

    # Best 4-key stacker: ordinal_median tiebreaker, ordinal fallback (matches
    # spec §5.2 default + project's existing best run).
    lookup = build_lookup_table(train_votes, train_gold,
                                 tiebreaker="ordinal_median",
                                 ordinal_map=AT_ORDINAL_MAP)
    stacker_preds = apply_lookup(test_votes, lookup,
                                  fallback="ordinal",
                                  fallback_label="FALSE",
                                  ordinal_map=AT_ORDINAL_MAP)
    md_preds_on_test = [null_to_false(md[k]["pred"]) for k in test_keys]

    rows = [("strategy", "MR(at)", "95% CI")]
    pt, lo, hi = bootstrap_ci(test_gold, stacker_preds, n=args.bootstrap)
    rows.append(("4-key stacker (baseline)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # mDeBERTa wins on disagreement
    p_md_priority = [m if m != s else s for m, s in zip(md_preds_on_test, stacker_preds)]
    pt, lo, hi = bootstrap_ci(test_gold, p_md_priority, n=args.bootstrap)
    rows.append(("md overrides stacker (always)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # Stacker wins on disagreement (= just the stacker; sanity)
    p_st_priority = [s for s in stacker_preds]
    pt, lo, hi = bootstrap_ci(test_gold, p_st_priority, n=args.bootstrap)
    rows.append(("stacker only (sanity)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # Plurality of (md, stacker, gemma)
    def _plurality3(a, b, c):
        cnt = Counter([a, b, c])
        top = max(cnt.values())
        winners = [l for l, n in cnt.items() if n == top]
        if len(winners) == 1:
            return winners[0]
        # ordinal tiebreaker
        ords = sorted(AT_ORDINAL_MAP[v] for v in (a, b, c))
        med = ords[len(ords) // 2]
        inv = {v: k for k, v in AT_ORDINAL_MAP.items()}
        cand = inv[med]
        return cand if cand in winners else sorted(winners)[0]

    p_combo = [
        _plurality3(m, s, g)
        for m, s, g in zip(md_preds_on_test, stacker_preds, test_votes["Gemma"])
    ]
    pt, lo, hi = bootstrap_ci(test_gold, p_combo, n=args.bootstrap)
    rows.append(("plurality(md, stacker, gemma)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    # 5-way plurality of all base models + stacker
    def _plurality5(a, b, c, d, e):
        cnt = Counter([a, b, c, d, e])
        top = max(cnt.values())
        winners = [l for l, n in cnt.items() if n == top]
        if len(winners) == 1:
            return winners[0]
        ords = sorted(AT_ORDINAL_MAP[v] for v in (a, b, c, d, e))
        med = ords[len(ords) // 2]
        inv = {v: k for k, v in AT_ORDINAL_MAP.items()}
        cand = inv[med]
        return cand if cand in winners else sorted(winners)[0]

    p_5plurality = [
        _plurality5(m, s, g, r, c)
        for m, s, g, r, c in zip(
            md_preds_on_test, stacker_preds, test_votes["Gemma"],
            test_votes["RF"], test_votes["C4"],
        )
    ]
    pt, lo, hi = bootstrap_ci(test_gold, p_5plurality, n=args.bootstrap)
    rows.append(("plurality(md, stacker, gm, rf, c4)", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))

    _print_table(rows)

    # Print disagreement breakdown between md and stacker
    print()
    print("=" * 78)
    print("Where do mDeBERTa and the 4-key stacker disagree on the 188?")
    print("=" * 78)
    n_agree = 0
    md_right = stacker_right = both_wrong = 0
    for m, s, g in zip(md_preds_on_test, stacker_preds, test_gold):
        if m == s:
            n_agree += 1
            continue
        if m == g and s != g:
            md_right += 1
        elif s == g and m != g:
            stacker_right += 1
        else:
            both_wrong += 1
    print(f"  agree            : {n_agree}/{len(test_gold)} ({n_agree/len(test_gold):.1%})")
    print(f"  disagree         : {len(test_gold) - n_agree}")
    print(f"    md right       : {md_right}")
    print(f"    stacker right  : {stacker_right}")
    print(f"    both wrong     : {both_wrong}")

    if args.print_cells:
        print()
        print("=" * 78)
        print("Stacker lookup cells (top 20 by support)")
        print("=" * 78)
        cs = cell_summary(train_votes, train_gold)
        for row in cs[:20]:
            print(f"  {row['cell']}  n={row['n']}  modal={row['modal_gold']}  "
                  f"breakdown={row['breakdown']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
