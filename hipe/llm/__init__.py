"""LLM-based classifier (Spec: Prompting & MASK §2-§5).

Thin wrapper around OpenAI-compatible chat APIs (OpenAI, DeepInfra) with
prompt variants P-A / P-B / P-AB / P-R and the spec's flat-text output
parser. Use :class:`LLMPredictor` as a ``predict_fn`` argument for
``hipe.evaluation.run_ablation_experiment``.
"""

from hipe.llm.client import LLMClient, LLMClientConfig, resolve_provider
from hipe.llm.justification import (
    JustificationAgent,
    JustificationAgentConfig,
    JustificationOutput,
    parse_justification,
)
from hipe.llm.parser import (
    ParseResult,
    parse_output,
)
from hipe.llm.pipeline import AgenticPredictor, AgenticPredictorConfig
from hipe.llm.predict import LLMPredictor, LLMPredictorConfig
from hipe.llm.prompts import (
    PROMPT_VARIANTS,
    build_user_message,
    insert_entity_markers,
    system_prompt,
)
from hipe.llm.validator import (
    ValidatorConfig,
    ValidatorOutput,
    run_checks,
    should_escalate,
    validate,
)

__all__ = [
    "AgenticPredictor",
    "AgenticPredictorConfig",
    "JustificationAgent",
    "JustificationAgentConfig",
    "JustificationOutput",
    "LLMClient",
    "LLMClientConfig",
    "LLMPredictor",
    "LLMPredictorConfig",
    "ParseResult",
    "PROMPT_VARIANTS",
    "ValidatorConfig",
    "ValidatorOutput",
    "build_user_message",
    "insert_entity_markers",
    "parse_justification",
    "parse_output",
    "resolve_provider",
    "run_checks",
    "should_escalate",
    "system_prompt",
    "validate",
]
