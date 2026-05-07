"""Classical-tier ensemble: RF + C4 + OrdContM1 (no neural LMs at all).

Reports MR(at) on mDeBERTa's 188-triplet val split and MR(isAt) on v1
isAt-test (where we have RF/C4 isAt classifiers; OrdContM1 has no isAt
predictions on v1, so isAt frugal options are RF + C4 + auxiliary MASK heads).
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

from hipe.evaluation.metrics import (
    AT_LABELS, ISAT_LABELS, compute_macro_recall, null_to_false,
)
from hipe.stacker import AT_ORDINAL_MAP, apply_lookup, build_lookup_table


REPO = Path(__file__).resolve().parent.parent


def macro_recall(g, p, labels):
    return compute_macro_recall(g, p, label_set=list(labels))["macro_recall"]


def bootstrap_ci(g, p, labels, n=2000, seed=42):
    rng = np.random.default_rng(seed)
    pt = macro_recall(g, p, labels)
    samples = []
    for _ in range(n):
        idx = rng.integers(0, len(g), len(g))
        samples.append(macro_recall([g[i] for i in idx], [p[i] for i in idx], labels))
    samples.sort()
    return pt, samples[int(0.025 * n)], samples[int(0.975 * n)]


def plurality_at(votes):
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


def majority_isat(votes):
    n_t = sum(1 for v in votes if v == "TRUE")
    return "TRUE" if n_t * 2 > len(votes) else "FALSE"


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


def _print(rows):
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def at_part():
    print("=" * 78)
    print("AT — Classical-tier ensembles on mDeBERTa-test split (n=188)")
    print("=" * 78)

    md = load_csv(REPO / "runs/runs_mdeberta/runs/at_task_prediction_result_updated.csv")
    rf = load_jsonl(REPO / "logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl")
    c4 = load_jsonl(REPO / "logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl")
    ord_p = load_jsonl(REPO / "logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl")

    v1 = {}
    with open(REPO / "data/v1_baseline_train_test_ids.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["task"] == "at":
                k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
                v1[k] = r["at_label"]

    test_keys = [k for k in md if k in rf and k in c4 and k in ord_p]
    train_keys = [k for k in v1 if k not in md and k in rf and k in c4 and k in ord_p]

    gold = [null_to_false(md[k]["true"]) for k in test_keys]
    rf_p = [null_to_false(rf[k]) for k in test_keys]
    c4_p = [null_to_false(c4[k]) for k in test_keys]
    ord_pred = [null_to_false(ord_p[k]) for k in test_keys]

    print()
    print("  Standalone (OOF, leakage-free):")
    rows = [("model", "MR(at)", "95% CI")]
    for name, p in [("RF handcrafted", rf_p), ("C4 mask+e1+e2+temp LR", c4_p),
                    ("OrdContM1 contrastive", ord_pred)]:
        pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    print()
    print("  Plurality voting:")
    rows = [("strategy", "MR(at)", "95% CI")]
    cases = [
        ("plurality(RF, C4) tb=ord", [plurality_at([r, c]) for r, c in zip(rf_p, c4_p)]),
        ("plurality(RF, OrdContM1) tb=ord", [plurality_at([r, o]) for r, o in zip(rf_p, ord_pred)]),
        ("plurality(C4, OrdContM1) tb=ord", [plurality_at([c, o]) for c, o in zip(c4_p, ord_pred)]),
        ("plurality(RF, C4, OrdContM1) tb=ord",
         [plurality_at([r, c, o]) for r, c, o in zip(rf_p, c4_p, ord_pred)]),
    ]
    for name, p in cases:
        pt, lo, hi = bootstrap_ci(gold, p, AT_LABELS)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    print()
    print("  3-model lookup-table stacker (proper disagreement stacker, no Gemma):")
    train_gold = [v1[k] for k in train_keys]
    train_votes = {
        "RF": [null_to_false(rf[k]) for k in train_keys],
        "C4": [null_to_false(c4[k]) for k in train_keys],
        "Ord": [null_to_false(ord_p[k]) for k in train_keys],
    }
    test_votes = {"RF": rf_p, "C4": c4_p, "Ord": ord_pred}

    rows = [("config", "MR(at)", "95% CI", "n_seen_cells", "lookup_size")]
    for tb in ("alphabetical", "ordinal_median", "last_model"):
        for fb in ("majority", "ordinal", "label"):
            lookup = build_lookup_table(train_votes, train_gold,
                                         tiebreaker=tb,
                                         ordinal_map=AT_ORDINAL_MAP)
            preds = apply_lookup(test_votes, lookup, fallback=fb,
                                  fallback_label="FALSE",
                                  ordinal_map=AT_ORDINAL_MAP)
            pt, lo, hi = bootstrap_ci(gold, preds, AT_LABELS)
            n_seen = sum(1 for vt in zip(*test_votes.values()) if vt in lookup)
            rows.append((f"tb={tb}, fb={fb}", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]",
                         n_seen, len(lookup)))
    _print(rows)


def isat_part():
    print()
    print("=" * 78)
    print("ISAT — Classical-tier ensembles on v1 isAt-test (n=188)")
    print("=" * 78)

    rf = load_jsonl(REPO / "logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_isAt_isAt-test_predictions.jsonl",
                    field="isAt_predicted")
    c4 = load_jsonl(REPO / "logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_isAt-test_predictions.jsonl",
                    field="isAt_predicted")
    t14 = load_jsonl(REPO / "logs/ablations/T1.4or5_mask_T1.4_temporal_only_LR_isAt_isAt-test_predictions.jsonl",
                     field="isAt_predicted")
    c1 = load_jsonl(REPO / "logs/ablations/T1.4or5_mask_C1_mask_LR_isAt_isAt-test_predictions.jsonl",
                    field="isAt_predicted")

    isat_golds = {}
    with open(REPO / "data/v1_baseline_train_test_ids.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["task"] == "isAt" and r["split"] == "test":
                k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
                isat_golds[k] = r["isAt_label"]

    keys = [k for k in isat_golds if k in rf and k in c4 and k in t14 and k in c1]
    gold = [isat_golds[k] for k in keys]
    rf_p = [null_to_false(rf[k]) for k in keys]
    c4_p = [null_to_false(c4[k]) for k in keys]
    t14_p = [null_to_false(t14[k]) for k in keys]
    c1_p = [null_to_false(c1[k]) for k in keys]

    print()
    print("  Standalone:")
    rows = [("model", "MR(isAt)", "95% CI")]
    for name, p in [("RF (T1.5 handcrafted)", rf_p), ("C4 mask+e1+e2+temp LR", c4_p),
                    ("T1.4 temporal-only LR", t14_p), ("C1 mask-only LR", c1_p)]:
        pt, lo, hi = bootstrap_ci(gold, p, ISAT_LABELS)
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print(rows)

    print()
    print("  Classical-tier ensembles (no LMs):")
    rows = [("strategy", "MR(isAt)", "95% CI", "rec_T", "rec_F", "n_pred_T")]
    cases = [
        ("majority(RF, C4)",
         [majority_isat([r, c]) for r, c in zip(rf_p, c4_p)]),
        ("majority(RF, C4, T1.4)",
         [majority_isat([r, c, t]) for r, c, t in zip(rf_p, c4_p, t14_p)]),
        ("majority(RF, C4, C1)",
         [majority_isat([r, c, x]) for r, c, x in zip(rf_p, c4_p, c1_p)]),
        ("majority(RF, C4, T1.4, C1)",
         [majority_isat([r, c, t, x]) for r, c, t, x in zip(rf_p, c4_p, t14_p, c1_p)]),
    ]
    for name, p in cases:
        pt, lo, hi = bootstrap_ci(gold, p, ISAT_LABELS)
        rec_T = sum(1 for g, q in zip(gold, p) if g == "TRUE" and q == "TRUE") / max(1, sum(1 for g in gold if g == "TRUE"))
        rec_F = sum(1 for g, q in zip(gold, p) if g == "FALSE" and q == "FALSE") / max(1, sum(1 for g in gold if g == "FALSE"))
        rows.append((name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]",
                     f"{rec_T:.3f}", f"{rec_F:.3f}", sum(1 for x in p if x == "TRUE")))
    _print(rows)


def main():
    at_part()
    isat_part()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
