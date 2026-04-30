"""Parsers for the spec's flat-text LLM output formats.

The spec (HIPE-2026 Prompting & MASK Spec §2-§5) uses a single literal output
line per variant:

    P-A / P-B  : ``<LABEL> | confidence=<X.XX>``
    P-AB / P-R : ``at=<LABEL> isAt=<LABEL> | conf_at=<X.XX> conf_isAt=<X.XX>``

P-R additionally prepends a 3-5 line ``ANALYSIS`` block. We extract the
classification line by scanning bottom-up.

The parser uses a layered strategy:

1. **Strict regex** matches the canonical format exactly.
2. **Loose regex** drops the confidence requirement and tolerates filler
   text between the label fragments (e.g. when the model leaks reasoning).
3. **Fuzzy fallback** handles the long tail of model misbehaviour:
   truncated outputs (``PRO`` / ``T``), label paraphrases (``yes`` /
   ``no`` / ``maybe`` / ``possibly``), template-parroting (``LABEL``),
   and free-form answers (``Label: TRUE``, ``The answer is FALSE``).

Invalid labels fall through to the official ``null -> FALSE`` rule
applied at evaluation time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from hipe.evaluation.metrics import AT_LABELS, ISAT_LABELS

_AT_RE = re.compile(
    r"at\s*=\s*(TRUE|FALSE|PROBABLE)\s+isAt\s*=\s*(TRUE|FALSE)\s*\|\s*"
    r"conf_at\s*=\s*([\d.]+)\s+conf_isAt\s*=\s*([\d.]+)",
    re.IGNORECASE,
)

_AT_LOOSE_RE = re.compile(
    r"at\s*=\s*(TRUE|FALSE|PROBABLE)[^\n]*?isAt\s*=\s*(TRUE|FALSE)",
    re.IGNORECASE,
)

_SINGLE_RE = re.compile(
    r"\b(TRUE|FALSE|PROBABLE)\b\s*\|\s*confidence\s*=\s*([\d.]+)",
    re.IGNORECASE,
)

_SINGLE_LOOSE_RE = re.compile(r"\b(TRUE|FALSE|PROBABLE)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Fuzzy fallback patterns
# ---------------------------------------------------------------------------

# Word-level synonyms / paraphrases the model may emit instead of the canonical
# label. Order matters within each list (longest / most specific first).
_AT_SYNONYMS: tuple[tuple[str, str], ...] = (
    # PROBABLE first — its keyword cluster overlaps with TRUE phrases (e.g.
    # "probably true"); we want the more specific one to win.
    (r"\bprobable\b", "PROBABLE"),
    (r"\bpossibly\b", "PROBABLE"),
    (r"\buncertain\b", "PROBABLE"),
    (r"\bmaybe\b", "PROBABLE"),
    (r"\bperhaps\b", "PROBABLE"),
    (r"\bplausible\b", "PROBABLE"),
    (r"\blikely\b", "PROBABLE"),
    (r"\btrue\b", "TRUE"),
    (r"\byes\b", "TRUE"),
    (r"\baffirmative\b", "TRUE"),
    (r"\bcorrect\b", "TRUE"),
    (r"\bfalse\b", "FALSE"),
    (r"\bno\b", "FALSE"),
    (r"\bnone\b", "FALSE"),
    (r"\bnegative\b", "FALSE"),
    (r"\bincorrect\b", "FALSE"),
)

_ISAT_SYNONYMS: tuple[tuple[str, str], ...] = (
    (r"\btrue\b", "TRUE"),
    (r"\byes\b", "TRUE"),
    (r"\bpresent\b", "TRUE"),
    (r"\bcurrently\b", "TRUE"),
    (r"\bfalse\b", "FALSE"),
    (r"\bno\b", "FALSE"),
    (r"\bnot\s+present\b", "FALSE"),
    (r"\babsent\b", "FALSE"),
)

# Truncations: when the model is cut off mid-label by max_tokens.
# Match prefixes only at the start of a token (anchored by a non-letter or
# the start of string).
_AT_PREFIXES: tuple[tuple[str, str], ...] = (
    (r"(?:^|\W)pro(?:b(?:a(?:b(?:l(?:e)?)?)?)?)?(?=$|\W|\d)", "PROBABLE"),
    (r"(?:^|\W)tr(?:u(?:e)?)?(?=$|\W|\d)", "TRUE"),
    (r"(?:^|\W)fa(?:l(?:s(?:e)?)?)?(?=$|\W|\d)", "FALSE"),
)

_ISAT_PREFIXES: tuple[tuple[str, str], ...] = (
    (r"(?:^|\W)tr(?:u(?:e)?)?(?=$|\W|\d)", "TRUE"),
    (r"(?:^|\W)fa(?:l(?:s(?:e)?)?)?(?=$|\W|\d)", "FALSE"),
)

_LABEL_PARROT_RE = re.compile(r"\bLABEL\b", re.IGNORECASE)

# Confidence patterns for fuzzy extraction. Try canonical first, then drift.
_CONF_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"confidence\s*[=:]\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"conf\s*[=:]\s*([\d.]+)", re.IGNORECASE),
    re.compile(r"([\d.]+)\s*(?:confidence|conf)", re.IGNORECASE),
)


def _strip_label_parrots(text: str) -> str:
    """Remove instances of the literal placeholder word 'LABEL' so the
    fuzzy matcher doesn't latch onto template-parroting (the most common
    Llama-8B failure on P-A / P-B with the verbatim spec prompts)."""
    return _LABEL_PARROT_RE.sub("", text)


def _fuzzy_label_search(
    text: str,
    *,
    allowed: tuple[str, ...],
    synonyms: tuple[tuple[str, str], ...],
    prefixes: tuple[tuple[str, str], ...],
) -> str | None:
    """Find the earliest-occurring valid label in *text*.

    Tries (in order): exact label tokens, synonym words, label prefixes
    (truncated outputs). Picks the earliest match across all categories so
    short-circuit reasoning bleed before the actual label doesn't override
    a clean later label.
    """
    text = _strip_label_parrots(text)

    candidates: list[tuple[int, str]] = []  # (position, normalized label)

    # Exact label tokens
    for label in allowed:
        m = re.search(rf"\b{re.escape(label)}\b", text, re.IGNORECASE)
        if m:
            candidates.append((m.start(), label))

    # Synonyms
    for pattern, target in synonyms:
        if target not in allowed:
            continue
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            candidates.append((m.start(), target))

    # Prefixes (truncated tokens). Lower priority — only used if no exact /
    # synonym match was found, because a prefix can spuriously match inside
    # longer words.
    if not candidates:
        for pattern, target in prefixes:
            if target not in allowed:
                continue
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                candidates.append((m.start(), target))

    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


def _fuzzy_confidence(text: str) -> float | None:
    for pattern in _CONF_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if 0.0 <= v <= 1.0:
            return v
    return None


@dataclass(slots=True)
class ParseResult:
    at: str | None
    isAt: str | None
    conf_at: float | None
    conf_isAt: float | None
    reasoning: str | None
    parse_status: str  # "ok" | "partial" | "fail"
    raw_text: str

    def as_prediction(self) -> dict[str, object]:
        """Shape expected by ``run_ablation_experiment``'s predict_fn."""
        return {
            "at": self.at,
            "isAt": self.isAt,
            "at_explanation": self.reasoning,
            "isAt_explanation": self.reasoning,
            "raw_output": self.raw_text,
            "conf_at": self.conf_at,
            "conf_isAt": self.conf_isAt,
            "parse_status": self.parse_status,
        }


def _normalise(label: str | None, allowed: tuple[str, ...]) -> str | None:
    if label is None:
        return None
    upper = label.strip().upper()
    return upper if upper in allowed else None


def _extract_reasoning(text: str) -> str | None:
    """Pull the analysis block out of a P-R response (everything before the
    classification line). Returns None when no analysis block is present.
    """
    if not text:
        return None
    match = _AT_RE.search(text)
    if not match:
        return None
    head = text[: match.start()].strip()
    return head or None


def parse_output(text: str, variant: str) -> ParseResult:
    """Dispatch to the variant-appropriate parser."""
    if variant in {"AB", "R"}:
        return _parse_combined(text, variant=variant)
    if variant == "A":
        return _parse_single(text, label_set=AT_LABELS, target="at", variant=variant)
    if variant == "B":
        return _parse_single(text, label_set=ISAT_LABELS, target="isAt", variant=variant)
    raise ValueError(f"Unknown variant: {variant!r}")


def _parse_combined(text: str, *, variant: str) -> ParseResult:
    raw = (text or "").strip()
    reasoning = _extract_reasoning(raw) if variant == "R" else None

    # Tier 1: strict — exact format with confidences.
    m = _AT_RE.search(raw)
    if m:
        at = _normalise(m.group(1), AT_LABELS)
        isAt = _normalise(m.group(2), ISAT_LABELS)
        try:
            conf_at = float(m.group(3))
            conf_isAt = float(m.group(4))
        except ValueError:
            conf_at = conf_isAt = None
        if at and isAt:
            return ParseResult(at, isAt, conf_at, conf_isAt, reasoning, "ok", raw)

    # Tier 2: loose — match `at=X ... isAt=Y` allowing filler between them.
    m_loose = _AT_LOOSE_RE.search(raw)
    if m_loose:
        at = _normalise(m_loose.group(1), AT_LABELS)
        isAt = _normalise(m_loose.group(2), ISAT_LABELS)
        if at and isAt:
            conf_at = _fuzzy_confidence(raw)
            return ParseResult(at, isAt, conf_at, None, reasoning, "partial", raw)
        if at or isAt:
            return ParseResult(at, isAt, None, None, reasoning, "partial", raw)

    # Tier 3: fuzzy — split the text into "at side" and "isAt side" using
    # whichever cue word appears first, then run the fuzzy label search on
    # each half.
    at_label, isAt_label, fuzzy_status = _parse_combined_fuzzy(raw)
    if at_label or isAt_label:
        return ParseResult(at_label, isAt_label, None, None, reasoning, fuzzy_status, raw)

    return ParseResult(None, None, None, None, reasoning, "fail", raw)


def _split_combined_text(raw: str) -> tuple[str, str]:
    """Split ``raw`` into (at_segment, isAt_segment) by locating cue words.

    Falls back to splitting at the midpoint when no cue is found, which is
    rare but keeps the fuzzy fallback strictly fail-safe.
    """
    # Look for explicit cue words first.
    at_match = re.search(r"\bat\s*[:=]?", raw, re.IGNORECASE)
    isAt_match = re.search(r"\bis\s*[_-]?\s*at\b\s*[:=]?", raw, re.IGNORECASE)

    if at_match and isAt_match:
        if at_match.start() < isAt_match.start():
            at_seg = raw[at_match.end() : isAt_match.start()]
            isAt_seg = raw[isAt_match.end() :]
        else:
            isAt_seg = raw[isAt_match.end() : at_match.start()]
            at_seg = raw[at_match.end() :]
        return at_seg, isAt_seg

    # Only one cue: assume the rest of the text belongs to that side, the
    # other side gets the segment before the cue.
    if at_match:
        return raw[at_match.end() :], raw[: at_match.start()]
    if isAt_match:
        return raw[: isAt_match.start()], raw[isAt_match.end() :]

    # No cue at all — fall back to splitting at the midpoint. This is a
    # last-ditch attempt; the caller will report this as a fuzzy / partial
    # parse so the result is auditable.
    mid = len(raw) // 2
    return raw[:mid], raw[mid:]


def _parse_combined_fuzzy(raw: str) -> tuple[str | None, str | None, str]:
    """Fuzzy fallback for combined (at + isAt) parsing.

    Returns (at_label, isAt_label, status) where status is ``"partial"`` if
    either side resolved or ``"fail"`` if neither did.
    """
    at_seg, isAt_seg = _split_combined_text(raw)
    at_label = _fuzzy_label_search(
        at_seg, allowed=AT_LABELS, synonyms=_AT_SYNONYMS, prefixes=_AT_PREFIXES
    )
    isAt_label = _fuzzy_label_search(
        isAt_seg, allowed=ISAT_LABELS, synonyms=_ISAT_SYNONYMS, prefixes=_ISAT_PREFIXES
    )
    if at_label or isAt_label:
        return at_label, isAt_label, "partial"
    return None, None, "fail"


def _parse_single(text: str, *, label_set: tuple[str, ...], target: str, variant: str) -> ParseResult:
    raw = (text or "").strip()

    # Tier 1: strict — `LABEL | confidence=X.XX`.
    m = _SINGLE_RE.search(raw)
    if m:
        label = _normalise(m.group(1), label_set)
        try:
            conf = float(m.group(2))
        except ValueError:
            conf = None
        if label:
            return _build_single(label, conf, target, "ok", raw)

    # Tier 2: loose — any whole-word label match, with fuzzy confidence.
    m_loose = _SINGLE_LOOSE_RE.search(raw)
    if m_loose:
        label = _normalise(m_loose.group(1), label_set)
        if label:
            conf = _fuzzy_confidence(raw)
            return _build_single(label, conf, target, "partial", raw)

    # Tier 3: fuzzy — synonyms + truncations, after stripping any leaked
    # template-parrot ``LABEL`` tokens.
    if target == "at":
        synonyms, prefixes = _AT_SYNONYMS, _AT_PREFIXES
    else:
        synonyms, prefixes = _ISAT_SYNONYMS, _ISAT_PREFIXES
    fuzzy = _fuzzy_label_search(raw, allowed=label_set, synonyms=synonyms, prefixes=prefixes)
    if fuzzy:
        conf = _fuzzy_confidence(raw)
        return _build_single(fuzzy, conf, target, "partial", raw)

    return ParseResult(None, None, None, None, None, "fail", raw)


def _build_single(
    label: str,
    conf: float | None,
    target: str,
    status: str,
    raw: str,
) -> ParseResult:
    return ParseResult(
        at=label if target == "at" else None,
        isAt=label if target == "isAt" else None,
        conf_at=conf if target == "at" else None,
        conf_isAt=conf if target == "isAt" else None,
        reasoning=None,
        parse_status=status,
        raw_text=raw,
    )
