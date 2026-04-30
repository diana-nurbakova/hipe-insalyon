"""Tests for hipe.llm.justification — JSON parser tolerance.

The agent runner itself requires a live LLM, so we don't exercise the round
trip here. The parser is the part that runs in the hot path on noisy model
outputs and needs to be defensively tested.
"""

from __future__ import annotations

from hipe.llm.justification import (
    NO_TEMPORAL_FLAG,
    JustificationOutput,
    parse_justification,
)


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


CANONICAL_JSON = """\
{
  "evidence_spans": [
    {"text": "born in Paris", "supports": "at", "explanation": "direct biographical statement"}
  ],
  "wikidata_corroboration": {"supports": true, "details": "P19=Paris matches"},
  "temporal_assessment": {
    "explicit_dates_found": ["1879-03-14"],
    "within_isat_window": false,
    "explanation": "biographical, not contemporaneous"
  },
  "evidence_strength": "strong",
  "narrative_justification": "The article confirms Paris as a known birthplace.",
  "flags": []
}
"""


def test_parse_canonical_json():
    out = parse_justification(CANONICAL_JSON)
    assert isinstance(out, JustificationOutput)
    assert out.parse_status == "ok"
    assert out.evidence_strength == "strong"
    assert out.evidence_spans[0]["supports"] == "at"
    assert out.wikidata_corroboration["supports"] is True
    assert out.temporal_assessment["within_isat_window"] is False


def test_parse_with_code_fence():
    """Models often wrap JSON in ```json fences — must still parse."""
    fenced = "Sure, here's the JSON:\n```json\n" + CANONICAL_JSON + "\n```\nLet me know if you need more."
    out = parse_justification(fenced)
    assert out.parse_status == "ok"
    assert out.evidence_strength == "strong"


def test_parse_with_trailing_commentary():
    """JSON followed by chatty text — the parser must extract a balanced object."""
    raw = CANONICAL_JSON + "\n\nI hope this helps!"
    out = parse_justification(raw)
    assert out.parse_status == "ok"


# ---------------------------------------------------------------------------
# Coercion / leniency
# ---------------------------------------------------------------------------


def test_supports_string_coercion():
    """`'true'` / `'false'` strings get coerced to booleans for wikidata.supports."""
    raw = """{
        "evidence_spans": [{"text": "x", "supports": "at", "explanation": "y"}],
        "wikidata_corroboration": {"supports": "true", "details": ""},
        "temporal_assessment": {"explicit_dates_found": [], "within_isat_window": "uncertain", "explanation": ""},
        "evidence_strength": "moderate",
        "narrative_justification": "ok",
        "flags": []
    }"""
    out = parse_justification(raw)
    assert out.wikidata_corroboration["supports"] is True
    assert out.temporal_assessment["within_isat_window"] == "uncertain"


def test_invalid_evidence_strength_drops_to_none():
    raw = """{
        "evidence_spans": [],
        "wikidata_corroboration": {"supports": null, "details": ""},
        "temporal_assessment": {"explicit_dates_found": [], "within_isat_window": null, "explanation": ""},
        "evidence_strength": "extremely strong",
        "narrative_justification": "x",
        "flags": []
    }"""
    out = parse_justification(raw)
    assert out.evidence_strength is None
    assert out.parse_status == "partial"


def test_unknown_supports_label_falls_back_to_neither():
    raw = """{
        "evidence_spans": [{"text": "span", "supports": "kinda", "explanation": ""}],
        "wikidata_corroboration": {"supports": null, "details": ""},
        "temporal_assessment": {"explicit_dates_found": [], "within_isat_window": null, "explanation": ""},
        "evidence_strength": "weak",
        "narrative_justification": "x",
        "flags": ["%s"]
    }""" % NO_TEMPORAL_FLAG
    out = parse_justification(raw)
    assert out.evidence_spans[0]["supports"] == "neither"
    assert NO_TEMPORAL_FLAG in out.flags


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_no_json_in_text_returns_fail():
    out = parse_justification("Sorry, I can't help with that.")
    assert out.parse_status == "fail"
    assert out.evidence_strength is None


def test_malformed_json_returns_fail():
    """Unclosed brace — the bracket walker returns no candidate."""
    out = parse_justification('{"evidence_spans": [')
    assert out.parse_status == "fail"


def test_empty_string_returns_fail():
    out = parse_justification("")
    assert out.parse_status == "fail"


def test_json_array_top_level_extracts_first_object():
    """A bare array isn't the spec'd shape, but if it wraps a single object
    we extract it (with a 'partial' status because key fields are missing)."""
    out = parse_justification('[{"evidence_strength": "weak"}]')
    assert out.parse_status == "partial"
    assert out.evidence_strength == "weak"
