"""Tests for hipe.llm.validator: consistency checks + escalation logic.

The validator is pure-Python (no LLM call) so we exercise it directly with
hand-crafted dicts that mirror the ClassifierOutput / JustificationOutput
shapes from Spec v0.7 §4.4 / §5.5.
"""

from __future__ import annotations

import pytest

from hipe.llm.validator import (
    NO_TEMPORAL_FLAG,
    ValidatorConfig,
    run_checks,
    should_escalate,
    validate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def cls(at="TRUE", isAt="FALSE", conf_at=0.9, conf_isAt=0.9, reasoning=""):
    return {"at": at, "isAt": isAt, "conf_at": conf_at,
            "conf_isAt": conf_isAt, "reasoning": reasoning}


def jus(strength="strong", flags=None, wd_supports=None, within_window=None):
    return {
        "evidence_strength": strength,
        "flags": list(flags or []),
        "wikidata_corroboration": {"supports": wd_supports, "details": ""},
        "temporal_assessment": {
            "explicit_dates_found": [],
            "within_isat_window": within_window,
            "explanation": "",
        },
    }


# ---------------------------------------------------------------------------
# Hard escalation triggers (§6.3)
# ---------------------------------------------------------------------------


def test_cross_label_coherence_escalates():
    """isAt=TRUE with at=FALSE must always escalate (logical impossibility)."""
    c = cls(at="FALSE", isAt="TRUE")
    out = validate(c, jus())
    assert out.escalated is True
    assert out.accepted is False
    assert "cross_label_coherence" in out.checks_failed
    assert "logically impossible" in out.escalation_reason


def test_contradictory_evidence_escalates():
    out = validate(cls(), jus(strength="contradictory"))
    assert out.escalated is True
    assert "evidence_alignment" in out.checks_failed


def test_hard_trigger_takes_priority_over_soft():
    """Two soft + one hard → reason cites the hard trigger first."""
    c = cls(at="FALSE", isAt="TRUE", conf_at=0.4, conf_isAt=0.3)
    j = jus(strength="contradictory")
    out = validate(c, j)
    assert out.escalated is True
    # Hard reason wins.
    assert "logically impossible" in out.escalation_reason


# ---------------------------------------------------------------------------
# Soft escalation (≥2 soft flags → escalate)
# ---------------------------------------------------------------------------


def test_one_soft_flag_does_not_escalate():
    c = cls(conf_at=0.5)  # one soft (low at confidence)
    out = validate(c, jus())
    assert out.escalated is False
    assert out.accepted is True


def test_two_soft_flags_escalate():
    c = cls(conf_at=0.5, conf_isAt=0.4)  # two soft
    out = validate(c, jus())
    assert out.escalated is True
    assert "soft:" in out.escalation_reason


def test_no_temporal_flag_counts_as_soft():
    c = cls(isAt="TRUE", conf_isAt=0.5)
    j = jus(flags=[NO_TEMPORAL_FLAG])
    out = validate(c, j)
    # isAt=TRUE + no temporal anchor (both temporal_logic and the matching
    # confidence soft) → ≥2 soft flags.
    assert out.escalated is True
    assert any("temporal anchor" in s.lower() for s in out.soft_flags)


def test_wikidata_unsupported_counts_as_soft():
    c = cls(conf_at=0.5)
    j = jus(wd_supports=False)
    out = validate(c, j)
    assert out.escalated is True
    assert any("wikidata" in s.lower() for s in out.soft_flags)


def test_weak_evidence_strength_is_soft():
    c = cls(conf_at=0.5)
    j = jus(strength="weak")
    out = validate(c, j)
    assert out.escalated is True
    assert any("weak" in s.lower() for s in out.soft_flags)


# ---------------------------------------------------------------------------
# Hard-only profile (§6.5)
# ---------------------------------------------------------------------------


def test_hard_only_ignores_soft_flags():
    """Efficiency profile: low confidence and weak evidence shouldn't escalate."""
    c = cls(conf_at=0.4, conf_isAt=0.3)
    j = jus(strength="weak", wd_supports=False, flags=[NO_TEMPORAL_FLAG])
    out = validate(c, j, config=ValidatorConfig(hard_only=True))
    assert out.escalated is False
    assert out.soft_flags == []


def test_hard_only_still_catches_logical_contradiction():
    c = cls(at="FALSE", isAt="TRUE")
    out = validate(c, jus(), config=ValidatorConfig(hard_only=True))
    assert out.escalated is True
    assert "cross_label_coherence" in out.checks_failed


def test_disabled_escalation_logs_but_does_not_escalate():
    """When enable_escalation=False, the validator records flags but
    accepted=True so the orchestrator doesn't kick off Tier 3."""
    c = cls(at="FALSE", isAt="TRUE")
    out = validate(c, jus(), config=ValidatorConfig(enable_escalation=False))
    assert out.escalated is False
    assert out.accepted is True
    assert "cross_label_coherence" in out.checks_failed


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


def test_internal_consistency_soft_flag():
    """Reasoning saying 'born in' but at=FALSE → soft flag."""
    c = cls(at="FALSE", reasoning="The article says he was born in Paris.")
    passed, failed, hard, soft = run_checks(c, jus())
    assert "internal_consistency" in failed
    assert any("association cue" in s for s in soft)


def test_should_escalate_matches_validate():
    """The thin should_escalate helper should agree with validate()."""
    c = cls(at="FALSE", isAt="TRUE")
    e, _ = should_escalate(c, jus())
    assert e is True
    out = validate(c, jus())
    assert out.escalated == e


def test_handles_missing_justification():
    """Validator must not crash when justification is None (e.g. efficiency
    profile where the Justification agent is disabled)."""
    out = validate(cls(), None)
    assert out.escalated is False
    assert out.accepted is True


def test_handles_missing_confidences():
    """conf_at=None must not raise — older classifiers may omit confidence."""
    c = {"at": "TRUE", "isAt": "FALSE", "conf_at": None, "conf_isAt": None}
    out = validate(c, jus())
    assert out.escalated is False
