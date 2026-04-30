"""OpenAI-compatible chat client for OpenAI + DeepInfra + OpenRouter.

DeepInfra exposes an OpenAI-compatible endpoint at
``https://api.deepinfra.com/v1/openai`` and OpenRouter at
``https://openrouter.ai/api/v1`` — a single client wraps all three by
swapping the base URL and API key. Pick by provider name + the appropriate
API key from the environment (loaded from ``.env``).

OpenRouter is Tier 0 in Spec v0.9: free models (Gemma 4 31B, Llama 3.3 70B,
DeepSeek R1) at the cost of a 200 req/day shared quota. Use opportunistically
for one-off cross-model checks; DeepInfra remains primary for k-fold and
systematic ablations.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError, APITimeoutError, RateLimitError

# Load .env once at import time. Idempotent.
load_dotenv()

DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Sensible defaults per provider; override with --model on CLI.
DEFAULT_MODELS = {
    "deepinfra": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "openai": "gpt-4o-mini",
    # Free Tier 0 default — strongest of the free models per Spec v0.9 §1.3.
    # Override with --model openrouter ID like
    # "google/gemma-4-31b-it:free" or "deepseek/deepseek-r1:free".
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
}

PROVIDER_API_KEY_ENV = {
    "deepinfra": "DEEPINFRA_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def resolve_provider(provider: str) -> tuple[str, str | None, str]:
    """Return (provider, base_url, api_key) for ``provider``.

    The api_key may be ``None`` if not in the environment — callers should
    handle that explicitly so missing keys produce a clear error rather than
    a 401 from the server.
    """
    provider = provider.lower()
    if provider == "deepinfra":
        return provider, DEEPINFRA_BASE_URL, os.getenv("DEEPINFRA_API_KEY")
    if provider == "openai":
        return provider, None, os.getenv("OPENAI_API_KEY")
    if provider == "openrouter":
        return provider, OPENROUTER_BASE_URL, os.getenv("OPENROUTER_API_KEY")
    raise ValueError(
        f"Unknown provider: {provider!r} "
        f"(expected 'deepinfra', 'openai', or 'openrouter')"
    )


@dataclass(slots=True)
class LLMClientConfig:
    provider: str = "deepinfra"
    model: str | None = None  # auto-pick from DEFAULT_MODELS when None
    temperature: float = 0.0
    # 512 covers a P-R reasoning block (4 numbered points, ~50-80 tokens each)
    # plus the final classification line. P-A / P-B need much less but the
    # extra headroom is essentially free.
    max_tokens: int = 512
    timeout: float = 60.0
    max_retries: int = 3
    retry_backoff: float = 2.0  # multiplicative backoff base in seconds
    extra_kwargs: dict[str, Any] = field(default_factory=dict)
    # Optional fallback provider engaged after the primary's retries are
    # exhausted. Use openrouter primary + deepinfra fallback to keep running
    # if the OpenRouter quota / 5xx storm hits. Set to a different provider
    # name (e.g. "deepinfra"); leave None to disable fallback.
    fallback_provider: str | None = None
    fallback_model: str | None = None  # auto-pick when None


class LLMClient:
    """Synchronous chat completion wrapper.

    Returns the raw response text alongside a usage dict for cost tracking.
    """

    def __init__(self, config: LLMClientConfig | None = None) -> None:
        self.config = config or LLMClientConfig()
        provider, base_url, api_key = resolve_provider(self.config.provider)
        if not api_key:
            env = PROVIDER_API_KEY_ENV[provider]
            raise RuntimeError(
                f"Missing API key for provider {provider!r}. "
                f"Set {env} in .env or as an environment variable."
            )
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = self.config.model or DEFAULT_MODELS[provider]
        self._provider = provider

        # Optional fallback. We build the fallback OpenAI client eagerly so
        # the first failure doesn't have to discover a missing API key.
        self._fallback_client: OpenAI | None = None
        self._fallback_model: str | None = None
        self._fallback_provider: str | None = None
        if self.config.fallback_provider:
            fb_provider, fb_base_url, fb_api_key = resolve_provider(
                self.config.fallback_provider
            )
            if not fb_api_key:
                env = PROVIDER_API_KEY_ENV[fb_provider]
                raise RuntimeError(
                    f"Missing API key for fallback provider {fb_provider!r}. "
                    f"Set {env} in .env or unset fallback_provider."
                )
            self._fallback_client = OpenAI(api_key=fb_api_key, base_url=fb_base_url)
            self._fallback_model = (
                self.config.fallback_model or DEFAULT_MODELS[fb_provider]
            )
            self._fallback_provider = fb_provider
        self._n_fallback_calls = 0

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def fallback_provider(self) -> str | None:
        return self._fallback_provider

    @property
    def n_fallback_calls(self) -> int:
        return self._n_fallback_calls

    def _attempt(
        self,
        client: OpenAI,
        model: str,
        provider: str,
        messages: list[dict[str, str]],
        kwargs: dict[str, Any],
        max_retries: int,
    ) -> dict[str, Any] | Exception:
        """Run up to ``max_retries + 1`` attempts on one client. Return the
        successful response dict, or the final exception object."""
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            t0 = time.perf_counter()
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=self.config.timeout,
                    **kwargs,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                text = resp.choices[0].message.content or ""
                usage = {
                    "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                    "total_tokens": getattr(resp.usage, "total_tokens", 0),
                }
                return {
                    "text": text,
                    "usage": usage,
                    "latency_ms": elapsed_ms,
                    "model": model,
                    "provider": provider,
                    "finish_reason": resp.choices[0].finish_reason,
                    "attempt": attempt,
                }
            except (RateLimitError, APITimeoutError, APIError) as exc:
                last_exc = exc
                if attempt >= max_retries:
                    break
                time.sleep(self.config.retry_backoff ** attempt)
        return last_exc if last_exc is not None else RuntimeError("unknown LLM failure")

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send a single chat request. Returns dict with ``text``, ``usage``, ``latency_ms``.

        If a fallback provider is configured, retries are exhausted on the
        primary first, then the fallback gets one shot (with its own retries).
        ``provider`` / ``model`` in the response identify which side served
        the call so cost analysis can split the totals correctly.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        kwargs = dict(self.config.extra_kwargs)
        kwargs.setdefault(
            "temperature",
            self.config.temperature if temperature is None else temperature,
        )
        kwargs.setdefault(
            "max_tokens",
            self.config.max_tokens if max_tokens is None else max_tokens,
        )

        primary_result = self._attempt(
            self._client, self._model, self._provider,
            messages, kwargs, self.config.max_retries,
        )
        if isinstance(primary_result, dict):
            return primary_result

        if self._fallback_client is None:
            raise RuntimeError(
                f"LLM call failed after {self.config.max_retries + 1} attempts: "
                f"{primary_result!r}"
            )
        # Fallback path. Same retry budget on the secondary provider.
        self._n_fallback_calls += 1
        fb_result = self._attempt(
            self._fallback_client, self._fallback_model, self._fallback_provider,
            messages, kwargs, self.config.max_retries,
        )
        if isinstance(fb_result, dict):
            fb_result["fallback_used"] = True
            fb_result["primary_error"] = repr(primary_result)
            return fb_result

        raise RuntimeError(
            f"LLM call failed on primary ({self._provider}) and fallback "
            f"({self._fallback_provider}): primary={primary_result!r}  "
            f"fallback={fb_result!r}"
        )
