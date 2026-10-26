"""Model provider adapters. Credentials come only from the environment.

    anthropic  ANTHROPIC_API_KEY            (default; model from POP_MODEL)
    vertex     Google ADC + GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION
               (Claude on Vertex AI through the same anthropic SDK)
    fake       scripted replies for tests; never touches the network

SDK imports are lazy so tests and CI run without the `model` extra installed.
The SDK's own retries are disabled: every request must be one counted call.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL = "claude-haiku-4-5"

# USD per million tokens (input, output). Source: Anthropic's published list
# price for Claude Haiku 4.5, as given in the claude-api reference cached
# 2026-10-06. Re-check https://www.anthropic.com/pricing on the day of a
# live run and update PRICE_DATE if it changed.
PRICE_DATE = "2026-10-06"
PRICES = {"claude-haiku-4-5": (1.00, 5.00)}


@dataclass
class Completion:
    text: str
    model: str               # model id as returned by the provider
    tokens_in: int
    tokens_out: int
    request_id: str | None = None


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float | None:
    for key, (p_in, p_out) in PRICES.items():
        if model == key or model.startswith(key):
            return round((tokens_in * p_in + tokens_out * p_out) / 1_000_000, 6)
    return None


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str, timeout_s: float = 15.0, max_tokens: int = 400):
        import anthropic  # lazy: only needed for live runs

        self.model = model
        self.max_tokens = max_tokens
        self._client = self._make_client(anthropic, timeout_s)

    def _make_client(self, anthropic, timeout_s):
        return anthropic.Anthropic(timeout=timeout_s, max_retries=0)

    def complete(self, system: str, user: str) -> Completion:
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        return Completion(text=text, model=msg.model, tokens_in=msg.usage.input_tokens,
                          tokens_out=msg.usage.output_tokens,
                          request_id=getattr(msg, "_request_id", None))


class VertexProvider(AnthropicProvider):
    """Claude on Vertex AI. Untested in this project so far (no live Vertex run)."""

    name = "vertex"

    def _make_client(self, anthropic, timeout_s):
        return anthropic.AnthropicVertex(
            project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
            region=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
            timeout=timeout_s, max_retries=0)


class FakeProvider:
    """Replays canned replies (cycling). For tests and dry runs; no network."""

    name = "fake"

    def __init__(self, replies, model: str = "fake-model", tokens=(50, 10)):
        self.replies = list(replies)
        self.model = model
        self.tokens = tokens
        self.calls = 0
        self.prompts: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> Completion:
        self.prompts.append((system, user))
        reply = self.replies[self.calls % len(self.replies)]
        self.calls += 1
        if isinstance(reply, Exception):
            raise reply
        return Completion(text=reply, model=self.model, tokens_in=self.tokens[0],
                          tokens_out=self.tokens[1])


def make_provider(name: str, model: str | None = None, timeout_s: float = 15.0):
    model = model or os.environ.get("POP_MODEL", DEFAULT_MODEL)
    if name == "anthropic":
        return AnthropicProvider(model, timeout_s)
    if name == "vertex":
        return VertexProvider(model, timeout_s)
    raise ValueError(f"Unknown provider {name!r}. Available: anthropic, vertex "
                     "(an OpenAI adapter is not implemented).")
