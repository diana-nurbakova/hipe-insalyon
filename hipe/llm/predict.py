"""LLMPredictor — glues client + prompt + parser into a ``predict_fn``.

Plug into ``hipe.evaluation.run_ablation_experiment`` like::

    predictor = LLMPredictor(LLMPredictorConfig(variant="AB", provider="deepinfra"))
    run_ablation_experiment(
        experiment_id="T1.1_llm_zeroshot_PAB",
        predict_fn=predictor.predict,
        dev_instances=test_split,
    )

When ``LLMPredictorConfig.retriever`` is set, each prediction first calls
``retriever.search(instance, k=...)`` and the retrieved annotated
neighbours are injected into the user message via the
``[SIMILAR EXAMPLES FROM TRAINING DATA]`` block (RAG few-shot).

For variants P-A and P-B (single-target), ``predict`` only fills in the
target it was asked about; the other slot defaults to ``FALSE`` so the
experiment harness can still score the dual-target report. Pair with the
opposite variant if you want both targets predicted independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from hipe.data import RelationInstance
from hipe.llm.client import LLMClient, LLMClientConfig
from hipe.llm.parser import parse_output
from hipe.llm.prompts import (
    PROMPT_VARIANTS,
    UserMessageOptions,
    build_user_message,
    system_prompt,
)

if TYPE_CHECKING:  # avoid heavy ML imports when LLMPredictor is used without RAG
    from hipe.retriever import Retriever


@dataclass(slots=True)
class LLMPredictorConfig:
    variant: str = "AB"
    provider: str = "deepinfra"
    model: str | None = None
    temperature: float = 0.0
    max_tokens: int = 512
    timeout: float = 60.0
    max_retries: int = 3
    user_message_options: UserMessageOptions = field(default_factory=UserMessageOptions)
    fallback_at: str = "FALSE"
    fallback_isAt: str = "FALSE"
    # RAG few-shot configuration
    retriever: "Retriever | None" = None
    k_retrieved: int = 0  # 0 disables retrieval; common values 3 / 5
    diversify_retrieved_labels: bool = False
    retriever_prefer_language: str | None = "auto"
    # Provider fallback (e.g. openrouter primary -> deepinfra secondary).
    fallback_provider: str | None = None
    fallback_model: str | None = None
    # Self-consistency: sample n times with sample_temperature and majority-vote
    # the (at, isAt) labels. n_samples == 1 is the deterministic baseline.
    n_samples: int = 1
    sample_temperature: float = 0.0

    def __post_init__(self) -> None:
        if self.variant not in PROMPT_VARIANTS:
            raise ValueError(
                f"variant must be one of {PROMPT_VARIANTS}, got {self.variant!r}"
            )
        if self.k_retrieved and self.retriever is None:
            raise ValueError("k_retrieved > 0 requires a retriever instance")
        if self.retriever is not None and self.k_retrieved <= 0:
            # Treat retriever-without-K as a no-op so the configuration is
            # symmetric: passing a retriever but k=0 disables RAG explicitly.
            pass

    def to_client_config(self) -> LLMClientConfig:
        return LLMClientConfig(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            max_retries=self.max_retries,
            fallback_provider=self.fallback_provider,
            fallback_model=self.fallback_model,
        )


class LLMPredictor:
    def __init__(self, config: LLMPredictorConfig | None = None, *, client: LLMClient | None = None) -> None:
        self.config = config or LLMPredictorConfig()
        self.client = client or LLMClient(self.config.to_client_config())
        self._sys = system_prompt(self.config.variant)
        # Counters surfaced via .stats() for cost / parse-success summaries.
        self._n_calls = 0
        self._n_parse_ok = 0
        self._n_parse_partial = 0
        self._n_parse_fail = 0
        self._tokens_in = 0
        self._tokens_out = 0
        self._n_retrieved_total = 0

    def _retrieve(self, instance: RelationInstance) -> list:
        """Run the retriever and exclude the query's own sample_id."""
        retriever = self.config.retriever
        if retriever is None or self.config.k_retrieved <= 0:
            return []
        return retriever.search(
            instance,
            k=self.config.k_retrieved,
            prefer_language=self.config.retriever_prefer_language,
            diversify_labels=self.config.diversify_retrieved_labels,
            exclude_sample_ids={instance.sample_id},
        )

    def _record_response(self, resp: dict[str, Any]) -> None:
        self._n_calls += 1
        self._tokens_in += int(resp.get("usage", {}).get("prompt_tokens", 0) or 0)
        self._tokens_out += int(resp.get("usage", {}).get("completion_tokens", 0) or 0)

    def _record_parse(self, parsed) -> None:
        if parsed.parse_status == "ok":
            self._n_parse_ok += 1
        elif parsed.parse_status == "partial":
            self._n_parse_partial += 1
        else:
            self._n_parse_fail += 1

    def predict(self, instance: RelationInstance) -> dict[str, Any]:
        """Single instance -> prediction dict (matches predict_fn contract).

        When ``config.n_samples > 1``, draws that many samples at
        ``sample_temperature`` and majority-votes the (at, isAt) labels
        independently. The first sample's reasoning is exposed as the
        explanation; the per-sample raw outputs are recorded under
        ``samples`` for post-hoc analysis.
        """
        retrieved = self._retrieve(instance)
        self._n_retrieved_total += len(retrieved)
        user = build_user_message(
            instance,
            variant=self.config.variant,
            options=self.config.user_message_options,
            retrieved_examples=retrieved or None,
        )

        n_samples = max(1, int(self.config.n_samples))
        # Use deterministic temperature for n=1 (matches old behaviour).
        per_sample_temp = (
            self.config.temperature if n_samples == 1 else self.config.sample_temperature
        )

        samples: list[dict[str, Any]] = []
        for _ in range(n_samples):
            resp = self.client.chat(self._sys, user, temperature=per_sample_temp)
            self._record_response(resp)
            parsed = parse_output(resp["text"], self.config.variant)
            self._record_parse(parsed)
            samples.append(
                {
                    "at": parsed.at,
                    "isAt": parsed.isAt,
                    "reasoning": parsed.reasoning,
                    "raw_output": resp["text"],
                    "parse_status": parsed.parse_status,
                    "conf_at": parsed.conf_at,
                    "conf_isAt": parsed.conf_isAt,
                    "model": resp.get("model"),
                    "provider": resp.get("provider"),
                    "fallback_used": bool(resp.get("fallback_used")),
                    "prompt_tokens": resp.get("usage", {}).get("prompt_tokens"),
                    "completion_tokens": resp.get("usage", {}).get("completion_tokens"),
                }
            )

        at = self._majority(
            [s["at"] for s in samples], fallback=self.config.fallback_at
        )
        isAt = self._majority(
            [s["isAt"] for s in samples], fallback=self.config.fallback_isAt
        )
        # Single-sample path collapses cleanly to the n=1 contract.
        first = samples[0]
        agreement_at = sum(1 for s in samples if s["at"] == at) / len(samples)
        agreement_isAt = sum(1 for s in samples if s["isAt"] == isAt) / len(samples)
        last = samples[-1]
        out: dict[str, Any] = {
            "at": at,
            "isAt": isAt,
            "at_explanation": first["reasoning"],
            "isAt_explanation": first["reasoning"],
            "raw_output": first["raw_output"],
            "conf_at": first["conf_at"],
            "conf_isAt": first["conf_isAt"],
            "parse_status": first["parse_status"],
            "model_used": last["model"],
            "provider": last["provider"],
            "prompt_tokens": sum(s["prompt_tokens"] or 0 for s in samples),
            "completion_tokens": sum(s["completion_tokens"] or 0 for s in samples),
            "n_retrieved": len(retrieved),
            "retrieved_sample_ids": [r.sample_id for r in retrieved] if retrieved else [],
            "n_samples": n_samples,
        }
        if n_samples > 1:
            out["sc_agreement_at"] = round(agreement_at, 3)
            out["sc_agreement_isAt"] = round(agreement_isAt, 3)
            out["samples"] = [
                {k: s[k] for k in ("at", "isAt", "parse_status", "fallback_used")}
                for s in samples
            ]
        if any(s["fallback_used"] for s in samples):
            out["fallback_used"] = True
        return out

    @staticmethod
    def _majority(labels: list[str | None], *, fallback: str) -> str:
        """Pick the most-frequent non-empty label; ties broken by first seen.

        If every label is empty/None, returns ``fallback`` so the experiment
        harness always gets a valid class.
        """
        counts: dict[str, int] = {}
        order: list[str] = []
        for lbl in labels:
            if not lbl:
                continue
            if lbl not in counts:
                counts[lbl] = 0
                order.append(lbl)
            counts[lbl] += 1
        if not counts:
            return fallback
        # Stable: max() picks the first label hit when counts tie because
        # we iterate `order` (insertion order) under a key sort.
        return max(order, key=lambda l: (counts[l], -order.index(l)))

    def stats(self) -> dict[str, Any]:
        avg_retrieved = (
            self._n_retrieved_total / self._n_calls if self._n_calls else 0.0
        )
        return {
            "n_calls": self._n_calls,
            "parse_ok": self._n_parse_ok,
            "parse_partial": self._n_parse_partial,
            "parse_fail": self._n_parse_fail,
            "prompt_tokens": self._tokens_in,
            "completion_tokens": self._tokens_out,
            "model": self.client.model,
            "provider": self.client.provider,
            "fallback_provider": self.client.fallback_provider,
            "n_fallback_calls": self.client.n_fallback_calls,
            "variant": self.config.variant,
            "k_retrieved": self.config.k_retrieved,
            "avg_retrieved_per_call": avg_retrieved,
            "n_samples": self.config.n_samples,
            "sample_temperature": self.config.sample_temperature,
        }
