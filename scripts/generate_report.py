"""Render a Markdown evaluation report from ``logs/final/results.json``.

Reads the aggregated bundle produced by ``aggregate_results.py`` and
emits a narrative report covering:
  - Executive summary (best system, top-line numbers)
  - Methodology (data, splits, metric definitions)
  - Per-baseline section (handcrafted, MASK, LLM zero-shot, LLM+RAG, LLM+ctx, LLM full)
  - Comparison tables (global / MR(at) / MR(isAt) / cost)
  - Per-language breakdown
  - Confusion matrices (rendered as ASCII tables)
  - Cost / quality discussion
  - Findings & recommendations
  - Appendix: raw configs

Usage:
    uv run python scripts/generate_report.py
    uv run python scripts/generate_report.py --results logs/final/results.json --out logs/final/evaluation_report.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_disagreement_module():
    """Import scripts/disagreement_analysis.py without requiring it to be on
    sys.path as a package. Cached so repeated calls are cheap."""
    if "disagreement_analysis" in sys.modules:
        return sys.modules["disagreement_analysis"]
    spec = importlib.util.spec_from_file_location(
        "disagreement_analysis", PROJECT_ROOT / "scripts" / "disagreement_analysis.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["disagreement_analysis"] = module
    spec.loader.exec_module(module)
    return module


# Mapping from a stable display name to the experiment_id we expect to find.
# Order is the order they'll appear in the comparison tables.
DISPLAY_ENTRIES: list[tuple[str, str, str]] = [
    # (group, display_name, experiment_id)
    ("Handcrafted / MASK (same-split)", "Handcrafted RF",                       "T1.4or5_mask_T1.5_handcrafted_RF_at_at-test"),
    ("Handcrafted / MASK (same-split)", "Handcrafted RF (isAt-target run)",     "T1.4or5_mask_T1.5_handcrafted_RF_isAt_at-test"),
    ("Handcrafted / MASK (same-split)", "MASK C4 LR (mask+e1+e2+temporal)",     "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test"),
    ("Handcrafted / MASK (same-split)", "MASK C4 LR (isAt-target run)",         "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test"),
    ("Handcrafted / MASK (same-split)", "MASK C1 LR (mask only)",               "T1.4or5_mask_C1_mask_LR_at_at-test"),
    ("Handcrafted / MASK (same-split)", "MASK C1 LR (isAt-target run)",         "T1.4or5_mask_C1_mask_LR_isAt_at-test"),
    ("Handcrafted / MASK (same-split)", "Temporal-only LR",                     "T1.4or5_mask_T1.4_temporal_only_LR_at_at-test"),
    ("Handcrafted / MASK (same-split)", "Temporal-only LR (isAt-target run)",   "T1.4or5_mask_T1.4_temporal_only_LR_isAt_at-test"),
    ("LLM zero-shot",                   "P-A (at only)",                        "T1.1_llm_zeroshot_PA_v2_fixed_prompt"),
    ("LLM zero-shot",                   "P-B (isAt only)",                      "T1.1_llm_zeroshot_PB_v2_fixed_prompt"),
    ("LLM zero-shot",                   "P-AB (combined)",                      "T1.1_llm_zeroshot_PAB_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
    ("LLM zero-shot",                   "P-A + P-B split",                      "T1.1_llm_zeroshot_PA+PB_split_v2"),
    ("LLM zero-shot",                   "P-R (combined + reasoning)",           "T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
    ("LLM with context",                "P-R + RAG K=3",                        "T1_llm_rag3_PR_at-test_v2"),
    ("LLM with context",                "P-R + Wikidata + Temporal",            "T1_llm_zeroshot_wd_temp_PR_at-test_v2"),
    ("LLM with context",                "P-R + RAG + WD + Temporal (full)",     "T1_llm_rag3_wd_temp_PR_at-test_v2"),
    ("LLM with context",                "P-R + RAG K=8 (no diversify, full 188)", "T2_ksweep_full_k8_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
    ("LLM with context",                "P-R + RAG K=8 (diversify, full 188)",  "T2_ksweep_full_k8_div_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
    ("Agentic pipeline",                "Classifier + Justification + Validator + GPT-4o-mini escalation", "T3_agentic_PR_rag3_wd_temp_full"),
    ("Hybrid (best per task)",          "RF(at) + MASK-C4(isAt)",               "T1_hybrid_RFat_MASKC4isAt_at-test"),
    ("Hybrid (best per task)",          "P-A+RAG (at) + P-B zero-shot (isAt)",  "T1_llm_hybrid_PA-rag3_PB-zeroshot_at-test_v3"),
]


def _fmt(v: Any, width: int = 8, kind: str = "f") -> str:
    if v is None or (isinstance(v, float) and v != v):
        return f"{'—':>{width}s}"
    if kind == "f":
        return f"{v:>{width}.4f}"
    if kind == "d":
        return f"{int(v):>{width}d}"
    return f"{str(v):>{width}s}"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def _confusion_table(cm: list[list[int]], labels: list[str], target_name: str) -> str:
    if not cm or not labels:
        return ""
    rows = []
    for lbl, row in zip(labels, cm):
        rows.append([f"**{lbl}**"] + [str(v) for v in row])
    headers = [f"`{target_name}` gold ↓ / pred →"] + labels
    return _md_table(headers, rows)


def _section_table(group: str, entries: list[tuple[str, str]], experiments: dict) -> str:
    rows = []
    for display, exp_id in entries:
        r = experiments.get(exp_id)
        if r is None:
            continue
        s = r.get("scores", {})
        md = r.get("metadata", {})
        ps = (md.get("predictor_stats") or {})
        n = r.get("n_instances", "—")
        gs = s.get("global_score")
        at = s.get("macro_recall_at")
        isAt = s.get("macro_recall_isAt")
        parse = (
            f"{ps.get('parse_ok') or '—'}/{ps.get('parse_partial') or '—'}/{ps.get('parse_fail') or '—'}"
            if ps.get('parse_ok') is not None or ps.get('n_calls') is not None
            else "—"
        )
        tok_in = ps.get("prompt_tokens", "")
        tok_out = ps.get("completion_tokens", "")
        cost = (
            f"{int(tok_in):,}/{int(tok_out):,}" if isinstance(tok_in, int) and isinstance(tok_out, int) else "—"
        )
        latency = md.get("avg_latency_ms")
        latency_str = f"{latency:.0f} ms" if isinstance(latency, (int, float)) else "—"
        rows.append([
            display,
            str(n),
            f"**{gs:.4f}**" if isinstance(gs, float) else "—",
            f"{at:.4f}" if isinstance(at, float) else "—",
            f"{isAt:.4f}" if isinstance(isAt, float) else "—",
            parse,
            cost,
            latency_str,
        ])
    if not rows:
        return f"_(no experiments matched group {group!r})_"
    headers = ["configuration", "n", "global", "MR(at)", "MR(isAt)", "parse ok/part/fail", "tokens in/out", "avg latency"]
    return _md_table(headers, rows)


def _per_language_section(experiments: dict, exp_id: str) -> str:
    r = experiments.get(exp_id)
    if r is None or "per_language" not in r:
        return f"_(no per-language breakdown available for {exp_id})_"
    headers = ["language", "n", "global", "MR(at)", "MR(isAt)"]
    rows = []
    for lang, b in sorted(r["per_language"].items()):
        rows.append([
            lang,
            str(b.get("n_instances", "—")),
            f"{b.get('global_score', 0):.4f}",
            f"{b.get('macro_recall_at', 0):.4f}",
            f"{b.get('macro_recall_isAt', 0):.4f}",
        ])
    return _md_table(headers, rows)


def _confusion_section(experiments: dict, exp_id: str) -> str:
    r = experiments.get(exp_id)
    if r is None:
        return ""
    parts = []
    cm_at = r.get("at_confusion_matrix")
    if cm_at:
        parts.append(_confusion_table(cm_at, list(r.get("at_labels", ["TRUE", "PROBABLE", "FALSE"])), "at"))
    cm_is = r.get("isAt_confusion_matrix")
    if cm_is:
        parts.append(_confusion_table(cm_is, list(r.get("isAt_labels", ["TRUE", "FALSE"])), "isAt"))
    return "\n\n".join(parts)


def _ranking_table(ranking: list[dict], top: int = 12) -> str:
    headers = ["rank", "experiment_id", "global", "MR(at)", "MR(isAt)", "parse ok/part/fail", "tokens in/out"]
    rows = []
    for i, r in enumerate(ranking[:top], start=1):
        if r.get("parse_ok") is None and r.get("n_instances") and "mask" in r.get("experiment_id", "").lower():
            parse = "—"
        else:
            parse = (
                f"{r.get('parse_ok') if r.get('parse_ok') is not None else '—'}"
                f"/{r.get('parse_partial') if r.get('parse_partial') is not None else '—'}"
                f"/{r.get('parse_fail') if r.get('parse_fail') is not None else '—'}"
            )
        tin = r.get("prompt_tokens")
        tout = r.get("completion_tokens")
        cost = f"{tin:,}/{tout:,}" if isinstance(tin, int) and isinstance(tout, int) else "—"
        rows.append([
            str(i),
            f"`{r.get('experiment_id','')}`",
            f"**{r['global_score']:.4f}**" if isinstance(r.get("global_score"), float) else "—",
            f"{r['macro_recall_at']:.4f}" if isinstance(r.get("macro_recall_at"), float) else "—",
            f"{r['macro_recall_isAt']:.4f}" if isinstance(r.get("macro_recall_isAt"), float) else "—",
            parse,
            cost,
        ])
    return _md_table(headers, rows)


def _render_k_sweep_section(k_sweep_dir: Path) -> str | None:
    """Render the K-sweep summary table from ``logs/k_sweep/k_sweep_summary.csv``.

    Returns ``None`` when no sweep has run yet, so the report still renders
    cleanly before any sweep is on disk.
    """
    csv_path = k_sweep_dir / "k_sweep_summary.csv"
    if not csv_path.exists():
        return None

    import csv as _csv

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = _csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return None

    # Sort by global score descending so the best cell is at the top.
    def _g(row: dict) -> float:
        try:
            return float(row.get("global_score", 0) or 0)
        except ValueError:
            return 0.0

    rows.sort(key=_g, reverse=True)

    # Pull a few useful header values from the first row.
    sample = rows[0]
    model = sample.get("model", "—")
    provider = sample.get("provider", "—")
    n = sample.get("n_calls", "—")

    header_block = (
        "## K-sweep ablation (RAG retrieval)\n"
        f"_Variant P-R, model `{model}` via {provider}, n={n} test instances per cell. "
        "All cells run with the adjustable-prompt rendering and `max_tokens=512`._\n\n"
    )

    headers = [
        "rank", "K", "diversify", "global", "MR(at)", "MR(isAt)",
        "parse ok/part/fail", "avg latency (ms)",
    ]
    table_rows: list[list[str]] = []
    for i, r in enumerate(rows, start=1):
        try:
            div = "on" if str(r.get("diversify_labels", "")).lower() in {"true", "1"} else "off"
        except Exception:
            div = "—"
        try:
            global_score = float(r.get("global_score", 0) or 0)
            at_recall = float(r.get("macro_recall_at", 0) or 0)
            isAt_recall = float(r.get("macro_recall_isAt", 0) or 0)
        except ValueError:
            global_score = at_recall = isAt_recall = float("nan")
        parse = (
            f"{r.get('parse_ok','—') or '—'}/"
            f"{r.get('parse_partial','—') or '—'}/"
            f"{r.get('parse_fail','—') or '—'}"
        )
        try:
            latency = float(r.get("avg_latency_ms", 0) or 0)
            latency_str = f"{latency:.0f}"
        except ValueError:
            latency_str = "—"
        table_rows.append([
            str(i),
            str(r.get("k", "—")),
            div,
            f"**{global_score:.4f}**" if i == 1 else f"{global_score:.4f}",
            f"{at_recall:.4f}",
            f"{isAt_recall:.4f}",
            parse,
            latency_str,
        ])

    table = _md_table(headers, table_rows)

    # Highlight top-line takeaways from the sweep.
    best = rows[0]
    best_k = best.get("k", "?")
    best_div = "on" if str(best.get("diversify_labels", "")).lower() in {"true", "1"} else "off"
    best_global = _g(best)
    notes_lines = ["", "**Findings from the sweep:**"]
    notes_lines.append(
        f"- Best cell: **K={best_k}, diversify={best_div}, global={best_global:.4f}** — "
        f"large lift over the comparable K=3 baseline run on the full 188-instance test split (≈0.526)."
    )
    notes_lines.append(
        "- Diversify-labels is K-dependent: it helps when K is small (K∈{1,3,5}) "
        "by forcing class coverage, but hurts at K=8 because the natural top-8 already spans labels — "
        "the constraint then displaces a high-similarity neighbour with a lower-ranked one."
    )
    notes_lines.append(
        "- _Caveat: cells use a 50-instance subset for cost efficiency; the absolute numbers are "
        "above the full-188 baseline partly because of sample variance. The relative ranking of "
        "(K, diversify) cells is the actionable signal._"
    )
    notes_lines.append("")
    notes_lines.append(f"Raw CSV: [`{csv_path.relative_to(PROJECT_ROOT)}`]({csv_path.relative_to(PROJECT_ROOT).as_posix()})")
    notes = "\n".join(notes_lines)

    return header_block + table + "\n" + notes + "\n\n"


def _render_disagreement_section(log_dir: Path, out_dir: Path) -> str | None:
    """Run the cross-config disagreement analysis on ``log_dir``, persist the
    artefacts to ``out_dir``, and return the markdown section for the report.

    Returns ``None`` when the analysis cannot run (no logs / module import
    failure) so the caller can skip the section without bringing down the
    whole report regeneration.
    """
    try:
        da = _load_disagreement_module()
    except Exception as exc:  # pragma: no cover — last-line defence
        print(f"  could not import disagreement_analysis: {exc!r}")
        return None

    try:
        configs = da.load_configs(log_dir)
    except Exception as exc:
        print(f"  disagreement: log load failed: {exc!r}")
        return None
    if not configs:
        print("  disagreement: no configurations matched, skipping section.")
        return None

    summ_at, cfgs_at = da.analyze_task(configs, task="at")
    summ_is, cfgs_is = da.analyze_task(configs, task="isAt")
    payload_at = da.summarize_payload("at", summ_at, cfgs_at)
    payload_is = da.summarize_payload("isAt", summ_is, cfgs_is)

    # Persist sidecar artefacts so they stay in sync with the report.
    out_dir.mkdir(parents=True, exist_ok=True)
    da._write_per_instance_csv(out_dir / "per_instance_at.csv", summ_at, cfgs_at)
    da._write_per_instance_csv(out_dir / "per_instance_isAt.csv", summ_is, cfgs_is)
    summary_full = {
        "log_dir": str(log_dir),
        "n_configurations": len(configs),
        "configurations": sorted(configs.keys()),
        "at": payload_at,
        "isAt": payload_is,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary_full, indent=2, default=str), encoding="utf-8"
    )

    # Hardest-instance markdown dumps need article context — load once.
    instance_index: dict[tuple, Any] = {}
    ds_path = PROJECT_ROOT / "data" / "dataset_reference.jsonl"
    if ds_path.exists():
        from hipe.data import load_jsonl
        for inst in load_jsonl(ds_path):
            instance_index[(inst.document_id, inst.pers_entity_id, inst.loc_entity_id)] = inst
    da._write_hardest_md(
        out_dir / "hardest_at.md", "at", summ_at, cfgs_at,
        instance_index, top_k=25, near_threshold=2,
    )
    da._write_hardest_md(
        out_dir / "hardest_isAt.md", "isAt", summ_is, cfgs_is,
        instance_index, top_k=25, near_threshold=2,
    )

    return da.format_disagreement_section(
        payload_at=payload_at,
        payload_is=payload_is,
        summaries_at=summ_at,
        summaries_is=summ_is,
        top_n_examples=5,
        near_threshold=2,
        instance_index=instance_index,
    )


def render(
    bundle: dict,
    *,
    log_dir: Path,
    disagreement_dir: Path,
    k_sweep_dir: Path,
) -> str:
    exps: dict = bundle.get("experiments", {})
    ranking: list[dict] = bundle.get("ranking_by_global_score", [])
    timestamp = bundle.get("generated_at", dt.datetime.now().isoformat())

    parts: list[str] = []
    parts.append("# HIPE-2026 Person-Place Relation Extraction — Evaluation Report\n")
    parts.append(f"_Generated {timestamp} from `logs/final/results.json` "
                 f"({bundle.get('n_experiments', 0)} experiments)_\n")

    # Executive summary
    parts.append("## Executive summary\n")
    if ranking:
        # Pick the best non-MASK-isAt-side row (the isAt-target MASK rows
        # report 0 on the at-target by construction)
        best = next(
            (r for r in ranking if "isAt" not in r.get("experiment_id", "").split("_LR_")[-1].split("_")[0]),
            ranking[0],
        )
        parts.append(
            f"- **Best overall:** `{best['experiment_id']}`  "
            f"global = **{best['global_score']:.4f}**, "
            f"MR(at) = {best['macro_recall_at']:.4f}, "
            f"MR(isAt) = {best['macro_recall_isAt']:.4f}\n"
        )

    parts.append(
        "- **Best overall configuration:** **per-task hybrid** — Handcrafted RF for `at` "
        "(MR=0.6627) plus MASK C4 LR (mask + e1 + e2 + temporal) for `isAt` (MR=0.7658). "
        "**Global = 0.7142** — exceeds every single-classifier configuration tested.\n"
    )
    parts.append("- **Best single-classifier (both tasks):** Handcrafted RF (mean=0.688).\n")
    parts.append("- **Best LLM (Llama 3.1 8B, P-R zero-shot):** global ≈ 0.538.\n")
    parts.append("- **Score gap LLM-vs-hybrid:** ~0.18 — the smaller open LLM trails the simple-feature hybrid by a wide margin.\n")
    parts.append(
        "- **Adding context (RAG / Wikidata / temporal) hurts the small LLM modestly** "
        "after fixing token-budget truncation — the model gets distracted; expect a "
        "stronger model to behave differently.\n"
    )
    parts.append(
        "- **Per-task strengths complement each other:** Handcrafted RF dominates `at` "
        "(0.66 vs MASK C4 at 0.57) because categorical features (language, person status, "
        "QID availability) capture general associations well; MASK C4 dominates `isAt` (0.77 "
        "vs RF at 0.71) because contextual embeddings + entity-span pooling carry the "
        "temporal nuance better than tabular features.\n"
    )
    parts.append("\n")

    # Methodology
    parts.append("## Methodology\n")
    parts.append("- **Dataset:** HIPE-2026 v1.0 reference (`data/dataset_reference.jsonl`, 1,251 instances).\n")
    parts.append("- **Split:** official `data/v1_baseline_train_test_ids.csv` per task; "
                 "1,063 train / 188 test for the `at` task. All comparable scores in this report "
                 "use the 188-instance `at`-task test split.\n")
    parts.append(
        "- **Metric:** macro-averaged Recall (HIPE-2026 official); "
        "GlobalScore = mean of MR(at) and MR(isAt). "
        "`null` predictions are converted to `FALSE` per the official rule. Evaluation primitives "
        "live in [`hipe.evaluation.metrics`](../../hipe/evaluation/metrics.py).\n"
    )
    parts.append("- **MASK / handcrafted baselines:** classifier trained on the 1,063 train rows, scored on the 188 test rows (no CV).\n")
    parts.append("- **LLM baselines:** Llama 3.1 8B Instruct via DeepInfra, temperature 0.0, "
                 "max_tokens=512 (256 in early runs caused truncation; v2 runs use 512). "
                 "Zero-shot, no fixed few-shot. RAG few-shot retrieves K=3 neighbours via "
                 "`BAAI/bge-m3` over the 1,063 train rows.\n")
    parts.append("\n")

    # Top-N ranking
    parts.append("## Top-12 by GlobalScore\n")
    parts.append(_ranking_table(ranking, top=12))
    parts.append("\n\n")

    # Per-group comparison tables
    grouped: dict[str, list[tuple[str, str]]] = {}
    for group, name, eid in DISPLAY_ENTRIES:
        grouped.setdefault(group, []).append((name, eid))
    for group, entries in grouped.items():
        parts.append(f"## {group}\n")
        parts.append(_section_table(group, entries, exps))
        parts.append("\n\n")

    # Per-language breakdown for the headline LLM and best feature baseline
    parts.append("## Per-language breakdown\n")
    headline_ids = [
        ("LLM P-R zero-shot",  "T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
        ("LLM P-R + RAG K=3",  "T1_llm_rag3_PR_at-test_v2"),
        ("LLM P-R + WD + Temp","T1_llm_zeroshot_wd_temp_PR_at-test_v2"),
        ("LLM P-R full",       "T1_llm_rag3_wd_temp_PR_at-test_v2"),
        ("MASK C4 (at target)", "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test"),
        ("Handcrafted RF (at target)", "T1.4or5_mask_T1.5_handcrafted_RF_at_at-test"),
    ]
    for name, eid in headline_ids:
        if eid not in exps:
            continue
        parts.append(f"### {name}\n")
        parts.append(_per_language_section(exps, eid))
        parts.append("\n\n")

    # Confusion matrices for the headline LLM rows
    parts.append("## Confusion matrices (headline runs)\n")
    cm_ids = [
        ("Hybrid RF(at) + MASK-C4(isAt) — best overall", "T1_hybrid_RFat_MASKC4isAt_at-test"),
        ("LLM P-R zero-shot",  "T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
        ("LLM P-R + RAG K=3",  "T1_llm_rag3_PR_at-test_v2"),
        ("LLM P-R + WD + Temp","T1_llm_zeroshot_wd_temp_PR_at-test_v2"),
        ("LLM P-R full",       "T1_llm_rag3_wd_temp_PR_at-test_v2"),
    ]
    for name, eid in cm_ids:
        if eid not in exps:
            continue
        parts.append(f"### {name}\n")
        parts.append(_confusion_section(exps, eid))
        parts.append("\n\n")

    # Findings
    parts.append("## Findings\n")
    parts.append("1. **PROBABLE class is the hardest target across all systems.** Recall on PROBABLE rarely exceeds 0.35; the dominant LLM behaviour is to never pick it. Few-shot or contrastive training is the next high-priority lever for this class.\n")
    parts.append("2. **Reasoning beats labels-only on small LLMs.** P-R (combined + 4-line reasoning) lifts global score from ≈0.45 (P-AB) to ≈0.54 — the largest single jump on Llama 3.1 8B. The cost is ~10× output tokens, still negligible at DeepInfra prices.\n")
    parts.append("3. **Token-budget truncation is a silent score thief.** `max_tokens=256` cuts the reasoning block before the classification line in ~14% of P-R+context runs. Bumping to 512 recovered ≈1.5 pp.\n")
    parts.append("4. **Adding context hurts a small LLM, even after the truncation fix.** P-R + Wikidata + Temporal is still ~0.06 below zero-shot P-R, and full-pipeline RAG + WD + Temp tracks RAG-only. Likely cause: 57% of persons have no Wikidata so the entity-context block is half-empty noise. A larger model (Llama 70B / GPT-4o) is the right A/B before redesigning the prompt.\n")
    parts.append("5. **Simple feature baselines crush small-LLM zero-shot.** Handcrafted RF (36 features, ~5 ms inference) outperforms every Llama 3.1 8B configuration tested, including the full pipeline. MASK C4 (mask + entity-span + temporal LR) sits between the two on `at` and beats handcrafted on `isAt`.\n")
    parts.append(
        "5b. **Per-task hybrid is the new ceiling.** Handcrafted RF for `at` + MASK C4 LR for "
        "`isAt` reaches **global = 0.7142** — +0.026 over Handcrafted RF used for both tasks "
        "(0.688) and +0.046 over MASK C4 used for both tasks (0.668). Each classifier wins on "
        "the target it was strongest on. The merge is free (no new training, no API calls): "
        "concatenate the two existing prediction files via "
        "`scripts/combine_split_predictions.py`. We enumerated all four pairings of "
        "{RF, MASK C4} × {at, isAt} and confirmed RF(at)+MASK-C4(isAt) is the optimum.\n"
    )
    parts.append("6. **Parse failures on P-A / P-B with the verbatim spec prompts** were caused by Llama parroting the literal placeholder word `LABEL`. Concrete output examples in the system prompt fixed this end-to-end.\n")
    parts.append(
        "6b. **Agentic pipeline (Classifier + Justification + Validator + Tier-3 escalation) "
        "lifts P-R zero-shot only marginally** on Llama 3.1 8B. Full agentic run (P-R + RAG K=3 + "
        "WD + Temp, GPT-4o-mini escalation) reached global=0.5412 (vs 0.5375 zero-shot, +0.004). "
        "The validator flagged 89% of instances and the escalator fired on 59%, but the underlying "
        "classifier already produced clean parses (188/0/0) so the escalation has little to fix. "
        "Where agentic adds value is in **traceability** (per-instance evidence assessment) rather "
        "than score — and we'd expect a stronger Tier-1 model to make the escalation more impactful.\n"
    )
    parts.append(
        "7. **Larger K helps RAG, especially without diversification.** Confirmed on the full "
        "188-instance test split: K=8 / no-diversify reaches global=0.5922 — **+0.055 over P-R "
        "zero-shot (0.5375)** and the new best LLM-only configuration. K=8 with diversify hits "
        "the highest LLM `isAt` recall yet (0.7196), close to MASK C4's 0.766. The 50-subset "
        "K-sweep flagged the right ranking; the absolute scores there were inflated by sample "
        "variance. See [K-sweep ablation (RAG retrieval)](#k-sweep-ablation-rag-retrieval) below.\n"
    )
    parts.append(
        "8. **Universally-hard instances are rare; the systems mostly fail on different rows.** "
        "Cross-config disagreement analysis shows only a handful of instances are wrong "
        "everywhere or right everywhere, and the broad bell-shaped `at` hardness histogram "
        "tells us each configuration's failure set only partially overlaps with the others' — "
        "an ensembling opportunity. See "
        "[Cross-config disagreement analysis](#cross-config-disagreement-analysis) below.\n"
    )
    parts.append("\n")

    # K-sweep ablation (renders only when logs/k_sweep/k_sweep_summary.csv exists).
    k_sweep_section = _render_k_sweep_section(k_sweep_dir)
    if k_sweep_section is not None:
        parts.append(k_sweep_section)

    # Cross-config disagreement (regenerated end-to-end from logs/ablations).
    section = _render_disagreement_section(log_dir, disagreement_dir)
    if section is not None:
        parts.append(section)

    # Recommendations
    parts.append("## Recommendations / Next steps\n")
    parts.append("- **Stronger model A/B (highest priority):** rerun P-R + RAG + WD + Temp on Llama 3.3 70B (DeepInfra) and GPT-4o-mini (OpenAI). Spec literature suggests +10-20 pp; both are within budget.\n")
    parts.append("- ~~**K-sweep for retrieval:** K∈{1,3,5,7} with `--diversify-labels`~~ — done at both 50-subset and full 188-test. K=8 / no-diversify is the best LLM-only configuration at global=0.592 (+0.055 over P-R zero-shot).\n")
    parts.append("- **Hybrid extension:** try ensembling K=8 LLM (best LLM `isAt` = 0.720) with MASK C4 (best classifier `isAt` = 0.766) via confidence-weighted vote — possible further lift on `isAt`.\n")
    parts.append("- **Few-shot (fixed) variant:** spec's 15-example balanced demonstration set, separate from RAG. Often complementary.\n")
    parts.append("- ~~**Justification + Validator agents (Pipeline §5-6):**~~ — implemented; full agentic run yields a marginal +0.004 lift over P-R zero-shot. Re-run on a stronger Tier-1 model (Llama 70B / GPT-4o-mini) where the escalator has more to act on.\n")
    parts.append("- **MASK ablations not yet run:** templates M1/M3/M4/M5; XLM-R-large encoder; multi-layer extraction (concat layers 6/9/12); MLP head with contrastive (SupCon for `isAt`, ordinal for `at`).\n")
    parts.append("- **Cross-validation:** Phase-0 numbers are 5-fold CV; the same-split numbers in this report are single-shot. Adding 5-fold CV to the same-split evaluator would make the comparison statistically grounded.\n")
    parts.append("- **OCR post-correction & live HeidelTime:** currently we use the dataset's pre-computed temporal/Wikidata fields; live extraction lets us run on raw v1.0 / sandbox data.\n")
    parts.append("\n")

    # Appendix: missing experiments
    parts.append("## Appendix A — Configurations tried\n")
    parts.append("All experiment IDs in `logs/ablations/` (in alphabetical order):\n\n")
    for eid in sorted(exps.keys()):
        parts.append(f"- `{eid}`\n")
    parts.append("\n")

    parts.append("## Appendix B — Reproduction commands\n")
    parts.append("```bash\n")
    parts.append("# Build retrieval index\n")
    parts.append("uv run python scripts/build_retrieval_index.py --model BAAI/bge-m3 \\\n")
    parts.append("    --out-dir runs/retriever_at_bgem3\n\n")
    parts.append("# Extract MASK embeddings (one-time)\n")
    parts.append("uv run python scripts/extract_mask_embeddings.py --template M2\n\n")
    parts.append("# Same-split MASK / handcrafted baselines\n")
    parts.append("uv run python scripts/mask_same_split_eval.py\n\n")
    parts.append("# LLM zero-shot P-R\n")
    parts.append("uv run python scripts/run_llm_baseline.py --variant R \\\n")
    parts.append("    --provider deepinfra --max-tokens 512\n\n")
    parts.append("# LLM P-R + RAG K=3\n")
    parts.append("uv run python scripts/run_llm_baseline.py --variant R \\\n")
    parts.append("    --provider deepinfra --max-tokens 512 \\\n")
    parts.append("    --retriever-dir runs/retriever_at_bgem3 --k 3\n\n")
    parts.append("# LLM P-R full pipeline\n")
    parts.append("uv run python scripts/run_llm_baseline.py --variant R \\\n")
    parts.append("    --provider deepinfra --max-tokens 512 \\\n")
    parts.append("    --retriever-dir runs/retriever_at_bgem3 --k 3 \\\n")
    parts.append("    --include-wikidata --include-temporal\n\n")
    parts.append("# Full agentic pipeline (Classifier + Justification + Validator + escalation)\n")
    parts.append("uv run python scripts/run_agentic_pipeline.py \\\n")
    parts.append("    --retriever-dir runs/retriever_at_bgem3 \\\n")
    parts.append("    --variant R --provider deepinfra --task at \\\n")
    parts.append("    --k-retrieved 3 --include-wikidata --include-temporal \\\n")
    parts.append("    --max-tokens 512 \\\n")
    parts.append("    --escalate-provider openai --escalate-model gpt-4o-mini\n\n")
    parts.append("# Per-task hybrid: RF for `at`, MASK-C4 for `isAt`\n")
    parts.append("uv run python scripts/combine_split_predictions.py \\\n")
    parts.append("    --pa logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_at_at-test_predictions.jsonl \\\n")
    parts.append("    --pb logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test_predictions.jsonl \\\n")
    parts.append("    --experiment-id T1_hybrid_RFat_MASKC4isAt_at-test\n\n")
    parts.append("# K-sweep over (K, diversify_labels) for RAG retrieval\n")
    parts.append("uv run python scripts/run_retrieval_k_sweep.py \\\n")
    parts.append("    --retriever-dir runs/retriever_at_bgem3 \\\n")
    parts.append("    --variant R --provider deepinfra --task at \\\n")
    parts.append("    --k-values 1 3 5 8 --diversify-modes both \\\n")
    parts.append("    --max-tokens 512 --limit 50\n\n")
    parts.append("# Aggregate everything + render this report\n")
    parts.append("# (generate_report.py runs the cross-config disagreement\n")
    parts.append("#  analysis inline and writes its sidecars to logs/final/disagreement/)\n")
    parts.append("uv run python scripts/aggregate_results.py\n")
    parts.append("uv run python scripts/generate_report.py\n\n")
    parts.append("# Or run the disagreement analysis on its own (e.g. against a custom log dir):\n")
    parts.append("uv run python scripts/disagreement_analysis.py \\\n")
    parts.append("    --log-dir logs/ablations --top-k 25\n")
    parts.append("```\n")

    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", default=str(PROJECT_ROOT / "logs" / "final" / "results.json"))
    ap.add_argument("--out", default=str(PROJECT_ROOT / "logs" / "final" / "evaluation_report.md"))
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"),
                    help="Directory of per-experiment prediction JSONLs, used "
                         "for the cross-config disagreement section.")
    ap.add_argument("--disagreement-dir",
                    default=str(PROJECT_ROOT / "logs" / "final" / "disagreement"),
                    help="Where to write per-instance CSVs / summary.json / "
                         "hardest_*.md sidecars.")
    ap.add_argument("--k-sweep-dir",
                    default=str(PROJECT_ROOT / "logs" / "k_sweep"),
                    help="Directory holding k_sweep_summary.csv from "
                         "scripts/run_retrieval_k_sweep.py.")
    args = ap.parse_args()

    bundle = json.loads(Path(args.results).read_text(encoding="utf-8"))
    out_text = render(
        bundle,
        log_dir=Path(args.log_dir),
        disagreement_dir=Path(args.disagreement_dir),
        k_sweep_dir=Path(args.k_sweep_dir),
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_text, encoding="utf-8")
    print(f"Wrote {out_path}  ({len(out_text):,} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
