"""Justification agent (Spec v0.7 §5).

Runs *after* the Classifier with the predicted labels in hand and
independently assembles supporting evidence (text spans, Wikidata facts,
temporal reasoning, flags). Its output feeds the Validator's escalation logic.

The agent uses the same ``LLMClient`` as the Classifier, but with its own
system prompt and a JSON-shaped output. ``parse_justification`` is tolerant
of code-fenced JSON, trailing commentary, and missing optional fields.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from hipe.data import RelationInstance
from hipe.llm.client import LLMClient, LLMClientConfig
from hipe.llm.prompts import insert_entity_markers

# Allowed values for evidence_strength / supports / within_isat_window.
EVIDENCE_STRENGTH = ("strong", "moderate", "weak", "contradictory")
SUPPORT_TARGETS = ("at", "isAt", "both", "neither")

# Canonical phrase the Validator's `temporal_logic` check looks for.
NO_TEMPORAL_FLAG = "no temporal anchor found"


# ---------------------------------------------------------------------------
# Output schema (Spec §5.5)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class JustificationOutput:
    evidence_spans: list[dict[str, Any]] = field(default_factory=list)
    wikidata_corroboration: dict[str, Any] = field(default_factory=dict)
    temporal_assessment: dict[str, Any] = field(default_factory=dict)
    evidence_strength: str | None = None
    narrative_justification: str = ""
    flags: list[str] = field(default_factory=list)
    parse_status: str = "ok"  # "ok" | "partial" | "fail"
    raw_output: str = ""
    model_used: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Prompt (Spec §5.3)
# ---------------------------------------------------------------------------

_JUSTIFICATION_SYSTEM = """You are a fact-checking analyst. Given a classified person-place relation
from a historical newspaper, your job is to gather evidence and produce a
structured justification. Be critical: if the evidence is weak or
contradictory, say so.

You will be given the classifier's predicted labels (at, isAt) and reasoning,
the article text with entity markers, the publication date, and any
Wikidata context. Your task is NOT to re-classify the relation but to
audit the evidence supporting it.

OUTPUT FORMAT:
Respond with a single JSON object containing exactly these keys:
  - evidence_spans: list of {text, supports, explanation}
      * "text": exact quoted span from the article
      * "supports": one of "at", "isAt", "both", "neither"
      * "explanation": one short sentence on why this span is relevant
  - wikidata_corroboration: {supports: true|false|null, details: string}
  - temporal_assessment: {explicit_dates_found: list, within_isat_window: true|false|"uncertain", explanation: string}
  - evidence_strength: one of "strong", "moderate", "weak", "contradictory"
  - narrative_justification: 2-3 sentence human-readable summary
  - flags: list of short strings naming concerns. Use the exact phrase
    "no temporal anchor found" when no temporal expression places the
    person at the location within approximately one month of the publication date.

Output the JSON object and nothing else. Do not wrap it in code fences."""


def _format_wikidata(ctx: dict | None) -> str:
    if not ctx:
        return "(none)"
    parts = []
    for key in ("label", "description", "born", "died", "country", "located_in"):
        v = ctx.get(key)
        if v:
            parts.append(f"{key}={v}")
    return "; ".join(parts) if parts else "(none)"


def build_justification_user_message(
    instance: RelationInstance,
    classifier: dict[str, Any],
) -> str:
    """Render the user-message prompt per Spec §5.3."""
    person = (instance.pers_mentions_list or [""])[0]
    location = (instance.loc_mentions_list or [""])[0]
    text = insert_entity_markers(instance, field="text")
    at = classifier.get("at")
    isAt = classifier.get("isAt")
    conf_at = classifier.get("conf_at")
    conf_isAt = classifier.get("conf_isAt")
    reasoning = classifier.get("reasoning") or classifier.get("at_explanation") or ""

    def _fmt_conf(c: Any) -> str:
        return f"{c:.2f}" if isinstance(c, (int, float)) else "n/a"

    sections = [
        "[CLASSIFIED RELATION]",
        f"Person: '{person}'  Location: '{location}'",
        f"at = {at} (confidence: {_fmt_conf(conf_at)})",
        f"isAt = {isAt} (confidence: {_fmt_conf(conf_isAt)})",
        f"Classifier reasoning: {reasoning or '(none provided)'}",
        "",
        f"Publication date: {instance.date}",
        f"Language: {instance.language}",
        "",
        "[ARTICLE TEXT]",
        f'"{text}"',
        "",
        "[WIKIDATA CONTEXT]",
        f"Person: {_format_wikidata(instance.person_context)}",
        f"Location: {_format_wikidata(instance.location_context)}",
    ]
    relations = instance.known_person_location_relations
    if relations:
        sections.append(f"Known links: {relations}")
    sections.extend(
        [
            "",
            "Produce the JSON justification described in the system prompt. "
            "If you find no temporal anchor placing the person at the location "
            "within approximately one month of the publication date, include the exact flag "
            f'"{NO_TEMPORAL_FLAG}".',
        ]
    )
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------

_CODE_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _extract_json_object(text: str) -> str | None:
    """Find a balanced top-level JSON object in *text*.

    Strategy: look inside `````json ... ````` fences first; otherwise scan for the
    first ``{`` and walk forward to its matching ``}`` while respecting
    string literals. Returns the substring (without the fences) or None
    when no candidate is found.
    """
    if not text:
        return None
    fence = _CODE_FENCE_RE.search(text)
    if fence:
        return fence.group(1).strip()

    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _coerce_supports(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes", "supports"}:
            return True
        if v in {"false", "no", "contradicts"}:
            return False
        if v in {"null", "none", "uncertain", "unknown"}:
            return None
    return None


def _coerce_strength(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    return v if v in EVIDENCE_STRENGTH else None


def _coerce_within_window(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"true", "yes"}:
            return True
        if v in {"false", "no"}:
            return False
        if v in {"uncertain", "unknown", "maybe"}:
            return "uncertain"
    return None


def _coerce_evidence_spans(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        supports_raw = item.get("supports")
        supports = (
            supports_raw.strip().lower()
            if isinstance(supports_raw, str) and supports_raw.strip().lower() in SUPPORT_TARGETS
            else "neither"
        )
        explanation = str(item.get("explanation", "")).strip()
        out.append({"text": text, "supports": supports, "explanation": explanation})
    return out


def _coerce_flags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def parse_justification(raw: str) -> JustificationOutput:
    """Tolerant parser for the Justification agent's JSON response."""
    raw = raw or ""
    candidate = _extract_json_object(raw)
    if candidate is None:
        return JustificationOutput(parse_status="fail", raw_output=raw)

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return JustificationOutput(parse_status="fail", raw_output=raw)

    if not isinstance(data, dict):
        return JustificationOutput(parse_status="fail", raw_output=raw)

    spans = _coerce_evidence_spans(data.get("evidence_spans"))
    wd = data.get("wikidata_corroboration") or {}
    if not isinstance(wd, dict):
        wd = {}
    wd_norm = {
        "supports": _coerce_supports(wd.get("supports")),
        "details": str(wd.get("details", "")).strip(),
    }

    temp = data.get("temporal_assessment") or {}
    if not isinstance(temp, dict):
        temp = {}
    temp_norm = {
        "explicit_dates_found": list(temp.get("explicit_dates_found") or []),
        "within_isat_window": _coerce_within_window(temp.get("within_isat_window")),
        "explanation": str(temp.get("explanation", "")).strip(),
    }

    strength = _coerce_strength(data.get("evidence_strength"))
    narrative = str(data.get("narrative_justification", "")).strip()
    flags = _coerce_flags(data.get("flags"))

    # "partial" if any required slot is missing or unparseable.
    required_ok = all([
        spans is not None,
        strength is not None,
        narrative,
    ])
    status = "ok" if required_ok else "partial"

    return JustificationOutput(
        evidence_spans=spans,
        wikidata_corroboration=wd_norm,
        temporal_assessment=temp_norm,
        evidence_strength=strength,
        narrative_justification=narrative,
        flags=flags,
        parse_status=status,
        raw_output=raw,
    )


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class JustificationAgentConfig:
    provider: str = "deepinfra"
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = 768  # JSON output with multiple spans
    timeout: float = 60.0
    max_retries: int = 3

    def to_client_config(self) -> LLMClientConfig:
        return LLMClientConfig(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )


class JustificationAgent:
    """Single-call wrapper that turns a (instance, classifier_dict) pair
    into a parsed ``JustificationOutput``."""

    def __init__(
        self,
        config: JustificationAgentConfig | None = None,
        *,
        client: LLMClient | None = None,
    ) -> None:
        self.config = config or JustificationAgentConfig()
        self.client = client or LLMClient(self.config.to_client_config())
        self._sys = _JUSTIFICATION_SYSTEM

    def run(
        self,
        instance: RelationInstance,
        classifier: dict[str, Any],
    ) -> JustificationOutput:
        user = build_justification_user_message(instance, classifier)
        resp = self.client.chat(self._sys, user)
        out = parse_justification(resp["text"])
        out.model_used = resp.get("model")
        out.prompt_tokens = int(resp.get("usage", {}).get("prompt_tokens", 0) or 0)
        out.completion_tokens = int(resp.get("usage", {}).get("completion_tokens", 0) or 0)
        out.latency_ms = resp.get("latency_ms")
        return out
