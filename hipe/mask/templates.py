"""MASK template builders (M1–M5 from HIPE-2026 Prompting & MASK Spec).

All templates use entity markers ``[E1]/[/E1]`` (person), ``[E2]/[/E2]``
(location). The MASK position is where the model will predict relation
semantics; downstream code reads the hidden state at that position.

M2 is the recommended default — it places the context first then asks
the model to fill in the relationship via a question-style prompt, which
gives the MASK position rich attention over the marked entity spans.
"""

from __future__ import annotations

from hipe.data import RelationInstance

PERS_OPEN, PERS_CLOSE = "[E1]", "[/E1]"
LOC_OPEN, LOC_CLOSE = "[E2]", "[/E2]"

ENTITY_MARKERS = [PERS_OPEN, PERS_CLOSE, LOC_OPEN, LOC_CLOSE]

DEFAULT_TEMPLATE = "M2"


def _wrap_first_match(text: str, mentions: list[str], open_tag: str, close_tag: str) -> tuple[str, bool]:
    """Wrap the earliest occurrence of any mention in *text* with marker tags.

    Mirrors the retriever's marker logic but kept local to avoid a cross-module
    dependency: the MASK module may evolve different marker semantics later.
    """
    if not mentions or not text:
        return text, False
    lowered = text.lower()
    best: tuple[int, int, str] | None = None
    for m in sorted({m for m in mentions if m}, key=len, reverse=True):
        idx = lowered.find(m.lower())
        if idx == -1:
            continue
        if best is None or idx < best[0]:
            best = (idx, idx + len(m), text[idx : idx + len(m)])
    if best is None:
        return text, False
    s, e, matched = best
    return f"{text[:s]}{open_tag} {matched} {close_tag}{text[e:]}", True


def locate_entity_spans(instance: RelationInstance, *, field: str = "context") -> tuple[str, bool, bool]:
    """Insert ``[E1]/[/E1]/[E2]/[/E2]`` into the chosen field.

    Returns (text_with_markers, pers_inline, loc_inline). When a span isn't
    found inline, the text is prefixed with a synthetic ``[E1] mention [/E1]``
    or ``[E2] mention [/E2]`` block so the marker tokens are still present.
    """
    base = instance.context if field == "context" else instance.text
    base = base or ""
    pers = instance.pers_mentions_list or []
    loc = instance.loc_mentions_list or []
    base, pers_in = _wrap_first_match(base, pers, PERS_OPEN, PERS_CLOSE)
    base, loc_in = _wrap_first_match(base, loc, LOC_OPEN, LOC_CLOSE)
    if not pers_in and pers:
        base = f"{PERS_OPEN} {pers[0]} {PERS_CLOSE} . " + base
    if not loc_in and loc:
        base = f"{LOC_OPEN} {loc[0]} {LOC_CLOSE} . " + base
    return base, pers_in, loc_in


def build_template(
    instance: RelationInstance,
    *,
    template: str = DEFAULT_TEMPLATE,
    field: str = "context",
    mask_token: str = "[MASK]",
) -> str:
    """Render an MLM template for a given instance.

    Parameters
    ----------
    instance : RelationInstance
    template : {"M1", "M2", "M3", "M4", "M5"}
        See HIPE-2026 Prompting & MASK Spec §M.
    field : {"context", "text"}
        Which text field to embed (default ``context``, fits 512 tokens).
    mask_token : str
        Tokenizer's mask token; pass through ``tokenizer.mask_token``.

    Returns
    -------
    str
        Rendered template string. CLS/SEP tokens are NOT prepended/appended —
        the tokenizer adds them when called with ``add_special_tokens=True``.
    """
    pers = (instance.pers_mentions_list or [""])[0]
    loc = (instance.loc_mentions_list or [""])[0]
    ctx_marked, _, _ = locate_entity_spans(instance, field=field)

    if template == "M1":
        # Minimal: entity-pair only, no surrounding context.
        return f"{PERS_OPEN} {pers} {PERS_CLOSE} {mask_token} {LOC_OPEN} {loc} {LOC_CLOSE} ."
    if template == "M2":
        # Recommended: context-enriched, mask in question form.
        return (
            f"{ctx_marked} "
            f"The relationship between {PERS_OPEN} and {LOC_OPEN} is {mask_token} ."
        )
    if template == "M3":
        # Temporal: prepend publication date, frame mask in present tense.
        date = instance.date or "unknown"
        return (
            f"Published: {date} . {ctx_marked} "
            f"At this time, {PERS_OPEN} is {mask_token} {LOC_OPEN} ."
        )
    if template == "M4":
        # Dual-MASK: separate slots for `at` and `isAt` semantics.
        date = instance.date or "unknown"
        return (
            f"{ctx_marked} "
            f"In general, {PERS_OPEN} is {mask_token} associated with {LOC_OPEN} . "
            f"Around {date}, {PERS_OPEN} is {mask_token} present at {LOC_OPEN} ."
        )
    if template == "M5":
        # Three consecutive masks for richer relation embedding.
        return (
            f"{ctx_marked} "
            f"{PERS_OPEN} {mask_token} {mask_token} {mask_token} {LOC_OPEN} ."
        )
    raise ValueError(f"Unknown template id: {template!r}")
