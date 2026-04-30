"""Prompt templates P-A, P-B, P-AB, P-R (verbatim from HIPE-2026 Prompting Spec).

System prompts are copied verbatim from the spec so the baseline matches the
authored design exactly. The user message is shared across variants and is
configurable: zero-shot mode strips entity/temporal context blocks, full
mode includes them (for downstream RAG / Wikidata / temporal experiments).

Per spec, LLM prompts use ``<PERSON>...</PERSON>`` / ``<LOCATION>...</LOCATION>``
markers (NOT ``[E1]/[E2]`` — those are reserved for the MASK encoder).
"""

from __future__ import annotations

from dataclasses import dataclass

from hipe.data import RelationInstance

PROMPT_VARIANTS = ("A", "B", "AB", "R")

PERS_OPEN, PERS_CLOSE = "<PERSON>", "</PERSON>"
LOC_OPEN, LOC_CLOSE = "<LOCATION>", "</LOCATION>"


# ---------------------------------------------------------------------------
# Marker insertion (LLM variant — distinct tags from the MASK encoder)
# ---------------------------------------------------------------------------


def _wrap_first_match(text: str, mentions: list[str], open_tag: str, close_tag: str) -> tuple[str, bool]:
    """Wrap the earliest occurrence of any mention in *text* with marker tags.

    OCR-noisy text often inserts newlines and extra whitespace inside multi-word
    entities (e.g. ``Myrtle\\nBeach Air Force Base``). We compile each mention
    into a regex that allows ``\\s+`` between words, and match case-insensitively
    against the original text (preserving its whitespace in the output).
    """
    if not mentions or not text:
        return text, False
    import re as _re

    best: tuple[int, int, str] | None = None
    for m in sorted({m for m in mentions if m}, key=len, reverse=True):
        # Collapse whitespace and convert each token into an escaped chunk
        # joined with `\s+`, so newlines/extra spaces in either side match.
        tokens = m.split()
        if not tokens:
            continue
        pattern = r"\s+".join(_re.escape(tok) for tok in tokens)
        match = _re.search(pattern, text, flags=_re.IGNORECASE)
        if not match:
            continue
        if best is None or match.start() < best[0]:
            best = (match.start(), match.end(), text[match.start() : match.end()])
    if best is None:
        return text, False
    s, e, matched = best
    return f"{text[:s]}{open_tag}{matched}{close_tag}{text[e:]}", True


def insert_entity_markers(instance: RelationInstance, *, field: str = "text") -> str:
    """Wrap entity surface forms with ``<PERSON>``/``<LOCATION>`` tags.

    Default field is ``text`` (full article) for LLM prompts; the spec
    recommends the model see the full article context when reasoning.
    """
    base = instance.text if field == "text" else instance.context
    base = base or ""
    pers = instance.pers_mentions_list or []
    loc = instance.loc_mentions_list or []
    base, _ = _wrap_first_match(base, pers, PERS_OPEN, PERS_CLOSE)
    base, _ = _wrap_first_match(base, loc, LOC_OPEN, LOC_CLOSE)
    return base


# ---------------------------------------------------------------------------
# System prompts (verbatim from spec)
# ---------------------------------------------------------------------------


_SYSTEM_P_A = """You are an expert annotator for historical named-entity relation extraction
in the HIPE-2026 shared task.

CONTEXT:
- Documents are historical newspaper articles from 1798-2018.
- Languages: English, French, German (read as-is - do NOT translate).
- OCR may introduce minor noise; focus on clear verbal structures and entities.

TASK DEFINITION:
The "at" relation captures whether a person has a GENERAL ASSOCIATION with a
location - born there, lived there, worked there, visited, traveled through,
or any other connection linking the person to the place. This association may
be past, present, or ongoing.

Values (from HIPE-2026 annotation guidelines):
  TRUE     - There is explicit evidence in the text that lets us assert with
             high certainty that the person was at the given place. Do NOT use
             world knowledge - only evidence present in the text.
  PROBABLE - The article does not explicitly state that the person was at the
             location, but it is implied, or indirectly reported.
  FALSE    - There is no clear evidence in the text that the person was at
             the location.

DECISION GUIDELINES:
1. VERB TENSE is the primary signal:
   - Present tense ("reside a", "works in", "wohnt in") -> TRUE
   - Past tense describing life events ("ne a", "born in", "geboren in") -> TRUE
   - Past tense with distancing ("formerly", "jadis", "ehemals") -> PROBABLE or FALSE
   - Negation ("no longer", "nicht mehr", "ne ... plus") -> FALSE

2. WIKIDATA CONTEXT (when provided):
   - If the person died before the publication date -> FALSE
     (a deceased person has no current association)
   - Known residence/work location matching the article -> TRUE
   - Birth place alone does NOT guarantee TRUE unless the text corroborates

3. TEXTUAL EVIDENCE STRENGTH:
   - Direct statement of association -> TRUE
   - Co-occurrence without linking language -> PROBABLE
   - Mere mention in same article, no connection -> FALSE

OUTPUT FORMAT:
Respond with exactly one line in this format:
  <LABEL> | confidence=<X.XX>

Replace <LABEL> with one of TRUE, FALSE, or PROBABLE.
Replace <X.XX> with a number between 0.00 and 1.00.

Examples (do not output these literally — they show the format):
  TRUE | confidence=0.95
  PROBABLE | confidence=0.55
  FALSE | confidence=0.80

Confidence scale:
  1.00 = absolute certainty, text provides unambiguous direct evidence
  0.80-0.99 = high confidence, strong textual evidence with minor ambiguity
  0.60-0.79 = moderate confidence, evidence present but requires some inference
  0.40-0.59 = low confidence, weak or indirect evidence, could go either way
  0.00-0.39 = very low confidence, near-random guess, almost no supporting evidence
Do NOT output explanations or any other text. Output the line and nothing else."""


_SYSTEM_P_B = """You are an expert annotator for historical named-entity relation extraction
in the HIPE-2026 shared task.

CONTEXT:
- Documents are historical newspaper articles from 1798-2018.
- Languages: English, French, German (read as-is - do NOT translate).
- OCR may introduce minor noise; focus on clear verbal structures and entities.

TASK DEFINITION:
The "isAt" relation captures whether a person is PHYSICALLY PRESENT at a
location AROUND THE TIME the newspaper article was published. "Around" means
within approximately one month before the publication date.

This is a TEMPORAL question: was this person at this place at this time?

Values (from HIPE-2026 annotation guidelines):
  TRUE  - There is explicit evidence in the text that lets us assert with
          high certainty that the person was at the given place within
          approximately one month before the publication date.
  FALSE - There is no clear evidence of physical presence at publication time,
          OR the association is historical/biographical only.

TEMPORAL REASONING GUIDELINES:
1. RESOLVE all temporal expressions relative to the publication date:
   - "yesterday" / "hier" / "gestern" -> publication_date minus 1 day
   - "last week" / "la semaine derniere" / "vorige Woche" -> ~7 days before
   - Absolute dates -> compare directly to publication date

2. CHECK if resolved dates fall within approximately one month of the publication date:
   - Within window -> strong evidence for TRUE
   - Outside window -> insufficient for TRUE

3. VERB TENSE as temporal anchor:
   - Present tense in a news article typically describes events at or near
     publication time -> supports TRUE
   - Present tense in a lead paragraph (first sentence) is the strongest
     signal for current events
   - Simple past in a news context often describes recent events (days ago)
     -> may support TRUE if no distancing language
   - Past perfect ("had been", "avait ete", "hatte ... gewesen") -> earlier
     than the main narrative -> usually FALSE

4. DISTANCING LANGUAGE always overrides tense:
   - "formerly", "autrefois", "jadis", "ehemals", "once" -> FALSE
   - "no longer", "ne ... plus", "nicht mehr" -> FALSE
   - Future tense ("will go", "ira", "wird ... gehen") -> FALSE (not yet there)

5. DECEASED PERSONS:
   - If the person died before the publication date -> FALSE
     (check Wikidata death date against publication date)

6. INVERTED PYRAMID HEURISTIC:
   - Newspaper lead paragraphs describe current events
   - If the entity pair appears in the lead (position 0-1) with present
     tense -> strong TRUE signal
   - If the entity pair appears deep in the article with past tense ->
     likely background context -> weaker signal

LANGUAGE-SPECIFIC TEMPORAL REASONING:

For FRENCH texts -- extra caution is required:
   - The passe compose ("est arrive", "a declare") is AMBIGUOUS: it can
     describe either a recent event (-> supports TRUE) or a completed past
     action with no recency implication. Look for temporal adverbs ("hier",
     "recemment", "ce matin") or discourse position to disambiguate.
   - The present historique (historical present) is common in French
     journalism: past events narrated in present tense for vividness.
     Do NOT automatically treat French present tense as evidence of current
     presence. Check whether surrounding sentences use past tense -- if so,
     the present tense may be stylistic, not temporal.
   - Appositional titles ("M. Dupont, ancien ministre de...") often encode
     temporal status: "ancien" (former) -> FALSE; absence of "ancien" with
     a current title -> supports TRUE.
   - French negation ("ne ... plus", "ne ... jamais") may be split across
     multiple words and disrupted by OCR. Look for BOTH particles.
   - Expressions like "se trouve a", "reside a", "sejourne a" in present
     tense are strong TRUE signals -- they explicitly describe current location.

For GERMAN texts:
   - German cleanly distinguishes Perfekt ("ist angekommen" -- recent,
     conversational) from Praeteritum ("kam an" -- narrative past). Perfekt
     in a news article strongly supports TRUE; Praeteritum is more neutral.
   - Compound verbs with separable prefixes ("ankommen", "abreisen") may
     have the prefix at the end of the clause -- look for both parts.
   - "derzeit", "gegenwaertig", "zurzeit" (currently) are strong TRUE signals.
   - "ehemals", "frueher", "einst" (formerly) are strong FALSE signals.

For ENGLISH texts:
   - Present perfect ("has arrived") strongly supports TRUE -- implies
     recency and current relevance.
   - Simple past ("arrived") is weaker -- may describe recent or distant events.
   - Progressive forms ("is staying at", "is visiting") are strong TRUE signals.
   - "former", "late", "once" are clear FALSE signals.

OUTPUT FORMAT:
Respond with exactly one line in this format:
  <LABEL> | confidence=<X.XX>

Replace <LABEL> with one of TRUE or FALSE.
Replace <X.XX> with a number between 0.00 and 1.00.

Examples (do not output these literally — they show the format):
  TRUE | confidence=0.92
  FALSE | confidence=0.78

Confidence scale:
  1.00 = absolute certainty, text provides unambiguous direct evidence
  0.80-0.99 = high confidence, strong textual evidence with minor ambiguity
  0.60-0.79 = moderate confidence, evidence present but requires some inference
  0.40-0.59 = low confidence, weak or indirect evidence, could go either way
  0.00-0.39 = very low confidence, near-random guess, almost no supporting evidence
Do NOT output explanations or any other text. Output the line and nothing else."""


_SYSTEM_P_AB = """You are an expert annotator for historical named-entity relation extraction
in the HIPE-2026 shared task.

CONTEXT:
- Documents are historical newspaper articles from 1798-2018.
- Languages: English, French, German (read as-is - do NOT translate).
- OCR may introduce minor noise; focus on clear verbal structures and entities.

YOUR TASK:
Classify TWO relations for a given person-location pair:

1. "at" - GENERAL ASSOCIATION
   Does this person have any connection to this location?
   (born there, lived there, worked there, visited, etc.)
   Values: TRUE / PROBABLE / FALSE

2. "isAt" - PHYSICAL PRESENCE AT PUBLICATION TIME
   Was this person physically present at this location around the time the
   article was published (within approximately one month)?
   Values: TRUE / FALSE

LOGICAL CONSTRAINT: If isAt=TRUE, then at must be TRUE or PROBABLE.
(If someone is currently at a place, they have an association with it.)

DECISION FRAMEWORK:

For "at" (general association):
  - Direct textual evidence of connection -> TRUE
  - Implicit or uncertain connection -> PROBABLE
  - No connection -> FALSE
  - Person deceased before publication -> FALSE

For "isAt" (temporal presence):
  - Resolve all temporal expressions relative to the publication date
  - Present tense in news context -> supports TRUE
  - "yesterday"/"hier"/"gestern" -> resolve to pub_date - 1 -> within window -> TRUE
  - Past tense with distancing language -> FALSE
  - Person deceased -> FALSE
  - No temporal anchor within ~1 month of publication -> FALSE

LANGUAGE-SPECIFIC NOTES:
  - French: passe compose is ambiguous; present historique may be stylistic, not
    temporal -- check surrounding tense. "ancien" (former) -> FALSE.
  - German: Perfekt -> recent (TRUE-leaning); Praeteritum -> narrative past (neutral).
  - English: present perfect / progressive -> TRUE-leaning; "former", "late" -> FALSE.

OUTPUT FORMAT:
Respond with exactly one line:
  at=LABEL isAt=LABEL | conf_at=X.XX conf_isAt=X.XX

Example: at=TRUE isAt=FALSE | conf_at=0.92 conf_isAt=0.85
Do NOT output explanations or any other text."""


_SYSTEM_P_R = """You are an expert annotator for historical named-entity relation extraction
in the HIPE-2026 shared task.

CONTEXT:
- Documents are historical newspaper articles from 1798-2018.
- Languages: English, French, German (read as-is - do NOT translate).
- OCR may introduce minor noise; focus on clear verbal structures and entities.

YOUR TASK:
Classify TWO relations for a given person-location pair:

1. "at" - GENERAL ASSOCIATION
   Does this person have any connection to this location?
   Values: TRUE / PROBABLE / FALSE

2. "isAt" - PHYSICAL PRESENCE AT PUBLICATION TIME
   Was this person physically present at this location around the time the
   article was published (within approximately one month)?
   Values: TRUE / FALSE

LOGICAL CONSTRAINT: If isAt=TRUE, then at must be TRUE or PROBABLE.

DECISION FRAMEWORK:

For "at" (general association):
  - Direct textual evidence of connection -> TRUE
  - Implicit or uncertain connection -> PROBABLE
  - No connection -> FALSE
  - Person deceased before publication -> FALSE

For "isAt" (temporal presence):
  - Resolve all temporal expressions relative to the publication date
  - Present tense in news context -> supports TRUE
  - "yesterday"/"hier"/"gestern" -> resolve to pub_date - 1 -> within window -> TRUE
  - Past tense with distancing language -> FALSE
  - Person deceased -> FALSE
  - No temporal anchor within ~1 month of publication -> FALSE

LANGUAGE-SPECIFIC NOTES:
  - French: passe compose is ambiguous; present historique may be stylistic, not
    temporal -- check surrounding tense. "ancien" (former) -> FALSE.
  - German: Perfekt -> recent (TRUE-leaning); Praeteritum -> narrative past (neutral).
  - English: present perfect / progressive -> TRUE-leaning; "former", "late" -> FALSE.

OUTPUT FORMAT:
Respond with a brief structured analysis followed by your classification.

ANALYSIS (keep concise - 3-5 lines max):
(1) VERB: identify the main verb linking person to location, its tense
(2) TEMPORAL: list any temporal expressions, resolve them relative to the publication date
(3) WIKIDATA: note if Wikidata confirms/contradicts (deceased? known residence?)
(4) EVIDENCE: overall strength of the textual evidence (strong/moderate/weak)

CLASSIFICATION:
  at=LABEL isAt=LABEL | conf_at=X.XX conf_isAt=X.XX"""


_SYSTEM_PROMPTS = {
    "A": _SYSTEM_P_A,
    "B": _SYSTEM_P_B,
    "AB": _SYSTEM_P_AB,
    "R": _SYSTEM_P_R,
}

_VARIANT_INSTRUCTIONS = {
    "A": 'Classify the "at" relation for this person-location pair.',
    "B": 'Classify the "isAt" relation for this person-location pair.',
    "AB": 'Classify both the "at" and "isAt" relations for this person-location pair.',
    "R": 'Analyse the "at" and "isAt" relations, then output your classification.',
}


def system_prompt(variant: str) -> str:
    if variant not in _SYSTEM_PROMPTS:
        raise ValueError(f"variant must be one of {PROMPT_VARIANTS}, got {variant!r}")
    return _SYSTEM_PROMPTS[variant]


# ---------------------------------------------------------------------------
# User message builder
# ---------------------------------------------------------------------------


def _format_wikidata_summary(ctx: dict | None) -> str | None:
    """Render a Wikidata context dict as a single line, or ``None`` when empty.

    Returning ``None`` (rather than ``"(none)"``) lets the user-message
    builder drop the line entirely when the data is missing — the spec's
    pre-fetched Wikidata is null for ~57% of persons, so rendering an
    empty placeholder is pure noise that distracts smaller LLMs.
    """
    if not ctx:
        return None
    parts = []
    for key in ("label", "description", "born", "died", "country", "located_in"):
        v = ctx.get(key)
        if v:
            parts.append(f"{key}={v}")
    aliases = ctx.get("aliases") or {}
    if isinstance(aliases, dict):
        flat = sum((aliases.get(lang, []) for lang in ("en", "fr", "de")), [])
        if flat:
            parts.append(f"aliases={flat[:6]}")
    return "; ".join(parts) if parts else None


def _format_temporal_block(instance: RelationInstance) -> str | None:
    """Render the temporal-signal summary, or ``None`` when there is no signal.

    "No signal" means: ``temporal_signal_category in {"", "no_signal"}``,
    no tense_aspect clusters, no temporal_signals, no in-window timex.
    The discourse position is intentionally NOT a sufficient reason to
    render the block on its own — position alone with no other signal is
    not informative.
    """
    parts = []
    if instance.tense_aspect:
        verbs = ", ".join(
            f"{c.get('verb_cluster','?')}[{c.get('tense','?')}{'.NEG' if c.get('negated') else ''}]"
            for c in instance.tense_aspect[:5]
        )
        parts.append(f"verbs: {verbs}")
    if instance.temporal_signals:
        sigs = ", ".join(str(s) for s in instance.temporal_signals[:5])
        parts.append(f"signals: {sigs}")
    cat = instance.temporal_signal_category
    if cat and cat != "no_signal":
        parts.append(f"category: {cat}")
    if instance.has_timex_in_isat_window:
        parts.append("timex_in_isat_window=true")
    if instance.nearest_timex_distance is not None:
        parts.append(f"nearest_timex={instance.nearest_timex_distance}d")
    if not parts:
        return None
    if instance.sentence_position is not None and instance.sentence_position >= 0:
        parts.append(f"sentence_position={instance.sentence_position}")
    return " | ".join(parts)


@dataclass(slots=True)
class UserMessageOptions:
    zero_shot: bool = True
    include_wikidata: bool = False  # True for non-zero-shot variants
    include_temporal: bool = False
    include_temporal_interpretation: bool = False
    text_field: str = "text"
    retrieved_excerpt_chars: int = 360  # truncation budget per retrieved example
    # Optional natural-language rules block (Option C — SD prompt injection,
    # Subgroup Discovery Specs §6.3). Rendered as a "[DOMAIN RULES]" section
    # right before the variant instructions. None / empty → block omitted.
    domain_rules: str | None = None


def _format_retrieved_example(rank: int, example: "RetrievedExample", max_chars: int) -> str:
    md = example.metadata
    person = md.get("pers_mention") or "?"
    location = md.get("loc_mention") or "?"
    pub_date = md.get("date") or "—"
    language = md.get("language") or "—"
    context = (md.get("context") or "").strip().replace("\n", " ")
    if len(context) > max_chars:
        context = context[: max_chars - 1].rstrip() + "…"
    at = md.get("at") or "?"
    isAt = md.get("isAt") or "?"
    return (
        f"Example {rank} (similarity={example.score:.2f}, lang={language}, date={pub_date}):\n"
        f"  Person: '{person}'   Location: '{location}'\n"
        f"  Excerpt: \"{context}\"\n"
        f"  Gold: at={at}, isAt={isAt}"
    )


def format_retrieved_examples_block(
    retrieved: list["RetrievedExample"],
    *,
    max_chars_per_example: int = 360,
) -> str:
    """Render a list of retrieved examples as a single user-message block.

    Returns the empty string if ``retrieved`` is empty so callers can blindly
    embed the block without testing for emptiness.
    """
    if not retrieved:
        return ""
    lines = ["[SIMILAR EXAMPLES FROM TRAINING DATA]"]
    for rank, ex in enumerate(retrieved, start=1):
        lines.append(_format_retrieved_example(rank, ex, max_chars_per_example))
    return "\n".join(lines)


def build_user_message(
    instance: RelationInstance,
    *,
    variant: str,
    options: UserMessageOptions | None = None,
    retrieved_examples: list["RetrievedExample"] | None = None,
) -> str:
    """Build the user message per spec §4.2 (shared template).

    When ``retrieved_examples`` is provided, a ``[SIMILAR EXAMPLES FROM TRAINING DATA]``
    block is inserted before the article text so the model sees the
    annotated neighbours alongside the new article.
    """
    if variant not in PROMPT_VARIANTS:
        raise ValueError(f"variant must be one of {PROMPT_VARIANTS}, got {variant!r}")
    options = options or UserMessageOptions()

    text_with_markers = insert_entity_markers(instance, field=options.text_field)
    person = (instance.pers_mentions_list or [""])[0]
    location = (instance.loc_mentions_list or [""])[0]
    person_qid = instance.pers_wikidata_QID or "—"
    location_qid = instance.loc_wikidata_QID or "—"

    sections: list[str] = []

    if retrieved_examples:
        sections.append(
            format_retrieved_examples_block(
                retrieved_examples,
                max_chars_per_example=options.retrieved_excerpt_chars,
            )
        )
        sections.append("")

    sections.extend(
        [
            f"Publication date: {instance.date}",
            f"Language: {instance.language}",
            "",
            "[ENTITY PAIR]",
            f"Person: '{person}' (QID: {person_qid})",
            f"Location: '{location}' (QID: {location_qid})",
            "",
            "[ARTICLE TEXT]",
            f'"{text_with_markers}"',
        ]
    )

    if options.include_wikidata:
        person_block = _format_wikidata_summary(instance.person_context)
        location_block = _format_wikidata_summary(instance.location_context)
        relations = instance.known_person_location_relations or None
        # Drop sub-lines whose content is empty. If every sub-line is empty
        # the block itself is omitted (avoids feeding the model "Person: (none)
        # / Location: (none)" — pure noise that distracts small models).
        ctx_lines = []
        if person_block:
            ctx_lines.append(f"Person: {person_block}")
        if location_block:
            ctx_lines.append(f"Location: {location_block}")
        if relations:
            ctx_lines.append(f"Known person-location links: {relations}")
        if ctx_lines:
            sections.append("")
            sections.append("[ENTITY CONTEXT]")
            sections.extend(ctx_lines)
    if options.include_temporal:
        temporal_line = _format_temporal_block(instance)
        if temporal_line:
            sections.extend(["", "[TEMPORAL SIGNALS]", temporal_line])
    if options.include_temporal_interpretation:
        # Placeholder block — populated by the agentic pipeline once we
        # add a HeidelTime / temporal-resolver stage.
        sections.extend(["", "[TEMPORAL INTERPRETATION]", "(not provided in zero-shot baseline)"])

    if options.domain_rules:
        rules = options.domain_rules.strip()
        if rules:
            sections.extend(["", "[DOMAIN RULES (high-precision triggers)]", rules])

    sections.extend(["", _VARIANT_INSTRUCTIONS[variant]])
    return "\n".join(sections)
