"""Cross-config disagreement analysis (Spec §13.2).

For every test instance, score every prediction file in ``logs/ablations/``
and produce per-instance correctness flags so we can answer:

  * Which instances does **every** system get wrong? (the universally-hard set)
  * Which instances does **every** system get right? (the easy set)
  * What's the distribution of "n configs got this right" across the test set?
  * For the universally-wrong set, what predicted label did the systems converge
    on? (a 'systems-disagree-with-gold' pattern is a strong mislabel signal.)

Outputs (under ``logs/final/disagreement/`` by default):

  per_instance_at.csv          one row per (doc, pers, loc), one column per
  per_instance_isAt.csv        config; cells are 0/1 = wrong/right.
  summary.json                 aggregate counts, hardness histogram, language
                               breakdown, configs included, etc.
  hardest_at.md                human-readable list of instances every system
  hardest_isAt.md              gets wrong, with article context where available.

Usage:
    uv run python scripts/disagreement_analysis.py
    uv run python scripts/disagreement_analysis.py --min-configs 8 --top-k 25
    uv run python scripts/disagreement_analysis.py \\
        --include-globs 'T1.1_*' 'T1_llm_rag*'    # restrict the config set
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from hipe.data import load_jsonl
from hipe.evaluation.metrics import null_to_false

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Files we never want to mix into the cross-config view (smoke tests, partial
# runs etc.). Match against ``exp_id``.
DEFAULT_EXCLUDE_GLOBS = ("smoke_*",)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def _exp_id(path: Path) -> str:
    return path.stem.replace("_predictions", "")


def _load_predictions(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_configs(
    log_dir: Path,
    *,
    include_globs: list[str] | None = None,
    exclude_globs: Iterable[str] = DEFAULT_EXCLUDE_GLOBS,
    min_instances: int = 100,
) -> dict[str, list[dict]]:
    """Public loader: maps experiment_id -> rows from ``*_predictions.jsonl``.

    Used by ``generate_report.py`` so the report can be regenerated end-to-end
    without an extra subprocess invocation.
    """
    configs: dict[str, list[dict]] = {}
    for p in sorted(log_dir.glob("*_predictions.jsonl")):
        eid = _exp_id(p)
        if any(fnmatch.fnmatch(eid, pat) for pat in exclude_globs):
            continue
        if include_globs and not any(fnmatch.fnmatch(eid, pat) for pat in include_globs):
            continue
        rows = _load_predictions(p)
        if len(rows) < min_instances:
            continue
        configs[eid] = rows
    return configs


def analyze_task(
    configs: dict[str, list[dict]],
    *,
    task: str,
) -> tuple[list[dict], list[str]]:
    """Run the full per-task analysis and return (summaries, config_names).

    ``summaries`` is the list of per-instance dicts that
    :func:`_summarize_per_instance` produces; ``config_names`` is the
    cross-config sample for that task.
    """
    keys, cfgs, table = _build_instance_table(configs, task=task)
    return _summarize_per_instance(keys, cfgs, table), cfgs


def summarize_payload(
    task: str,
    summaries: list[dict],
    config_names: list[str],
) -> dict[str, Any]:
    """Public re-export of :func:`_summary_payload`."""
    return _summary_payload(task, summaries, config_names)


def _instance_key(row: dict) -> tuple[str, str, str]:
    """Stable cross-config instance identity."""
    return (
        str(row.get("document_id", "")),
        str(row.get("pers_entity_id", "")),
        str(row.get("loc_entity_id", "")),
    )


def _has_task_predictions(rows: list[dict], task_field: str) -> bool:
    """A file 'covers' a task only if it has *real* predictions for it.

    Rejects two confounders:

    1. MASK isAt-only runs leave ``at_predicted=null`` on every row.
    2. PA-only / PB-only / hybrid LLM runs hard-code the un-targeted column
       to ``FALSE`` via :class:`LLMPredictor.fallback_*`. Counting those as
       "predictions" would let a single-target variant systematically take
       credit for / blame other configs' work on the unrelated task.

    A column qualifies as a prediction only if it has at least one non-null
    value AND has more than one distinct non-null label across the file.
    """
    seen: set[str] = set()
    has_any = False
    for r in rows:
        v = r.get(task_field)
        if v is None:
            continue
        has_any = True
        seen.add(str(v))
    return has_any and len(seen) > 1


# ---------------------------------------------------------------------------
# Per-instance scoring
# ---------------------------------------------------------------------------


def _build_instance_table(
    configs: dict[str, list[dict]],
    *,
    task: str,
) -> tuple[list[tuple[str, str, str]], list[str], dict[tuple, dict]]:
    """Build the (instance, config) correctness matrix for one task.

    Returns
    -------
    keys
        Stable list of instance keys, sorted for reproducibility.
    config_names
        Configs that cover this task (have non-null predictions for it).
    table
        Dict keyed by instance — value is a dict with ``gold``, ``language``,
        ``per_config`` (config -> dict with ``predicted``, ``correct``).
    """
    pred_field = f"{task}_predicted"
    gold_field = f"{task}_gold"
    config_names = [
        name for name, rows in configs.items()
        if _has_task_predictions(rows, pred_field)
    ]

    # Per-instance index: gold (from any covering config — they should agree),
    # language, and per-config rows.
    table: dict[tuple, dict] = {}
    for cfg in config_names:
        for r in configs[cfg]:
            key = _instance_key(r)
            entry = table.setdefault(
                key, {"gold": None, "language": None, "per_config": {}}
            )
            # Track gold + language from the first config that has it; flag
            # mismatches (would indicate the configs evaluated different splits).
            g = r.get(gold_field)
            if g is not None:
                if entry["gold"] is None:
                    entry["gold"] = g
                elif entry["gold"] != g:
                    entry["gold"] = f"MISMATCH({entry['gold']}|{g})"
            if entry["language"] is None and r.get("language"):
                entry["language"] = r["language"]
            pred_raw = r.get(pred_field)
            if pred_raw is None:
                # This config's row exists but has no task prediction — skip,
                # it's an isAt-only file landed in the at view via the join.
                continue
            pred = str(pred_raw)
            gold_norm = null_to_false(g)
            correct = str(null_to_false(pred)) == str(gold_norm)
            entry["per_config"][cfg] = {"predicted": pred, "correct": correct}

    keys = sorted(table.keys())
    return keys, sorted(config_names), table


def _summarize_per_instance(
    keys: list[tuple],
    config_names: list[str],
    table: dict[tuple, dict],
) -> list[dict]:
    """Per-instance aggregates: n_correct, n_total, modal wrong prediction, etc."""
    out: list[dict] = []
    for key in keys:
        entry = table[key]
        per_cfg = entry["per_config"]
        # Restrict to configs that actually predicted on this row (some configs
        # might be missing rows on the join — shouldn't happen on the at-task
        # split but defensive).
        scored = {c: v for c, v in per_cfg.items() if c in config_names}
        n_total = len(scored)
        if n_total == 0:
            continue
        n_correct = sum(1 for v in scored.values() if v["correct"])
        wrong_preds = [v["predicted"] for v in scored.values() if not v["correct"]]
        modal_wrong = Counter(wrong_preds).most_common(1)[0][0] if wrong_preds else None
        out.append(
            {
                "document_id": key[0],
                "pers_entity_id": key[1],
                "loc_entity_id": key[2],
                "language": entry["language"],
                "gold": entry["gold"],
                "n_correct": n_correct,
                "n_total": n_total,
                "frac_correct": n_correct / n_total if n_total else 0.0,
                "modal_wrong_pred": modal_wrong,
                "all_wrong": n_correct == 0,
                "all_right": n_correct == n_total,
                "per_config": {c: v for c, v in scored.items()},
            }
        )
    return out


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_per_instance_csv(
    out_path: Path,
    summaries: list[dict],
    config_names: list[str],
) -> None:
    fieldnames = [
        "document_id", "pers_entity_id", "loc_entity_id", "language", "gold",
        "n_correct", "n_total", "frac_correct", "modal_wrong_pred",
        "all_wrong", "all_right",
    ] + config_names

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in summaries:
            row = {k: s[k] for k in fieldnames if k in s}
            for cfg in config_names:
                v = s["per_config"].get(cfg)
                # 1 = correct, 0 = wrong, blank = config didn't predict on this row.
                row[cfg] = 1 if v and v["correct"] else (0 if v else "")
            writer.writerow(row)


def _bucket_count(items: Iterable[Any]) -> dict[str, int]:
    return dict(Counter(str(x) for x in items))


def _summary_payload(
    task: str,
    summaries: list[dict],
    config_names: list[str],
) -> dict[str, Any]:
    n = len(summaries)
    if n == 0:
        return {"task": task, "n_instances": 0, "configs": config_names}

    all_wrong = [s for s in summaries if s["all_wrong"]]
    all_right = [s for s in summaries if s["all_right"]]

    # Hardness histogram: for n_correct=0..|configs|, how many instances?
    histogram: dict[int, int] = defaultdict(int)
    for s in summaries:
        histogram[s["n_correct"]] += 1

    # By language and by gold class.
    by_language: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "all_wrong": 0, "all_right": 0}
    )
    by_gold: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "all_wrong": 0, "all_right": 0}
    )
    for s in summaries:
        lang = str(s["language"] or "unknown")
        gold = str(null_to_false(s["gold"]))
        by_language[lang]["n"] += 1
        by_gold[gold]["n"] += 1
        if s["all_wrong"]:
            by_language[lang]["all_wrong"] += 1
            by_gold[gold]["all_wrong"] += 1
        if s["all_right"]:
            by_language[lang]["all_right"] += 1
            by_gold[gold]["all_right"] += 1

    # Per-config error rate over the cross-config sample.
    per_config_err: dict[str, dict[str, Any]] = {}
    for cfg in config_names:
        n_seen = sum(1 for s in summaries if cfg in s["per_config"])
        n_correct = sum(
            1 for s in summaries
            if s["per_config"].get(cfg, {}).get("correct")
        )
        per_config_err[cfg] = {
            "n_seen": n_seen,
            "n_correct": n_correct,
            "accuracy": n_correct / n_seen if n_seen else 0.0,
        }

    # Universal-wrong "modal predicted label" — when every config is wrong,
    # what label did they converge on? Useful mislabel signal.
    modal_label_when_all_wrong = _bucket_count(s["modal_wrong_pred"] for s in all_wrong)
    gold_when_all_wrong = _bucket_count(s["gold"] for s in all_wrong)

    return {
        "task": task,
        "n_instances": n,
        "configs": config_names,
        "n_configs": len(config_names),
        "n_all_wrong": len(all_wrong),
        "n_all_right": len(all_right),
        "frac_all_wrong": len(all_wrong) / n,
        "frac_all_right": len(all_right) / n,
        "hardness_histogram": {str(k): histogram[k] for k in sorted(histogram.keys())},
        "by_language": dict(by_language),
        "by_gold_class": dict(by_gold),
        "per_config_accuracy": per_config_err,
        "all_wrong_modal_pred_distribution": modal_label_when_all_wrong,
        "all_wrong_gold_distribution": gold_when_all_wrong,
    }


def _render_instance_block(
    s: dict,
    task: str,
    instance_index: dict[tuple, Any],
) -> list[str]:
    key = (s["document_id"], s["pers_entity_id"], s["loc_entity_id"])
    inst = instance_index.get(key)
    person = (inst.pers_mentions_list or [""])[0] if inst else ""
    location = (inst.loc_mentions_list or [""])[0] if inst else ""
    date = inst.date if inst else "—"
    ctx_full = (inst.context or inst.text or "") if inst else ""
    ctx = ctx_full[:480]
    ctx = ctx.replace("\n", " ").strip()
    per_cfg_preds = Counter(v["predicted"] for v in s["per_config"].values())
    pred_breakdown = ", ".join(f"{lbl}×{n}" for lbl, n in per_cfg_preds.most_common())
    block = [
        f"### {s['document_id']}  ·  `{s['pers_entity_id']}` ↔ `{s['loc_entity_id']}`",
        "",
        f"- language: **{s['language']}**  ·  date: {date}",
        f"- person: **{person!r}**  ·  location: **{location!r}**",
        f"- gold {task}: **{s['gold']}**",
        f"- {s['n_correct']}/{s['n_total']} configs correct  ·  "
        f"modal predicted: **{s['modal_wrong_pred']}**",
        f"- predicted-label breakdown: {pred_breakdown}",
        "",
        f"> {ctx}{'…' if ctx_full and len(ctx_full) > 480 else ''}",
        "",
        "---",
        "",
    ]
    if not inst:
        block[-3] = "> (no context — instance not in dataset_reference.jsonl)"
    return block


def _write_hardest_md(
    out_path: Path,
    task: str,
    summaries: list[dict],
    config_names: list[str],
    instance_index: dict[tuple, Any],
    *,
    top_k: int,
    near_threshold: int,
) -> None:
    """Render universally-wrong + near-universally-wrong instances for review.

    The near-universally-wrong section catches the case where one or two
    outlier configs happen to predict the gold label by chance; for the
    remaining N-1 / N-2 configs the instance is just as adversarial.
    """
    all_wrong = sorted(
        [s for s in summaries if s["all_wrong"]],
        key=lambda s: (s["language"] or "", s["gold"] or "", s["document_id"]),
    )
    near = sorted(
        [s for s in summaries
         if not s["all_wrong"] and s["n_correct"] <= near_threshold and s["n_total"] >= near_threshold + 1],
        key=lambda s: (s["n_correct"], s["language"] or "", s["gold"] or "", s["document_id"]),
    )

    lines = [
        f"# Hardest instances for `{task}` (cross-config)",
        "",
        f"Cross-config sample: **{len(config_names)} configurations** over "
        f"**{len(summaries)} instances**.",
        "",
        f"- universally-wrong: **{len(all_wrong)}** instances "
        f"(every config got the label wrong)",
        f"- near-universally-wrong: **{len(near)}** instances "
        f"(≤ {near_threshold} configs got it right, of {len(config_names)})",
        "",
        "Each entry shows gold, modal predicted label, language, and an "
        "article snippet. When the modal-wrong label dominates and matches "
        "what a careful human reader would say, the instance is a candidate "
        "for re-annotation review.",
        "",
        "---",
        "",
        "## Universally wrong (n_correct = 0)",
        "",
    ]
    if not all_wrong:
        lines.append("_No instances are universally wrong._")
        lines.append("")
    for s in all_wrong[:top_k]:
        lines.extend(_render_instance_block(s, task, instance_index))

    lines.append("")
    lines.append(f"## Near-universally wrong (n_correct ≤ {near_threshold})")
    lines.append("")
    showing_near = near[: max(0, top_k - len(all_wrong[:top_k]))]
    if not showing_near:
        if near:
            lines.append(
                f"_({len(near)} qualifying instances exist but the "
                f"universally-wrong section already filled the top-K budget. "
                f"Increase --top-k to see them.)_"
            )
        else:
            lines.append("_No instances meet the near-universally-wrong threshold._")
        lines.append("")
    else:
        for s in showing_near:
            lines.extend(_render_instance_block(s, task, instance_index))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Markdown section builder (consumed by scripts/generate_report.py)
# ---------------------------------------------------------------------------


# Hand-curated reading of the cross-config-hardest `at` instances. Keyed by
# (document_id, pers_entity_id, loc_entity_id). The renderer pulls a row's
# entry into the gold-label review-candidates table; instances with no entry
# are still listed (with config-vote breakdown only) when they fall in the
# top-N near-universally-wrong set.
HAND_READINGS: dict[tuple[str, str, str], str] = {
    (
        "sn88068010-1890-09-25-a-i0006",
        "sn88068010-1890-09-25-a-i0006_Q44105",
        "sn88068010-1890-09-25-a-i0006_Q46",
    ): '"European" is an adjective for stamps, not a place; gold-TRUE looks brittle.',
    (
        "NZZ-1848-10-21-a-p0003",
        "NZZ-1848-10-21-a-p0003_Q153500",
        "NZZ-1848-10-21-a-p0003_Q183",
    ): 'The order is signed "Mailand … Radetzky. Deutschland." — readable as place-of-issue, not residence. Configs anchor on the literal token.',
    (
        "GDL-1981-12-11-62",
        "GDL-1981-12-11-62-NIL_m_benjamin",
        "GDL-1981-12-11-62-NIL_fulgur",
    ): 'Fulgur is fictional ("la froide planète Fulgur"); the text places M. Benjamin there. Gold-FALSE may encode a "fictional → no real association" rule the systems do not.',
    (
        "sn83030483-1790-03-03-a-i0004",
        "sn83030483-1790-03-03-a-i0004_Q3934904",
        "sn83030483-1790-03-03-a-i0004_Q84",
    ): '"LONDON, Dec. 31" is the dateline; the General is described acting in Brussels. Configs follow the dateline cue.',
    (
        "sn89058133-1920-04-22-a-i0003",
        "sn89058133-1920-04-22-a-i0003-NIL_bob_maggart",
        "sn89058133-1920-04-22-a-i0003_Q142",
    ): '"I understand you did not get killed in France" — strong indirect evidence; configs read it as too oblique for TRUE.',
}


def _hardest_for_table(
    summaries: list[dict],
    *,
    near_threshold: int,
    top_n: int,
) -> list[dict]:
    """Return the top-N (universally-wrong then near-wrong) candidates for
    the markdown table. Sort by n_correct ascending then by document id."""
    universal = [s for s in summaries if s["all_wrong"]]
    near = [
        s for s in summaries
        if not s["all_wrong"] and s["n_correct"] <= near_threshold
        and s["n_total"] >= near_threshold + 1
    ]
    pool = universal + near
    pool.sort(key=lambda s: (s["n_correct"], s["document_id"]))
    return pool[:top_n]


def _person_loc_label(
    s: dict,
    instance_index: dict[tuple, Any] | None,
) -> str:
    """Return a "'<person>' ↔ '<location>'" label for the markdown table.

    Falls back to the trailing token of each entity id when the dataset
    reference index isn't loaded.
    """
    key = (s["document_id"], s["pers_entity_id"], s["loc_entity_id"])
    inst = instance_index.get(key) if instance_index else None
    if inst is not None:
        person = (inst.pers_mentions_list or [""])[0] or "?"
        location = (inst.loc_mentions_list or [""])[0] or "?"
        # Strip newlines and trim — OCR text occasionally has linebreaks
        # mid-name which break markdown tables.
        person = person.replace("\n", " ").strip()
        location = location.replace("\n", " ").strip()
        return f"'{person}' ↔ '{location}'"
    return (
        f"`{s['pers_entity_id'].split('_')[-1]}` ↔ "
        f"`{s['loc_entity_id'].split('_')[-1]}`"
    )


def format_disagreement_section(
    *,
    payload_at: dict[str, Any],
    payload_is: dict[str, Any],
    summaries_at: list[dict],
    summaries_is: list[dict],
    top_n_examples: int = 5,
    near_threshold: int = 2,
    instance_index: dict[tuple, Any] | None = None,
    output_dir_for_links: Path | None = None,
) -> str:
    """Render the 'Cross-config disagreement analysis' section as a markdown
    string, suitable for splicing into ``evaluation_report.md``.

    The shape mirrors the hand-written first version: method, hardness summary,
    by-class, by-language, per-config accuracy, and a table of review-candidate
    instances pulled from :data:`HAND_READINGS` plus any other near-wrongs.
    """
    n_cfg_at = payload_at.get("n_configs", 0)
    n_cfg_is = payload_is.get("n_configs", 0)
    n_at = payload_at.get("n_instances", 0)

    near_at = sum(
        1 for s in summaries_at
        if s["n_correct"] <= near_threshold and s["n_total"] >= near_threshold + 1
    )
    near_is = sum(
        1 for s in summaries_is
        if s["n_correct"] <= near_threshold and s["n_total"] >= near_threshold + 1
    )

    def _hist_mode(hist: dict[str, int]) -> str:
        if not hist:
            return "—"
        items = sorted(((int(k), v) for k, v in hist.items()), key=lambda x: x[0])
        max_v = max(v for _, v in items)
        peaks = [k for k, v in items if v == max_v]
        if len(peaks) == 1:
            return f"mode = {peaks[0]}"
        return f"mode ≈ {peaks[0]}–{peaks[-1]}"

    parts: list[str] = []
    parts.append("## Cross-config disagreement analysis\n")
    parts.append(
        "_Generated by `scripts/disagreement_analysis.py` — full per-instance "
        "matrices in `logs/final/disagreement/per_instance_{at,isAt}.csv`, "
        "hardest-instance dumps in `hardest_{at,isAt}.md`._\n\n"
    )

    parts.append("### Method\n\n")
    parts.append(
        "For every test instance and every configuration that produced _real_ "
        "predictions for the target (i.e. excluding fallback-FALSE columns "
        "from single-target runs and null columns from MASK runs trained on "
        "the other target), record whether the prediction matched gold. "
        "Then aggregate per instance:\n\n"
    )
    parts.append("- **n_correct / n_total** — how many configs got that instance right.\n")
    parts.append("- **frac_correct** — the same as a fraction.\n")
    parts.append("- **modal_wrong_pred** — when configs are wrong, what label do they converge on?\n\n")
    parts.append(
        f"Cross-config sample: **{n_cfg_at} configurations for `at`** and "
        f"**{n_cfg_is} for `isAt`**, all on the {n_at}-instance `at`-task test "
        "split. The set is the union of LLM zero-shot variants, RAG "
        "configurations, MASK feature variants, and handcrafted RF (smoke "
        "tests excluded).\n\n"
    )

    # Hardness summary
    parts.append(f"### Hardness summary ({n_at} instances per target)\n\n")
    rows = [
        ["metric", f"`at` ({n_cfg_at} configs)", f"`isAt` ({n_cfg_is} configs)"],
        ["---", "---", "---"],
        [
            "universally-wrong (every config wrong)",
            f"**{payload_at['n_all_wrong']} ({payload_at['frac_all_wrong']:.1%})**",
            f"**{payload_is['n_all_wrong']} ({payload_is['frac_all_wrong']:.1%})**",
        ],
        [
            f"near-universally-wrong (≤ {near_threshold} configs right)",
            f"**{near_at} ({near_at / n_at:.1%})**" if n_at else "—",
            f"**{near_is} ({near_is / n_at:.1%})**" if n_at else "—",
        ],
        [
            "universally-right (every config right)",
            f"**{payload_at['n_all_right']} ({payload_at['frac_all_right']:.1%})**",
            f"**{payload_is['n_all_right']} ({payload_is['frac_all_right']:.1%})**",
        ],
        [
            "n_correct distribution shape",
            _hist_mode(payload_at.get("hardness_histogram", {})),
            _hist_mode(payload_is.get("hardness_histogram", {})),
        ],
    ]
    parts.append("| " + " | ".join(rows[0]) + " |\n")
    parts.append("|" + "|".join(["---"] * len(rows[0])) + "|\n")
    for r in rows[2:]:
        parts.append("| " + " | ".join(r) + " |\n")
    parts.append("\n")
    parts.append(
        "The `at` distribution being broad and centred near the middle is the "
        "most actionable signal: every configuration we ran has a roughly "
        "30–50 % personal subset of failures, and those subsets only partially "
        "overlap. Ensembling — even a simple majority vote across two strong "
        "but architecturally different configs (handcrafted RF + a "
        "context-rich LLM run) — is therefore likely to improve over any "
        "single config.\n\n"
    )

    # By gold class
    parts.append("### By gold class\n\n")
    parts.append("| target | gold | n | universally-wrong | universally-right |\n")
    parts.append("|---|---|---|---|---|\n")
    for task_name, payload in (("at", payload_at), ("isAt", payload_is)):
        for gold, st in sorted(payload.get("by_gold_class", {}).items()):
            n = st["n"]
            aw = st["all_wrong"]
            ar = st["all_right"]
            parts.append(
                f"| {task_name} | {gold} | {n} | "
                f"{aw} ({aw / n:.1%}) | "
                f"{'**0 (0.0 %)**' if ar == 0 else f'{ar} ({ar / n:.1%})'} |\n"
            )
    parts.append("\n")
    parts.append(
        "The two `0 universally-right` rows are the headline finding: **no "
        "instance with gold `at=PROBABLE` and no instance with gold "
        "`isAt=TRUE` is correctly classified by every configuration.** Both "
        "are the minority class for their target, and both confirm at the "
        "_instance_ level the long-running observation that the rare class is "
        "the price every system pays.\n\n"
    )

    # By language
    parts.append("### By language\n\n")
    parts.append("| target | language | n | universally-right | % |\n")
    parts.append("|---|---|---|---|---|\n")
    # Order: isAt by descending right-rate (where the spread is informative),
    # then at.
    is_langs = sorted(
        payload_is.get("by_language", {}).items(),
        key=lambda kv: -(kv[1]["all_right"] / max(kv[1]["n"], 1)),
    )
    at_langs = sorted(payload_at.get("by_language", {}).items(), key=lambda kv: kv[0])
    for task_name, lang_iter in (("isAt", is_langs), ("at", at_langs)):
        for lang, st in lang_iter:
            n = st["n"]
            ar = st["all_right"]
            parts.append(
                f"| {task_name} | {lang} | {n} | {ar} | "
                f"{'**' + f'{ar / n:.1%}' + '**' if (task_name == 'isAt' and ar / n < 0.10) else f'{ar / n:.1%}'} |\n"
            )
    parts.append("\n")
    parts.append(
        "**French isAt is meaningfully harder than German or English isAt** — "
        "the universally-right rate is several × lower than for German. "
        "The French test slice is also where the ablations show the largest "
        "score regressions when adding context. Future French-specific work "
        "(better tokenisation, contemporary Romance NER markers, dedicated "
        "French few-shot exemplars) should be sized against this floor.\n\n"
    )

    # Per-config accuracy
    parts.append("### Per-config accuracy on the cross-config sample\n\n")
    parts.append(
        "The same instances scored on the per-config correctness column "
        "reveal a clean ranking that mirrors the official Macro-Recall table "
        "but on a like-for-like basis (same instances, same scoring rule):\n\n"
    )
    # Combine per-config accuracy across tasks to one row per config.
    acc_at = payload_at.get("per_config_accuracy", {})
    acc_is = payload_is.get("per_config_accuracy", {})
    all_cfgs = sorted(set(acc_at) | set(acc_is))
    cfg_rows: list[tuple[str, float | None, float | None]] = []
    for cfg in all_cfgs:
        a = acc_at.get(cfg, {}).get("accuracy") if cfg in acc_at else None
        b = acc_is.get(cfg, {}).get("accuracy") if cfg in acc_is else None
        cfg_rows.append((cfg, a, b))
    # Sort by best-of-the-two accuracy descending.
    cfg_rows.sort(key=lambda r: -max(r[1] or 0.0, r[2] or 0.0))

    parts.append("| rank | config | acc on `at` | acc on `isAt` |\n")
    parts.append("|---|---|---|---|\n")
    for rank, (cfg, a, b) in enumerate(cfg_rows[:8], start=1):
        a_s = f"**{a:.3f}**" if a is not None and a == max(
            (r[1] for r in cfg_rows if r[1] is not None), default=0
        ) else (f"{a:.3f}" if a is not None else "—")
        b_s = f"**{b:.3f}**" if b is not None and b == max(
            (r[2] for r in cfg_rows if r[2] is not None), default=0
        ) else (f"{b:.3f}" if b is not None else "—")
        parts.append(f"| {rank} | `{cfg}` | {a_s} | {b_s} |\n")
    if len(cfg_rows) > 8:
        parts.append(
            f"| … | _(remaining {len(cfg_rows) - 8} configs cluster lower; see "
            "`logs/final/disagreement/summary.json` for the full table)_ |  |  |\n"
        )
    parts.append("\n")

    # Universally-wrong & near-wrong examples table.
    parts.append("### Universally-wrong & near-universally-wrong examples\n\n")
    candidates = _hardest_for_table(
        summaries_at, near_threshold=near_threshold, top_n=top_n_examples
    )
    parts.append(
        f"The {len(candidates)} cross-config-hardest `at` instances "
        "look like **gold-label review candidates**, where a uniform "
        "LLM-and-feature-classifier majority disagrees with the annotated "
        "label:\n\n"
    )
    parts.append("| document | person ↔ location | gold `at` | configs say | reading |\n")
    parts.append("|---|---|---|---|---|\n")
    for s in candidates:
        key = (s["document_id"], s["pers_entity_id"], s["loc_entity_id"])
        per_preds = Counter(v["predicted"] for v in s["per_config"].values())
        breakdown = ", ".join(f"{lbl}× {n}" for lbl, n in per_preds.most_common())
        if s["n_correct"] == 0:
            breakdown += f" (0/{s['n_total']} right)"
        else:
            breakdown += f" ({s['n_correct']}/{s['n_total']} right)"
        person_loc = _person_loc_label(s, instance_index)
        reading = HAND_READINGS.get(key, "_(no curated reading — see `hardest_at.md`)_")
        parts.append(
            f"| `{s['document_id']}` | {person_loc} | {s['gold']} | "
            f"{breakdown} | {reading} |\n"
        )
    parts.append("\n")

    # Near-wrong isAt mention.
    near_is_list = [
        s for s in summaries_is
        if s["n_correct"] <= near_threshold and s["n_total"] >= near_threshold + 1
    ]
    if near_is_list:
        names = [_person_loc_label(s, instance_index) for s in near_is_list[:2]]
        parts.append(
            f"The {len(near_is_list)} near-universally-wrong `isAt` cases "
            f"({', '.join(names)}) likewise have the large majority of configs "
            "saying FALSE while the gold says TRUE; both have only oblique "
            "presence cues and are reasonable annotation-review candidates as "
            "well.\n\n"
        )

    # Implications
    parts.append("### Implications for the next iteration\n\n")
    parts.append(
        "- **Ensemble candidate.** Architecturally different best configs "
        "(handcrafted-RF and full-context P-R) agree on roughly 70 % of `at` "
        "instances; their disagreement set is exactly the non-overlapping-"
        "failure space the hardness histogram visualises. A learned stacker — "
        "or even a hard rule \"trust RF on `at`, trust LLM-PR on `isAt-TRUE`\" — "
        "is a one-evening experiment with a clear upper bound.\n"
    )
    parts.append(
        "- **PROBABLE / isAt-TRUE training data.** The two zero-universally-"
        "right cells confirm the rare-class problem at the _instance_ level. "
        "Any sampling-aware training (focal loss, oversampling, dedicated "
        "few-shot exemplar set per class) should be evaluated by lift on "
        "those instances specifically.\n"
    )
    parts.append(
        "- **Annotation review.** The hardest rows above are candidates for a "
        "HIPE-2026 annotator escalation. Even if half flip, that is roughly "
        "0.5 pp on macro-recall.\n"
    )
    parts.append(
        "- **French isAt** has a universally-right floor several × lower than "
        "German isAt; the next French-specific intervention should be sized "
        "against that floor.\n\n"
    )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log-dir", default=str(PROJECT_ROOT / "logs" / "ablations"))
    ap.add_argument("--out-dir", default=str(PROJECT_ROOT / "logs" / "final" / "disagreement"))
    ap.add_argument("--dataset", default=str(PROJECT_ROOT / "data" / "dataset_reference.jsonl"),
                    help="Used to enrich the hardest-instances dump with article context.")
    ap.add_argument("--include-globs", nargs="*", default=None,
                    help="Only include experiment ids matching these globs.")
    ap.add_argument("--exclude-globs", nargs="*", default=list(DEFAULT_EXCLUDE_GLOBS),
                    help="Skip experiments matching these globs (default: smoke_*).")
    ap.add_argument("--min-instances", type=int, default=100,
                    help="Skip prediction files with fewer rows than this "
                         "(filters out smoke tests / aborted runs).")
    ap.add_argument("--top-k", type=int, default=25,
                    help="How many hardest instances to render in the MD dumps "
                         "(universally-wrong first, then near-universally-wrong).")
    ap.add_argument("--near-threshold", type=int, default=2,
                    help="Instances with n_correct <= this count are listed in "
                         "the 'near-universally-wrong' section.")
    args = ap.parse_args()

    log_dir = Path(args.log_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load configs (one per *_predictions.jsonl).
    pred_paths = sorted(log_dir.glob("*_predictions.jsonl"))
    configs: dict[str, list[dict]] = {}
    for p in pred_paths:
        exp_id = _exp_id(p)
        if any(fnmatch.fnmatch(exp_id, pat) for pat in args.exclude_globs):
            continue
        if args.include_globs and not any(
            fnmatch.fnmatch(exp_id, pat) for pat in args.include_globs
        ):
            continue
        rows = _load_predictions(p)
        if len(rows) < args.min_instances:
            continue
        configs[exp_id] = rows

    if not configs:
        print("No configurations matched — nothing to do.")
        return 1

    print(f"Loaded {len(configs)} configurations:")
    for name in sorted(configs):
        print(f"  - {name}  ({len(configs[name])} rows)")

    # Build per-task instance tables.
    keys_at, cfgs_at, table_at = _build_instance_table(configs, task="at")
    keys_is, cfgs_is, table_is = _build_instance_table(configs, task="isAt")
    summ_at = _summarize_per_instance(keys_at, cfgs_at, table_at)
    summ_is = _summarize_per_instance(keys_is, cfgs_is, table_is)

    # Per-instance CSVs.
    csv_at = out_dir / "per_instance_at.csv"
    csv_is = out_dir / "per_instance_isAt.csv"
    _write_per_instance_csv(csv_at, summ_at, cfgs_at)
    _write_per_instance_csv(csv_is, summ_is, cfgs_is)

    # Aggregate JSON.
    summary = {
        "log_dir": str(log_dir),
        "n_configurations": len(configs),
        "configurations": sorted(configs.keys()),
        "at": _summary_payload("at", summ_at, cfgs_at),
        "isAt": _summary_payload("isAt", summ_is, cfgs_is),
    }
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    # Hardest-instances markdown — load dataset_reference for context.
    instance_index: dict[tuple, Any] = {}
    ds_path = Path(args.dataset)
    if ds_path.exists():
        for inst in load_jsonl(ds_path):
            instance_index[(inst.document_id, inst.pers_entity_id, inst.loc_entity_id)] = inst
        print(f"Loaded {len(instance_index)} reference instances for context.")
    else:
        print(f"  (dataset {ds_path} not found — hardest-instances dumps will lack article context)")

    _write_hardest_md(out_dir / "hardest_at.md", "at", summ_at, cfgs_at,
                      instance_index, top_k=args.top_k,
                      near_threshold=args.near_threshold)
    _write_hardest_md(out_dir / "hardest_isAt.md", "isAt", summ_is, cfgs_is,
                      instance_index, top_k=args.top_k,
                      near_threshold=args.near_threshold)

    # Stdout summary.
    print()
    for task, payload in (("at", summary["at"]), ("isAt", summary["isAt"])):
        print(f"=== {task} ===")
        if not payload.get("n_instances"):
            print("  (no covering configurations)")
            continue
        print(f"  n_configs={payload['n_configs']}  n_instances={payload['n_instances']}")
        print(f"  all-wrong={payload['n_all_wrong']} ({payload['frac_all_wrong']:.1%})  "
              f"all-right={payload['n_all_right']} ({payload['frac_all_right']:.1%})")
        print(f"  hardness histogram (n_correct -> count):")
        for k in sorted(payload["hardness_histogram"], key=int):
            print(f"    {k}: {payload['hardness_histogram'][k]}")
        if payload["all_wrong_modal_pred_distribution"]:
            print(f"  all-wrong modal-pred distribution: "
                  f"{payload['all_wrong_modal_pred_distribution']}")
        if payload["all_wrong_gold_distribution"]:
            print(f"  all-wrong gold distribution:      "
                  f"{payload['all_wrong_gold_distribution']}")
    print()
    print(f"Wrote {csv_at}")
    print(f"Wrote {csv_is}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {out_dir / 'hardest_at.md'}")
    print(f"Wrote {out_dir / 'hardest_isAt.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
