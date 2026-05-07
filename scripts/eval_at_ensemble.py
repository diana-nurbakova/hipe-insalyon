"""at-task ensemble analysis on mDeBERTa's 188 test triplets.

mDeBERTa's val split is 80/20 of the labeled pool (1063/188), DIFFERENT from
v1's at-test split: 118 of mDeBERTa's 188 test triplets overlap with v1
at-test, the other 70 are in v1 at-train. So we use OOF predictions for the
other models (which cover all 1,251 labelled instances leakage-free) to get
honest base-model predictions on the same 188 triplets.

Models compared (all aligned by (doc, pers, loc) on the 188 mdeberta-test):
  - mDeBERTa-v3 (at_task_prediction_result_updated.csv)  — with margin/entropy
  - RF handcrafted        (logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl)
  - C4 mask+e1+e2+temp    (logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl)
  - OrdContM1 contrastive (logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl)
  - Gemma-4-31b PAB       (logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl)
  - Llama-3.3-70b PAB     (full-dataset run if available — currently only on
                           official test; reported as "missing" if absent here)

Reports MR(at) and 95% bootstrap CI for each model + several ensemble
strategies (plurality vote, ambiguity-routed mDeBERTa, etc.).
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
    compute_macro_recall,
    null_to_false,
)


REPO = Path(__file__).resolve().parent.parent
MD_AT = REPO / "runs/runs_mdeberta/runs/at_task_prediction_result_updated.csv"
RF_OOF = REPO / "logs/kfold_oof/RF_handcrafted_at_oof_predictions.jsonl"
C4_OOF = REPO / "logs/kfold_oof/C4_mask_e1e2_temp_at_oof_predictions.jsonl"
ORD_OOF = REPO / "logs/kfold_oof/OrdContM1_at_oof_predictions.jsonl"
GEMMA_FULL = REPO / "logs/llm_full/gemma4_31b_PAB_full_dataset_predictions.jsonl"

# at-task labels in fixed order (FALSE < PROBABLE < TRUE for ordinal-aware tiebreaks)
AT_ORDER = ["FALSE", "PROBABLE", "TRUE"]


def _key(row: dict) -> tuple[str, str, str]:
    return (row["document_id"], row["pers_entity_id"], row["loc_entity_id"])


def load_md_at(path: Path) -> dict[tuple, dict]:
    """Load mDeBERTa at predictions with margin/entropy (3-class)."""
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
            probs = {
                "FALSE": float(r["prob_FALSE"]),
                "TRUE": float(r["prob_TRUE"]),
                "PROBABLE": float(r["prob_PROBABLE"]),
            }
            sorted_p = sorted(probs.values(), reverse=True)
            margin = sorted_p[0] - sorted_p[1]
            ent = 0.0
            for p in probs.values():
                if p > 1e-9:
                    ent -= p * math.log(p)
            norm_ent = ent / math.log(3)
            ambig = norm_ent * (1.0 - margin)
            out[k] = {
                "pred": r["pred_label"],
                "true": r["true_label"],
                "conf": float(r["confidence"]),
                "margin": margin,
                "entropy": ent,
                "norm_entropy": norm_ent,
                "ambiguity": ambig,
                "probs": probs,
            }
    return out


def load_jsonl_preds(path: Path, field: str = "at_predicted") -> dict[tuple, str | None]:
    out: dict[tuple, str | None] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            k = _key(d)
            out[k] = d.get(field)
    return out


def macro_recall(gold: list[str], pred: list[str]) -> float:
    return compute_macro_recall(gold, pred, label_set=list(AT_LABELS))["macro_recall"]


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
    return point, samples[int(0.025 * n)], samples[int(0.975 * n)]


def _print_table(rows: list[tuple]) -> None:
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  " + "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))


def plurality_vote(votes: list[str], tiebreaker: str = "ordinal") -> str:
    """Plurality vote among 3-class at predictions.

    tiebreaker:
      - 'ordinal': pick the ordinal median of tied labels under FALSE<PROBABLE<TRUE
      - 'first': pick the first label in AT_ORDER among tied labels
      - 'false': prefer FALSE on ties
    """
    if not votes:
        return "FALSE"
    cnt = Counter(votes)
    top = max(cnt.values())
    tied = [lbl for lbl, c in cnt.items() if c == top]
    if len(tied) == 1:
        return tied[0]
    if tiebreaker == "ordinal":
        # ordinal median across the tied labels
        ordinal_idxs = [AT_ORDER.index(t) for t in tied if t in AT_ORDER]
        ordinal_idxs.sort()
        median_idx = ordinal_idxs[len(ordinal_idxs) // 2]
        return AT_ORDER[median_idx]
    if tiebreaker == "false":
        return "FALSE" if "FALSE" in tied else tied[0]
    return tied[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bootstrap", type=int, default=2000)
    args = ap.parse_args()

    md = load_md_at(MD_AT)
    rf = load_jsonl_preds(RF_OOF)
    c4 = load_jsonl_preds(C4_OOF)
    ord_p = load_jsonl_preds(ORD_OOF)
    gemma = load_jsonl_preds(GEMMA_FULL)

    keys = [k for k in md if k in rf and k in c4 and k in ord_p and k in gemma]
    n_drop = len(md) - len(keys)
    print(f"Aligned n={len(keys)} (dropped {n_drop} for missing partner OOF/full preds)")

    gold = [null_to_false(md[k]["true"]) for k in keys]
    md_pred = [null_to_false(md[k]["pred"]) for k in keys]
    rf_pred = [null_to_false(rf[k]) for k in keys]
    c4_pred = [null_to_false(c4[k]) for k in keys]
    ord_pred = [null_to_false(ord_p[k]) for k in keys]
    gm_pred = [null_to_false(gemma[k]) for k in keys]

    print()
    print("=" * 78)
    print(f"Standalone MR(at) on mDeBERTa's 188 test triplets")
    print("=" * 78)
    rows = [("model", "MR(at)", "95% CI", "rec_T", "rec_P", "rec_F", "n_pred_TRUE")]
    for label, p in [("mDeBERTa-v3", md_pred), ("RF (OOF)", rf_pred),
                     ("C4 LR (OOF)", c4_pred), ("OrdContM1 (OOF)", ord_pred),
                     ("Gemma-4-31b PAB", gm_pred)]:
        pt, lo, hi = bootstrap_ci(gold, p, n=args.bootstrap)
        details = compute_macro_recall(gold, p, label_set=list(AT_LABELS))
        rt = details.get("recall_TRUE")
        rp = details.get("recall_PROBABLE")
        rf_r = details.get("recall_FALSE")
        rows.append((
            label, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]",
            f"{rt:.3f}" if rt is not None else "n/a",
            f"{rp:.3f}" if rp is not None else "n/a",
            f"{rf_r:.3f}" if rf_r is not None else "n/a",
            sum(1 for x in p if x == "TRUE"),
        ))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Pairwise disagreement (% items where pair differs)")
    print("=" * 78)
    models = [("md", md_pred), ("rf", rf_pred), ("c4", c4_pred),
              ("ord", ord_pred), ("gm", gm_pred)]
    rows = [("",) + tuple(name for name, _ in models)]
    for n1, p1 in models:
        cells = [n1]
        for n2, p2 in models:
            if n1 == n2:
                cells.append("---")
            else:
                d = sum(1 for a, b in zip(p1, p2) if a != b) / len(keys)
                cells.append(f"{d:.3f}")
        rows.append(tuple(cells))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Ensemble strategies (no confidence)")
    print("=" * 78)
    rows = [("strategy", "MR(at)", "95% CI")]

    for name, votes_per_item in [
        ("plurality(md, rf, c4, ord, gm)",
         list(zip(md_pred, rf_pred, c4_pred, ord_pred, gm_pred))),
        ("plurality(md, rf, c4, gm) [no ord]",
         list(zip(md_pred, rf_pred, c4_pred, gm_pred))),
        ("plurality(md, rf, c4, ord) [no gm]",
         list(zip(md_pred, rf_pred, c4_pred, ord_pred))),
        ("plurality(rf, c4, ord, gm) [no md]",
         list(zip(rf_pred, c4_pred, ord_pred, gm_pred))),
    ]:
        for tb in ("ordinal", "false"):
            s = [plurality_vote(list(vs), tiebreaker=tb) for vs in votes_per_item]
            pt, lo, hi = bootstrap_ci(gold, s, n=args.bootstrap)
            rows.append((f"{name}  tb={tb}", f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Ambiguity-routed: keep mDeBERTa for low-amb, route top X% to fallback")
    print("=" * 78)
    print(f"  ambiguity stats: max={max(md[k]['ambiguity'] for k in keys):.3f}")
    print(f"                   median={sorted(md[k]['ambiguity'] for k in keys)[len(keys)//2]:.3f}")
    print(f"                   min={min(md[k]['ambiguity'] for k in keys):.3f}")
    print()

    keys_by_ambig = sorted(range(len(keys)), key=lambda i: -md[keys[i]]["ambiguity"])

    fallbacks = {
        "Gemma alone": lambda i: gm_pred[i],
        "OrdContM1 alone": lambda i: ord_pred[i],
        "plurality(rf,c4,ord,gm) tb=ord":
            lambda i: plurality_vote([rf_pred[i], c4_pred[i], ord_pred[i], gm_pred[i]], "ordinal"),
        "plurality(rf,c4,gm) tb=ord":
            lambda i: plurality_vote([rf_pred[i], c4_pred[i], gm_pred[i]], "ordinal"),
        "plurality(c4,ord,gm) tb=ord":
            lambda i: plurality_vote([c4_pred[i], ord_pred[i], gm_pred[i]], "ordinal"),
    }
    rows = [("top X%", "n_routed", "fallback", "MR(at)", "95% CI")]
    for X in (10, 20, 30, 40, 50):
        n_route = int(round(X / 100.0 * len(keys)))
        routed_set = set(keys_by_ambig[:n_route])
        for fb_name, fb_fn in fallbacks.items():
            out = [fb_fn(i) if i in routed_set else md_pred[i] for i in range(len(keys))]
            pt, lo, hi = bootstrap_ci(gold, out, n=args.bootstrap)
            rows.append((f"{X}%", n_route, fb_name, f"{pt:.4f}", f"[{lo:.4f}, {hi:.4f}]"))
    _print_table(rows)

    print()
    print("=" * 78)
    print("Oracle ceilings on this 188-set")
    print("=" * 78)
    # Pick winning vote per item
    def oracle(votes_per_item, gold):
        out = []
        for vs, g in zip(votes_per_item, gold):
            out.append(g if g in vs else vs[0])
        return out
    o3 = oracle(list(zip(md_pred, gm_pred, ord_pred)), gold)
    o4 = oracle(list(zip(md_pred, rf_pred, c4_pred, gm_pred)), gold)
    o5 = oracle(list(zip(md_pred, rf_pred, c4_pred, ord_pred, gm_pred)), gold)
    print(f"  oracle (md, gm, ord)         : {macro_recall(gold, o3):.4f}")
    print(f"  oracle (md, rf, c4, gm)      : {macro_recall(gold, o4):.4f}")
    print(f"  oracle (md, rf, c4, ord, gm) : {macro_recall(gold, o5):.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
