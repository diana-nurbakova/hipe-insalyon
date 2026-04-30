"""End-to-end test for hipe.llm.pipeline.AgenticPredictor with mocked agents.

We don't hit a live LLM here — instead we stub out the classifier and the
JustificationAgent.run method so the orchestrator's wiring is exercised
deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

from hipe.data import RelationInstance
from hipe.llm.justification import JustificationOutput
from hipe.llm.pipeline import AgenticPredictor, AgenticPredictorConfig
from hipe.llm.validator import ValidatorConfig


def _make_instance() -> RelationInstance:
    return RelationInstance(
        document_id="doc1",
        pers_entity_id="p1",
        loc_entity_id="l1",
        language="fr",
        date="1900-01-15",
        pers_mentions_list=["Hugo"],
        loc_mentions_list=["Paris"],
        pers_wikidata_QID="Q535",
        loc_wikidata_QID="Q90",
        text="Victor Hugo se trouve à Paris.",
        context="Victor Hugo se trouve à Paris.",
    )


def _classifier_pred(at="TRUE", isAt="TRUE", conf_at=0.9, conf_isAt=0.9, model="cls-base"):
    return {
        "at": at,
        "isAt": isAt,
        "at_explanation": "stub reasoning",
        "isAt_explanation": "stub reasoning",
        "conf_at": conf_at,
        "conf_isAt": conf_isAt,
        "raw_output": "raw",
        "parse_status": "ok",
        "model_used": model,
        "provider": "stub",
        "n_retrieved": 0,
        "retrieved_sample_ids": [],
    }


def _justification(strength="strong", flags=None, wd_supports=None, narrative="ok"):
    return JustificationOutput(
        evidence_spans=[{"text": "x", "supports": "at", "explanation": ""}],
        wikidata_corroboration={"supports": wd_supports, "details": ""},
        temporal_assessment={"explicit_dates_found": [], "within_isat_window": None, "explanation": ""},
        evidence_strength=strength,
        narrative_justification=narrative,
        flags=list(flags or []),
        parse_status="ok",
        raw_output="{}",
        model_used="just-base",
    )


def test_pipeline_accepts_classifier_output_when_validator_passes():
    classifier = MagicMock()
    classifier.predict.return_value = _classifier_pred()
    classifier.stats.return_value = {"n_calls": 1}

    justifier = MagicMock()
    justifier.run.return_value = _justification()

    pipeline = AgenticPredictor(
        classifier=classifier,
        justifier=justifier,
        escalator=None,
        config=AgenticPredictorConfig(),
    )
    out = pipeline.predict(_make_instance())

    assert out["at"] == "TRUE"
    assert out["isAt"] == "TRUE"
    assert out["was_escalated"] is False
    assert out["validator"]["accepted"] is True
    assert out["justification"] is not None


def test_pipeline_escalates_on_logical_contradiction():
    classifier = MagicMock()
    # at=FALSE + isAt=TRUE is a hard escalation trigger.
    classifier.predict.return_value = _classifier_pred(at="FALSE", isAt="TRUE")
    classifier.stats.return_value = {"n_calls": 1}

    justifier = MagicMock()
    justifier.run.side_effect = [
        _justification(strength="weak"),  # first pass
        _justification(strength="strong", narrative="re-justified"),  # after escalation
    ]

    escalator = MagicMock()
    # Escalator returns a coherent re-classification.
    fixed = _classifier_pred(at="TRUE", isAt="TRUE", model="cls-strong")
    # The orchestrator goes through the escalator's _retrieve and client.chat
    # rather than calling .predict — patch those instead of .predict.
    escalator._retrieve.return_value = []
    escalator.client.chat.return_value = {
        "text": "at=TRUE isAt=TRUE | conf_at=0.95 conf_isAt=0.95",
        "model": "cls-strong",
        "provider": "stub",
        "usage": {"prompt_tokens": 100, "completion_tokens": 20},
    }
    # The escalation path reads escalator.config.* — give it a real config.
    from hipe.llm.predict import LLMPredictorConfig
    from hipe.llm.prompts import UserMessageOptions
    # Avoid the post-init retriever check by faking variant-only config.
    cfg = LLMPredictorConfig(variant="AB", user_message_options=UserMessageOptions())
    escalator.config = cfg

    pipeline = AgenticPredictor(
        classifier=classifier,
        justifier=justifier,
        escalator=escalator,
        config=AgenticPredictorConfig(),
    )
    out = pipeline.predict(_make_instance())

    assert out["was_escalated"] is True
    assert out["at"] == "TRUE"
    assert out["isAt"] == "TRUE"
    # The stronger model's output replaces the original.
    assert out["escalated_classifier"]["model_used"] == "cls-strong"
    # The justification re-ran on the escalated output.
    assert out["escalated_justification"]["narrative_justification"] == "re-justified"


def test_pipeline_skips_justification_when_disabled():
    classifier = MagicMock()
    classifier.predict.return_value = _classifier_pred()
    classifier.stats.return_value = {"n_calls": 1}

    justifier = MagicMock()
    justifier.run.return_value = _justification()

    pipeline = AgenticPredictor(
        classifier=classifier,
        justifier=justifier,
        escalator=None,
        config=AgenticPredictorConfig(enable_justification=False),
    )
    out = pipeline.predict(_make_instance())

    assert out["justification"] is None
    justifier.run.assert_not_called()


def test_pipeline_hard_only_validator_does_not_escalate_on_low_confidence():
    classifier = MagicMock()
    # Low confidences would normally trigger soft escalation (≥2 soft flags),
    # but hard_only collapses soft flags to zero.
    classifier.predict.return_value = _classifier_pred(conf_at=0.4, conf_isAt=0.3)
    classifier.stats.return_value = {"n_calls": 1}

    justifier = MagicMock()
    justifier.run.return_value = _justification(strength="weak")

    pipeline = AgenticPredictor(
        classifier=classifier,
        justifier=justifier,
        escalator=None,
        config=AgenticPredictorConfig(validator=ValidatorConfig(hard_only=True)),
    )
    out = pipeline.predict(_make_instance())
    assert out["was_escalated"] is False
    assert out["validator"]["accepted"] is True
