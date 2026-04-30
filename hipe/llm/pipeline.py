"""Agentic pipeline: Classifier → Justification → Validator → (escalation).

Implements the ordering described in Spec v0.7 §1.2 / §5 / §6:

1. ``LLMPredictor`` (Tier 2 classifier) produces ``ClassifierOutput``.
2. ``JustificationAgent`` independently audits the prediction.
3. The pure-Python Validator runs consistency checks (§6.2). When it
   triggers escalation (§6.3), an optional Tier 3 ``LLMPredictor``
   re-classifies with the first-pass output included as context, the
   Justification agent re-runs on the new labels, and the Validator
   produces the final accepted output.

``AgenticPredictor.predict`` is a drop-in ``predict_fn`` for
``run_ablation_experiment`` — it returns the same dict keys as
``LLMPredictor.predict`` plus structured ``justification`` /
``validator`` payloads suitable for the per-step log payloads in §8.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hipe.data import RelationInstance
from hipe.llm.justification import JustificationAgent, JustificationOutput
from hipe.llm.predict import LLMPredictor
from hipe.llm.validator import ValidatorConfig, ValidatorOutput, validate


@dataclass(slots=True)
class AgenticPredictorConfig:
    """Knobs for ``AgenticPredictor``.

    The classifier and (optional) escalation predictor are passed in
    pre-built so callers control prompt variant, retriever, model, etc.
    """

    enable_justification: bool = True
    enable_validator: bool = True
    validator: ValidatorConfig = field(default_factory=ValidatorConfig)
    # When True, the Justification agent re-runs on the escalated output
    # before the Validator's final pass (§6.4 step 3).
    rejustify_after_escalation: bool = True


def _classifier_dict(prediction: dict[str, Any]) -> dict[str, Any]:
    """Pull the canonical classifier slots out of ``LLMPredictor.predict``."""
    return {
        "at": prediction.get("at"),
        "isAt": prediction.get("isAt"),
        "conf_at": prediction.get("conf_at"),
        "conf_isAt": prediction.get("conf_isAt"),
        "reasoning": prediction.get("at_explanation") or prediction.get("isAt_explanation"),
    }


def _build_escalation_user_message_addendum(
    classifier: dict[str, Any],
    justification: JustificationOutput | None,
    validator_out: ValidatorOutput,
) -> str:
    """Spec §6.4 — when escalating to Tier 3, prepend the first-pass
    analysis and the validator's flagged issues so the stronger model has
    the context it needs to address them.
    """
    parts = ["[FIRST-PASS ANALYSIS — TIER 2]"]
    parts.append(f"at={classifier.get('at')}, isAt={classifier.get('isAt')}")
    if classifier.get("conf_at") is not None or classifier.get("conf_isAt") is not None:
        parts.append(
            f"conf_at={classifier.get('conf_at')}, conf_isAt={classifier.get('conf_isAt')}"
        )
    if classifier.get("reasoning"):
        parts.append(f"reasoning: {classifier['reasoning']}")
    if justification is not None:
        parts.append("")
        parts.append("[JUSTIFICATION AGENT FINDINGS]")
        parts.append(f"evidence_strength: {justification.evidence_strength}")
        if justification.flags:
            parts.append(f"flags: {justification.flags}")
        if justification.narrative_justification:
            parts.append(f"narrative: {justification.narrative_justification}")
    if validator_out.escalation_reason:
        parts.append("")
        parts.append("[VALIDATOR FLAGS]")
        parts.append(validator_out.escalation_reason)
    parts.append("")
    parts.append(
        "The first-pass analysis above is offered as context. Re-classify "
        "the relation, addressing the flagged issues. Output ONLY the "
        "classification line per the system prompt — no analysis."
    )
    return "\n".join(parts)


class AgenticPredictor:
    """Wires Classifier → Justification → Validator (+ optional escalation)."""

    def __init__(
        self,
        classifier: LLMPredictor,
        *,
        justifier: JustificationAgent | None = None,
        escalator: LLMPredictor | None = None,
        config: AgenticPredictorConfig | None = None,
    ) -> None:
        self.classifier = classifier
        self.justifier = justifier
        self.escalator = escalator
        self.config = config or AgenticPredictorConfig()
        # Per-instance counters so ``stats()`` can report aggregates without
        # walking the log files.
        self._n_calls = 0
        self._n_justified = 0
        self._n_escalated = 0
        self._n_validator_failed = 0

    # ------------------------------------------------------------------ #
    # Stage runners                                                      #
    # ------------------------------------------------------------------ #

    def _run_classifier(self, instance: RelationInstance) -> dict[str, Any]:
        return self.classifier.predict(instance)

    def _run_justification(
        self,
        instance: RelationInstance,
        classifier_pred: dict[str, Any],
    ) -> JustificationOutput | None:
        if not self.config.enable_justification or self.justifier is None:
            return None
        out = self.justifier.run(instance, _classifier_dict(classifier_pred))
        self._n_justified += 1
        return out

    def _run_escalation(
        self,
        instance: RelationInstance,
        classifier_pred: dict[str, Any],
        justification: JustificationOutput | None,
        validator_out: ValidatorOutput,
    ) -> dict[str, Any] | None:
        """Re-classify with the Tier 3 predictor, threading first-pass context."""
        if self.escalator is None:
            return None
        # The escalator is a normal LLMPredictor; we re-use its full prompt
        # pipeline (retriever, options) by going through .predict and then
        # tucking the Tier-2 analysis into the user message via a
        # monkey-patched call. Simpler: call the client directly with the
        # escalator's system + a user message that includes both the
        # standard prompt body and the addendum.
        from hipe.llm.parser import parse_output
        from hipe.llm.prompts import build_user_message, system_prompt

        cfg = self.escalator.config
        retrieved = self.escalator._retrieve(instance)
        base_user = build_user_message(
            instance,
            variant=cfg.variant,
            options=cfg.user_message_options,
            retrieved_examples=retrieved or None,
        )
        addendum = _build_escalation_user_message_addendum(
            _classifier_dict(classifier_pred), justification, validator_out
        )
        user = base_user + "\n\n" + addendum
        resp = self.escalator.client.chat(system_prompt(cfg.variant), user)
        parsed = parse_output(resp["text"], cfg.variant)
        # Mirror LLMPredictor.predict's output shape so downstream code
        # doesn't have to special-case escalated predictions.
        return {
            "at": parsed.at or cfg.fallback_at,
            "isAt": parsed.isAt or cfg.fallback_isAt,
            "at_explanation": parsed.reasoning,
            "isAt_explanation": parsed.reasoning,
            "raw_output": resp["text"],
            "conf_at": parsed.conf_at,
            "conf_isAt": parsed.conf_isAt,
            "parse_status": parsed.parse_status,
            "model_used": resp.get("model"),
            "provider": resp.get("provider"),
            "prompt_tokens": resp.get("usage", {}).get("prompt_tokens"),
            "completion_tokens": resp.get("usage", {}).get("completion_tokens"),
            "n_retrieved": len(retrieved),
            "retrieved_sample_ids": [r.sample_id for r in retrieved] if retrieved else [],
        }

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def predict(self, instance: RelationInstance) -> dict[str, Any]:
        self._n_calls += 1

        classifier_pred = self._run_classifier(instance)
        justification = self._run_justification(instance, classifier_pred)

        if not self.config.enable_validator:
            return self._assemble_output(
                instance,
                classifier_pred=classifier_pred,
                justification=justification,
                validator_out=None,
                escalated_pred=None,
                escalated_justification=None,
            )

        validator_out = validate(
            _classifier_dict(classifier_pred),
            justification.as_dict() if justification is not None else None,
            config=self.config.validator,
        )
        if validator_out.checks_failed:
            self._n_validator_failed += 1

        escalated_pred = None
        escalated_justification = None
        if validator_out.escalated and self.escalator is not None:
            self._n_escalated += 1
            escalated_pred = self._run_escalation(
                instance, classifier_pred, justification, validator_out
            )
            if escalated_pred is not None:
                if (
                    self.config.rejustify_after_escalation
                    and self.config.enable_justification
                    and self.justifier is not None
                ):
                    escalated_justification = self.justifier.run(
                        instance, _classifier_dict(escalated_pred)
                    )
                # Final validator pass on the escalated output.
                validator_out = validate(
                    _classifier_dict(escalated_pred),
                    (escalated_justification or justification).as_dict()
                    if (escalated_justification or justification) is not None
                    else None,
                    config=self.config.validator,
                )
                # Force accepted=True after escalation: spec §6.4 caps at
                # two passes, the escalated output replaces the original
                # regardless of remaining flags.
                validator_out.accepted = True
                validator_out.escalated = True

        return self._assemble_output(
            instance,
            classifier_pred=classifier_pred,
            justification=justification,
            validator_out=validator_out,
            escalated_pred=escalated_pred,
            escalated_justification=escalated_justification,
        )

    def _assemble_output(
        self,
        instance: RelationInstance,
        *,
        classifier_pred: dict[str, Any],
        justification: JustificationOutput | None,
        validator_out: ValidatorOutput | None,
        escalated_pred: dict[str, Any] | None,
        escalated_justification: JustificationOutput | None,
    ) -> dict[str, Any]:
        # Choose final labels: validator's final fields win when present,
        # else escalated, else first-pass classifier.
        final_pred = escalated_pred or classifier_pred
        if validator_out is not None and validator_out.final_at_label is not None:
            at = validator_out.final_at_label
            isAt = validator_out.final_isAt_label
            conf_at = validator_out.final_confidence_at
            conf_isAt = validator_out.final_confidence_isAt
        else:
            at = final_pred.get("at")
            isAt = final_pred.get("isAt")
            conf_at = final_pred.get("conf_at")
            conf_isAt = final_pred.get("conf_isAt")

        models_used = [final_pred.get("model_used")]
        if escalated_pred is not None and escalated_pred is not classifier_pred:
            models_used = [classifier_pred.get("model_used"), escalated_pred.get("model_used")]

        narrative = ""
        if escalated_justification is not None:
            narrative = escalated_justification.narrative_justification
        elif justification is not None:
            narrative = justification.narrative_justification

        return {
            "at": at,
            "isAt": isAt,
            "conf_at": conf_at,
            "conf_isAt": conf_isAt,
            "at_explanation": narrative or final_pred.get("at_explanation"),
            "isAt_explanation": narrative or final_pred.get("isAt_explanation"),
            "raw_output": final_pred.get("raw_output"),
            "parse_status": final_pred.get("parse_status"),
            "model_used": final_pred.get("model_used"),
            "provider": final_pred.get("provider"),
            "models_used": [m for m in models_used if m],
            "n_retrieved": final_pred.get("n_retrieved"),
            "retrieved_sample_ids": final_pred.get("retrieved_sample_ids"),
            # Structured per-stage payloads for §8.3 logging.
            "classifier": {
                "at": classifier_pred.get("at"),
                "isAt": classifier_pred.get("isAt"),
                "conf_at": classifier_pred.get("conf_at"),
                "conf_isAt": classifier_pred.get("conf_isAt"),
                "model_used": classifier_pred.get("model_used"),
                "parse_status": classifier_pred.get("parse_status"),
                "raw_output": classifier_pred.get("raw_output"),
            },
            "justification": justification.as_dict() if justification is not None else None,
            "escalated_classifier": (
                {
                    "at": escalated_pred.get("at"),
                    "isAt": escalated_pred.get("isAt"),
                    "conf_at": escalated_pred.get("conf_at"),
                    "conf_isAt": escalated_pred.get("conf_isAt"),
                    "model_used": escalated_pred.get("model_used"),
                    "raw_output": escalated_pred.get("raw_output"),
                }
                if escalated_pred is not None
                else None
            ),
            "escalated_justification": (
                escalated_justification.as_dict() if escalated_justification is not None else None
            ),
            "validator": validator_out.as_dict() if validator_out is not None else None,
            "was_escalated": bool(validator_out and validator_out.escalated and escalated_pred is not None),
        }

    def stats(self) -> dict[str, Any]:
        base = self.classifier.stats()
        base.update(
            {
                "n_agentic_calls": self._n_calls,
                "n_justified": self._n_justified,
                "n_escalated": self._n_escalated,
                "n_validator_failed": self._n_validator_failed,
                "escalation_rate": (
                    self._n_escalated / self._n_calls if self._n_calls else 0.0
                ),
                "justification_enabled": self.config.enable_justification,
                "validator_enabled": self.config.enable_validator,
                "escalation_enabled": self.escalator is not None,
            }
        )
        return base
