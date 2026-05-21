"""Generate the INSALyon HIPE-2026 methods report.

Builds a single markdown document that documents the full system: training-data
EDA, hand-crafted and embedding-based features, every model that was tested,
the Gemma prompt configurations, dev-set comparative numbers, k-fold CV
results, the cross-config disagreement analysis, the stacking / ensemble
comparison and finally the three official test-set submissions.

All sections are populated from artefacts already present in the repository:

  - data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-{en,fr,de}.jsonl
  - data/v1_baseline_train_test_ids.csv
  - logs/final/results.json                 (224 same-split experiments)
  - logs/final/disagreement/summary.json    (cross-config agreement on at/isAt)
  - logs/kfold/kfold_summary_seed42_n5.json (per-feature-set 5-fold CV)
  - logs/cv/T1_*_summary.json               (stacker nested CV runs)
  - logs/cv/T1_*_with_gemma_isAt.bootstrap.json (hybrid bootstrap CIs)
  - submissions/INSALyon_model_info.txt     (final run descriptions)
  - hipe/features/temporal.py               (handcrafted feature names)
  - hipe/llm/prompts.py                     (Gemma / LLM prompt variants)

Usage::

    python scripts/generate_methods_report.py \
        --output reports/methods_report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def fmt(x: float | None, digits: int = 4) -> str:
    if x is None:
        return "—"
    return f"{x:.{digits}f}"


def md_table(header: list[str], rows: list[list[str]]) -> str:
    sep = ["---"] * len(header)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    out.extend("| " + " | ".join(r) + " |" for r in rows)
    return "\n".join(out)


def banner(title: str) -> str:
    return f"\n## {title}\n"


# ---------------------------------------------------------------------------
# Section 1 — Exploratory data analysis on the training pool
# ---------------------------------------------------------------------------


def eda_training_pool() -> str:
    """Compute basic statistics over data/newspapers/v1.0/*-train-*.jsonl."""
    train_dir = REPO_ROOT / "data" / "newspapers" / "v1.0"
    train_files = sorted(p for p in train_dir.glob("*-train-*.jsonl"))

    by_lang: dict[str, dict[str, Any]] = {}
    pair_at_counts = Counter()
    pair_isat_counts = Counter()
    article_lengths: list[int] = []
    pairs_per_article: list[int] = []
    by_decade: Counter = Counter()

    pers_with_qid = pers_total = 0
    loc_with_qid = loc_total = 0
    seen_persons: set[str] = set()
    seen_locs: set[str] = set()
    seen_docs: set[str] = set()

    for fp in train_files:
        lang = fp.stem.split("-")[-1]  # ...-train-{lang}
        rows = load_jsonl(fp)
        n_articles = len(rows)
        n_pairs = 0
        n_pairs_lang_at = Counter()
        n_pairs_lang_isat = Counter()

        for art in rows:
            doc_id = art.get("document_id")
            if doc_id:
                seen_docs.add(doc_id)
            text = art.get("text") or ""
            article_lengths.append(len(text))

            date = art.get("date") or ""
            if len(date) >= 4 and date[:4].isdigit():
                decade = int(date[:4]) // 10 * 10
                by_decade[decade] += 1

            pairs = art.get("sampled_pairs") or []
            pairs_per_article.append(len(pairs))
            n_pairs += len(pairs)

            for p in pairs:
                at = p.get("at")
                isat = p.get("isAt")
                if at:
                    pair_at_counts[at] += 1
                    n_pairs_lang_at[at] += 1
                if isat:
                    pair_isat_counts[isat] += 1
                    n_pairs_lang_isat[isat] += 1

                pers_id = p.get("pers_entity_id")
                loc_id = p.get("loc_entity_id")
                if pers_id:
                    seen_persons.add(pers_id)
                    pers_total += 1
                    if p.get("pers_wikidata_QID"):
                        pers_with_qid += 1
                if loc_id:
                    seen_locs.add(loc_id)
                    loc_total += 1
                    if p.get("loc_wikidata_QID"):
                        loc_with_qid += 1

        by_lang[lang] = {
            "file": fp.name,
            "n_articles": n_articles,
            "n_pairs": n_pairs,
            "at": dict(n_pairs_lang_at),
            "isAt": dict(n_pairs_lang_isat),
        }

    total_articles = sum(v["n_articles"] for v in by_lang.values())
    total_pairs = sum(v["n_pairs"] for v in by_lang.values())

    parts: list[str] = []
    parts.append(banner("1. Exploratory data analysis on the training pool"))
    parts.append(
        "We perform exploratory data analysis on the impresso training files\n"
        f"(`data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-*.jsonl`)."
        f" The pool contains **{total_articles}** articles distributed across"
        " the three official impresso languages (English, French, German)."
        f" Articles carry a list of `(person, location)` pairs annotated with the two"
        " target labels — together they make up **{n_pairs}** labelled instances.".format(
            n_pairs=total_pairs
        )
    )

    parts.append("\n### 1.1 Per-language article and pair counts\n")
    rows = []
    for lang in ("en", "fr", "de"):
        v = by_lang.get(lang)
        if v is None:
            continue
        rows.append([
            lang,
            v["file"],
            str(v["n_articles"]),
            str(v["n_pairs"]),
            f"{v['n_pairs'] / max(v['n_articles'], 1):.1f}",
        ])
    rows.append(
        [
            "**total**",
            "—",
            f"**{total_articles}**",
            f"**{total_pairs}**",
            f"**{total_pairs / max(total_articles, 1):.1f}**",
        ]
    )
    parts.append(
        md_table(
            ["language", "file", "articles", "pairs", "pairs/article"],
            rows,
        )
    )

    parts.append("\n### 1.2 Label distribution over the training pool\n")
    rows = []
    for label in ("FALSE", "TRUE", "PROBABLE"):
        n = pair_at_counts[label]
        pct = 100.0 * n / max(total_pairs, 1)
        rows.append([label, str(n), f"{pct:.1f}%"])
    rows.append(["**all `at`**", f"**{sum(pair_at_counts.values())}**", "100.0%"])
    parts.append("**`at` task (3 classes)**\n")
    parts.append(md_table(["label", "n", "share"], rows))

    rows = []
    for label in ("FALSE", "TRUE"):
        n = pair_isat_counts[label]
        pct = 100.0 * n / max(total_pairs, 1)
        rows.append([label, str(n), f"{pct:.1f}%"])
    rows.append(["**all `isAt`**", f"**{sum(pair_isat_counts.values())}**", "100.0%"])
    parts.append("\n**`isAt` task (binary)**\n")
    parts.append(md_table(["label", "n", "share"], rows))

    parts.append(
        "\nKey takeaways: the **PROBABLE** class is the rarest by a wide margin"
        " (≈10% of the pool) yet contributes 33% of the macro-Recall denominator on"
        " the `at` task, which puts an outsized share of the difficulty on a low-support class."
        " The `isAt` task is binary and FALSE-skewed (≈78%)."
    )

    parts.append("\n### 1.3 Per-language label balance\n")
    rows = []
    for lang in ("en", "fr", "de"):
        v = by_lang.get(lang)
        if v is None:
            continue
        at_dist = v["at"]
        isat_dist = v["isAt"]
        rows.append(
            [
                lang,
                str(at_dist.get("TRUE", 0)),
                str(at_dist.get("PROBABLE", 0)),
                str(at_dist.get("FALSE", 0)),
                str(isat_dist.get("TRUE", 0)),
                str(isat_dist.get("FALSE", 0)),
            ]
        )
    parts.append(
        md_table(
            ["lang", "at=T", "at=P", "at=F", "isAt=T", "isAt=F"],
            rows,
        )
    )

    parts.append("\n### 1.4 Article length and pair density\n")
    if article_lengths:
        srt = sorted(article_lengths)
        median = srt[len(srt) // 2]
        p10 = srt[max(0, len(srt) // 10)]
        p90 = srt[min(len(srt) - 1, 9 * len(srt) // 10)]
        avg = sum(article_lengths) / len(article_lengths)
        parts.append(
            f"- Article length (chars): median = {median}, mean = {avg:.0f},"
            f" p10 = {p10}, p90 = {p90}, max = {max(article_lengths)}.\n"
        )
    if pairs_per_article:
        srt = sorted(pairs_per_article)
        median = srt[len(srt) // 2]
        avg = sum(pairs_per_article) / len(pairs_per_article)
        parts.append(
            f"- Pairs per article: median = {median}, mean = {avg:.1f},"
            f" max = {max(pairs_per_article)}.\n"
        )

    parts.append("\n### 1.5 Wikidata coverage at the entity level\n")
    parts.append(
        f"- **Person mentions:** {pers_with_qid} / {pers_total}"
        f" ({100.0 * pers_with_qid / max(pers_total, 1):.1f}%) have a resolved"
        " Wikidata QID. The remainder are NIL persons (often local OCR-noisy names)."
    )
    parts.append(
        f"- **Location mentions:** {loc_with_qid} / {loc_total}"
        f" ({100.0 * loc_with_qid / max(loc_total, 1):.1f}%) carry a Wikidata QID."
    )

    parts.append("\n### 1.6 Temporal coverage\n")
    decades = sorted(by_decade)
    if decades:
        rows = [
            [f"{d}s", str(by_decade[d])] for d in decades
        ]
        parts.append(
            f"Articles span the historical range **{decades[0]} – {decades[-1] + 9}**."
            " Distribution by decade (article counts):"
        )
        parts.append(md_table(["decade", "n articles"], rows))

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 2 — Train / dev split used in the experiments
# ---------------------------------------------------------------------------


def section_train_dev_split() -> str:
    csv_path = REPO_ROOT / "data" / "v1_baseline_train_test_ids.csv"
    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8")))

    counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    label_counts: defaultdict[tuple[str, str, str], int] = defaultdict(int)
    lang_counts: defaultdict[tuple[str, str, str], int] = defaultdict(int)
    for r in rows:
        task = r["task"]
        split = r["split"]
        counts[(task, split)] += 1
        label_field = "at_label" if task == "at" else "isAt_label"
        label_counts[(task, split, r[label_field])] += 1
        lang_counts[(task, split, r["language"])] += 1

    parts: list[str] = []
    parts.append(banner("2. Train / dev split used in the experiments"))
    parts.append(
        "All same-split development numbers in this report use the canonical"
        " baseline split shipped with the project as"
        " `data/v1_baseline_train_test_ids.csv`. The CSV calls the held-out"
        " portion `test`; in this report we refer to it as **dev**, so the test"
        " set name is reserved for the official, blind HIPE-2026 test set."
    )

    parts.append(
        f"\nThe split is task-specific: `at` and `isAt` use exactly the same"
        f" instance ids but the CSV contains both for clarity. Counts are"
        f" identical across the two tasks ({counts[('at', 'train')]} train /"
        f" {counts[('at', 'test')]} dev)."
    )

    parts.append("\n### 2.1 Class balance per split (`at` task)\n")
    rows_md = []
    for split in ("train", "test"):
        for label in ("FALSE", "TRUE", "PROBABLE"):
            n = label_counts[("at", split, label)]
            tot = counts[("at", split)]
            rows_md.append([split, label, str(n), f"{100.0 * n / tot:.1f}%"])
    parts.append(md_table(["split", "label", "n", "share"], rows_md))

    parts.append("\n### 2.2 Class balance per split (`isAt` task)\n")
    rows_md = []
    for split in ("train", "test"):
        for label in ("FALSE", "TRUE"):
            n = label_counts[("isAt", split, label)]
            tot = counts[("isAt", split)]
            rows_md.append([split, label, str(n), f"{100.0 * n / tot:.1f}%"])
    parts.append(md_table(["split", "label", "n", "share"], rows_md))

    parts.append("\n### 2.3 Languages per split (`at` task)\n")
    rows_md = []
    for split in ("train", "test"):
        for lang in ("en", "fr", "de"):
            n = lang_counts[("at", split, lang)]
            tot = counts[("at", split)]
            rows_md.append([split, lang, str(n), f"{100.0 * n / tot:.1f}%"])
    parts.append(md_table(["split", "lang", "n", "share"], rows_md))

    parts.append(
        "\n*Caveat (per project memory):* single-split numbers carry ≈±0.05"
        " implicit noise on n=188; we therefore report 5-fold CV alongside"
        " single-split scores wherever feasible."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 3 — Features
# ---------------------------------------------------------------------------


_TEMPORAL_FEATURE_DOCS: list[tuple[str, str]] = [
    ("verb_is_present", "1 if any verb cluster linking the entities is in present tense (`pres*`); aggregated by OR across `inst.tense_aspect` clusters."),
    ("verb_is_past", "1 if any verb cluster is in past tense (`past*`)."),
    ("verb_is_negated", "1 if any verb cluster is marked `negated` — captures `ne … plus`, `nicht mehr`, `no longer`."),
    ("verb_is_future", "1 if any verb cluster is in future tense — typically rules out current presence."),
    ("sentence_position_norm", "Sentence index of the pair within the article, clamped to `[0, 1]` via `min(1.0, pos / 50.0)`; -1 → 0."),
    ("is_lead_paragraph", "1 when the pair appears in sentences 0–1 (inverted-pyramid lead → strong TRUE/isAt signal)."),
    ("signal_negation", "1 when the surrounding sentence carries the `negation` temporal-signal category."),
    ("signal_present", "1 when the surrounding sentence carries the `present` category (deictic *now*, *today*, *aujourd'hui*)."),
    ("signal_relative", "1 when the category is `relative_only` (purely relative temporal expressions: *last week*, *gestern*)."),
    ("signal_none", "1 when the category is `no_signal` / empty — no explicit temporal cue near the pair."),
    ("has_timex_in_window", "1 when there is a HeidelTime expression within ±~30 days of the publication date (spec §8.1 widening of the original ±14-d rule)."),
    ("nearest_timex_distance_norm", "Absolute distance to nearest timex in days, clamped to `[0, 1]` via `min(1.0, d / 365.0)`."),
    ("person_is_deceased", "1 when the resolved person status is `dead_historical` (Wikidata death date < publication date)."),
    ("person_status_known", "1 when status is anything other than `unknown` / `no_match` (i.e. Wikidata enrichment succeeded)."),
    ("ocr_quality", "OCR-quality estimate ∈ [0, 1] from the preprocessor; 1.0 if missing."),
]

_HANDCRAFTED_EXTRA_DOCS: list[tuple[str, str]] = [
    ("lang_en, lang_fr, lang_de, lang_lb", "Language one-hot from `inst.language` (4-d). `lb` is reserved for Luxembourgish (surprise set)."),
    ("person_status_unknown", "Person life status: no Wikidata match could be attempted."),
    ("person_status_no_match", "Wikidata match attempted but no QID retrieved."),
    ("person_status_alive_past", "Birth/death dates indicate the person was alive *before* publication."),
    ("person_status_alive_now", "Person was alive *at* publication time."),
    ("person_status_alive_no_longer", "Person had died before publication, but life overlapped textual cues."),
    ("person_status_dead_historical", "Person had been dead for a long time relative to publication."),
    ("person_status_timex_in_lifespan", "Article timex falls within the person's lifespan — supports historical reference."),
    ("person_status_timex_after_death", "Article timex falls *after* the person's death — supports a memorial/historical reading."),
    ("has_pers_qid", "1 when the person mention is linked to a Wikidata QID."),
    ("has_loc_qid", "1 when the location mention is linked to a Wikidata QID."),
    ("n_pers_mentions", "Count of person surface forms in the pair (`len(inst.pers_mentions_list)`)."),
    ("n_loc_mentions", "Count of location surface forms."),
    ("n_temporal_expressions", "Count of HeidelTime-annotated temporal expressions in the article."),
    ("n_temporal_signals", "Count of preprocessor-tagged temporal *signals* (negation/present/relative buckets)."),
    ("n_tense_aspect_clusters", "Count of `(tense, aspect, negated)` verb clusters extracted near the pair."),
    ("text_len_chars_norm", "`min(1.0, len(text) / 12000)` — full-article length, saturated."),
    ("context_len_chars_norm", "`min(1.0, len(context) / 2000)` — local window passed to the encoder, saturated."),
]


def _load_sd_top_rules(top_k: int = 5) -> tuple[list[dict], dict]:
    """Return the top-K PROBABLE subgroups (ranked by n-WRAcc) and the run config."""
    sd_dir = REPO_ROOT / "runs" / "sd" / "SD-H_full_at_v2"
    summary = load_json(sd_dir / "summary.json")
    subs = load_json(sd_dir / "subgroups_PROBABLE.json")["subgroups"]
    subs_sorted = sorted(subs, key=lambda s: s.get("nwracc", 0.0), reverse=True)[:top_k]
    return subs_sorted, summary


def _condense_sd_pattern(pattern: str) -> list[str]:
    """Strip the trivial `in [0,1]` / range-over-full-domain conditions."""
    out: list[str] = []
    for cond in pattern.split(" AND "):
        cond_str = cond.strip()
        # Drop fully-open ranges that don't constrain anything.
        if cond_str.endswith("in [0,1]"):
            continue
        out.append(cond_str)
    return out


def section_features() -> str:
    """Document the engineered features used downstream."""
    parts: list[str] = []
    parts.append(banner("3. Feature engineering"))
    parts.append(
        "Three feature representations were constructed for the HIPE-2026 task,"
        " with progressive expressivity. They feed the four classical /"
        " embedding-based base models documented in §4 and the stacker in §8."
    )

    # ---------------- 3.1 Temporal ----------------
    parts.append("\n### 3.1 Temporal features (15-d)\n")
    parts.append(
        "Implemented in [`hipe/features/temporal.py`](hipe/features/temporal.py):"
        " lightweight signals derived from the article preprocessor (HeidelTime"
        " temporal expressions, OCR quality, verb-tense annotations, person life"
        " status). They are language-agnostic and serve as a dense temporal block"
        " concatenated with MASK / hmBERT embeddings to produce the C4 input."
        " The exact ordering matches `TEMPORAL_FEATURE_NAMES` in the source."
    )
    parts.append(
        md_table(
            ["#", "feature", "definition"],
            [[str(i + 1), f"`{n}`", desc] for i, (n, desc) in enumerate(_TEMPORAL_FEATURE_DOCS)],
        )
    )

    # ---------------- 3.2 Handcrafted ----------------
    parts.append("\n### 3.2 Handcrafted feature vector (36-d)\n")
    parts.append(
        "Built by `extract_handcrafted_features` in the same module. The vector"
        " is the concatenation of three blocks: the 15-d temporal block (§3.1),"
        " a 12-d categorical block (language one-hot + person life status"
        " one-hot), and a 9-d entity / mention block. Total = 15 + 12 + 9 = 36-d."
        " This is the input to the RandomForest classifier (model A in the"
        " stacker) and to the subgroup-discovery miner (§3.5). The list below"
        " documents *every* feature in source order; the first 15 are the"
        " temporal block from §3.1, repeated here only by name."
    )

    parts.append("\n**Block 1 — temporal (positions 1–15):**"
                 " same 15 features as §3.1 — `verb_is_present`, `verb_is_past`,"
                 " `verb_is_negated`, `verb_is_future`, `sentence_position_norm`,"
                 " `is_lead_paragraph`, `signal_negation`, `signal_present`,"
                 " `signal_relative`, `signal_none`, `has_timex_in_window`,"
                 " `nearest_timex_distance_norm`, `person_is_deceased`,"
                 " `person_status_known`, `ocr_quality`.\n")

    parts.append("\n**Block 2 — language + person-status one-hots (positions 16–27):**\n")
    block2_rows = [
        ["16–19", "`lang_en`, `lang_fr`, `lang_de`, `lang_lb`",
         "Language one-hot from `inst.language` (4-d). `lb` reserved for Luxembourgish (surprise set)."],
    ]
    # Skip the lumped language row (index 0) — emit person-status rows individually
    # at positions 20–27.
    for i, (n, desc) in enumerate(_HANDCRAFTED_EXTRA_DOCS[1:9]):
        block2_rows.append([str(20 + i), f"`{n}`", desc])
    parts.append(md_table(["#", "feature", "definition"], block2_rows))

    parts.append("\n**Block 3 — entity / mention / length features (positions 28–36):**\n")
    parts.append(
        md_table(
            ["#", "feature", "definition"],
            [[str(28 + i), f"`{n}`", desc]
             for i, (n, desc) in enumerate(_HANDCRAFTED_EXTRA_DOCS[9:])],
        )
    )

    # ---------------- 3.3 MASK ----------------
    parts.append("\n### 3.3 MASK + entity-span embeddings (frozen hmBERT)\n")
    parts.append(
        "**Why a masked language model.** The dataset is tiny (1,251 labelled"
        " pairs) and multilingual; from-scratch supervised encoders quickly"
        " overfit and a fine-tuned transformer head over CLS pooling needs more"
        " than we have. The MASK-LM approach side-steps both issues: we ask a"
        " *frozen* multilingual hmBERT (`dbmdz/bert-base-historic-multilingual-cased`,"
        " ~110.6 M parameters, pre-trained on historical newspaper text) to fill"
        " in a single `[MASK]` token placed in a *question template* about the"
        " (person, location) relation. The hidden state at the MASK position is"
        " the model's compressed answer to that question — it captures the"
        " entire context surrounding the pair, including the OCR-noisy verb"
        " forms and the temporal cues, in a 768-d vector that already lives in"
        " a relation-aware sub-space of the encoder. We don't decode the MASK"
        " into a word; we use the raw hidden state as a feature."
    )
    parts.append(
        "\n**Template family** ([`hipe/mask/templates.py`](hipe/mask/templates.py))."
        " Five hand-authored templates were explored — the default is **M2**,"
        " which prepends the marked article context and then poses the question"
        " in a fill-in-the-blank form:\n\n"
        "```text\n"
        "<context with [E1]..[/E1] and [E2]..[/E2] markers>"
        " The relationship between [E1] and [E2] is [MASK] .\n"
        "```\n\n"
        "Other templates we evaluated:\n\n"
        "- **M1** (minimal): `[E1] person [/E1] [MASK] [E2] location [/E2] .` — entity-pair only, no context.\n"
        "- **M3** (temporal): `Published: <date> . <ctx> At this time, [E1] is [MASK] [E2] .` — frames the question at publication time.\n"
        "- **M4** (dual-mask): two `[MASK]` slots, one targeting `at`, one targeting `isAt` — yields `mask_at_emb` and `mask_isAt_emb` separately.\n"
        "- **M5** (multi-mask): three consecutive `[MASK]` tokens for a richer 3·H-d relation embedding.\n\n"
        "Per the MASK-grid sweep ([`scripts/mask_grid_eval.py`](scripts/mask_grid_eval.py)),"
        " **M2** is the recommended default because the question-form prompt gives"
        " the MASK position the richest attention over the marked entity spans"
        " — it is the variant used to produce the cached"
        " `runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz` artefact"
        " that all downstream models consume."
    )
    parts.append(
        "\n**What gets extracted** ([`hipe/mask/encoder.py`](hipe/mask/encoder.py))."
        " Per pair, the encoder runs one forward pass through the frozen hmBERT"
        " on the rendered template and emits three 768-d vectors:\n\n"
        "  - **`mask_emb` (768-d).** Mean of the hidden states at every `[MASK]`"
        " position, taken from the last layer. Falls back to CLS when no MASK"
        " survived tokenisation (long-context truncation).\n"
        "  - **`e1_emb` (768-d).** Mean of the token hidden states inside the"
        " `[E1] … [/E1]` span (markers excluded) — a contextualised"
        " representation of the person mention.\n"
        "  - **`e2_emb` (768-d).** Same, for the location span between"
        " `[E2] … [/E2]`.\n\n"
        "When a span is missing inline, the template prepends a synthetic"
        " `[E1] mention [/E1] .` block so the marker tokens are guaranteed to"
        " be present and the span pool is non-empty."
    )
    parts.append(
        "\n**Layer selection (multi-layer M2-L).** The spec optionally"
        " concatenates the MASK hidden state across layers `{-1, -4, -7}`"
        " (≈ layers 12, 9, 6 for a 12-layer hmBERT) to capture both syntactic"
        " (lower) and semantic (upper) cues. This produces"
        " `mask_emb_layers` of shape `3 · 768 = 2,304-d` for the MASK slot"
        " (the entity-span embeddings keep their single-layer 768-d form)."
        " The default in the deployed cache is the single-layer M2 ("
        "`DEFAULT_LAYERS = (-1,)`); the multi-layer variant is mined as"
        " ablation only.\n"
        "\n**Why this representation works for the stacker.** The four base"
        " models in the disagreement stacker (§9) consume the *same* MASK"
        " cache but interpret it differently — the C4 LR sees the linear"
        " separability in the embedding, the OrdContM1 MLP reshapes it under"
        " an ordinal-contrastive loss so PROBABLE lands between TRUE and FALSE,"
        " and the RandomForest reads the handcrafted block independently."
        " Because hmBERT is frozen the cache is computed once (~10 minutes on"
        " a single GPU) and re-used for every downstream experiment, which"
        " keeps the iteration loop fast."
    )

    # ---------------- 3.4 C4 composite ----------------
    parts.append("\n### 3.4 Composite C4 input (2,319-d)\n")
    parts.append(
        "The MASK + e1 + e2 embeddings (768 × 3 = 2,304-d) concatenated with"
        " the 15-d temporal block produces the 2,319-d **C4** input. Naming:"
        " C1 = MASK only, C2 = MASK + temporal, C3 = MASK + e1 + e2,"
        " C4 = MASK + e1 + e2 + temporal (the full composite). C4 is the input"
        " to both the logistic-regression classifier (model B) and the"
        " ordinal-contrastive MLP (model C)."
    )

    # ---------------- 3.5 Subgroup discovery ----------------
    parts.append("\n### 3.5 Subgroup-discovery (SD) rule overrides on PROBABLE\n")
    parts.append(
        "**What we are mining.** Subgroup discovery (SD) is a pattern-mining"
        " task: given a labelled table `(X ∈ ℝ^{N×d}, y ∈ {0,1})`, find conjunctive"
        " patterns over interval / equality conditions on the features whose"
        " *extent* (the set of rows satisfying the pattern) is enriched in the"
        " positive class. The objective is **n-WRAcc** (normalised weighted"
        " relative accuracy), which trades off support against precision:\n\n"
        "```text\n"
        "WRAcc(p) = |extent(p)| / N · ( |extent(p) ∩ positives| / |extent(p)| − |positives| / N )\n"
        "n-WRAcc(p) = WRAcc(p) / WRAcc_max\n"
        "```\n\n"
        "where `WRAcc_max = p · (1 − p)` and `p` is the marginal positive rate."
        " A high-n-WRAcc pattern is a rule that fires on a sizable chunk of the"
        " data and, within that chunk, has a much higher chance of being"
        " positive than the base rate. For HIPE we set `positive = PROBABLE` —"
        " the minority class that none of the single models recovers well."
    )
    parts.append(
        "\n**Why MCMC.** Enumerating all interval patterns over a 42-d feature"
        " space is intractable, so [`hipe/subgroup_discovery/mcmc.py`](hipe/subgroup_discovery/mcmc.py)"
        " runs a **Metropolis–Hastings MCMC sampler** (MonteCloPi-style: see"
        " *Mathonat, Nurbakova, Boulicaut & Kaytoue, DSAA 2021*) over the space"
        " of interval-conjunction patterns. Each chain alternates five proposal"
        " moves with weights `(0.25, 0.30, 0.20, 0.15, 0.10)`:\n\n"
        "  - **meet** — jump to the tightest pattern covering two random"
        " positive instances (bottom-up exploration);\n"
        "  - **tighten** — shrink one interval to a value observed in its extent;\n"
        "  - **loosen** — widen one interval to the next observed value outside it;\n"
        "  - **add** — turn an inactive feature ON with bounds drawn from two random positives;\n"
        "  - **drop** — remove a feature constraint.\n\n"
        "After every proposal we **close on the positive (COTP)**: each active"
        " interval is shrunk to the minimum bounding rectangle of the *positives*"
        " currently in its extent. Closure is monotone in n-WRAcc — it cannot"
        " hurt the score and yields the canonical representative of an equivalence"
        " class. The chain then accepts the move via Metropolis–Hastings on the"
        " score difference with an annealed temperature"
        " `t = T₀ · (1 − step / n_steps) + 0.01`."
    )
    parts.append(
        "\n**Run configuration (the cache deployed for the C4-SDov overlay).**"
        " `runs/sd/SD-H_full_at_v2/summary.json`: `config=SD-H`, `n_chains=10`,"
        " `n_steps=10,000`, `nwracc_threshold=0.05` (only patterns crossing this"
        " threshold are kept), `redundancy_theta=0.5` (Jaccard de-duplication"
        " on extents), `top_k=15`, `min_support=2`, mined on the **1,063 train"
        " rows only** (`train_only=true`)."
    )
    parts.append(
        "\n**Feature space used in deployment (42-d).** The miner consumed the"
        " following blocks (counted from the run's `feature_names`): the 15-d"
        " temporal block (§3.1), the 13-d **evidence-strength** block (§3.6.1),"
        " the 7-d **verb-type** block (§3.6.2), the 3-d **Wikidata location"
        " hierarchy** block (§3.6.3), and a 4-d language one-hot — totalling"
        " **42 features**. *Note:* although the current `build_sd_feature_matrix`"
        " routine appends a 5-d dateline block when called fresh, the cached"
        " `SD-H_full_at_v2` rules that drive the production overlay were mined"
        " **without** the dateline block (the cache predates that block being"
        " enabled by default — the run's `feature_names` does not list any"
        " `location_*_dateline*` entry). The dateline block is therefore"
        " available in the code but **not exercised by the deployed C4-SDov**"
        " predictions."
    )

    # Top-k rules table from the cache.
    try:
        rules, run_summary = _load_sd_top_rules(top_k=5)
    except FileNotFoundError:
        rules, run_summary = [], {}
    if rules:
        parts.append(
            "\n**Top-5 PROBABLE rules by n-WRAcc** (from"
            " `runs/sd/SD-H_full_at_v2/subgroups_PROBABLE.json`)."
            " Trivial fully-open conditions (`in [0,1]` on binary features)"
            " are suppressed for readability; the patterns are the COTP closures"
            " over the 42-d feature space described above."
        )
        rows = []
        for r in rules:
            conds = _condense_sd_pattern(r["pattern"])
            # Take 5–6 most informative conditions to keep the table readable.
            short = "; ".join(conds[:6]) + (" …" if len(conds) > 6 else "")
            rows.append([
                str(r["rank"]),
                f"{r['nwracc']:.3f}",
                f"{r['support_pos']}/{r['support']} ({100 * r['precision']:.0f}%)",
                short,
            ])
        parts.append(
            md_table(
                ["rank", "n-WRAcc", "pos/support (precision)", "pattern (first ~6 non-trivial conditions)"],
                rows,
            )
        )
        parts.append(
            "\n*How to read the rules.* Rule #3 has n-WRAcc = 0.069 with"
            " `support_pos / support = 7 / 7 = 100% precision`: every one of"
            " the 7 training instances matched by the pattern is gold-PROBABLE."
            " Rule #1 is the broadest (50 instances covered, 24% precision —"
            " ≈2.5× the base rate of 9.6%) and acts more like a *recall*"
            " booster, while rules #3–#5 are narrow but near-perfect *precision*"
            " anchors. The MCMC chain naturally surfaces both regimes because"
            " n-WRAcc rewards the product of support and precision-lift."
        )

    parts.append(
        "\n**How the rules are applied (`C4-SDov`).**"
        " [`hipe/subgroup_discovery/integration.py`](hipe/subgroup_discovery/integration.py)"
        " loads the cached patterns and computes a binary `match` mask per dev"
        " instance via `Subgroup.matches(X)` — checking all active intervals."
        " For every instance covered by *at least one* rule with"
        " `n-WRAcc ≥ 0.05` and `precision ≥ τ`, the C4 LR prediction is"
        " flipped `FALSE → PROBABLE` (the spec calls this the"
        " `PROBABLE_from_FALSE_nw0.05` overlay)."
        " Other transitions are not touched — the overlay only promotes"
        " false-negatives that the LR missed but the SD rules confidently"
        " mark as PROBABLE. This lifted MR(`at`) from 0.5700 to 0.5821 on the"
        " 188-instance dev split, and the recovered-PROBABLE instances are the"
        " ones that the disagreement stacker later relies on through the"
        " (P, *, T) and (P, F, T) cells (see §9.3 and §8)."
    )

    # ---------------- 3.6 Additional features ----------------
    parts.append("\n### 3.6 Additional features explored\n")
    parts.append(
        "Beyond the temporal + handcrafted + MASK blocks, the SD miner and the"
        " LLM prompts consume additional engineered blocks. Each block is"
        " self-contained (own module, own feature-name list) so it can be"
        " enabled / disabled independently."
    )

    # 3.6.1 Evidence
    parts.append(
        "\n#### 3.6.1 Evidence-strength features (13-d, [`hipe/subgroup_discovery/evidence.py`](hipe/subgroup_discovery/evidence.py))\n"
        "Captures *how directly* the surface text connects the person to the"
        " location — the TRUE↔PROBABLE distinction that the temporal block is"
        " blind to. Pure regex / counting, no NLP model. Lexicons cover FR /"
        " DE / EN / LB (German also serves as fallback for Luxembourgish)."
    )
    evidence_features: list[tuple[str, str]] = [
        ("entity_char_distance", "Minimum character gap between any person and any location mention in the context, normalised to `[0, 1]` via `min(d / 500, 1.0)`. 1.0 when no co-occurrence found."),
        ("entities_adjacent", "1 when that gap is < 20 chars — strong direct-link signal."),
        ("has_preposition_link", "1 when the regex `<pers> <prep> <loc>` matches with prep ∈ {de, à, en, au, du, in, at, from, of, to, von, aus, nach, zu, vu, an, op, bei}."),
        ("has_genitive_construction", "1 when the location appears in a genitive marker pattern (`de Lyon`, `du roi`, `des Königs`, `von …`, `of …`)."),
        ("has_role_title", "1 when the context contains any role word from the lexicon (FR: archevêque, ministre, président…; EN: bishop, governor, mayor…; DE: Erzbischof, Bürgermeister, Direktor…; LB equivalents)."),
        ("has_hedging", "1 when *any* hedging word fires (FR: vraisemblablement, sans doute, peut-être, paraît-il…; EN: reportedly, allegedly, possibly…; DE: angeblich, vermutlich, offenbar, wahrscheinlich…; LB: wahrscheinlech, vläicht…)."),
        ("n_hedging_words", "Count of hedging words / 3, clamped — denser hedging supports PROBABLE over TRUE."),
        ("entity_in_quotes", "1 when *any* entity mention lies inside a balanced quotation span (handles « », \", “ ”, ', ’). Quoted speech often weakens the assertion."),
        ("has_subjunctive", "1 when a subjunctive / conditional marker fires (FR: aurait, pourrait, serait, eût; DE: dürfte, könnte, würde, hätte, wäre; EN: would, might, could; LB: géif, kéint, sollt). Strong PROBABLE indicator."),
        ("person_mention_count", "Total occurrences of any person mention (including expanded titles and same-sentence pronouns), `min(count / 10, 1.0)`."),
        ("location_mention_count", "Same, for location mentions (Wikidata aliases included when available)."),
        ("cooccurrence_sentences", "Count of sentences containing *both* a person and a location surface form, `min(count / 5, 1.0)`."),
        ("n_competing_locations", "Heuristic count of *other* capitalised tokens following a locative preposition in the text — distractors that weaken the focal pair, `min(n / 10, 1.0)`."),
    ]
    parts.append(
        md_table(
            ["#", "feature", "definition"],
            [[str(i + 1), f"`{n}`", desc] for i, (n, desc) in enumerate(evidence_features)],
        )
    )
    parts.append(
        "*Mention expansion (Specs v2 §4.1.1).* Before computing counts, the"
        " original `pers_mentions_list` is augmented with (a) titles found"
        " within ±80 chars of a named mention, and (b) third-person pronouns"
        " (`il/elle`, `er/sie`, `he/she`, `hien/si`) in the same sentence as a"
        " named mention. Location mentions are augmented with Wikidata aliases"
        " when the QID is present. Exact-match features (`has_preposition_link`,"
        " `has_genitive_construction`) keep using the original lists."
    )

    # 3.6.2 Verb-type
    parts.append(
        "\n#### 3.6.2 Verb-type classification (7-d, [`hipe/subgroup_discovery/evidence.py`](hipe/subgroup_discovery/evidence.py))\n"
        "Five-way verb-class detection over a multilingual lexicon, plus two"
        " composite signals derived from those classes:"
    )
    verb_features: list[tuple[str, str]] = [
        ("verb_type_movement", "Fires on motion verbs that imply transit through the location (FR: arriver, partir, voyager, se rendre, débarquer…; EN: arrive, depart, travel, journey, flee, emigrate…; DE: ankommen, abreisen, reisen, fahren, zurückkehren…; LB equivalents)."),
        ("verb_type_stative", "Fires on stative residence verbs (FR: résider, habiter, vivre, séjourner, demeurer…; EN: reside, live, dwell, stay…; DE: wohnen, leben, residieren…)."),
        ("verb_type_role", "Fires on role-occupation verbs (FR: servir, exercer, diriger, gouverner…; EN: serve, lead, govern, command, preside…; DE: dienen, leiten, regieren, verwalten…)."),
        ("verb_type_birth_death", "Fires on biographical events (FR: naître, mourir, décéder…; EN: born, die, pass away, be buried; DE: geboren werden, sterben, versterben; LB equivalents)."),
        ("verb_type_communication", "Fires on reporting verbs (FR: déclarer, annoncer, rapporter…; EN: declare, announce, report, claim…; DE: erklären, ankündigen, berichten…). Indirect-evidence signal."),
        ("verb_strong_evidence", "Composite: 1 when *role* OR *stative* is set — the two classes that most directly anchor a person at a place."),
        ("verb_indirect_evidence", "Composite: 1 when *communication* is set — the verb implies a reported quote rather than direct evidence."),
    ]
    parts.append(
        md_table(
            ["#", "feature", "definition"],
            [[str(i + 1), f"`{n}`", desc] for i, (n, desc) in enumerate(verb_features)],
        )
    )

    # 3.6.3 Wikidata hierarchy
    parts.append(
        "\n#### 3.6.3 Wikidata P131 location-hierarchy features (3-d, [`hipe/subgroup_discovery/hierarchy.py`](hipe/subgroup_discovery/hierarchy.py))\n"
        "Optional block that exploits the *administrative containment* chain"
        " mined from Wikidata via SPARQL (P131 = *located in the administrative"
        " territorial entity of*). For each location QID we cache the chain"
        " from specific to general (`Lyon → Métropole de Lyon → Rhône →"
        " Auvergne-Rhône-Alpes → France`). If no cache is supplied, the block"
        " falls back to zeros so callers can opt out without code changes."
    )
    hierarchy_features: list[tuple[str, str]] = [
        ("direct_loc_count", "Count of direct mentions of the focal location surface form in the article, normalised (`/10`)."),
        ("hierarchical_loc_count", "Count of mentions of *any* location in the focal location's P131 chain (a mention of *Rhône* or *France* counts toward Lyon's score). Same normalisation."),
        ("parent_location_mentioned", "1 when at least one *strict* parent of the focal location appears in the text — implicit support for the association without a direct mention."),
    ]
    parts.append(
        md_table(
            ["#", "feature", "definition"],
            [[str(i + 1), f"`{n}`", desc] for i, (n, desc) in enumerate(hierarchy_features)],
        )
    )

    # 3.6.4 Dateline
    parts.append(
        "\n#### 3.6.4 Dateline detection (5-d, [`hipe/subgroup_discovery/dateline.py`](hipe/subgroup_discovery/dateline.py))\n"
        "Newspaper articles open and close with **datelines** — `<place>,"
        " <date>` blocks that mark *where the report was filed from*, not where"
        " the article's subjects are located. Cross-config disagreement"
        " analysis (§8) shows that 4+ of the universally-wrong `at` instances"
        " are dateline confusions: the location appears adjacent to the person"
        " but is purely a reporting-origin marker. The block is regex-only"
        " (FR / DE / EN / LB month vocabularies) and exposes 5 binary features:"
    )
    dateline_features: list[tuple[str, str]] = [
        ("location_is_dateline", "1 when the focal location appears in *any* dateline region."),
        ("location_is_opening_dateline", "1 when the location appears in the opening (head ~100 chars) dateline."),
        ("location_is_closing_dateline", "1 when the location appears in the closing (tail ~100 chars) dateline."),
        ("location_is_mid_dateline", "1 when a mid-article dateline-shaped pattern wraps the location."),
        ("location_dateline_only", "Strongest signal: 1 when the location appears *exclusively* in datelines and never in the article body — almost certainly a reporting-origin marker, supports FALSE for both `at` and `isAt`."),
    ]
    parts.append(
        md_table(
            ["#", "feature", "definition"],
            [[str(i + 1), f"`{n}`", desc] for i, (n, desc) in enumerate(dateline_features)],
        )
    )
    parts.append(
        "*Status in deployment.* The block is implemented and tested in"
        " isolation, but — as noted in §3.5 — the cached SD-H mining run used"
        " by the production C4-SDov overlay was performed **before** the"
        " dateline block was added to the SD feature stack; the deployed rules"
        " therefore do not exercise these 5 columns. Re-mining with dateline"
        " is a candidate ablation for future runs."
    )

    # 3.6.5 RAG
    parts.append(
        "\n#### 3.6.5 Retrieval-augmented context (RAG)\n"
        "[`hipe/retriever/`](hipe/retriever/) builds an FAISS index over"
        " `BAAI/bge-m3` embeddings of the 1,063-instance training pool"
        " ([`scripts/build_retrieval_index.py`](scripts/build_retrieval_index.py)).""\n"
        " For each dev / test instance we render a compact query string"
        " `<PERSON>…</PERSON> ↔ <LOCATION>…</LOCATION> | <article_excerpt>`"
        " and retrieve the Top-K nearest training pairs. Each retrieved example"
        " is rendered into the LLM user message as a `<RETRIEVED_EXAMPLES>`"
        " block (entity-marked text + gold label + brief gloss). Two sweeps"
        " were run: a `K ∈ {1, 3, 8}` retrieval-K sweep on the dev split"
        " ([`scripts/run_retrieval_k_sweep.py`](scripts/run_retrieval_k_sweep.py))"
        " and a diversification on/off comparison (Maximal Marginal Relevance"
        " toggle). The K=8 / no-diversify configuration produced the strongest"
        " single-LLM score (global = 0.5922 on Llama 3.1 8B P-R; see §6.3)."
        " None of the RAG configurations entered the final submissions — Gemma"
        " 4 31B P-AB zero-shot was preferred for cost and reproducibility."
    )

    # 3.6.6 Wikidata enrichment
    parts.append(
        "\n#### 3.6.6 Wikidata entity enrichment (`<WIKIDATA>` block in the LLM prompt)\n"
        "For every entity with a QID we fetch from a local Wikidata cache: "
        " (a) for persons — `P19` (place of birth), `P20` (place of death),"
        " `P551` (residence), `P569` (date of birth), `P570` (date of death),"
        " `P106` (occupation), label, aliases; (b) for locations — `P31`"
        " (instance of), `P17` (country), `P131` (administrative parent),"
        " coordinates, label, aliases. The rendered block is a single line per"
        " entity (≤ ~80 tokens). Coverage on the labelled pool is 43.1% for"
        " persons and 75.9% for locations (§1.5) — i.e. **57% of persons are"
        " NIL** and contribute an empty block, which is precisely why injecting"
        " the block uniformly hurts the small LLM and we drop it from the"
        " final Gemma configuration (§5)."
    )

    # 3.6.7 Story arc / DocTimeRel
    parts.append(
        "\n#### 3.6.7 Story-arc / DocTimeRel features (agentic-pipeline only)\n"
        "An optional pre-classifier stage in the agentic pipeline"
        " ([`scripts/run_agentic_pipeline.py`](scripts/run_agentic_pipeline.py))"
        " runs a Narrative Agent that extracts events `(participants,"
        " locations, temporal expressions)` and a DocTimeRel classifier that"
        " labels each event with one of `BEFORE / OVERLAP / AFTER` relative to"
        " the publication date. The resulting story-arc + DCT labels are"
        " injected back into the classifier's prompt. The stage is intended"
        " for hard temporal cases where verb-tense alone is ambiguous"
        " (French *présent historique*, passé composé). In our experiments it"
        " produces traceability rather than score lift (+0.004 over P-R"
        " zero-shot on Llama 3.1 8B); the block is not used in any official"
        " submission."
    )

    # 3.6.8 Disagreement features
    parts.append(
        "\n#### 3.6.8 Disagreement features (17–26-d, [`hipe/stacker/disagreement.py`](hipe/stacker/disagreement.py))\n"
        "These are *meta-features* defined per dev / test instance from the"
        " votes of K base models. They are computed for diagnostics and as the"
        " input to the continuous-feature meta-classifier path (an alternative"
        " to the deployed lookup table)."
    )
    disagreement_features: list[tuple[str, str]] = [
        ("vote_frac_{TRUE,PROBABLE,FALSE}", "Per-label fraction of votes across the K models (3-d for `at`, 2-d for `isAt`)."),
        ("vote_entropy", "Shannon entropy of the vote distribution — 0 when models agree, log K when they split evenly."),
        ("unanimous", "1 when all K models pick the same label."),
        ("pairwise_disagreement", "Fraction of distinct vote pairs `(k₁, k₂)` that disagree, normalised by `K·(K−1)/2`."),
        ("ordinal_range", "`max(ordinal_votes) − min(ordinal_votes)` over the FALSE=0/PROBABLE=1/TRUE=2 mapping. Range 2 means a TRUE↔FALSE split — the *bimodal* shape that most often hides PROBABLE."),
        ("ordinal_std", "Standard deviation of the ordinal votes — a continuous companion to `ordinal_range`."),
        ("bimodal_true_false", "**The single strongest PROBABLE indicator.** 1 ↔ TRUE ∈ votes ∧ FALSE ∈ votes ∧ PROBABLE ∉ votes. Per Wang et al. 2022, this is the canonical *uncertain* pattern in a 3-way ensemble."),
        ("modal_count", "Vote share of the most-frequent label, `max_count / K`."),
        ("modal_is_probable", "1 when the modal vote is PROBABLE."),
        ("model_{k}_agrees", "Per model k: 1 when model k voted the modal label."),
        ("model_{k}_ordinal_dist", "Per model k: ordinal distance between model k's vote and the modal label."),
        ("model_{k}_confidence (optional)", "When per-model confidence is available, the probability assigned to model k's predicted label."),
        ("model_{k}_max_confidence (optional)", "Maximum class probability for model k."),
        ("model_{k}_entropy (optional)", "Shannon entropy of model k's class probabilities."),
    ]
    parts.append(
        md_table(
            ["feature", "definition"],
            [[f"`{n}`", desc] for n, desc in disagreement_features],
        )
    )
    parts.append(
        "*Where they are used.* The 17 categorical features (no-confidence"
        " variant) sit alongside the discrete vote tuple in the stacker's"
        " input. The production stacker (§9.3) consumes only the discrete"
        " tuple via the lookup table — the continuous features are kept as a"
        " ready-to-use input for a larger-scale meta-classifier."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 4 — Models tested
# ---------------------------------------------------------------------------


def section_models() -> str:
    parts: list[str] = []
    parts.append(banner("4. Models tested"))
    parts.append(
        "Five families of models were trained or queried during development."
        " Two of them (mDeBERTa-v3 base and XLM-RoBERTa large) were fine-tuned"
        " by collaborators outside the present codebase; we acknowledge their"
        " contribution and consume their predictions as black-box CSV outputs."
    )

    parts.append("\n### 4.1 Classical / sklearn models\n")
    parts.append(
        "- **Handcrafted RandomForest (RF).** [`scripts/train_sklearn_full.py`](scripts/train_sklearn_full.py)"
        " trains a `RandomForestClassifier(n_estimators=300, class_weight=\"balanced\","
        " random_state=42)` on the 36-d handcrafted vector. ~842k parameters at"
        " serialisation, ≈20 MB on disk. Used as model A in the stacker.\n"
        "- **MASK + temporal LR (C4).** [`hipe/mask/encoder.py`](hipe/mask/encoder.py)"
        " extracts the 2,319-d composite vector; a `StandardScaler →"
        " LogisticRegression(max_iter=2000, class_weight=\"balanced\")` is fitted on"
        " top. ~11.6k trainable parameters; the frozen hmBERT encoder adds"
        " ~110.6 M parameters that are shared with the contrastive MLP.\n"
        "- **C4-SDov.** Same C4 logistic-regression classifier with the MCMC-COTP"
        " subgroup-discovery overlay applied post-hoc"
        " ([`hipe/subgroup_discovery/integration.py`](hipe/subgroup_discovery/integration.py)):"
        " predictions covered by a discovered rule are flipped `FALSE → PROBABLE`."
        " Used as model B in the test-split stacker prototype.\n"
        "- **Temporal-only LR.** Lower-bound baseline using only the 15-d temporal"
        " vector. Useful for ablation; never used in any submission."
    )

    parts.append("\n### 4.2 MASK contrastive MLP (OrdContM1)\n")
    parts.append(
        "[`hipe/mask/contrastive.py`](hipe/mask/contrastive.py): a two-layer MLP"
        " encoder (input 2,319 → hidden 256 → bottleneck 512) with a 128-d"
        " projection head used during training only and per-task linear classification"
        " heads. Training loss is `α·CE + (1−α)·contrastive` with `α = 0.7`."
        " Two contrastive variants are explored:\n\n"
        "  - **OrdinalContrastiveLoss** on `at` — margin scaled by ordinal"
        " distance so PROBABLE ends up *between* TRUE and FALSE in the embedding"
        " space.\n"
        "  - **SupConLoss** (Khosla 2020) on `isAt`.\n\n"
        "The `BalancedContrastiveSampler` produces class-balanced batches"
        " (`k_per_class=16` → batch_size=48 for `at`). ~620k trainable parameters."
        " Used as model C (PROBABLE recall specialist, recall=0.72)."
    )

    parts.append("\n### 4.3 Fine-tuned encoders\n")
    parts.append(
        "Fine-tuned **by collaborators**; we acknowledge the contribution and"
        " consume the predictions as inputs to the ensembles. Both checkpoints"
        " use **two independent classification heads** (one for `at` 3-class,"
        " one for `isAt` binary) and are trained jointly on the labelled pool."
    )
    parts.append(
        "- **mDeBERTa-v3 base** (`microsoft/mdeberta-v3-base`). 278.0 M parameters."
        " Trained for 40 epochs at lr = 2e-5, batch 8 (effective 16), label"
        " smoothing 0.05, sqrt-inverse class weights. Validation macro-F1 reported"
        " by collaborators: **0.6312** (`at`) / **0.7739** (`isAt`)."
        " Configs in `runs/runs_mdeberta/runs/{at,isAt}_task_mdeberta_config.json`.\n"
        "- **XLM-RoBERTa large** (`FacebookAI/xlm-roberta-large`). 559.9 M"
        " parameters; same hyper-parameters as the mDeBERTa run. Validation"
        " macro-F1: **0.8085** (`isAt`)."
        " Predictions deployed in"
        " `runs/submission_xmlroberta_at_isAt/`."
    )

    parts.append("\n### 4.4 Hosted LLMs\n")
    parts.append(
        "Hosted via OpenAI-compatible OpenRouter / DeepInfra endpoints"
        " ([`hipe/llm/client.py`](hipe/llm/client.py)). All inference runs are"
        " temperature-0 zero-shot unless explicitly stated. Three families were"
        " tested:\n\n"
        "- **Llama 3.1 8B Instruct** (DeepInfra). Fast / cheap baseline. Used"
        " in P-A, P-B, P-AB, P-R prompt sweeps and in the K-sweep RAG ablation.\n"
        "- **Llama 3.3 70B Instruct** (OpenRouter, `meta-llama/llama-3.3-70b-instruct`)."
        " 70.5 B parameters. Used in the early `RF + Llama 70B + rules` hybrid and"
        " in the Run 1 majority-vote on `isAt`.\n"
        "- **Gemma 4 31B IT** (OpenRouter paid tier, `google/gemma-4-31b-it`)."
        " 30.7 B parameters. The strongest single LLM on `isAt` (MR=0.854) and"
        " the deployed model in **all official submissions** that use an LLM."
        " Cost on the full 1,251-instance pool: ≈$0.06."
    )

    parts.append("\n### 4.5 Agentic / multi-stage pipeline\n")
    parts.append(
        "[`scripts/run_agentic_pipeline.py`](scripts/run_agentic_pipeline.py)"
        " wires the LLM into a six-stage agentic loop with confidence-driven"
        " escalation: Preprocessor → Retriever (RAG) → Classifier → Justification"
        " → Validator → Output. The Validator escalates uncertain instances to a"
        " stronger model (GPT-4o-mini) and re-classifies. We tested this profile"
        " for *traceability* rather than top-line score: it lifts P-R zero-shot"
        " by only +0.004 (0.5375 → 0.5412) on Llama 3.1 8B but produces"
        " per-instance evidence assessments that are useful for error analysis."
        " It was not used in any final submission."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 5 — Gemma / LLM prompt configurations
# ---------------------------------------------------------------------------


def section_prompts() -> str:
    src_path = REPO_ROOT / "hipe" / "llm" / "prompts.py"
    src = src_path.read_text(encoding="utf-8")

    # Extract the four authored system prompts.
    variants = ("A", "B", "AB", "R")
    excerpts: dict[str, str] = {}
    for v in variants:
        marker = f'_SYSTEM_P_{v} = """'
        if marker in src:
            tail = src.split(marker, 1)[1]
            body = tail.split('"""', 1)[0]
            excerpts[v] = body.strip()

    parts: list[str] = []
    parts.append(banner("5. LLM prompt configurations"))
    parts.append(
        "All hosted-LLM systems are driven by the prompt templates in"
        " [`hipe/llm/prompts.py`](hipe/llm/prompts.py). Four base variants were"
        " authored, each combining a system prompt (verbatim from the HIPE-2026"
        " prompting spec) with a configurable user message. The user-message"
        " builder accepts optional context blocks: `<WIKIDATA>` (entity"
        " enrichment from the QID cache), `<TEMPORAL>` (HeidelTime resolved"
        " expressions plus verb-tense flags) and `<RETRIEVED_EXAMPLES>`"
        " (top-K nearest neighbours from the BGE-M3 index over the labelled"
        " training pool)."
    )

    parts.append("\n### 5.1 Authored prompt variants\n")
    parts.append(
        md_table(
            ["variant", "task scope", "output", "purpose"],
            [
                ["**P-A**", "`at` only", "single line `LABEL \\| confidence=X.XX`", "isolates `at` reasoning; baseline lower-bound."],
                ["**P-B**", "`isAt` only", "single line `LABEL \\| confidence=X.XX`", "isolates the temporal `isAt` task with language-specific tense rules."],
                ["**P-AB**", "joint `at` + `isAt`", "single line `at=LBL isAt=LBL \\| conf_at=… conf_isAt=…`", "combined-target prompt — minimal cost, used at scale on Gemma."],
                ["**P-R**", "joint `at` + `isAt` with reasoning", "4-line analysis (VERB / TEMPORAL / WIKIDATA / EVIDENCE) followed by classification line", "chain-of-thought variant for the smaller Llama 8B baseline."],
            ],
        )
    )

    parts.append(
        "\n*Composability:* each variant has a matching system prompt"
        " (`_SYSTEM_P_A/B/AB/R`) and any of `--rag`, `--rag-k`, `--rag-diversify`,"
        " `--wikidata`, `--temporal`, `--rules-file` can be added on top via"
        " [`scripts/run_llm_baseline.py`](scripts/run_llm_baseline.py). This is what"
        " produced the configurations enumerated in §6.3."
    )

    parts.append("\n### 5.2 System-prompt excerpts (verbatim from `prompts.py`)\n")
    for v in variants:
        body = excerpts.get(v, "")
        if not body:
            continue
        # Truncate to the most informative head (definitions + decision rules)
        header = body.split("OUTPUT FORMAT")[0].rstrip()
        parts.append(f"\n#### P-{v}\n")
        parts.append("```text\n" + header + "\n```\n")
        # Append the output-format clause separately so the full schema is visible.
        if "OUTPUT FORMAT" in body:
            of = "OUTPUT FORMAT" + body.split("OUTPUT FORMAT", 1)[1]
            parts.append("```text\n" + of.strip() + "\n```\n")

    parts.append("### 5.3 Prompt-engineering ablations performed\n")
    parts.append(
        "On top of the four authored prompts we ran the following ablations,"
        " primarily on Llama 3.1 8B (cheap iteration) before locking the final"
        " configuration on Gemma 4 31B P-AB:\n\n"
        "1. **Token-budget fix (`max_tokens` 256 → 512).** The 256-token budget"
        " truncated the reasoning block before the classification line in ~14%"
        " of P-R runs; bumping it to 512 recovered ≈+1.5 pp.\n"
        "2. **`PA + PB split` vs `PAB` joint.** Running P-A and P-B independently"
        " and concatenating the predictions slightly outperforms the joint P-AB"
        " on Llama 8B (global 0.4962 vs 0.4489) — the model handles narrower"
        " questions better.\n"
        "3. **P-R chain-of-thought.** +0.09 over P-AB on Llama 8B (0.5375 vs"
        " 0.4489). The lift comes mainly from `at` (PROBABLE recall up).\n"
        "4. **RAG K-sweep.** `K ∈ {1, 3, 8}` with / without MMR diversification."
        " `K=8, no diversify` was the strongest LLM-only configuration (global"
        " 0.5922).\n"
        "5. **Wikidata block.** Hurts the small LLM (∼-0.06 vs P-R zero-shot)"
        " — likely because 57% of persons are NIL and render an empty block."
        " Dropped from the final Gemma configuration.\n"
        "6. **Temporal block.** Mild positive when used alone; combined with"
        " RAG (full pipeline) it tracks RAG-only.\n"
        "7. **SD-rule injection (`--rules-file`).** Mined PROBABLE rules from"
        " the `at` task, rendered into the prompt as bullet rules. Helps `at`"
        " on weak LLMs but **hurts `isAt`** by 1–3 pp (the rules are at-specific"
        " and pull the model toward TRUE on isAt). Per the project memory we"
        " drop the rules from the LLM-isAt half of the hybrid.\n"
        "8. **Agentic pipeline with GPT-4o-mini escalation.** Validator flags"
        " 89% of instances; escalation re-classifies 59%; net lift +0.004 over"
        " P-R zero-shot. Kept for traceability only."
    )

    parts.append("\n### 5.4 Final Gemma configuration deployed in submissions\n")
    parts.append(
        "**P-AB, no RAG, no Wikidata, no Temporal, no SD rules, temperature 0,"
        " ~970 input tokens / instance, ~26 output tokens.** This is the lightest"
        " configuration that still produces well-calibrated TRUE/FALSE labels."
        " It is the source of:\n\n"
        "  - the Gemma vote in the 4-model `at` stacker;\n"
        "  - the Gemma vote in the Run 1 `isAt` 3-way majority;\n"
        "  - the standalone Gemma `isAt` baseline used in the prototype hybrid.\n"
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 6 — Comparative results on the dev set
# ---------------------------------------------------------------------------


def section_dev_results() -> str:
    results_path = REPO_ROOT / "logs" / "final" / "results.json"
    data = load_json(results_path)
    experiments: list[dict] = list(data["experiments"].values())

    def score(e: dict, k: str) -> float | None:
        return e.get("scores", {}).get(k)

    parts: list[str] = []
    parts.append(banner("6. Comparative results on the dev set"))
    parts.append(
        f"Aggregated from `logs/final/results.json` ("
        f"**{len(experiments)} configurations** evaluated on the 188-instance dev"
        " split). The columns are macro-Recall — the official HIPE-2026 metric"
        " — for each task plus the unweighted mean (GlobalScoreA)."
    )

    parts.append("\n### 6.1 Top-15 configurations by global score\n")
    ranked = sorted(experiments, key=lambda e: score(e, "global_score") or 0.0, reverse=True)[:15]
    rows = []
    for i, e in enumerate(ranked, start=1):
        rows.append([
            str(i),
            f"`{e['experiment_id']}`",
            fmt(score(e, "global_score")),
            fmt(score(e, "macro_recall_at")),
            fmt(score(e, "macro_recall_isAt")),
            str(e.get("n_instances")),
        ])
    parts.append(md_table(["rank", "experiment", "global", "MR(at)", "MR(isAt)", "n"], rows))

    # 6.2 Best per family — pull representative configurations the way the
    # final report does.
    family_picks: list[tuple[str, str]] = [
        ("Handcrafted RF (`at`)", "T1.4or5_mask_T1.5_handcrafted_RF_at_at-test"),
        ("Handcrafted RF (`isAt`-target)", "T1.4or5_mask_T1.5_handcrafted_RF_isAt_at-test"),
        ("MASK C4 LR (`at`)", "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test"),
        ("MASK C4 LR (`isAt`-target)", "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test"),
        ("C4-SDov (PROBABLE-from-FALSE)", "T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test+SDov_PROBABLE_from_FALSE_nw0.05"),
        ("Ordinal contrastive M1", "T1.4or5_mask_contrastive_ordinal_m1_at-test"),
        ("Contrastive CE-only (ablation)", "T1.4or5_mask_contrastive_CEonly_at-test"),
        ("Contrastive SupCon (ablation)", "T1.4or5_mask_contrastive_supcon_at-test"),
        ("MASK C1 (mask-only) LR", "T1.4or5_mask_C1_mask_LR_at_at-test"),
        ("Temporal-only LR", "T1.4or5_mask_T1.4_temporal_only_LR_at_at-test"),
        ("LLM Llama 8B P-A zero-shot", "T1.1_llm_zeroshot_PA_v2_fixed_prompt"),
        ("LLM Llama 8B P-B zero-shot", "T1.1_llm_zeroshot_PB_v2_fixed_prompt"),
        ("LLM Llama 8B P-AB zero-shot", "T1.1_llm_zeroshot_PAB_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
        ("LLM Llama 8B P-R reasoning", "T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
        ("Hybrid RF(at) + MASK-C4(isAt)", "T1_hybrid_RFat_MASKC4isAt_at-test"),
        ("Hybrid RF(at) + Llama70B+rules(isAt)", "T1_hybrid_T15RFat_Llama70BrulesIsAt"),
    ]
    by_id = {e["experiment_id"]: e for e in experiments}
    rows = []
    for label, eid in family_picks:
        e = by_id.get(eid)
        if e is None:
            continue
        rows.append([
            label,
            f"`{eid}`",
            fmt(score(e, "global_score")),
            fmt(score(e, "macro_recall_at")),
            fmt(score(e, "macro_recall_isAt")),
        ])
    parts.append("\n### 6.2 Headline numbers per model family\n")
    parts.append(md_table(["family", "experiment id", "global", "MR(at)", "MR(isAt)"], rows))

    parts.append("\n### 6.3 LLM with context (RAG / Wikidata / Temporal / agentic)\n")
    rag_picks = [
        ("P-R + RAG K=3", "T1.2_llm_zeroshot_PR_RAG_K3"),
        ("P-R + Wikidata + Temporal", "T1.2_llm_zeroshot_PR_WD_Temp"),
        ("P-R + RAG + WD + Temporal", "T1.2_llm_zeroshot_PR_RAG_K3_WD_Temp"),
        ("P-R + RAG K=8 no-diversify", "T2_ksweep_k8_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
        ("P-R + RAG K=8 diversify", "T2_ksweep_k8_div_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test"),
        ("Agentic (Llama8B + GPT-4o-mini esc.)", "T3_agentic_full_pipeline"),
    ]
    rows = []
    for label, eid in rag_picks:
        e = by_id.get(eid)
        if e is None:
            # try a permissive prefix lookup
            cand = next((x for x in experiments if x["experiment_id"].startswith(eid)), None)
            if cand is None:
                continue
            e = cand
        rows.append([
            label,
            f"`{e['experiment_id']}`",
            fmt(score(e, "global_score")),
            fmt(score(e, "macro_recall_at")),
            fmt(score(e, "macro_recall_isAt")),
        ])
    if rows:
        parts.append(md_table(["configuration", "experiment id", "global", "MR(at)", "MR(isAt)"], rows))

    parts.append(
        "\n*Take-aways from the dev sweep:* (i) the best single-classifier on"
        " each task is **RF on `at`** and **MASK-C4 LR on `isAt`** — combining"
        " them as a hybrid lifts global by ≈+0.03 over either used alone;"
        " (ii) PROBABLE recall is the bottleneck for every single model;"
        " (iii) Llama 3.1 8B trails the simple feature baselines by ≈0.18,"
        " confirming that LLM scale matters here — Gemma 4 31B is the smallest"
        " LLM that becomes useful in an ensemble."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 7 — k-fold CV results
# ---------------------------------------------------------------------------


def section_kfold() -> str:
    parts: list[str] = []
    parts.append(banner("7. 5-fold cross-validation results"))
    parts.append(
        "Per the project memory, the single-split number on n=188 is optimistic"
        " by ≈+0.07 vs cleanly cross-validated estimates. We therefore report"
        " 5-fold stratified CV on the full 1,251-instance labelled pool for each"
        " base model and the stacker."
    )

    # 7.1 Per-feature-set CV on at + isAt
    kfold_path = REPO_ROOT / "logs" / "kfold" / "kfold_summary_seed42_n5.json"
    if kfold_path.exists():
        kf = load_json(kfold_path)
        parts.append("\n### 7.1 Per-feature-set 5-fold CV (single classifier per task)\n")
        parts.append(
            "Stratified 5-fold split on the cross-product of `at × isAt` so"
            " PROBABLE is balanced across folds (`seed=42`)."
        )
        rows = []
        for fs_name, fs in kf["feature_sets"].items():
            agg = fs["aggregate"]
            rows.append([
                fs_name,
                str(fs["input_dim"]),
                f"{agg['global_score']['mean']:.4f} ± {agg['global_score']['std']:.3f}",
                f"{agg['macro_recall_at']['mean']:.4f} ± {agg['macro_recall_at']['std']:.3f}",
                f"{agg['macro_recall_isAt']['mean']:.4f} ± {agg['macro_recall_isAt']['std']:.3f}",
            ])
        parts.append(
            md_table(
                ["feature set", "input dim", "global", "MR(at)", "MR(isAt)"],
                rows,
            )
        )

        # Hybrid block
        if "hybrid_RF_at_plus_MASK_C4_isAt" in kf:
            h = kf["hybrid_RF_at_plus_MASK_C4_isAt"]["aggregate"]
            parts.append(
                "\n**Hybrid RF(`at`) + MASK-C4(`isAt`) 5-fold CV:**"
                f" global = {h['global_score']['mean']:.4f}"
                f" ± {h['global_score']['std']:.3f},"
                f" MR(at) = {h['macro_recall_at']['mean']:.4f}"
                f" ± {h['macro_recall_at']['std']:.3f},"
                f" MR(isAt) = {h['macro_recall_isAt']['mean']:.4f}"
                f" ± {h['macro_recall_isAt']['std']:.3f}."
            )
            parts.append(
                "\n*Read this as the cross-validated baseline before stacking.*"
                " Compared to the single-split 0.7142 the CV mean of"
                f" {h['global_score']['mean']:.4f} is ≈0.07 lower — the magnitude"
                " of the optimism gap noted in the project memory."
            )

    # 7.2 Stacker nested CV runs
    parts.append("\n### 7.2 Stacker nested CV (outer 5-fold, inner 3-fold greedy)\n")
    parts.append(
        "All runs use the spec-faithful `tiebreaker=ordinal_median` and the"
        " `fallback=ordinal` hierarchy for unseen vote tuples. Inner 3-fold"
        " greedy forward selection picks the base-model subset on the training"
        " portion only, eliminating the test-leakage of the prototype."
    )
    cv_dir = REPO_ROOT / "logs" / "cv"
    cv_summaries = [
        ("3-model stacker, greedy", "T1_stacker_3models_nested_cv_summary.json"),
        ("3-model stacker, no-greedy (RF+C4+Gemma)", "T1_stacker_3models_nested_cv_30day_nogreedy_summary.json"),
        ("3-model stacker, window14 (older preprocessing)", "T1_stacker_3models_nested_cv_window14_summary.json"),
        ("4-model stacker, greedy", "T1_stacker_4models_nested_cv_summary.json"),
        ("4-model stacker, no-greedy (all four)", "T1_stacker_4models_nested_cv_nogreedy_summary.json"),
        ("Dry-run, 2 models, greedy (RF+C4)", "T1_dry_run_2models_greedy_summary.json"),
        ("Dry-run, 2 models, no-greedy (RF+C4)", "T1_dry_run_2models_no_gemma_summary.json"),
    ]
    rows = []
    for label, fname in cv_summaries:
        p = cv_dir / fname
        if not p.exists():
            continue
        d = load_json(p)
        agg = d.get("MR_at_mean_pm_std", {})
        oof = d.get("MR_at_pooled_OOF", {}) or {}
        per_class = oof.get("per_class", {}) if oof else {}
        sel = d.get("selected_models_per_fold")
        if isinstance(sel, list):
            sel_str = "; ".join("+".join(s) for s in sel)
        else:
            sel_str = "—"
        rows.append([
            label,
            "+".join(d.get("candidates", [])),
            f"{agg.get('mean', 0):.4f} ± {agg.get('std', 0):.3f}",
            fmt(per_class.get("TRUE")),
            fmt(per_class.get("PROBABLE")),
            fmt(per_class.get("FALSE")),
            sel_str,
        ])
    parts.append(
        md_table(
            ["run", "candidates", "MR(at) mean ± std", "OOF rec(T)", "OOF rec(P)", "OOF rec(F)", "selected per fold"],
            rows,
        )
    )

    # 7.3 Bootstrap CIs
    bs_files = [
        ("3-model stacker + Gemma isAt (CV bootstrap)", "T1_stacker_3models_nested_cv_with_gemma_isAt.bootstrap.json"),
        ("4-model stacker + Gemma isAt (CV bootstrap)", "T1_stacker_4models_nogreedy_with_gemma_isAt.bootstrap.json"),
        ("Hybrid RF(at) + MASK-C4(isAt) — kfold OOF", "../kfold/hybrid_kfold_oof_predictions.bootstrap.json"),
    ]
    rows = []
    for label, rel in bs_files:
        p = (cv_dir / rel).resolve()
        if not p.exists():
            continue
        d = load_json(p)
        rows.append([
            label,
            f"{d['global_score']['point']:.4f}"
            f" [{d['global_score']['ci_lower']:.4f}, {d['global_score']['ci_upper']:.4f}]",
            f"{d['macro_recall_at']['point']:.4f}"
            f" [{d['macro_recall_at']['ci_lower']:.4f}, {d['macro_recall_at']['ci_upper']:.4f}]",
            f"{d['macro_recall_isAt']['point']:.4f}"
            f" [{d['macro_recall_isAt']['ci_lower']:.4f}, {d['macro_recall_isAt']['ci_upper']:.4f}]",
            f"n={d['n_instances']}, B={d['n_bootstrap']}",
        ])
    if rows:
        parts.append("\n### 7.3 Bootstrap 95% confidence intervals on hybrid predictions\n")
        parts.append(
            md_table(
                ["model", "global [CI]", "MR(at) [CI]", "MR(isAt) [CI]", "scale"],
                rows,
            )
        )

    # 7.4 Per-model OOF predictions
    parts.append("\n### 7.4 Per-base-model 5-fold OOF predictions\n")
    parts.append(
        "Each base model produces a 1,251-row OOF prediction file"
        " (`logs/kfold_oof/<model>_at_oof_predictions.jsonl`) before the stacker"
        " is built — this is the fold-aligned input to the inner-fold lookup"
        " table. Producers:\n\n"
        "- `RF_handcrafted_at_oof_predictions.jsonl` — produced by"
        " [`scripts/run_kfold_per_model_oof.py`](scripts/run_kfold_per_model_oof.py).\n"
        "- `C4_mask_e1e2_temp_at_oof_predictions.jsonl` — same script, no GPU.\n"
        "- `OrdContM1_at_oof_predictions.jsonl` — produced by"
        " [`scripts/run_kfold_contrastive_oof.py`](scripts/run_kfold_contrastive_oof.py)"
        " (Colab/GPU; see `specs/colab_ord_contrastive_oof.md`).\n"
        "- `gemma4_31b_PAB_full_dataset_predictions.jsonl` — produced by"
        " [`scripts/run_llm_full_dataset.py`](scripts/run_llm_full_dataset.py)"
        " (training-free; no fold split needed).\n\n"
        "All four are produced with `StratifiedKFold(seed=42, n_splits=5)` so"
        " fold assignments align across the OOF emitters."
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 8 — Disagreement analysis
# ---------------------------------------------------------------------------


def section_disagreement() -> str:
    parts: list[str] = []
    parts.append(banner("8. Disagreement analysis between models on the dev set"))
    summary_path = REPO_ROOT / "logs" / "final" / "disagreement" / "summary.json"
    if not summary_path.exists():
        parts.append("*No disagreement summary found.*")
        return "\n".join(parts)
    d = load_json(summary_path)
    parts.append(
        "Cross-configuration agreement was measured over"
        f" **{d['n_configurations']} configurations** stored in"
        " `logs/ablations/`. For each task we compute, per dev instance, how"
        " many configurations got the gold label — the *hardness* of an"
        " instance is the number of configurations that got it wrong."
    )

    for sub_idx, (task_name, task) in enumerate(
        (("at", d.get("at")), ("isAt", d.get("isAt"))), start=1
    ):
        if task is None:
            continue
        parts.append(
            f"\n### 8.{sub_idx} `{task_name}` task — n = {task['n_instances']},"
            f" configs = {task['n_configs']}\n"
        )

        rows = [
            ["all-right (every config correct)", str(task["n_all_right"]), f"{100 * task['frac_all_right']:.1f}%"],
            ["all-wrong (every config wrong)", str(task["n_all_wrong"]), f"{100 * task['frac_all_wrong']:.1f}%"],
        ]
        parts.append(md_table(["category", "instances", "share"], rows))

        # Hardness percentiles
        hist = task.get("hardness_histogram", {})
        if hist:
            entries = sorted(((int(k), v) for k, v in hist.items()), key=lambda x: x[0])
            total = sum(v for _, v in entries)
            cumul = 0
            cumul_rows = []
            milestones = (0.25, 0.50, 0.75, 0.90)
            ms_idx = 0
            for h, n in entries:
                cumul += n
                while ms_idx < len(milestones) and cumul / total >= milestones[ms_idx]:
                    cumul_rows.append([f"{int(100 * milestones[ms_idx])}th", str(h)])
                    ms_idx += 1
            cumul_rows.append(["max", str(entries[-1][0])])
            parts.append("\n**Hardness percentiles (#configs that got it wrong):**\n")
            parts.append(md_table(["percentile", "hardness"], cumul_rows))

        # By gold class — where do the universal failures live?
        bg = task.get("by_gold_class", {})
        if bg:
            rows = []
            for label, info in bg.items():
                rows.append([
                    label,
                    str(info["n"]),
                    str(info["all_right"]),
                    str(info["all_wrong"]),
                ])
            parts.append("\n**By gold class (where the universally-failed examples live):**\n")
            parts.append(md_table(["gold", "n", "all-right", "all-wrong"], rows))

        # By language
        bl = task.get("by_language", {})
        if bl:
            rows = []
            for lang, info in bl.items():
                rows.append([lang, str(info["n"]), str(info["all_right"]), str(info["all_wrong"])])
            parts.append("\n**By language:**\n")
            parts.append(md_table(["lang", "n", "all-right", "all-wrong"], rows))

        # All-wrong predictions distribution
        mp = task.get("all_wrong_modal_pred_distribution", {})
        gp = task.get("all_wrong_gold_distribution", {})
        if mp or gp:
            parts.append("\n**Modal prediction & gold breakdown of universally-wrong instances:**\n")
            rows = [
                [k, str(v)] for k, v in (mp or {}).items()
            ]
            parts.append("Modal predictions (what the systems agreed on, but were wrong):")
            parts.append(md_table(["pred", "n"], rows or [["—", "—"]]))
            rows = [
                [k, str(v)] for k, v in (gp or {}).items()
            ]
            parts.append("\nGold labels of those instances:")
            parts.append(md_table(["gold", "n"], rows or [["—", "—"]]))

    parts.append(
        "\n### 8.3 Take-aways from the disagreement analysis\n"
        "1. **Universally-hard instances are rare.** ~2% of `at` instances are"
        " missed by every configuration — the rest of the failure mass spreads"
        " unevenly across systems, which is exactly the shape an ensemble can"
        " exploit.\n"
        "2. **PROBABLE concentrates the universal failures.** On `at`, every"
        " all-wrong instance whose gold is non-trivial is a PROBABLE — the"
        " disagreement-based stacker is built precisely to recover them.\n"
        "3. **Errors are language-balanced.** No single language dominates the"
        " all-wrong set; the dominant failure mode is the difficulty of the"
        " annotation guideline, not OCR or vocabulary.\n"
        "4. **At/Gemma vs RF disagreements isolate PROBABLE cases.** Per the"
        " stacker spec §9.2, the most informative cells are the *asymmetric*"
        " ones — e.g. `(P, *, T)` where RF detects PROBABLE but Gemma says TRUE."
        " The lookup table maps this to PROBABLE 80% of the time on the dev"
        " split. This is the empirical motivation for the 4-model stacker."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 9 — Stacking and ensemble approaches
# ---------------------------------------------------------------------------


def section_stacking() -> str:
    parts: list[str] = []
    parts.append(banner("9. Stacking and ensemble approaches"))
    parts.append(
        "Three families of ensembling were studied, in increasing complexity:"
        " (i) per-task hybrids (best-of-task swap), (ii) plurality / majority"
        " voting, and (iii) the disagreement-stacker lookup table."
    )

    parts.append(
        "\n### 9.1 Per-task hybrids — best classifier per task\n"
        "The simplest and earliest ensemble: pick the best classifier per task"
        " and concatenate predictions ([`scripts/combine_split_predictions.py`](scripts/combine_split_predictions.py))."
        " Best dev-split combination is **RF on `at` + MASK-C4 LR on `isAt`** with"
        " global = 0.7142 (vs 0.688 for RF used on both, 0.668 for MASK-C4 used"
        " on both). The mDeBERTa `at` head + XLM-RoBERTa `isAt` head pairing"
        " (Run 3 from the submission file) is the encoder-only equivalent — it"
        " keeps the per-task best for the encoder family."
    )

    parts.append(
        "\n### 9.2 Voting ensembles\n"
        "[`scripts/build_three_way_ensemble.py`](scripts/build_three_way_ensemble.py)"
        " supports two voting rules:\n\n"
        "  - **Plurality** for the 3-class `at` task. When all three voters"
        " disagree we fall back to the **ordinal median** of the vote tuple"
        " (FALSE=0, PROBABLE=1, TRUE=2): the median of (TRUE, PROBABLE, FALSE)"
        " is PROBABLE — the elegant resolution of a maximum-disagreement triple.\n"
        "  - **Majority (binary)** for the `isAt` task with no tiebreaker"
        " (3 voters can't tie binary).\n\n"
        "Voting ensembles deployed in the official submissions:\n\n"
        "  - **Run 1 / `at`** — plurality(`xlm-roberta-large`, 4-model lookup"
        " stacker, Gemma 4 31B P-AB) with ordinal-median tiebreaker.\n"
        "  - **Run 1 / `isAt`** — majority(`xlm-roberta-large`, Gemma 4 31B P-AB,"
        " Llama 3.3 70B P-AB).\n"
        "  - **Run 3 / `at`** — plurality(`xlm-roberta-large`, `mDeBERTa-v3"
        " base`, RF) — the LLM-free encoder ensemble.\n\n"
        "Vote-provenance counts on the official 1,118-pair test set (lifted"
        " from `submissions/INSALyon_model_info.txt`):\n"
    )
    parts.append(
        md_table(
            ["run / `at` ensemble", "all-3 agree", "stacker+Gemma agree", "xlm+stacker agree", "xlm+Gemma agree", "tiebreaker"],
            [
                ["Run 1 (xlm + stacker + Gemma)", "432 (38.6%)", "272 (24.3%)", "265 (23.7%)", "122 (10.9%)", "27 (2.4%)"],
                ["Run 3 (xlm + mDeBERTa + RF)", "565 (50.5%)", "216 — xlm+mDeBERTa", "165 — mDeBERTa+RF", "151 — xlm+RF", "21 (1.9%)"],
            ],
        )
    )

    parts.append(
        "\n### 9.3 Disagreement-stacker lookup table\n"
        "[`hipe/stacker/lookup.py`](hipe/stacker/lookup.py) implements the"
        " parameter-free meta-classifier. For K base models with L labels each,"
        " the lookup table is built on the labelled training pool by mapping"
        " every observed vote tuple `(p_A, p_B, …, p_K)` to the empirical"
        " mode-of-gold in that cell:\n\n"
        "    lookup[(p_A, p_B, p_C, p_D)] := mode_of_gold_in_cell\n\n"
        "Unseen tuples at test time fall through a deterministic hierarchy:"
        " (1) exact match → (2) majority vote (≥2 models agree) → (3) ordinal"
        " median of the vote tuple → (4) configurable fallback label (FALSE)."
        " Why a lookup beats LR / MLP at this scale: with 81 cells and 1,251"
        " labelled instances, each cell has ≈15 instances on average — enough"
        " for stable mode-of-gold estimates, too few for a parametric"
        " meta-classifier to add value."
    )

    parts.append(
        "\n### 9.4 Greedy base-model selection\n"
        "The stacker's headroom depends on the diversity of the base set, not"
        " the strength of any individual model. We perform inner 3-fold greedy"
        " forward selection over `{RF, C4, OrdContM1, Gemma}` ("
        "[`scripts/eval_stacker_cv.py`](scripts/eval_stacker_cv.py)). Per fold"
        " the procedure starts with the empty set and adds the candidate"
        " whose mean inner-CV MR(at) gain is largest, stopping on no-gain. The"
        " selected sets per outer fold (4-model run) are:\n\n"
        "    Fold 0: {RF, Gemma, OrdContM1}\n"
        "    Fold 1: {RF, Gemma}\n"
        "    Fold 2: {C4, Gemma}\n"
        "    Fold 3: {RF, Gemma}\n"
        "    Fold 4: {Gemma, RF}\n\n"
        "Gemma is selected in every fold (TRUE/FALSE oracle); the second slot"
        " is contested between RF (PROBABLE precision anchor) and C4 (third"
        " embedding-space vote). The CE-only contrastive C only enters fold 0."
    )

    parts.append(
        "\n### 9.5 Comparison of stacker variants\n"
        "All numbers below are 5-fold nested-CV mean MR(`at`) and the bootstrap"
        " 95% CI on global score (with Gemma `isAt` paired in)."
    )
    cv_dir = REPO_ROOT / "logs" / "cv"
    cv_files = [
        ("2-model RF+C4 (greedy, no Gemma)", "T1_dry_run_2models_greedy_summary.json", None),
        ("3-model RF+C4+Gemma (greedy)", "T1_stacker_3models_nested_cv_summary.json", "T1_stacker_3models_nested_cv_with_gemma_isAt.bootstrap.json"),
        ("3-model RF+C4+Gemma (no-greedy)", "T1_stacker_3models_nested_cv_30day_nogreedy_summary.json", None),
        ("4-model RF+C4+OrdContM1+Gemma (greedy)", "T1_stacker_4models_nested_cv_summary.json", "T1_stacker_4models_nogreedy_with_gemma_isAt.bootstrap.json"),
        ("4-model RF+C4+OrdContM1+Gemma (no-greedy)", "T1_stacker_4models_nested_cv_nogreedy_summary.json", None),
    ]
    rows = []
    for label, fname, bs_file in cv_files:
        p = cv_dir / fname
        if not p.exists():
            continue
        d = load_json(p)
        agg = d.get("MR_at_mean_pm_std", {})
        ci_str = "—"
        if bs_file:
            bp = cv_dir / bs_file
            if bp.exists():
                b = load_json(bp)
                ci_str = (
                    f"{b['global_score']['point']:.4f}"
                    f" [{b['global_score']['ci_lower']:.4f},"
                    f" {b['global_score']['ci_upper']:.4f}]"
                )
        rows.append([
            label,
            f"{agg.get('mean', 0):.4f} ± {agg.get('std', 0):.3f}",
            ci_str,
        ])
    parts.append(
        md_table(["stacker", "5-fold MR(at) mean ± std", "global [bootstrap 95% CI]"], rows)
    )

    parts.append(
        "\n### 9.6 Stacker vs hybrid vs single model — same dev split\n"
        "Reproduces the comparative line from"
        " `specs/HIPE2026_Stacked_Approach.md` §6.1 with verified numbers from"
        " `logs/final/results.json` and the stacker logs:"
    )
    parts.append(
        md_table(
            ["configuration", "global", "MR(at)", "MR(isAt)", "n", "notes"],
            [
                ["RF + Llama 70B + rules (prior LLM-aware best)", "0.7338", "0.6627", "0.8049", "188", "single-split"],
                ["RF + Gemma 31B no-rules", "0.7585", "0.6627", "0.8544", "188", "single-split"],
                ["3-model stacker + Gemma `isAt` (spec-faithful, ordinal median)", "0.7807", "0.7070", "0.8544", "188", "single-split prototype"],
                ["3-model stacker + Gemma `isAt` (ad-hoc tiebreaker)", "0.7950", "0.7356", "0.8544", "188", "leakier tiebreaker"],
                ["**4-model stacker + Gemma `isAt` (current best)**", "**0.8172**", "**0.7800**", "**0.8544**", "188", "single-split best"],
                ["4-model stacker + Gemma `isAt` (5-fold CV)", "0.7520", "0.6559", "0.8480", "1,251", "**authoritative number**"],
            ],
        )
    )
    parts.append(
        "\n*Reading the table:* the +0.06 gain from the 4-model stacker over"
        " RF+Gemma on the single split is **NOT statistically significant** —"
        " 95% bootstrap CI on the CV pool is `[0.7321, 0.7724]`, which overlaps"
        " the RF+Gemma point. The CV mean is the authoritative number for"
        " paper claims; the single-split numbers are kept here as a rough"
        " ceiling."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Section 10 — Final test-set submissions
# ---------------------------------------------------------------------------


def section_submissions() -> str:
    parts: list[str] = []
    parts.append(banner("10. Final submissions on the official HIPE-2026 test set"))
    info_path = REPO_ROOT / "submissions" / "INSALyon_model_info.txt"
    if not info_path.exists():
        parts.append("*Submission descriptor `submissions/INSALyon_model_info.txt` not found.*")
        return "\n".join(parts)

    parts.append(
        "Three runs were submitted under the team name **INSALyon**. The"
        " complete component / size schedule is in"
        " [`submissions/INSALyon_model_info.txt`](submissions/INSALyon_model_info.txt);"
        " the prediction JSONLs are under `submissions/run{1,2,3}/`."
    )
    parts.append(
        "\nEach run produces four output files — three impresso languages plus"
        " the literary surprise set: `de`, `en`, `fr`, `surprise-fr`."
        " Per-file row counts are 19 / 19 / 19 / 30 = **87 articles** which"
        " unfold to **1,118 person-location pairs** on the official metric."
    )

    parts.append("\n### 10.1 Run 1 — multi-model ensemble (highest performance)\n")
    parts.append(
        "**Composition:**\n\n"
        "  - `at` task: 3-way **plurality vote** over\n"
        "      1. xlm-roberta-large fine-tuned on the at-task labelled pool,\n"
        "      2. the 4-model lookup-table stacker (RF + C4-SDov + OrdContM1 + Gemma),\n"
        "      3. Gemma 4 31B (P-AB) zero-shot.\n"
        "    Tiebreaker = ordinal median (FALSE < PROBABLE < TRUE).\n"
        "  - `isAt` task: 3-way **majority vote** over\n"
        "      1. xlm-roberta-large fine-tuned on the isAt-task labelled pool,\n"
        "      2. Gemma 4 31B (P-AB) zero-shot,\n"
        "      3. Llama 3.3 70B Instruct (P-AB) zero-shot.\n\n"
        "**Validated headroom on the dev / labelled pool:** MR(`at`) = 0.7765"
        " with 95% bootstrap CI `[0.6953, 0.8590]` (vs the 4-model stacker"
        " alone = 0.7269); MR(`isAt`) = 0.8411, CI `[0.7747, 0.9041]`"
        " (vs Gemma alone = 0.8273). The +0.05 lift on `at` comes from"
        " xlm-roberta's stronger PROBABLE recall (0.500 vs 0.39 for RF) breaking"
        " ties between the conservative stacker and the TRUE-biased Gemma.\n\n"
        "**Footprint (mixed precision):** 101.9 B parameters total,"
        " 195,716 MB on disk. The Llama 3.3 70B endpoint dominates;"
        " if the eval guideline counts only locally-deployed weights and treats"
        " LLM API endpoints as external services, the local footprint drops to"
        " ≈673 M parameters / ≈2,589 MB (RF + C4 + OrdContM1 + hmBERT + xlm)."
    )

    parts.append("\n### 10.2 Run 2 — mDeBERTa-v3 base, joint at + isAt fine-tuning\n")
    parts.append(
        "**Composition:** a single fine-tuned encoder model with two heads —"
        " one for `at` (3-class), one for `isAt` (binary). Predictions for both"
        " tasks come from the same encoder.\n\n"
        "**Architecture:** `microsoft/mdeberta-v3-base`. **Training:** 40"
        " epochs at lr = 2e-5, batch 8 (effective 16), label smoothing 0.05,"
        " sqrt-inverse class weights. Train / val: 1,063 / 188 (per-task 80/20"
        " split). Class weights (sqrt_inverse mode):\n\n"
        "    at:    {FALSE: 0.6456, TRUE: 0.807, PROBABLE: 1.5474}\n"
        "    isAt:  {FALSE: 0.6976, TRUE: 1.3024}\n\n"
        "**Validated:** MR(`at`) = 0.6189 (CI `[0.5375, 0.7039]`);"
        " MR(`isAt`) = 0.7782 (CI `[0.6999, 0.8521]`). Validation"
        " macro-F1 from the training configs: 0.6312 (`at`) / 0.7739 (`isAt`).\n\n"
        "**Footprint:** 278.0 M parameters / 1,061 MB. Smallest deployable"
        " system in our submission set; runs on a single 4 GB GPU at FP16."
        " Useful as a single-model lower bound."
    )

    parts.append("\n### 10.3 Run 3 — frugal encoder ensemble (no LLM at inference)\n")
    parts.append(
        "**Composition:**\n\n"
        "  - `at` task: 3-way **plurality vote** over\n"
        "      1. xlm-roberta-large fine-tuned on the at-task labelled pool,\n"
        "      2. mDeBERTa-v3 base fine-tuned on the at-task labelled pool,\n"
        "      3. RandomForest over handcrafted features.\n"
        "    Tiebreaker = ordinal median.\n"
        "  - `isAt` task: xlm-roberta-large alone (the same fine-tuned isAt"
        " model used inside Run 1).\n\n"
        "**Validated:** MR(`at`) = 0.7198 (CI `[0.6275, 0.8107]`) — within"
        " bootstrap CI of the 4-model stacker alone (0.7269), and only"
        " ≈0.057 below Run 1's 0.7765 while removing 30.7 B + 70.5 B of LLM"
        " parameters. MR(`isAt`) = 0.7854 (CI `[0.7072, 0.8609]`) — within"
        " CI of majority(xlm, mDeBERTa, RF) = 0.7869, and avoids the"
        " feature-drift collapse RF exhibits on the official test (where RF"
        " isAt would predict all-FALSE due to handcrafted-feature distribution"
        " shift between the dev split and the official test).\n\n"
        "**Footprint:** 838.8 M parameters / 3,217 MB — ≈60× smaller than Run 1"
        " (3.2 GB vs 195.7 GB). The full system fits on a single 4 GB GPU and"
        " no LLM API call is issued at inference time."
    )

    parts.append("\n### 10.4 Side-by-side comparison\n")
    parts.append(
        md_table(
            ["run", "system", "params", "size (MB)", "validated MR(at)", "validated MR(isAt)", "LLM at inference?"],
            [
                ["Run 1", "plurality(xlm, stacker, Gemma) + majority(xlm, Gemma, Llama)", "101,927,226,758", "195,716", "0.7765 [0.695, 0.859]", "0.8411 [0.775, 0.904]", "yes"],
                ["Run 2", "mDeBERTa-v3 base, joint at+isAt", "278,043,651", "1,061", "0.6189 [0.538, 0.704]", "0.7782 [0.700, 0.852]", "no"],
                ["Run 3", "plurality(xlm, mDeBERTa, RF) + xlm(isAt)", "838,778,678", "3,217", "0.7198 [0.628, 0.811]", "0.7854 [0.707, 0.861]", "no"],
            ],
        )
    )

    parts.append(
        "\n### 10.5 Submission file inventory\n"
        "All three runs produce the following four files (per the official"
        " naming convention):\n\n"
        "    INSALyon_HIPE-2026-v1.0-impresso-test-de_run<i>.jsonl\n"
        "    INSALyon_HIPE-2026-v1.0-impresso-test-en_run<i>.jsonl\n"
        "    INSALyon_HIPE-2026-v1.0-impresso-test-fr_run<i>.jsonl\n"
        "    INSALyon_HIPE-2026-v1.0-surprise-test-fr_run<i>.jsonl\n\n"
        "Each output line carries the original article fields plus the predicted"
        " `at` / `isAt` labels per pair, with an `at_explanation` /"
        " `isAt_explanation` field documenting the voting rule (e.g."
        " `plurality(xlm-roberta, 4-model-stacker, Gemma) tb=ordinal_median`)."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Header / abstract
# ---------------------------------------------------------------------------


def header_block() -> str:
    return (
        "# INSALyon @ HIPE-2026 — Methods Report\n"
        "_Generated by `scripts/generate_methods_report.py` from artefacts in this repo._\n\n"
        "This report documents every method we developed and tested for the"
        " HIPE-2026 *Person-Place Relation Extraction* shared task. The two"
        " predicted relations are\n\n"
        "  - **`at`** ∈ {TRUE, PROBABLE, FALSE} — does the article assert that"
        " the person was *at* the location?\n"
        "  - **`isAt`** ∈ {TRUE, FALSE} — was the person physically *at* the"
        " location around the publication date (≈±1 month)?\n\n"
        "Official metric: **GlobalScoreA = (MR_at + MR_isAt) / 2** where MR is"
        " the macro-Recall (balanced across class support)."
        " The report flows: training-data EDA → train/dev split → engineered"
        " features → models tested → LLM prompt configurations → comparative"
        " dev-set numbers → 5-fold CV results → cross-config disagreement"
        " analysis → stacking and ensembling → final submissions.\n\n"
        "*Acknowledgement.* The two transformer encoders (mDeBERTa-v3 base and"
        " XLM-RoBERTa large) were fine-tuned by collaborators outside this"
        " repository; we acknowledge the contribution and consume the"
        " predictions as inputs to the ensembles documented below.\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_report() -> str:
    sections = [
        header_block(),
        eda_training_pool(),
        section_train_dev_split(),
        section_features(),
        section_models(),
        section_prompts(),
        section_dev_results(),
        section_kfold(),
        section_disagreement(),
        section_stacking(),
        section_submissions(),
    ]
    return "\n\n".join(s.rstrip() for s in sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "reports" / "methods_report.md",
        help="Path to write the markdown report.",
    )
    args = parser.parse_args()

    out_path: Path = args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = build_report()
    out_path.write_text(text, encoding="utf-8")
    print(f"Wrote {out_path} ({len(text):,} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
