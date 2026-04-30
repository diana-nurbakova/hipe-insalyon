"""Print a unified comparison of every configuration scored on at-test (188).

Reads existing report JSONs from ``logs/ablations/`` and prints a single
side-by-side table covering LLM zero-shot variants, RAG, Wikidata/temporal
context, the full pipeline, plus all MASK / handcrafted same-split baselines.

Configurations missing from disk are silently skipped — handy as
experiments are added incrementally.

Usage:
    uv run python scripts/unified_comparison.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# (label_in_table, report_filename_relative_to_log_dir)
DEFAULT_ENTRIES: list[tuple[str, str]] = [
    # --- Feature-based baselines (same-split, 1063 train / 188 test) ---
    ("Handcrafted RF (same-split)",         "T1.4or5_mask_T1.5_handcrafted_RF_at_at-test_report.json"),
    ("Handcrafted RF (isAt target)",        "T1.4or5_mask_T1.5_handcrafted_RF_isAt_at-test_report.json"),
    ("MASK C4 LR (mask+e1+e2+temporal)",    "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test_report.json"),
    ("MASK C4 LR (isAt target)",            "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test_report.json"),
    ("MASK C1 LR (mask only)",              "T1.4or5_mask_C1_mask_LR_at_at-test_report.json"),
    ("MASK C1 LR (isAt target)",            "T1.4or5_mask_C1_mask_LR_isAt_at-test_report.json"),
    ("Temporal-only LR (15-d)",             "T1.4or5_mask_T1.4_temporal_only_LR_at_at-test_report.json"),
    ("Temporal-only LR (isAt target)",      "T1.4or5_mask_T1.4_temporal_only_LR_isAt_at-test_report.json"),
    # --- LLM zero-shot (Llama 3.1 8B via DeepInfra) ---
    ("LLM P-A (zero-shot, fixed prompt)",   "T1.1_llm_zeroshot_PA_v2_fixed_prompt_report.json"),
    ("LLM P-B (zero-shot, fixed prompt)",   "T1.1_llm_zeroshot_PB_v2_fixed_prompt_report.json"),
    ("LLM P-AB (zero-shot)",                "T1.1_llm_zeroshot_PAB_deepinfra_Meta-Llama-31-8B-Instruct_at-test_report.json"),
    ("LLM P-A+P-B split",                   "T1.1_llm_zeroshot_PA+PB_split_v2_report.json"),
    ("LLM P-R (zero-shot)",                 "T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test_report.json"),
    # --- LLM with context blocks ---
    ("LLM P-R + RAG K=3",                   "T1_llm_rag3_PR_at-test_report.json"),
    ("LLM P-R + Wikidata + Temporal",       "T1_llm_zeroshot_wd_temp_PR_at-test_report.json"),
    ("LLM P-R + RAG + WD + Temporal",       "T1_llm_rag3_wd_temp_PR_at-test_report.json"),
]


def _safe_load(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _row(label: str, report: dict) -> str:
    s = report["scores"]
    md = report.get("metadata", {})
    pred_stats = md.get("predictor_stats") or {}
    n_calls = pred_stats.get("n_calls", "-")
    parse_ok = pred_stats.get("parse_ok", "-")
    parse_str = (
        f"{parse_ok}/{n_calls}" if isinstance(parse_ok, int) and isinstance(n_calls, int) else "-"
    )
    tok_in = pred_stats.get("prompt_tokens", 0) or 0
    tok_out = pred_stats.get("completion_tokens", 0) or 0
    tok_str = f"{tok_in:>7d}/{tok_out:>5d}" if (tok_in or tok_out) else "       -"
    return (
        f"{label:<40s}"
        f"{s['global_score']:>8.4f}"
        f"{s['macro_recall_at']:>8.4f}"
        f"{s['macro_recall_isAt']:>9.4f}"
        f"{parse_str:>10s}"
        f"  {tok_str}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    print(f"Reading reports from {log_dir}\n")

    print(f"{'configuration':<40s}{'global':>8s}{'MR(at)':>8s}{'MR(isAt)':>9s}{'parse':>10s}  {'tok in/out':>14s}")
    print("-" * 89)

    n_found = 0
    n_missing = 0
    best_global = -1.0
    best_label = ""
    for label, fname in DEFAULT_ENTRIES:
        report = _safe_load(log_dir / fname)
        if report is None:
            n_missing += 1
            continue
        n_found += 1
        # MASK same-split reports zero out the non-target slot — skip those
        # rows to avoid double counting; the target-isAt row holds the real
        # MR(isAt) and we already see MR(at) on its own row. To present a
        # cleaner summary, collapse them into a single feature_set row when
        # both sides are available (this is a presentation choice — the raw
        # values in the JSON files are unchanged).
        print(_row(label, report))
        gs = report["scores"]["global_score"]
        if gs > best_global and "isAt target" not in label:
            best_global = gs
            best_label = label

    print("-" * 89)
    print(f"\n{n_found} reports found, {n_missing} missing.")
    if best_global >= 0:
        print(f"Best (excluding isAt-only rows): {best_label}  global={best_global:.4f}")

    # Collapsed feature-set table, where each MASK entry combines its at +
    # isAt rows into a single "mean" line for direct comparison with the
    # combined-task LLM rows.
    print("\n" + "=" * 89)
    print("Collapsed comparison (MASK rows combine `at` + `isAt` targets):")
    print("=" * 89)
    feature_pairs = [
        ("Handcrafted RF (same-split)",
         "T1.4or5_mask_T1.5_handcrafted_RF_at_at-test_report.json",
         "T1.4or5_mask_T1.5_handcrafted_RF_isAt_at-test_report.json"),
        ("MASK C4 LR (mask+e1+e2+temporal)",
         "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test_report.json",
         "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test_report.json"),
        ("MASK C1 LR (mask only)",
         "T1.4or5_mask_C1_mask_LR_at_at-test_report.json",
         "T1.4or5_mask_C1_mask_LR_isAt_at-test_report.json"),
        ("Temporal-only LR (15-d)",
         "T1.4or5_mask_T1.4_temporal_only_LR_at_at-test_report.json",
         "T1.4or5_mask_T1.4_temporal_only_LR_isAt_at-test_report.json"),
    ]
    print(f"{'configuration':<40s}{'global':>8s}{'MR(at)':>8s}{'MR(isAt)':>9s}")
    print("-" * 65)
    for label, at_file, isAt_file in feature_pairs:
        ar = _safe_load(log_dir / at_file)
        ir = _safe_load(log_dir / isAt_file)
        if ar is None or ir is None:
            continue
        mr_at = ar["scores"]["macro_recall_at"]
        mr_is = ir["scores"]["macro_recall_isAt"]
        global_mean = (mr_at + mr_is) / 2
        print(f"{label:<40s}{global_mean:>8.4f}{mr_at:>8.4f}{mr_is:>9.4f}")

    # LLM rows score both targets in the same call, so they fit the same row
    # without combining. Re-print them under the same header for
    # apples-to-apples comparison.
    llm_rows = [
        ("LLM P-AB zero-shot (8B)",          "T1.1_llm_zeroshot_PAB_deepinfra_Meta-Llama-31-8B-Instruct_at-test_report.json"),
        ("LLM P-A+P-B split (8B)",           "T1.1_llm_zeroshot_PA+PB_split_v2_report.json"),
        ("LLM P-R zero-shot (8B)",           "T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test_report.json"),
        ("LLM P-R + RAG K=3 (8B)",           "T1_llm_rag3_PR_at-test_report.json"),
        ("LLM P-R + WD + Temporal (8B)",     "T1_llm_zeroshot_wd_temp_PR_at-test_report.json"),
        ("LLM P-R + RAG + WD + Temp (8B)",   "T1_llm_rag3_wd_temp_PR_at-test_report.json"),
    ]
    for label, fname in llm_rows:
        r = _safe_load(log_dir / fname)
        if r is None:
            continue
        s = r["scores"]
        print(f"{label:<40s}{s['global_score']:>8.4f}{s['macro_recall_at']:>8.4f}{s['macro_recall_isAt']:>9.4f}")
    print("-" * 65)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
