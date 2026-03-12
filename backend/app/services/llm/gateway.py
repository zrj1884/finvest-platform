"""Unified LLM Gateway — supports DeepSeek, Qwen, OpenAI-compatible APIs.

All providers expose an OpenAI-compatible chat completions endpoint,
so we use httpx to call them uniformly.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from an LLM API call."""

    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""

    api_key: str
    base_url: str
    model: str
    # Cost per 1M tokens (input, output) in USD
    cost_per_m_input: float = 0.0
    cost_per_m_output: float = 0.0


# Cost estimates per 1M tokens (approximate, may change)
PROVIDER_COSTS: dict[str, tuple[float, float]] = {
    "deepseek": (0.14, 0.28),  # DeepSeek V3
    "qwen": (0.80, 2.00),  # Qwen Plus
    "openai": (0.15, 0.60),  # GPT-4o-mini
}


@dataclass
class UsageTracker:
    """Track cumulative LLM API usage and cost."""

    total_requests: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_usd: float = 0.0
    by_provider: dict[str, dict[str, float]] = field(default_factory=dict)

    def record(self, resp: LLMResponse) -> None:
        self.total_requests += 1
        self.total_prompt_tokens += resp.prompt_tokens
        self.total_completion_tokens += resp.completion_tokens
        self.total_cost_usd += resp.cost_usd
        if resp.provider not in self.by_provider:
            self.by_provider[resp.provider] = {"requests": 0, "tokens": 0, "cost_usd": 0.0}
        self.by_provider[resp.provider]["requests"] += 1
        self.by_provider[resp.provider]["tokens"] += resp.total_tokens
        self.by_provider[resp.provider]["cost_usd"] += resp.cost_usd

    def summary(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "by_provider": self.by_provider,
        }


class LLMGateway:
    """Unified gateway for calling LLM APIs.

    Supports provider switching at runtime and tracks usage/cost.
    """

    def __init__(self, provider: str | None = None) -> None:
        self.provider = provider or settings.LLM_PROVIDER
        self.usage = UsageTracker()
        self._configs: dict[str, ProviderConfig] = {
            "deepseek": ProviderConfig(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                model=settings.DEEPSEEK_MODEL,
                cost_per_m_input=PROVIDER_COSTS["deepseek"][0],
                cost_per_m_output=PROVIDER_COSTS["deepseek"][1],
            ),
            "qwen": ProviderConfig(
                api_key=settings.QWEN_API_KEY,
                base_url=settings.QWEN_BASE_URL,
                model=settings.QWEN_MODEL,
                cost_per_m_input=PROVIDER_COSTS["qwen"][0],
                cost_per_m_output=PROVIDER_COSTS["qwen"][1],
            ),
            "openai": ProviderConfig(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model=settings.OPENAI_MODEL,
                cost_per_m_input=PROVIDER_COSTS["openai"][0],
                cost_per_m_output=PROVIDER_COSTS["openai"][1],
            ),
        }

    def _get_config(self, provider: str | None = None) -> ProviderConfig:
        p = provider or self.provider
        if p not in self._configs:
            raise ValueError(f"Unknown LLM provider: {p}")
        return self._configs[p]

    async def chat(
        self,
        messages: list[dict[str, str]],
        provider: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Send a chat completion request.

        Args:
            messages: Chat messages in OpenAI format [{"role": "...", "content": "..."}].
            provider: Override the default provider for this call.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            LLMResponse with content and usage metrics.
        """
        config = self._get_config(provider)
        p = provider or self.provider

        if not config.api_key:
            raise ValueError(f"API key not configured for provider: {p}")

        url = f"{config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()

        latency = (time.monotonic() - start) * 1000
        data = resp.json()

        # Parse response
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Calculate cost
        cost = (
            prompt_tokens * config.cost_per_m_input / 1_000_000
            + completion_tokens * config.cost_per_m_output / 1_000_000
        )

        result = LLMResponse(
            content=content,
            model=config.model,
            provider=p,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency,
            cost_usd=cost,
        )

        self.usage.record(result)
        logger.info(
            "LLM call: provider=%s model=%s tokens=%d cost=$%.6f latency=%.0fms",
            p, config.model, total_tokens, cost, latency,
        )

        return result

    async def complete(
        self,
        prompt: str,
        system: str = "You are a helpful financial analyst.",
        provider: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Convenience method: single prompt → response."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        return await self.chat(messages, provider=provider, temperature=temperature, max_tokens=max_tokens)
