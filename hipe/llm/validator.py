"""Validator agent — pure-Python rule engine (Spec v0.7 §6).

The validator runs *after* the Classifier and Justification agents. It takes
their outputs and runs the consistency checks listed in §6.2, then applies the
escalation logic from §6.3. It does **not** call an LLM itself; if it decides
to escalate, the orchestrator (``AgenticPredictor``) re-runs the Classifier
with a stronger model and feeds that output back through the Justification
agent before producing the final ``ValidatorOutput``.

Inputs are deliberately loose dicts (not dataclasses) so the validator can
sit between any classifier/justification implementation as long as the keys
agree:

  classifier dict expected keys
    at, isAt                            : str ("TRUE"|"PROBABLE"|"FALSE" / "TRUE"|"FALSE")
    conf_at, conf_isAt                  : float | None
    reasoning                           : str | None  (used for soft heuristics)

  justification dict expected keys
    evidence_strength                   : "strong"|"moderate"|"weak"|"contradictory"|None
    wikidata_corroboration              : dict with "supports": bool | None
    flags                               : list[str]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Spec §6.2.5 — confidence escalation thresholds.
DEFAULT_AT_CONF_THRESHOLD = 0.7
DEFAULT_ISAT_CONF_THRESHOLD = 0.6
# Spec §6.3 — number of soft flags required to escalate.
DEFAULT_SOFT_FLAG_THRESHOLD = 2

# Canonical phrase the Justification agent emits when no temporal evidence
# was found within the ~1-month isAt window. Validators key off this exact
# string (the wording was tightened from "+/-14d" to "approximately one month"
# in Spec v0.9 / Prompting v1.5 to match the official annotation guidelines).
NO_TEMPORAL_FLAG = "no temporal anchor found"


@dataclass(slots=True)
class ValidatorOutput:
    """Spec §6.6."""

    accepted: bool
    escalated: bool
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    escalation_reason: str = ""
    soft_flags: list[str] = field(default_factory=list)
    hard_flags: list[str] = field(default_factory=list)
    final_at_label: str | None = None
    final_isAt_label: str | None = None
    final_confidence_at: float | None = None
    final_confidence_isAt: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "escalated": self.escalated,
            "checks_passed": list(self.checks_passed),
            "checks_failed": list(self.checks_failed),
            "escalation_reason": self.escalation_reason,
            "soft_flags": list(self.soft_flags),
            "hard_flags": list(self.hard_flags),
            "final_at_label": self.final_at_label,
            "final_isAt_label": self.final_isAt_label,
            "final_confidence_at": self.final_confidence_at,
            "final_confidence_isAt": self.final_confidence_isAt,
        }


@dataclass(slots=True)
class ValidatorConfig:
    """Knobs per profile (§6.5).

    ``hard_only=True`` reproduces the efficiency-profile behaviour: only
    logical contradictions get flagged, soft signals are ignored, no
    escalation is triggered.
    """

    hard_only: bool = False
    at_conf_threshold: float = DEFAULT_AT_CONF_THRESHOLD
    isAt_conf_threshold: float = DEFAULT_ISAT_CONF_THRESHOLD
    soft_flag_threshold: int = DEFAULT_SOFT_FLAG_THRESHOLD
    enable_escalation: bool = True


def _norm(label: str | None) -> str | None:
    return label.upper() if isinstance(label, str) else None


def _wikidata_supports(justification: dict[str, Any] | None) -> Any:
    if not justification:
        return None
    wc = justification.get("wikidata_corroboration") or {}
    if not isinstance(wc, dict):
        return None
    return wc.get("supports")


def _flags(justification: dict[str, Any] | None) -> list[str]:
    if not justification:
        return []
    flags = justification.get("flags") or []
    if isinstance(flags, list):
        return [str(f).strip() for f in flags if f]
    return []


def _has_no_temporal_flag(flags: list[str]) -> bool:
    """Match the canonical 'no temporal anchor' flag tolerantly.

    The Justification prompt suggests the literal phrase but small models
    occasionally emit lightly paraphrased variants ("no temporal anchor",
    "temporal anchor missing"). We accept any flag containing the
    substring "temporal anchor" so the soft trigger fires consistently.
    """
    return any("temporal anchor" in f.lower() for f in flags)


def run_checks(
    classifier: dict[str, Any],
    justification: dict[str, Any] | None,
    *,
    config: ValidatorConfig | None = None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Run §6.2 consistency checks.

    Returns ``(checks_passed, checks_failed, hard_flags, soft_flags)``. The
    hard/soft separation drives the escalation logic.
    """
    cfg = config or ValidatorConfig()
    passed: list[str] = []
    failed: list[str] = []
    hard: list[str] = []
    soft: list[str] = []

    at = _norm(classifier.get("at"))
    isAt = _norm(classifier.get("isAt"))
    conf_at = classifier.get("conf_at")
    conf_isAt = classifier.get("conf_isAt")
    reasoning = (classifier.get("reasoning") or "").lower()

    # 6.2.6 / 6.3 hard: cross-label coherence — isAt=TRUE must imply at != FALSE.
    name = "cross_label_coherence"
    if isAt == "TRUE" and at == "FALSE":
        failed.append(name)
        hard.append("isAt=TRUE with at=FALSE is logically impossible")
    else:
        passed.append(name)

    # 6.2.2 / 6.3 hard: justification reports contradictory evidence.
    name = "evidence_alignment"
    strength = (justification or {}).get("evidence_strength")
    if strength == "contradictory":
        failed.append(name)
        hard.append("justification.evidence_strength=contradictory")
    else:
        passed.append(name)

    # 6.2.1: internal consistency — reasoning mentions "born in"/etc. but at=FALSE.
    # Cheap heuristic: if the classifier's free-text reasoning contains a
    # strong association cue but the label is FALSE, flag a soft mismatch.
    name = "internal_consistency"
    association_cues = ("born in", "lived in", "resides in", "works in",
                        "né à", "né a", "habite", "demeure",
                        "geboren in", "wohnt in", "lebt in")
    if at == "FALSE" and any(cue in reasoning for cue in association_cues):
        failed.append(name)
        soft.append("classifier reasoning mentions association cue but at=FALSE")
    else:
        passed.append(name)

    if cfg.hard_only:
        # Efficiency profile (§6.5): drop soft signals so escalation can't
        # be triggered by them.
        soft = []
        return passed, failed, hard, soft

    # 6.2.3: temporal logic — isAt=TRUE requires a within-window temporal
    # anchor. The Justification flag is authoritative; if not present, fall
    # back to the temporal_assessment block.
    name = "temporal_logic"
    flags_list = _flags(justification)
    no_temporal = _has_no_temporal_flag(flags_list)
    temporal = (justification or {}).get("temporal_assessment") or {}
    within_window = temporal.get("within_isat_window") if isinstance(temporal, dict) else None
    if isAt == "TRUE" and (no_temporal or within_window is False):
        failed.append(name)
        soft.append("isAt=TRUE but justification finds no temporal anchor within ~1 month")
    else:
        passed.append(name)

    # 6.2.4: Wikidata contradiction.
    name = "wikidata_alignment"
    wd_supports = _wikidata_supports(justification)
    if wd_supports is False:
        failed.append(name)
        soft.append("Wikidata corroboration says label is unsupported")
    else:
        passed.append(name)

    # 6.2.5: confidence thresholds.
    if isinstance(conf_at, (int, float)) and conf_at < cfg.at_conf_threshold:
        failed.append("confidence_at")
        soft.append(f"at confidence {conf_at:.2f} < {cfg.at_conf_threshold:.2f}")
    else:
        passed.append("confidence_at")
    if isinstance(conf_isAt, (int, float)) and conf_isAt < cfg.isAt_conf_threshold:
        failed.append("confidence_isAt")
        soft.append(f"isAt confidence {conf_isAt:.2f} < {cfg.isAt_conf_threshold:.2f}")
    else:
        passed.append("confidence_isAt")

    # Justification weak-evidence soft signal (§6.3).
    if strength == "weak":
        soft.append("justification.evidence_strength=weak")

    return passed, failed, hard, soft


def should_escalate(
    classifier: dict[str, Any],
    justification: dict[str, Any] | None,
    *,
    config: ValidatorConfig | None = None,
) -> tuple[bool, str]:
    """Spec §6.3.

    Returns ``(escalate, reason)`` where ``reason`` is the first hard trigger
    or a comma-joined list of soft triggers when ≥ ``soft_flag_threshold`` fire.
    """
    cfg = config or ValidatorConfig()
    if not cfg.enable_escalation:
        return False, ""

    _, _, hard, soft = run_checks(classifier, justification, config=cfg)
    if hard:
        return True, hard[0]
    if cfg.hard_only:
        return False, ""
    if len(soft) >= cfg.soft_flag_threshold:
        return True, "soft: " + "; ".join(soft)
    return False, ""


def validate(
    classifier: dict[str, Any],
    justification: dict[str, Any] | None,
    *,
    config: ValidatorConfig | None = None,
) -> ValidatorOutput:
    """Run all checks and produce a ValidatorOutput (no escalation step).

    The orchestrator decides what to do with ``escalated=True`` — typically
    re-running classification with a stronger model and re-validating.
    """
    cfg = config or ValidatorConfig()
    passed, failed, hard, soft = run_checks(classifier, justification, config=cfg)
    escalate = bool(hard) or (not cfg.hard_only and len(soft) >= cfg.soft_flag_threshold)
    if not cfg.enable_escalation:
        escalate = False

    if hard:
        reason = hard[0]
    elif escalate:
        reason = "soft: " + "; ".join(soft)
    else:
        reason = ""

    return ValidatorOutput(
        accepted=not escalate,
        escalated=escalate,
        checks_passed=passed,
        checks_failed=failed,
        escalation_reason=reason,
        soft_flags=soft,
        hard_flags=hard,
        final_at_label=_norm(classifier.get("at")),
        final_isAt_label=_norm(classifier.get("isAt")),
        final_confidence_at=classifier.get("conf_at"),
        final_confidence_isAt=classifier.get("conf_isAt"),
    )
