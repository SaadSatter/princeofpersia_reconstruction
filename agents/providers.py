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

# USD per million tokens (input, output), base rates, no caching or batch.
# Verified 2026-10-26 against https://platform.claude.com/docs/en/about-claude/pricing
# ("Claude Haiku 4.5 | $1 / MTok ... | $5 / MTok"). Earlier value came from a
# reference cached 2026-10-06 and was the same. Re-check before each live
# trial day and update PRICE_DATE. A model missing here has unknown cost
# (None), never $0.
PRICE_DATE = "2026-10-26"
PRICE_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
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


class ProviderConfigError(RuntimeError):
    """A setup problem found before any model call. Nothing was sent or counted."""


def check_credentials(provider: str) -> None:
    """Fail before the first call if the credential cannot work.

    The anthropic SDK accepts a missing or empty key when the client is built
    and fails only inside each request, so a bad setup used to look like an
    episode of failed calls (first live attempt, 2026-10-26). Messages name
    the variable, never its value."""
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if key is None:
            raise ProviderConfigError("ANTHROPIC_API_KEY is not set in this process. "
                                      "Export it in the same shell that runs evaluate.py.")
        if not key.strip():
            raise ProviderConfigError("ANTHROPIC_API_KEY is set but empty. "
                                      "Set it again, then re-run.")
        if key != key.strip():
            raise ProviderConfigError("ANTHROPIC_API_KEY has leading or trailing whitespace "
                                      "(for example a newline). Remove it, then re-run.")
    elif provider == "vertex" and not os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip():
        raise ProviderConfigError("GOOGLE_CLOUD_PROJECT is not set (needed for Vertex AI).")


# HTTP status -> failed-call kind (platform.claude.com API errors page).
_STATUS_KINDS = {400: "bad_request", 401: "auth_rejected", 403: "permission_denied",
                 404: "model_not_found", 413: "request_too_large", 429: "rate_limited",
                 529: "overloaded"}


def classify_error(exc: BaseException) -> str:
    """A short, safe category for a failed call; it never contains the message."""
    if isinstance(exc, ProviderConfigError) or (
            isinstance(exc, TypeError) and "authentication method" in str(exc)):
        return "auth_missing"           # the SDK's error for a missing or empty key
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return _STATUS_KINDS.get(status) or ("server_error" if status >= 500 else f"http_{status}")
    name = type(exc).__name__           # SDK: APITimeoutError subclasses APIConnectionError
    if "Timeout" in name:
        return "provider_timeout"
    if "Connection" in name:
        return "connection_error"
    return "other"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, model: str, timeout_s: float = 15.0, max_tokens: int = 400):
        check_credentials(self.name)
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
