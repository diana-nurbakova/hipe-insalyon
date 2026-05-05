"""Block-1 feature extractor implementation.

Per ``specs/HIPE2026_Pipeline_Specs_v4.md`` §2.3, the temporal/discourse/
person-status fields in ``dataset_reference.jsonl`` are derived from:

- **`temporal_signals`** + **`temporal_signal_category`**: regex/lexicon over
  the article text covering FR/DE/EN/LB.
- **`tense_aspect`**: spaCy per-language verb-cluster tagging.
- **`sentence_position`**: spaCy sentencizer + locate the entity-pair sentence.
- **`temporal_expressions`** + **`nearest_timex_distance`**: HeidelTime TIMEX3
  extraction (optional; falls back to None if py-heideltime is not installed
  or Java is unavailable). The 14-day boolean is then derived from the
  signed distance.
- **`temporal_person_status`**: Wikidata SPARQL on the person QID for birth/
  death years compared to the article's publication date.
- **`ocr_quality`**: default 1.0 (spec range was 0.983–1.0 for impresso, so
  barely informative; revisit if a heuristic is needed).
- **`context`**: sentence window around the entity pair (falls back to
  ``text`` if no sentencization).

The orchestrator :func:`enrich_instance` accepts an official-format
``(document, sampled_pair)`` pair and returns a flat ``RelationInstance``
with all Block-1 fields populated. :func:`enrich_official_jsonl` streams a
nested official JSONL and writes a flat enriched JSONL ready for
:func:`scripts.extract_mask_embeddings`.

External dependencies
---------------------
- ``spacy>=3.7`` (in the ``nlp`` extras) and per-language models
  (``fr_core_news_md``, ``de_core_news_md``, ``en_core_web_md``).
- ``py-heideltime>=0.1.6`` (optional; ``nlp`` extras, non-Windows).
- ``requests`` (already in core deps) for Wikidata SPARQL.
"""

from __future__ import annotations

import functools
import json
import logging
import re
import time
from collections.abc import Iterable, Iterator
from dataclasses import asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from hipe.data.instance import RelationInstance
from hipe.data.official import iter_official_documents

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Temporal signals — regex/lexicon over article text
# =====================================================================
#
# Categories per spec §2.3 Priority 3:
# - "negation"     : 11% of training instances; strong FALSE
# - "present"      : 10% of training instances; strong isAt=TRUE
# - "relative_only": 27% of training instances; need verb-tense context
# - "no_signal"    : 48% of training instances
# - "other"        : catch-all
#
# Each lexicon entry is a (category, regex) pair. Multiple matches keep all;
# `temporal_signal_category` picks the highest-priority category found.

_NEGATION_LEXICON = [
    # FR
    r"\bne\s+\w+\s+plus\b", r"\bautrefois\b", r"\bjadis\b", r"\bnaguère\b",
    # DE
    r"\bnicht\s+mehr\b", r"\bfrüher\b", r"\bseinerzeit\b", r"\behemals\b",
    r"\beinst\b", r"\bvormals\b",
    # EN
    r"\bno\s+longer\b", r"\bformerly\b", r"\bonce\b(?:\s+was)?",
    r"\bin\s+former\s+times\b", r"\bonetime\b",
    # LB
    r"\bnët\s+méi\b",
]
_PRESENT_LEXICON = [
    # FR
    r"\bactuellement\b", r"\bmaintenant\b", r"\bà\s+présent\b",
    r"\bde\s+nos\s+jours\b", r"\baujourd['’]hui\b",
    # DE
    r"\bderzeit\b", r"\bzurzeit\b", r"\bgegenwärtig\b",
    r"\bheutzutage\b", r"\bmomentan\b",
    # EN
    r"\bcurrently\b", r"\bat\s+present\b", r"\bnowadays\b",
    r"\bthese\s+days\b", r"\bat\s+the\s+moment\b",
    # LB
    r"\bdäerzäit\b", r"\bhaut\b", r"\baktuell\b",
]
_RELATIVE_LEXICON = [
    # FR
    r"\brécemment\b", r"\bdernièrement\b", r"\bauparavant\b", r"\bnaguère\b",
    r"\bautrefois\b", r"\bla\s+veille\b", r"\bhier\b", r"\bdemain\b",
    # DE
    r"\bkürzlich\b", r"\bneulich\b", r"\bjüngst\b", r"\bgestern\b", r"\bmorgen\b",
    # EN
    r"\brecently\b", r"\blately\b", r"\byesterday\b", r"\btomorrow\b",
    r"\bthe\s+other\s+day\b",
]


def _compile(lexicon: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, flags=re.IGNORECASE) for p in lexicon]


_LEX = {
    "negation": _compile(_NEGATION_LEXICON),
    "present": _compile(_PRESENT_LEXICON),
    "relative_only": _compile(_RELATIVE_LEXICON),
}

# Priority order for the categorical bucket: negation > present > relative_only
# > no_signal. Matches the spec's discriminative ordering — negation is the
# strongest single-feature signal, hence wins over present.
_CATEGORY_PRIORITY = ("negation", "present", "relative_only")


def extract_temporal_signals(text: str) -> tuple[list[dict[str, str]], str]:
    """Return (list of matched signal entries, single category bucket).

    Each entry has ``{"surface": <matched span>, "category": <category>}``.
    Matching is case-insensitive across all four supported languages —
    ambiguity between FR/DE near-cognates is rare enough to ignore.
    """
    if not text:
        return [], "no_signal"
    matches: list[dict[str, str]] = []
    seen_categories: set[str] = set()
    for cat, regexes in _LEX.items():
        for r in regexes:
            for m in r.finditer(text):
                matches.append({"surface": m.group(0), "category": cat})
                seen_categories.add(cat)
    if not seen_categories:
        return matches, "no_signal"
    for cat in _CATEGORY_PRIORITY:
        if cat in seen_categories:
            return matches, cat
    return matches, "other"


# =====================================================================
# 2. spaCy-backed verb-tense + sentence-position extraction
# =====================================================================

_SPACY_MODEL_BY_LANG = {
    "fr": "fr_core_news_md",
    "de": "de_core_news_md",
    "en": "en_core_web_md",
    # Luxembourgish has no spaCy model; fall back to German.
    "lb": "de_core_news_md",
}


@functools.lru_cache(maxsize=8)
def _spacy_model(lang: str):
    """Load a spaCy model lazily, once per language. Returns None if missing."""
    try:
        import spacy
    except ImportError:
        logger.warning("spaCy not installed; tense_aspect/sentence_position skipped")
        return None
    name = _SPACY_MODEL_BY_LANG.get(lang)
    if name is None:
        logger.warning("no spaCy model configured for language %r", lang)
        return None
    try:
        nlp = spacy.load(name, disable=["ner", "lemmatizer"])
    except OSError:
        logger.warning(
            "spaCy model %r not installed; download via "
            "`python -m spacy download %s`", name, name,
        )
        return None
    return nlp


def extract_tense_aspect(text: str, language: str) -> list[dict[str, Any]]:
    """spaCy-based verb-cluster annotation matching the dataset schema.

    Returns a list of ``{"verb": str, "tense": str, "aspect": str, "mood": str,
    "negated": bool}`` for each finite verb cluster found in ``text``. Tense
    values mirror Universal Dependencies feature names (Pres, Past, Fut).
    Returns an empty list if spaCy is unavailable.
    """
    nlp = _spacy_model(language)
    if nlp is None or not text:
        return []
    doc = nlp(text)
    out: list[dict[str, Any]] = []
    for tok in doc:
        if tok.pos_ not in ("VERB", "AUX"):
            continue
        morph = tok.morph
        tense = morph.get("Tense")
        aspect = morph.get("Aspect")
        mood = morph.get("Mood")
        negated = any(c.dep_ == "advmod" and c.lemma_.lower() in {"not", "ne", "nicht", "n't"}
                      for c in tok.children)
        out.append({
            "verb": tok.lemma_ or tok.text,
            "tense": tense[0] if tense else "",
            "aspect": aspect[0] if aspect else "",
            "mood": mood[0] if mood else "",
            "negated": bool(negated),
        })
    return out


def derive_sentence_position(
    text: str,
    pers_mentions: list[str],
    loc_mentions: list[str],
    language: str,
) -> int:
    """Index of the first sentence containing a person AND location mention.

    Returns ``-1`` if either entity is not found, or if spaCy is unavailable
    (callers should treat ``-1`` as "unknown" — temporal_matrix already does).
    """
    nlp = _spacy_model(language)
    if nlp is None or not text or not pers_mentions or not loc_mentions:
        return -1
    # Spacy sentencizer already runs as part of the small/medium models.
    doc = nlp(text)
    pers_lc = [m.lower() for m in pers_mentions if m]
    loc_lc = [m.lower() for m in loc_mentions if m]
    for i, sent in enumerate(doc.sents):
        s_lc = sent.text.lower()
        if any(p in s_lc for p in pers_lc) and any(l in s_lc for l in loc_lc):
            return i
    return -1


def extract_context(
    text: str,
    pers_mentions: list[str],
    loc_mentions: list[str],
    language: str,
    *,
    sent_window: int = 1,
) -> str:
    """Sentence-level window around the first sentence containing both entities.

    Falls back to the full ``text`` if the entity pair isn't located or if
    spaCy is unavailable. Mirrors the ``context`` field's role for the MASK
    encoder (~256 BERT tokens).
    """
    nlp = _spacy_model(language)
    if nlp is None or not text:
        return text
    doc = nlp(text)
    sents = list(doc.sents)
    if not sents:
        return text
    pers_lc = [m.lower() for m in pers_mentions if m]
    loc_lc = [m.lower() for m in loc_mentions if m]
    for i, sent in enumerate(sents):
        s_lc = sent.text.lower()
        if any(p in s_lc for p in pers_lc) and any(l in s_lc for l in loc_lc):
            lo = max(0, i - sent_window)
            hi = min(len(sents), i + sent_window + 1)
            return " ".join(s.text for s in sents[lo:hi])
    return text


# =====================================================================
# 3. HeidelTime TIMEX3 extraction (optional)
# =====================================================================

_HEIDELTIME_LANG = {"fr": "french", "de": "german", "en": "english"}


@functools.lru_cache(maxsize=4)
def _heideltime(language: str):
    try:
        from py_heideltime import heideltime
    except ImportError:
        logger.warning("py-heideltime not installed; TIMEX extraction skipped")
        return None
    lang = _HEIDELTIME_LANG.get(language)
    if lang is None:
        return None
    return functools.partial(heideltime, language=lang, document_type="news")


def extract_temporal_expressions_heideltime(
    text: str,
    pub_date: str | None,
    language: str,
) -> list[dict[str, Any]]:
    """HeidelTime TIMEX3 extraction. Returns [] if HeidelTime unavailable.

    Each entry is ``{"surface": str, "value": str, "type": str}`` where
    ``value`` is the HeidelTime-resolved date in ISO format if computable.
    """
    fn = _heideltime(language)
    if fn is None or not text:
        return []
    try:
        result = fn(text, dct=pub_date or "1900-01-01")
    except Exception as exc:  # heideltime raises on Java startup failure
        logger.warning("HeidelTime failed: %s", exc)
        return []
    out = []
    for entry in result or []:
        # py-heideltime returns dicts like {"text": ..., "value": ..., "type": ...}
        out.append({
            "surface": entry.get("text", ""),
            "value": entry.get("value", ""),
            "type": entry.get("type", ""),
        })
    return out


def derive_nearest_timex_distance(
    timexes: list[dict[str, Any]],
    pub_date: str | None,
) -> int | None:
    """Signed days from publication date to the nearest TIMEX-resolved date.

    Returns ``None`` if no TIMEX has a parseable ISO value, or if pub_date
    is missing. Sign convention: negative = TIMEX before publication.
    """
    if not pub_date or not timexes:
        return None
    try:
        pub = datetime.fromisoformat(pub_date).date()
    except (ValueError, TypeError):
        return None
    best: int | None = None
    for t in timexes:
        v = t.get("value", "")
        if not v or len(v) < 7:  # expect at least YYYY-MM
            continue
        try:
            # HeidelTime values can be partial dates ("1920", "1920-08").
            parts = v.split("-")
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else 1
            day = int(parts[2]) if len(parts) > 2 else 1
            d = date(year, month, day)
        except (ValueError, IndexError):
            continue
        delta = (d - pub).days
        if best is None or abs(delta) < abs(best):
            best = delta
    return best


# =====================================================================
# 4. Wikidata-derived person status
# =====================================================================
#
# Lookup birth/death years for the person QID via the public Wikidata
# SPARQL endpoint and bucket into the same categories as
# ``dataset_reference.jsonl``:
#   - "unknown"          : QID is None or SPARQL fails
#   - "no_match"         : QID exists but no P569 (birth) value
#   - "alive_now"        : born; either no death year or death > pub_date
#                          AND birth <= pub_date — and pub_date is "recent"
#   - "alive_past"       : alive at pub_date but pub_date is historical
#   - "dead_historical"  : died before pub_date — hard `at`/`isAt` = FALSE override
#   - "alive_no_longer"  : died after pub_date (i.e., alive then, dead now)
#                          — for the purposes of the dataset, treated as alive_past

_WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
_WIKIDATA_USER_AGENT = "HIPE-2026 enrichment/0.1 (research)"


@functools.lru_cache(maxsize=4096)
def _wikidata_birth_death(qid: str) -> tuple[int | None, int | None]:
    """Return (birth_year, death_year). Cached. Either may be None."""
    if not qid or not qid.startswith("Q"):
        return None, None
    query = (
        "SELECT ?birth ?death WHERE {"
        f"  wd:{qid} wdt:P569 ?birth ."
        f"  OPTIONAL {{ wd:{qid} wdt:P570 ?death . }}"
        "} LIMIT 1"
    )
    try:
        r = requests.get(
            _WIKIDATA_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={"User-Agent": _WIKIDATA_USER_AGENT, "Accept": "application/json"},
            timeout=15,
        )
        if r.status_code != 200:
            return None, None
        bindings = r.json().get("results", {}).get("bindings", [])
        if not bindings:
            return None, None
        b = bindings[0]
        birth_year = int(b["birth"]["value"][:4]) if "birth" in b else None
        death_year = int(b["death"]["value"][:4]) if "death" in b else None
        return birth_year, death_year
    except Exception as exc:
        logger.warning("Wikidata SPARQL failed for %s: %s", qid, exc)
        return None, None


def derive_temporal_person_status(
    pers_qid: str | None,
    pub_date: str | None,
    *,
    historical_pub_year_threshold: int = 1980,
    rate_limit_seconds: float = 0.05,
) -> str:
    """Bucket the person's life status relative to the publication date."""
    if not pers_qid or not pub_date:
        return "unknown"
    try:
        pub_year = datetime.fromisoformat(pub_date).year
    except (ValueError, TypeError):
        return "unknown"
    birth, death = _wikidata_birth_death(pers_qid)
    if rate_limit_seconds:
        # Polite ~20 req/s pace under Wikidata's anonymous quota.
        time.sleep(rate_limit_seconds)
    if birth is None:
        return "no_match"
    if birth > pub_year:
        # Person not yet born at publication — undefined; treat as no_match.
        return "no_match"
    if death is not None and death < pub_year:
        return "dead_historical"
    if pub_year < historical_pub_year_threshold:
        return "alive_past"
    return "alive_now"


# =====================================================================
# 5. Orchestrator
# =====================================================================


def enrich_instance(
    doc: dict[str, Any],
    pair: dict[str, Any],
    *,
    use_heideltime: bool = False,
    use_wikidata: bool = False,
    isat_window_days: int = 14,
) -> RelationInstance:
    """Build a fully-populated RelationInstance from one official-format pair.

    Defaults stay conservative: HeidelTime and Wikidata calls are off so a
    bare CPU-only run produces deterministic output without external deps.
    Enable them once you've confirmed Java + Wikidata access.
    """
    text = doc.get("text", "") or ""
    language = doc.get("language", "") or ""
    pub_date = doc.get("date", None) or None
    pers_mentions = list(pair.get("pers_mentions_list") or [])
    loc_mentions = list(pair.get("loc_mentions_list") or [])

    signals, signal_category = extract_temporal_signals(text)
    tense_aspect = extract_tense_aspect(text, language)
    sentence_position = derive_sentence_position(text, pers_mentions, loc_mentions, language)
    context = extract_context(text, pers_mentions, loc_mentions, language)

    timexes: list[dict[str, Any]] = []
    nearest = None
    if use_heideltime:
        timexes = extract_temporal_expressions_heideltime(text, pub_date, language)
        nearest = derive_nearest_timex_distance(timexes, pub_date)
    has_timex_in_window = (
        nearest is not None and abs(nearest) <= isat_window_days
    )

    person_status = "unknown"
    if use_wikidata:
        person_status = derive_temporal_person_status(
            pair.get("pers_wikidata_QID"), pub_date,
        )

    return RelationInstance(
        document_id=doc["document_id"],
        pers_entity_id=pair["pers_entity_id"],
        loc_entity_id=pair["loc_entity_id"],
        language=language,
        date=pub_date or "",
        pers_mentions_list=pers_mentions,
        loc_mentions_list=loc_mentions,
        pers_wikidata_QID=pair.get("pers_wikidata_QID"),
        loc_wikidata_QID=pair.get("loc_wikidata_QID"),
        text=text,
        context=context,
        person_context={},
        location_context={},
        known_person_location_relations={},
        similar_examples=[],
        temporal_expressions=timexes,
        temporal_signals=signals,
        tense_aspect=tense_aspect,
        sentence_position=sentence_position,
        ocr_quality=1.0,
        has_timex_in_isat_window=has_timex_in_window,
        nearest_timex_distance=nearest,
        person_location_match="unknown",
        temporal_person_status=person_status,
        temporal_signal_category=signal_category,
        at=pair.get("at"),
        isAt=pair.get("isAt"),
        at_explanation=pair.get("at_explanation"),
        isAt_explanation=pair.get("isAt_explanation"),
    )


def enrich_official_jsonl(
    in_path: str | Path,
    out_path: str | Path,
    *,
    use_heideltime: bool = False,
    use_wikidata: bool = False,
    isat_window_days: int = 14,
    progress_every: int = 50,
) -> int:
    """Stream an official nested JSONL into a flat enriched JSONL.

    Returns the number of pairs written. The output format matches what
    ``hipe.data.load_jsonl`` reads (so ``scripts/extract_mask_embeddings.py``
    can consume it without the auto-detect path).
    """
    in_path = Path(in_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_written = 0
    t0 = time.perf_counter()
    with out_path.open("w", encoding="utf-8") as f:
        for doc in iter_official_documents(in_path):
            for pair in doc.get("sampled_pairs", []):
                inst = enrich_instance(
                    doc, pair,
                    use_heideltime=use_heideltime,
                    use_wikidata=use_wikidata,
                    isat_window_days=isat_window_days,
                )
                f.write(json.dumps(asdict(inst), ensure_ascii=False, default=str) + "\n")
                n_written += 1
                if n_written % progress_every == 0:
                    rate = n_written / max(1e-3, time.perf_counter() - t0)
                    print(f"  enriched {n_written} pairs ({rate:.1f}/s)", flush=True)
    return n_written


def iter_enriched_instances(
    in_path: str | Path,
    *,
    use_heideltime: bool = False,
    use_wikidata: bool = False,
    isat_window_days: int = 14,
) -> Iterator[RelationInstance]:
    """Streamed equivalent of :func:`enrich_official_jsonl` — keeps memory bounded
    when callers want RelationInstance objects instead of writing to disk."""
    for doc in iter_official_documents(in_path):
        for pair in doc.get("sampled_pairs", []):
            yield enrich_instance(
                doc, pair,
                use_heideltime=use_heideltime,
                use_wikidata=use_wikidata,
                isat_window_days=isat_window_days,
            )
