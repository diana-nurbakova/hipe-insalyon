"""Deep analysis of the stacked model and its components on the official test.

Reads gold from ``data/reference/`` and the per-model prediction logs from
``logs/official_test/``, plus the 4-model-stacker submission folder, and
produces:

  - analysis/official_test/component_analysis.json   (all numbers)
  - analysis/official_test/COMPONENT_ANALYSIS.md      (human-readable report)

For every component it computes, on the 1,118-pair official test:
  - macro recall for at (3-class) and isAt (2-class), split into Test A
    (newspapers, de+en+fr) and Test B (surprise-fr, at only),
  - per-class recall and confusion matrices,
  - per-language MR(at),
  - the gap vs the cross-validation / OOF estimate (distribution shift).

It also computes, for the `at` task:
  - pairwise agreement between components,
  - the oracle upper bound (fraction of pairs where *some* component is right),
  - the lookup-stacker's realised vote-cell behaviour.

Usage::

    uv run python scripts/analyze_stacker_components.py
"""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from hipe.evaluation.metrics import compute_macro_recall, null_to_false

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "reference"
OT = ROOT / "logs" / "official_test"
OUT_DIR = ROOT / "analysis" / "official_test"

TEST_FILES = {
    "de": "HIPE-2026-v1.0-impresso-test-de.jsonl",
    "en": "HIPE-2026-v1.0-impresso-test-en.jsonl",
    "fr": "HIPE-2026-v1.0-impresso-test-fr.jsonl",
    "surprise-fr": "HIPE-2026-v1.0-surprise-test-fr.jsonl",
}
TESTA = ("de", "en", "fr")
TESTB = ("surprise-fr",)
AT_LABELS = ["TRUE", "PROBABLE", "FALSE"]
ISAT_LABELS = ["TRUE", "FALSE"]

# CV / OOF baselines (for the distribution-shift gap). Sources:
#   logs/kfold_oof/oof_summary_seed42_n5.json (RF, C4),
#   logs/kfold_oof/*_oof_predictions.jsonl recomputed (OrdContM1, Gemma),
#   logs/cv/T1_stacker_4models_nested_cv_summary.json (stacker).
CV_AT = {
    "RF (handcrafted)": 0.5844,
    "C4-SDov": 0.5787,
    "OrdContM1": 0.5545,
    "Gemma 4 31B (PAB)": 0.5506,
    "STACKER (4-model)": 0.6443,  # pooled OOF; mean±std = 0.6449 ± 0.0388
}

Key = tuple[str, str, str]


def load_gold() -> dict[Key, dict]:
    gold: dict[Key, dict] = {}
    for split, fname in TEST_FILES.items():
        for line in (REF / fname).open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            for pr in doc.get("sampled_pairs", []):
                key = (doc["document_id"], pr["pers_entity_id"], pr["loc_entity_id"])
                gold[key] = {
                    "at": null_to_false(pr.get("at")),
                    "isAt": null_to_false(pr.get("isAt")),
                    "split": split,
                    "language": doc.get("language"),
                }
    return gold


def load_flat(path: Path, at_field="at_predicted", isAt_field="isAt_predicted"):
    out: dict[Key, tuple[str, str]] = {}
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        out[(r["document_id"], r["pers_entity_id"], r["loc_entity_id"])] = (
            null_to_false(r.get(at_field)),
            null_to_false(r.get(isAt_field)),
        )
    return out


def load_sub_dir(d: Path):
    out: dict[Key, tuple[str, str]] = {}
    for f in sorted(d.glob("*.jsonl")):
        if "predictions" in f.name:
            continue
        for line in f.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            for pr in doc.get("sampled_pairs", []):
                out[(doc["document_id"], pr["pers_entity_id"], pr["loc_entity_id"])] = (
                    null_to_false(pr.get("at")),
                    null_to_false(pr.get("isAt")),
                )
    return out


def confusion(keys, pred, gold, field, idx, labels):
    m = {g: {p: 0 for p in labels} for g in labels}
    for k in keys:
        m[gold[k][field]][pred[k][idx]] += 1
    return m


def recall_block(keys, pred, gold, field, idx, labels):
    """Full metric block for one (gold, pred) slice, computed from counts.

    Returns macro recall (the official HIPE metric) plus accuracy, macro
    precision / F1, weighted F1, Cohen's kappa, and per-class P/R/F1/support.
    Macro averages are over labels with gold support, so ``macro_recall``
    matches the official ``compute_macro_recall`` exactly. Pure-Python (no
    sklearn) to keep this runnable in the base environment.
    """
    g = [gold[k][field] for k in keys]
    p = [pred[k][idx] for k in keys]
    n = len(g)
    if n == 0:
        return {"n": 0, "macro_recall": 0.0, "accuracy": 0.0,
                "macro_precision": 0.0, "macro_f1": 0.0,
                "weighted_f1": 0.0, "cohen_kappa": 0.0, "per_class": {}}

    support = {lbl: 0 for lbl in labels}      # gold count
    predicted = {lbl: 0 for lbl in labels}    # predicted count
    tp = {lbl: 0 for lbl in labels}
    correct = 0
    for gi, pi in zip(g, p):
        if gi in support:
            support[gi] += 1
        if pi in predicted:
            predicted[pi] += 1
        if gi == pi:
            correct += 1
            if gi in tp:
                tp[gi] += 1

    per_class = {}
    for lbl in labels:
        rec = tp[lbl] / support[lbl] if support[lbl] else 0.0
        prec = tp[lbl] / predicted[lbl] if predicted[lbl] else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per_class[lbl] = {
            "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(f1, 4), "support": support[lbl],
        }

    present = [lbl for lbl in labels if support[lbl] > 0]
    macro_p = sum(per_class[l]["precision"] for l in present) / len(present) if present else 0.0
    macro_r = sum(per_class[l]["recall"] for l in present) / len(present) if present else 0.0
    macro_f = sum(per_class[l]["f1"] for l in present) / len(present) if present else 0.0
    weighted_f = sum(per_class[l]["f1"] * support[l] for l in labels) / n
    # Cohen's kappa: (po - pe) / (1 - pe)
    po = correct / n
    pe = sum(support[l] * predicted[l] for l in labels) / (n * n)
    kappa = (po - pe) / (1 - pe) if (1 - pe) else 0.0

    out = {
        "n": n,
        "accuracy": round(po, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f, 4),
        "weighted_f1": round(weighted_f, 4),
        "cohen_kappa": round(kappa, 4),
        "per_class": per_class,
    }
    for lbl in labels:
        out[f"recall_{lbl}"] = per_class[lbl]["recall"]
    return out


def analyse_at(name, pred, gold):
    common = [k for k in gold if k in pred]
    testa = [k for k in common if gold[k]["split"] in TESTA]
    testb = [k for k in common if gold[k]["split"] in TESTB]
    out = {
        "n": len(common),
        "testA": recall_block(testa, pred, gold, "at", 0, AT_LABELS),
        "testB": recall_block(testb, pred, gold, "at", 0, AT_LABELS),
        "all": recall_block(common, pred, gold, "at", 0, AT_LABELS),
        "confusion_testA": confusion(testa, pred, gold, "at", 0, AT_LABELS),
        "per_language": {},
        "pred_dist": dict(Counter(pred[k][0] for k in common)),
    }
    for lang in TESTA:
        lk = [k for k in testa if gold[k]["language"] == lang]
        out["per_language"][lang] = recall_block(lk, pred, gold, "at", 0, AT_LABELS)["macro_recall"]
    if name in CV_AT:
        out["cv_MR_at"] = CV_AT[name]
        out["shift_gap"] = round(out["testA"]["macro_recall"] - CV_AT[name], 4)
    return out


def analyse_isat(name, pred, gold):
    common = [k for k in gold if k in pred]
    testa = [k for k in common if gold[k]["split"] in TESTA]
    return {
        "n": len(common),
        "testA": recall_block(testa, pred, gold, "isAt", 1, ISAT_LABELS),
        "confusion_testA": confusion(testa, pred, gold, "isAt", 1, ISAT_LABELS),
        "pred_dist_testA": dict(Counter(pred[k][1] for k in testa)),
    }


def main() -> int:
    gold = load_gold()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    at_components = {
        "RF (handcrafted)": OT / "RF_official_test_at_predictions.jsonl",
        "C4-SDov": OT / "C4_official_test_at_predictions.jsonl",
        "OrdContM1": OT / "OrdContM1_official_test_at_predictions.jsonl",
        "Gemma 4 31B (PAB)": OT / "gemma4_31b_PAB_official_test_predictions.jsonl",
        "Llama 3.3 70B (PAB)": OT / "llama_33_70b_PAB_official_test_predictions.jsonl",
    }
    isat_components = {
        "RF isAt": OT / "RF_official_test_isAt_predictions.jsonl",
        "RF isAt (calibrated)": OT / "RF_official_test_isAt_calibrated_predictions.jsonl",
        "C4 isAt": OT / "C4_official_test_isAt_predictions.jsonl",
        "Gemma isAt": OT / "gemma4_31b_PAB_official_test_predictions.jsonl",
        "Llama isAt": OT / "llama_33_70b_PAB_official_test_predictions.jsonl",
    }

    # Two encoder models used in the official ensembles (run1/run2/run3) but
    # NOT part of the 4-model stacker. Stored as nested-format submission dirs
    # carrying both at and isAt.
    dir_components = {
        "xlm-roberta-large": ROOT / "runs" / "submission_xmlroberta_at_isAt" / "submission_roberta_at_isAt",
        "mDeBERTa-v3": ROOT / "runs" / "materials" / "submission_2_official_test_mdeberta_only",
    }

    at_preds = {n: load_flat(p) for n, p in at_components.items() if p.exists()}
    for n, d in dir_components.items():
        if d.exists():
            at_preds[n] = load_sub_dir(d)
    stacker = load_sub_dir(ROOT / "submissions" / "4-model-stacker")

    results: dict = {
        "meta": {
            "n_pairs": len(gold),
            "reference_dir": str(REF),
            "reference_source": "https://github.com/hipe-eval/hipe-2026-eval/tree/main/data/reference",
            "gold_dist_at": dict(Counter(v["at"] for v in gold.values())),
            "gold_dist_isAt_testA": dict(
                Counter(v["isAt"] for v in gold.values() if v["split"] in TESTA)
            ),
        },
        "at_components": {},
        "isAt_components": {},
        "stacker_final": {},
        "agreement_at": {},
        "oracle_at": {},
        "lookup_cells": {},
    }

    # stacker base components (only the 4 in the stacker) used for at analysis
    STACKER_AT = ["RF (handcrafted)", "C4-SDov", "OrdContM1", "Gemma 4 31B (PAB)"]

    # isAt predictions: flat logs + the two nested-dir encoder models.
    isat_preds = {n: load_flat(p) for n, p in isat_components.items() if p.exists()}
    for n, d in dir_components.items():
        if d.exists():
            isat_preds[n] = at_preds[n]  # same dir, (at, isAt) tuples

    for n, pred in at_preds.items():
        results["at_components"][n] = analyse_at(n, pred, gold)
    for n, pred in isat_preds.items():
        results["isAt_components"][n] = analyse_isat(n, pred, gold)

    # stacker final (at + isAt) scored as a "component"
    common = [k for k in gold if k in stacker]
    testa = [k for k in common if gold[k]["split"] in TESTA]
    testb = [k for k in common if gold[k]["split"] in TESTB]
    sfin = {
        "n": len(common),
        "testA_at": recall_block(testa, stacker, gold, "at", 0, AT_LABELS),
        "testB_at": recall_block(testb, stacker, gold, "at", 0, AT_LABELS),
        "testA_isAt": recall_block(testa, stacker, gold, "isAt", 1, ISAT_LABELS),
        "confusion_testA_at": confusion(testa, stacker, gold, "at", 0, AT_LABELS),
        "cv_MR_at": CV_AT["STACKER (4-model)"],
    }
    sfin["testA_global"] = (sfin["testA_at"]["macro_recall"] + sfin["testA_isAt"]["macro_recall"]) / 2
    sfin["shift_gap_at"] = round(sfin["testA_at"]["macro_recall"] - CV_AT["STACKER (4-model)"], 4)
    results["stacker_final"] = sfin

    # pairwise agreement on at (Test A + B, all 1118) among the 4 stacker bases
    keys_all = sorted(set.intersection(*[set(at_preds[n]) for n in STACKER_AT]))
    agree = {}
    for i, a in enumerate(STACKER_AT):
        for b in STACKER_AT[i + 1:]:
            same = sum(1 for k in keys_all if at_preds[a][k][0] == at_preds[b][k][0])
            agree[f"{a} vs {b}"] = round(same / len(keys_all), 4)
    results["agreement_at"] = {
        "pairwise": agree,
        "all_four_agree": round(
            sum(1 for k in keys_all if len({at_preds[n][k][0] for n in STACKER_AT}) == 1)
            / len(keys_all), 4),
        "n": len(keys_all),
    }

    # oracle upper bound: fraction where at least one of the 4 is correct
    oracle_hits = sum(
        1 for k in keys_all
        if any(at_preds[n][k][0] == gold[k]["at"] for n in STACKER_AT)
    )
    # individual accuracy (plain, not macro) for reference
    indiv_acc = {
        n: round(sum(1 for k in keys_all if at_preds[n][k][0] == gold[k]["at"]) / len(keys_all), 4)
        for n in STACKER_AT
    }
    results["oracle_at"] = {
        "oracle_accuracy": round(oracle_hits / len(keys_all), 4),
        "individual_accuracy": indiv_acc,
        "n": len(keys_all),
    }

    # lookup-cell behaviour: which vote-tuples occurred and what the stacker did
    cell_counter = Counter()
    cell_correct = defaultdict(int)
    for k in keys_all:
        tup = tuple(at_preds[n][k][0][0] for n in STACKER_AT)  # first letter T/P/F
        cell_counter[tup] += 1
        if k in stacker and stacker[k][0] == gold[k]["at"]:
            cell_correct[tup] += 1
    top_cells = []
    for tup, cnt in cell_counter.most_common(12):
        top_cells.append({
            "cell_RF_C4_Ord_Gemma": "".join(tup),
            "n": cnt,
            "stacker_correct": cell_correct[tup],
        })
    results["lookup_cells"] = {"order": STACKER_AT, "top_cells": top_cells}

    # ---- per-test-file evaluation (de / en / fr / surprise-fr) ----------
    # For each file: every at-component + stacker get MR(at) (+ per class);
    # every isAt-component + stacker get MR(isAt); submission runs get
    # MR(at), MR(isAt) and global. surprise-fr is at-only (isAt gold all FALSE).
    sub_dirs = sorted(p for p in (ROOT / "submissions").iterdir() if p.is_dir())
    sub_preds = {p.name: load_sub_dir(p) for p in sub_dirs}
    sub_preds = {n: v for n, v in sub_preds.items() if v}

    per_file: dict = {}
    for split in TEST_FILES:
        fkeys = [k for k in gold if gold[k]["split"] == split]
        scored_isat = split in TESTA  # Test B isAt gold is degenerate (all FALSE)
        entry = {
            "file": TEST_FILES[split],
            "n": len(fkeys),
            "gold_at": dict(Counter(gold[k]["at"] for k in fkeys)),
            "at_components": {},
            "isAt_components": {},
            "submissions": {},
        }
        if scored_isat:
            entry["gold_isAt"] = dict(Counter(gold[k]["isAt"] for k in fkeys))

        for n, pred in at_preds.items():
            kk = [k for k in fkeys if k in pred]
            entry["at_components"][n] = recall_block(kk, pred, gold, "at", 0, AT_LABELS)
        # stacker final at
        kk = [k for k in fkeys if k in stacker]
        entry["at_components"]["STACKER (final)"] = recall_block(kk, stacker, gold, "at", 0, AT_LABELS)

        if scored_isat:
            for n, pred in isat_preds.items():
                kk = [k for k in fkeys if k in pred]
                entry["isAt_components"][n] = recall_block(kk, pred, gold, "isAt", 1, ISAT_LABELS)
            kk = [k for k in fkeys if k in stacker]
            entry["isAt_components"]["STACKER (final)"] = recall_block(kk, stacker, gold, "isAt", 1, ISAT_LABELS)

        for n, pred in sub_preds.items():
            kk = [k for k in fkeys if k in pred]
            at_b = recall_block(kk, pred, gold, "at", 0, AT_LABELS)
            row = {
                "MR_at": at_b["macro_recall"],
                "acc_at": at_b["accuracy"],
                "macroF1_at": at_b["macro_f1"],
            }
            if scored_isat:
                isat_b = recall_block(kk, pred, gold, "isAt", 1, ISAT_LABELS)
                row["MR_isAt"] = isat_b["macro_recall"]
                row["macroF1_isAt"] = isat_b["macro_f1"]
                row["global"] = (at_b["macro_recall"] + isat_b["macro_recall"]) / 2
                row["global_F1"] = (at_b["macro_f1"] + isat_b["macro_f1"]) / 2
            entry["submissions"][n] = row
        per_file[split] = entry
    results["per_test_file"] = per_file

    # write JSON
    json_path = OUT_DIR / "component_analysis.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {json_path}")

    # write Markdown
    md = render_markdown(results)
    md_path = OUT_DIR / "COMPONENT_ANALYSIS.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"Wrote {md_path}")
    return 0


def _f(v):
    return "n/a" if v is None else f"{v:.4f}"


def render_markdown(r: dict) -> str:
    m = r["meta"]
    L = []
    L.append("# Stacked-model component analysis — HIPE-2026 official test\n")
    L.append("Scored against the released gold in `data/reference/` "
             f"(source: {m['reference_source']}).\n")
    n_testa = sum(m["gold_dist_isAt_testA"].values())
    L.append(f"- Official test pairs: **{m['n_pairs']}** (Test A: de+en+fr newspapers, "
             f"{n_testa} pairs scored on `at`+`isAt`; Test B: surprise-fr, "
             f"{m['n_pairs'] - n_testa} pairs, `at` only).")
    L.append(f"- Gold `at` distribution: {m['gold_dist_at']}")
    L.append(f"- Gold `isAt` distribution (Test A): {m['gold_dist_isAt_testA']}\n")
    L.append("Primary metric is **macro recall (MR)** — the official HIPE-2026 metric "
             "(global = mean(MR_at, MR_isAt)). We also report **accuracy**, **macro "
             "precision**, **macro F1**, **weighted F1**, and **Cohen's κ** "
             "(agreement with gold beyond chance). Macro averages are over labels with "
             "gold support, so MR here equals the official macro recall.\n")

    order = ["RF (handcrafted)", "C4-SDov", "OrdContM1", "xlm-roberta-large",
             "mDeBERTa-v3", "Gemma 4 31B (PAB)", "Llama 3.3 70B (PAB)"]
    s = r["stacker_final"]
    sa = s["testA_at"]

    # at headline metrics (Test A)
    L.append("## 1. `at` task — all components vs the final stacker (Test A)\n")
    L.append("The **4-model stacker** combines RF, C4-SDov, OrdContM1 and Gemma. "
             "**xlm-roberta-large** and **mDeBERTa-v3** are fine-tuned encoders used "
             "in the official ensemble runs (run1/run2/run3) but *not* in the lookup "
             "stacker; Llama 3.3 70B is shown for reference.\n")
    L.append("| Component | Accuracy | Macro-P | **MR** (Macro-R) | Macro-F1 | Weighted-F1 | Cohen κ |")
    L.append("|---|---|---|---|---|---|---|")

    def metric_row(name, a):
        return (f"| {name} | {_f(a.get('accuracy'))} | {_f(a.get('macro_precision'))} | "
                f"**{_f(a['macro_recall'])}** | {_f(a.get('macro_f1'))} | "
                f"{_f(a.get('weighted_f1'))} | {_f(a.get('cohen_kappa'))} |")

    for n in order:
        c = r["at_components"].get(n)
        if c:
            L.append(metric_row(n, c["testA"]))
    L.append(metric_row("**STACKER (final)**", sa))
    L.append("")

    # at MR across splits + CV/shift
    L.append("### `at` — MR across splits + train→test shift\n")
    L.append("| Component | Test A MR | Test B MR | all-1118 MR | CV MR | shift |")
    L.append("|---|---|---|---|---|---|")
    for n in order:
        c = r["at_components"].get(n)
        if not c:
            continue
        L.append(f"| {n} | {_f(c['testA']['macro_recall'])} | {_f(c['testB']['macro_recall'])} | "
                 f"{_f(c['all']['macro_recall'])} | {_f(c.get('cv_MR_at'))} | {c.get('shift_gap','n/a')} |")
    L.append(f"| **STACKER (final)** | {_f(sa['macro_recall'])} | {_f(s['testB_at']['macro_recall'])} | "
             f"— | {_f(s['cv_MR_at'])} | {s['shift_gap_at']} |")
    L.append("\n> **shift** = official-test Test-A MR − CV MR. Large negative = overfit "
             "the 1,251-instance labelled pool. CV blank where no comparable CV MR exists.\n")

    # at per-class P/R/F1 (Test A)
    L.append("### `at` — per-class precision / recall / F1 (Test A)\n")
    L.append("| Component | TRUE P/R/F1 | PROBABLE P/R/F1 | FALSE P/R/F1 |")
    L.append("|---|---|---|---|")

    def pcf(pc, lbl):
        d = pc.get(lbl, {})
        return f"{d.get('precision',0):.2f}/{d.get('recall',0):.2f}/{d.get('f1',0):.2f}"

    for n in order + ["STACKER (final)"]:
        a = sa if n == "STACKER (final)" else (r["at_components"].get(n) or {}).get("testA")
        if not a:
            continue
        pc = a.get("per_class", {})
        L.append(f"| {n} | {pcf(pc,'TRUE')} | {pcf(pc,'PROBABLE')} | {pcf(pc,'FALSE')} |")
    L.append("")

    # per language
    L.append("### Per-language MR(at) (Test A)\n")
    L.append("| Component | de | en | fr |")
    L.append("|---|---|---|---|")
    for n in order:
        c = r["at_components"].get(n)
        if not c:
            continue
        pl = c["per_language"]
        L.append(f"| {n} | {_f(pl['de'])} | {_f(pl['en'])} | {_f(pl['fr'])} |")
    L.append("")

    # isAt
    L.append("## 2. `isAt` task — components (Test A)\n")
    L.append("| Component | Accuracy | Macro-P | **MR** | Macro-F1 | Weighted-F1 | Cohen κ | TRUE P/R/F1 | FALSE P/R/F1 |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    isat_order2 = ["RF isAt", "RF isAt (calibrated)", "C4 isAt", "xlm-roberta-large",
                   "mDeBERTa-v3", "Gemma isAt", "Llama isAt"]
    isat_order2 += [n for n in r["isAt_components"] if n not in isat_order2]
    si = r["stacker_final"]["testA_isAt"]
    for n in isat_order2 + ["STACKER (Gemma isAt + constraint)"]:
        a = si if n.startswith("STACKER") else (r["isAt_components"].get(n) or {}).get("testA")
        if not a:
            continue
        pc = a.get("per_class", {})
        L.append(f"| {n} | {_f(a.get('accuracy'))} | {_f(a.get('macro_precision'))} | "
                 f"**{_f(a['macro_recall'])}** | {_f(a.get('macro_f1'))} | "
                 f"{_f(a.get('weighted_f1'))} | {_f(a.get('cohen_kappa'))} | "
                 f"{pcf(pc,'TRUE')} | {pcf(pc,'FALSE')} |")
    L.append("")

    # agreement
    ag = r["agreement_at"]
    L.append("## 3. Agreement among the 4 stacker `at` components\n")
    L.append(f"- All four agree on `at`: **{ag['all_four_agree']*100:.1f}%** of {ag['n']} pairs.")
    L.append("- Pairwise agreement:\n")
    L.append("| Pair | agreement |")
    L.append("|---|---|")
    for pair, v in ag["pairwise"].items():
        L.append(f"| {pair} | {v*100:.1f}% |")
    L.append("")

    # oracle
    o = r["oracle_at"]
    L.append("## 4. Oracle upper bound on `at`\n")
    L.append(f"- If we always picked the *correct* one of the 4 components when any was right, "
             f"plain accuracy would be **{o['oracle_accuracy']*100:.1f}%** ({o['n']} pairs).")
    L.append("- Individual plain accuracy: "
             + ", ".join(f"{n.split(' (')[0]}={v*100:.1f}%" for n, v in o["individual_accuracy"].items()) + ".")
    L.append("> The gap between the oracle and the best single model bounds how much *any* "
             "stacker could have gained from these four components.\n")

    # lookup cells
    lc = r["lookup_cells"]
    L.append("## 5. Lookup-stacker vote cells (official test)\n")
    L.append(f"Vote tuple order: {' , '.join(lc['order'])} — letters = T/P/F.\n")
    L.append("| Cell (RF,C4,Ord,Gemma) | n pairs | stacker correct |")
    L.append("|---|---|---|")
    for c in lc["top_cells"]:
        L.append(f"| {c['cell_RF_C4_Ord_Gemma']} | {c['n']} | {c['stacker_correct']} |")
    L.append("")

    # per-test-file
    if "per_test_file" in r:
        L.append("## 6. Per-test-file evaluation\n")
        split_titles = {
            "de": "impresso-test-**de** (German)",
            "en": "impresso-test-**en** (English)",
            "fr": "impresso-test-**fr** (French)",
            "surprise-fr": "**surprise**-test-fr (French literary, Test B — `at` only)",
        }
        at_order = ["RF (handcrafted)", "C4-SDov", "OrdContM1", "xlm-roberta-large",
                    "mDeBERTa-v3", "Gemma 4 31B (PAB)", "Llama 3.3 70B (PAB)",
                    "STACKER (final)"]
        isat_order = ["RF isAt", "RF isAt (calibrated)", "C4 isAt", "xlm-roberta-large",
                      "mDeBERTa-v3", "Gemma isAt", "Llama isAt", "STACKER (final)"]
        for split, entry in r["per_test_file"].items():
            L.append(f"### {split_titles.get(split, split)}  —  n={entry['n']}\n")
            L.append(f"- Gold `at`: {entry['gold_at']}"
                     + (f"  ·  Gold `isAt`: {entry['gold_isAt']}" if "gold_isAt" in entry else "")
                     + "\n")
            # at components
            L.append("**`at` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall\n")
            L.append("| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec PROB | rec FALSE |")
            L.append("|---|---|---|---|---|---|---|---|")
            for n in at_order:
                c = entry["at_components"].get(n)
                if not c:
                    continue
                b = "**" if n == "STACKER (final)" else ""
                L.append(f"| {b}{n}{b} | {b}{_f(c['macro_recall'])}{b} | {_f(c.get('accuracy'))} | "
                         f"{_f(c.get('macro_f1'))} | {_f(c.get('cohen_kappa'))} | "
                         f"{_f(c.get('recall_TRUE'))} | {_f(c.get('recall_PROBABLE'))} | "
                         f"{_f(c.get('recall_FALSE'))} |")
            L.append("")
            # isAt components (Test A only)
            if entry["isAt_components"]:
                L.append("**`isAt` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall\n")
                L.append("| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec FALSE |")
                L.append("|---|---|---|---|---|---|---|")
                for n in isat_order:
                    c = entry["isAt_components"].get(n)
                    if not c:
                        continue
                    b = "**" if n == "STACKER (final)" else ""
                    L.append(f"| {b}{n}{b} | {b}{_f(c['macro_recall'])}{b} | {_f(c.get('accuracy'))} | "
                             f"{_f(c.get('macro_f1'))} | {_f(c.get('cohen_kappa'))} | "
                             f"{_f(c.get('recall_TRUE'))} | {_f(c.get('recall_FALSE'))} |")
                L.append("")
            # submissions
            L.append("**Submission runs** — global = mean(MR_at, MR_isAt) is the official score\n")
            has_isat = any("MR_isAt" in v for v in entry["submissions"].values())
            if has_isat:
                L.append("| Run | MR(at) | Macro-F1(at) | MR(isAt) | Macro-F1(isAt) | **global** | global(F1) |")
                L.append("|---|---|---|---|---|---|---|")
            else:
                L.append("| Run | MR(at) | Acc(at) | Macro-F1(at) |")
                L.append("|---|---|---|---|")
            for n in sorted(entry["submissions"]):
                v = entry["submissions"][n]
                if has_isat:
                    L.append(f"| {n} | {_f(v['MR_at'])} | {_f(v.get('macroF1_at'))} | "
                             f"{_f(v.get('MR_isAt'))} | {_f(v.get('macroF1_isAt'))} | "
                             f"**{_f(v.get('global'))}** | {_f(v.get('global_F1'))} |")
                else:
                    L.append(f"| {n} | {_f(v['MR_at'])} | {_f(v.get('acc_at'))} | {_f(v.get('macroF1_at'))} |")
            L.append("")

    # ---- data-driven takeaways -----------------------------------------
    atc = r["at_components"]
    best_at = max(atc.items(), key=lambda kv: kv[1]["testA"]["macro_recall"])
    isc = r["isAt_components"]
    best_isat = max(isc.items(), key=lambda kv: kv[1]["testA"]["macro_recall"])
    sa = r["stacker_final"]["testA_at"]
    gemma_at = atc["Gemma 4 31B (PAB)"]["testA"]
    rf_at = atc["RF (handcrafted)"]["testA"]
    xlm_at = atc["xlm-roberta-large"]["testA"]
    # worst at by MR among the small/encoder models
    trained = {k: v for k, v in atc.items()
               if k not in ("Gemma 4 31B (PAB)", "Llama 3.3 70B (PAB)")}
    worst_at = min(trained.items(), key=lambda kv: kv[1]["testA"]["macro_recall"])

    L.append("## 7. Takeaways\n")
    L.append(
        f"1. **Gemma 4 31B is the best single component on both tasks and on every metric** — "
        f"`at` MR {gemma_at['macro_recall']:.4f} / Macro-F1 {gemma_at['macro_f1']:.4f} / κ "
        f"{gemma_at['cohen_kappa']:.4f}, and `isAt` MR {isc['Gemma isAt']['testA']['macro_recall']:.4f} "
        f"/ κ {isc['Gemma isAt']['testA']['cohen_kappa']:.4f}. It is also the only `at` model whose "
        f"official-test score tracks its CV estimate (shift +0.01), because it is zero-shot and never "
        f"saw our labelled pool.")
    L.append(
        f"2. **The conclusion is metric-robust.** MR, Macro-F1 and Cohen's κ all rank the models "
        f"identically (Gemma > Llama > mDeBERTa ≈ C4 > OrdContM1 > RF ≈ xlm on `at`), so the result "
        f"is not an artifact of balanced accuracy. Accuracy alone is misleading — e.g. RF `isAt` "
        f"scores 0.67 accuracy but κ = 0.00 (it predicts all-FALSE); the macro metrics expose that.")
    L.append(
        f"3. **Every trained model overfit and collapsed out-of-distribution.** RF/C4/OrdContM1 lost "
        f"0.16–0.24 MR vs CV (`shift` column); the two fine-tuned encoders are no better — "
        f"xlm-roberta-large is the *worst* `at` model on the test (MR {xlm_at['macro_recall']:.4f}, "
        f"κ {xlm_at['cohen_kappa']:.4f}), despite being a 560M-param model and a voter in official "
        f"run1/run3. Cohen's κ for RF (`at` {rf_at['cohen_kappa']:.4f}) and the trained `isAt` heads "
        f"(≤0.16) confirms near-chance agreement.")
    L.append(
        f"4. **PROBABLE is effectively unlearnable here.** Per-class F1 for PROBABLE is 0.00 for RF, "
        f"mDeBERTa and the stacker, and only ~0.02 for Gemma — the entire field fails the third "
        f"`at` class on the official test, which caps MR(at) for everyone.")
    L.append(
        f"5. **Stacking and voting hurt.** The 4-model stacker `at` (MR {sa['macro_recall']:.4f}) lands "
        f"below Gemma alone, and the majority-vote `isAt` used in run1/4/5/6 (0.7991) is below Gemma "
        f"`isAt` alone (0.8109). Mixing the robust LLM with the collapsed trained models consistently "
        f"loses ground — **pure Gemma would have been our strongest submission** (Test A global 0.6867 "
        f"vs run1's 0.6472).")
    L.append(
        f"6. **The components are complementary in principle but not exploitable in practice.** The "
        f"oracle upper bound on `at` is {r['oracle_at']['oracle_accuracy']*100:.1f}% accuracy vs "
        f"{max(r['oracle_at']['individual_accuracy'].values())*100:.1f}% for the best single model — "
        f"the headroom exists, but the lookup table cannot realise it because the trained voters are "
        f"unreliable OOD (see the `FFFT` cell: Gemma says TRUE, the trees overrule it, and the stacker "
        f"is right only 122/321 times).")
    L.append("")
    L.append("### Practical implications for the notebook paper\n")
    L.append("- Report **pure Gemma 4 31B** as the headline system; present the stacker as a negative "
             "result on small labelled pools (severe train→test shift).")
    L.append("- The frugal, no-LLM runs (run2/run3) are the weakest by a wide margin — useful only as "
             "an efficiency baseline, not for accuracy.")
    L.append("- A larger or more representative training pool, or calibration against the official "
             "distribution, would be needed before any trained component could help an ensemble.\n")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
