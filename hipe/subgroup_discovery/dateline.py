"""Dateline detection for HIPE-2026 (Dateline & QA Specs §2).

Historical newspaper articles open and close with *datelines* — a place name
plus a date that indicates where the report was filed from rather than where
the people mentioned in the body are located. Cross-config disagreement
analysis (``logs/final/disagreement``) shows that 4+ of the 10 universally
wrong ``at`` instances are dateline confusions: the location appears in close
proximity to the person but is purely a reporting-origin marker.

The module exposes a 5-d binary feature block built with regex only — no
NLP, no GPU. The strongest signal, ``location_dateline_only``, fires when
the location appears exclusively in a dateline region and never in the
article body.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Final

import numpy as np

from hipe.data import RelationInstance


DATELINE_FEATURE_NAMES: Final[tuple[str, ...]] = (
    "location_is_dateline",
    "location_is_opening_dateline",
    "location_is_closing_dateline",
    "location_is_mid_dateline",
    "location_dateline_only",
)


# ---------------------------------------------------------------------------
# Month vocabularies (FR / DE / EN / LB)
# ---------------------------------------------------------------------------

_MONTHS: dict[str, str] = {
    "de": (
        r"(?:Jan(?:uar)?|Feb(?:ruar)?|Mär(?:z)?|Apr(?:il)?|Mai|Jun(?:i)?|"
        r"Jul(?:i)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Okt(?:ober)?|"
        r"Nov(?:ember)?|Dez(?:ember)?)"
    ),
    "fr": (
        r"(?:janv(?:ier)?|févr(?:ier)?|mars|avr(?:il)?|mai|juin|juil(?:let)?|"
        r"août|sept(?:embre)?|oct(?:obre)?|nov(?:embre)?|déc(?:embre)?)"
    ),
    "en": (
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)"
    ),
    "lb": (
        r"(?:Jan(?:uar)?|Feb(?:ruar)?|Mäe(?:rz)?|Abr(?:ëll)?|Mee|Jun(?:i)?|"
        r"Jul(?:i)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Okt(?:ober)?|"
        r"Nov(?:ember)?|Dez(?:ember)?)"
    ),
}

_ALL_MONTHS: Final[str] = "|".join(_MONTHS.values())

# Date variants seen in 19th–20th century newspaper datelines.
_DATE_PATTERN: Final[str] = (
    r"(?:"
    r"\d{1,2}\.?\s*(?:" + _ALL_MONTHS + r")"            # "14. Oktober" / "12 mars"
    r"|(?:" + _ALL_MONTHS + r")\.?\s*\d{1,2}"           # "Dec. 31" / "octobre 12"
    r"|(?:le\s+|den\s+|am\s+)?\d{1,2}\.?\s*(?:" + _ALL_MONTHS + r")"
    r"|\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}"                 # "14.10.1848"
    r")"
)

# How many characters at the head/tail of ``text`` are considered the
# dateline region for the "ALSO appears in prose" check (§2.2).
_DATELINE_REGION_CHARS: Final[int] = 100


# Optional year suffix that newspaper datelines often append after the month
# ("Paris, le 22 avril 1918" / "Berlin, den 15. Oktober 1848").
_YEAR_TAIL: Final[str] = r"(?:\s*,?\s*\d{2,4})?"


def _build_opening_patterns(loc_esc: str) -> tuple[str, ...]:
    return (
        # "Berlin, 14. Oktober." / "Berlin, 14. Okt. —"
        rf"^[\s\n]*{loc_esc}\s*[,.]\s*{_DATE_PATTERN}{_YEAR_TAIL}",
        # "LONDON, Dec. 31." (alternation in _DATE_PATTERN handles US order)
        rf"^[\s\n]*{loc_esc}\s*[,.]\s*{_DATE_PATTERN}{_YEAR_TAIL}",
        # Just "Berlin." at start (common short dateline)
        rf"^[\s\n]*{loc_esc}\s*\.\s",
    )


def _build_closing_patterns(loc_esc: str) -> tuple[str, ...]:
    return (
        rf"{loc_esc}\s*[,.]\s*(?:den\s+|le\s+)?{_DATE_PATTERN}{_YEAR_TAIL}[\s.]*$",
        rf"\n\s*{loc_esc}\s*[,.]\s*{_DATE_PATTERN}{_YEAR_TAIL}[\s.]*$",
        rf"{_DATE_PATTERN}{_YEAR_TAIL}\s*[,.]\s*{loc_esc}[\s.]*$",
    )


def _build_mid_patterns(loc_esc: str) -> tuple[str, ...]:
    # Section breaks in OCR'd 19th-century newspapers often collapse to
    # ``. `` (period + space) instead of a real newline, so we accept either
    # boundary. The patterns are still anchored at a sentence boundary (so a
    # body mention like "in Frankfurt zu" cannot fire).
    boundary = r"(?:\n\s*|\.\s+)"
    return (
        # "...prior text. Frankfurt. Am 14. Oktober" or with explicit newline
        rf"{boundary}{loc_esc}\s*[,.]\s*(?:Am\s+|Le\s+|On\s+)?{_DATE_PATTERN}",
        # "Ausland. Deutschland. Einer der..." — section-header chain, no date
        # required. Anchored on a capital letter following the trailing period
        # so we don't trigger on mid-sentence "X. y" lowercase continuations.
        rf"{boundary}{loc_esc}\s*\.\s+[A-ZÄÖÜÉÈÀÂÔÛÇŞ]",
        # Newline-bounded "X." (conservative, covers cases where the OCR did
        # preserve hard line breaks).
        rf"(?<!\A)\n\s*{loc_esc}\s*\.\s*\n",
    )


_RE_FLAGS = re.IGNORECASE | re.MULTILINE


def detect_dateline(inst: RelationInstance) -> dict[str, float]:
    """Detect whether the target location is a dateline marker.

    Returns the 5-d feature dict described in §2.3. All values are 0.0/1.0.
    """
    text = inst.text or ""
    locations = [lm for lm in (inst.loc_mentions_list or []) if lm]

    is_opening = False
    is_closing = False
    is_mid = False

    if text and locations:
        for loc in locations:
            loc_esc = re.escape(loc)
            if not is_opening:
                for pat in _build_opening_patterns(loc_esc):
                    if re.search(pat, text, _RE_FLAGS):
                        is_opening = True
                        break
            if not is_closing:
                for pat in _build_closing_patterns(loc_esc):
                    if re.search(pat, text, _RE_FLAGS):
                        is_closing = True
                        break
            if not is_mid:
                for pat in _build_mid_patterns(loc_esc):
                    if re.search(pat, text, _RE_FLAGS):
                        is_mid = True
                        break
            if is_opening and is_closing and is_mid:
                break

    is_any = is_opening or is_closing or is_mid

    # Does the location ALSO appear in the prose region (i.e. outside the
    # dateline head/tail)? If so, the dateline_only signal weakens.
    location_in_prose = False
    if is_any and len(text) > 2 * _DATELINE_REGION_CHARS:
        prose = text[_DATELINE_REGION_CHARS:-_DATELINE_REGION_CHARS]
        for loc in locations:
            if loc and loc in prose:
                location_in_prose = True
                break

    return {
        "location_is_dateline": float(is_any),
        "location_is_opening_dateline": float(is_opening),
        "location_is_closing_dateline": float(is_closing),
        "location_is_mid_dateline": float(is_mid),
        "location_dateline_only": float(is_any and not location_in_prose),
    }


def dateline_matrix(instances: Iterable[RelationInstance]) -> np.ndarray:
    """Stack ``detect_dateline`` over a list of instances → ``(N, 5)``."""
    rows = [detect_dateline(i) for i in instances]
    return np.array(
        [[r[name] for name in DATELINE_FEATURE_NAMES] for r in rows],
        dtype=np.float32,
    )


__all__ = [
    "DATELINE_FEATURE_NAMES",
    "detect_dateline",
    "dateline_matrix",
]
