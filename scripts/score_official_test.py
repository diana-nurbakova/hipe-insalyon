"""Score submissions and stacker components against the official test gold.

The gold reference files live in ``data/reference/`` (fetched from
https://github.com/hipe-eval/hipe-2026-eval/tree/main/data/reference). They
carry the same (document_id, pers_entity_id, loc_entity_id) keys and per-pair
``at`` / ``isAt`` labels as the test inputs, now filled with gold values.

This script scores two families of artefacts on the 1,118-pair official test:

1. Submission folders under ``submissions/`` (each holds the 4 per-test-file
   JSONLs in official nested format) -- our actual runs.
2. Per-model prediction logs under ``logs/official_test/`` (flat one-row-per-
   pair format with ``at_predicted`` / ``isAt_predicted``) -- the individual
   stacker components.

Metrics follow HIPE-2026: macro recall over labels, global = mean of the two.
Test B (surprise-test-fr) is ``at``-only, so its isAt is reported but excluded
from the Test-A isAt aggregate.

Usage::

    uv run python scripts/score_official_test.py
    uv run python scripts/score_official_test.py --per-language
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hipe.evaluation.metrics import compute_macro_recall, null_to_false

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"

TEST_FILES = {
    "de": "HIPE-2026-v1.0-impresso-test-de.jsonl",
    "en": "HIPE-2026-v1.0-impresso-test-en.jsonl",
    "fr": "HIPE-2026-v1.0-impresso-test-fr.jsonl",
    "surprise-fr": "HIPE-2026-v1.0-surprise-test-fr.jsonl",
}
TESTA = ("de", "en", "fr")  # newspapers: at + isAt scored
TESTB = ("surprise-fr",)    # literary surprise: at only

Key = tuple[str, str, str]


def load_gold() -> dict[Key, dict]:
    """Return {key: {at, isAt, split, language}} from data/reference/."""
    gold: dict[Key, dict] = {}
    for split, fname in TEST_FILES.items():
        path = REFERENCE_DIR / fname
        if not path.exists():
            raise FileNotFoundError(
                f"Missing gold file {path}. Fetch data/reference/ from "
                "https://github.com/hipe-eval/hipe-2026-eval first."
            )
        for line in path.open(encoding="utf-8"):
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


def load_submission_dir(d: Path) -> dict[Key, tuple[str, str]]:
    """Read a submission folder (nested official JSONLs) -> {key: (at, isAt)}."""
    out: dict[Key, tuple[str, str]] = {}
    for f in sorted(d.glob("*.jsonl")):
        if "predictions" in f.name:  # skip the merged flat log
            continue
        for line in f.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            for pr in doc.get("sampled_pairs", []):
                key = (doc["document_id"], pr["pers_entity_id"], pr["loc_entity_id"])
                out[key] = (null_to_false(pr.get("at")), null_to_false(pr.get("isAt")))
    return out


def load_flat_log(path: Path, at_field="at_predicted", isAt_field="isAt_predicted"):
    """Read a flat per-pair prediction log -> {key: (at, isAt)}."""
    out: dict[Key, tuple[str, str]] = {}
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        key = (r["document_id"], r["pers_entity_id"], r["loc_entity_id"])
        out[key] = (null_to_false(r.get(at_field)), null_to_false(r.get(isAt_field)))
    return out


def _mr(gold_keys, pred, gold, field, idx, label_set):
    g = [gold[k][field] for k in gold_keys]
    p = [pred[k][idx] for k in gold_keys]
    return compute_macro_recall(g, p, label_set=label_set)["macro_recall"]


def score(pred: dict[Key, tuple[str, str]], gold: dict[Key, dict]) -> dict:
    """Compute MR(at), MR(isAt), global on Test A; MR(at) on Test B."""
    common = [k for k in gold if k in pred]
    testa = [k for k in common if gold[k]["split"] in TESTA]
    testb = [k for k in common if gold[k]["split"] in TESTB]

    at_a = _mr(testa, pred, gold, "at", 0, ["TRUE", "PROBABLE", "FALSE"])
    isat_a = _mr(testa, pred, gold, "isAt", 1, ["TRUE", "FALSE"])
    at_b = _mr(testb, pred, gold, "at", 0, ["TRUE", "PROBABLE", "FALSE"]) if testb else None
    at_all = _mr(common, pred, gold, "at", 0, ["TRUE", "PROBABLE", "FALSE"])

    return {
        "n": len(common),
        "n_missing": len(gold) - len(common),
        "testA_MR_at": at_a,
        "testA_MR_isAt": isat_a,
        "testA_global": (at_a + isat_a) / 2,
        "testB_MR_at": at_b,
        "MR_at_all": at_all,
    }


def fmt(v):
    return "  n/a " if v is None else f"{v:.4f}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-language", action="store_true",
                    help="Also break MR(at) down per language.")
    args = ap.parse_args()

    gold = load_gold()
    print(f"Loaded gold: {len(gold)} pairs from {REFERENCE_DIR}\n")

    # --- submissions ---
    sub_root = PROJECT_ROOT / "submissions"
    sub_dirs = sorted(p for p in sub_root.iterdir() if p.is_dir())
    print("=" * 92)
    print("SUBMISSION RUNS                          n   TestA:MR_at  MR_isAt   global | TestB:MR_at")
    print("=" * 92)
    for d in sub_dirs:
        pred = load_submission_dir(d)
        if not pred:
            continue
        s = score(pred, gold)
        print(f"{d.name:<34} {s['n']:>5}     {fmt(s['testA_MR_at'])}   {fmt(s['testA_MR_isAt'])}  "
              f"{fmt(s['testA_global'])} |   {fmt(s['testB_MR_at'])}")

    # --- stacker base components (at task) ---
    ot = PROJECT_ROOT / "logs" / "official_test"
    components = {
        "RF (handcrafted)": ot / "RF_official_test_at_predictions.jsonl",
        "C4-SDov": ot / "C4_official_test_at_predictions.jsonl",
        "OrdContM1": ot / "OrdContM1_official_test_at_predictions.jsonl",
        "Gemma 4 31B (PAB)": ot / "gemma4_31b_PAB_official_test_predictions.jsonl",
        "Llama 3.3 70B (PAB)": ot / "llama_33_70b_PAB_official_test_predictions.jsonl",
    }
    print("\n" + "=" * 92)
    print("STACKER COMPONENTS (at task)             n   TestA:MR_at            | TestB:MR_at | MR_at(all)")
    print("=" * 92)
    for name, path in components.items():
        if not path.exists():
            print(f"{name:<34} MISSING {path}")
            continue
        pred = load_flat_log(path)
        s = score(pred, gold)
        print(f"{name:<34} {s['n']:>5}     {fmt(s['testA_MR_at'])}              |   {fmt(s['testB_MR_at'])}  |  {fmt(s['MR_at_all'])}")

    # --- isAt components ---
    isat_components = {
        "RF isAt": ot / "RF_official_test_isAt_predictions.jsonl",
        "RF isAt (calibrated)": ot / "RF_official_test_isAt_calibrated_predictions.jsonl",
        "C4 isAt": ot / "C4_official_test_isAt_predictions.jsonl",
        "Gemma isAt": ot / "gemma4_31b_PAB_official_test_predictions.jsonl",
        "Llama isAt": ot / "llama_33_70b_PAB_official_test_predictions.jsonl",
    }
    print("\n" + "=" * 92)
    print("isAt COMPONENTS                          n   TestA:MR_isAt")
    print("=" * 92)
    for name, path in isat_components.items():
        if not path.exists():
            print(f"{name:<34} MISSING {path}")
            continue
        pred = load_flat_log(path)
        s = score(pred, gold)
        print(f"{name:<34} {s['n']:>5}     {fmt(s['testA_MR_isAt'])}")

    if args.per_language:
        print("\n" + "=" * 92)
        print("PER-LANGUAGE MR(at) — stacker components (Test A only)")
        print("=" * 92)
        for name, path in components.items():
            if not path.exists():
                continue
            pred = load_flat_log(path)
            row = [f"{name:<22}"]
            for lang in TESTA:
                keys = [k for k in gold if gold[k]["language"] == lang and k in pred
                        and gold[k]["split"] in TESTA]
                mr = _mr(keys, pred, gold, "at", 0, ["TRUE", "PROBABLE", "FALSE"])
                row.append(f"{lang}={mr:.4f}")
            print("  ".join(row))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
