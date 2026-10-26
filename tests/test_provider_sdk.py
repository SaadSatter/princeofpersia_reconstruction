"""AnthropicProvider against the installed `anthropic` SDK, with no network.

The SDK talks to a mock HTTP transport, so this checks the request we build
and how we read the response, not the live API. It is skipped when the
`model` extra is not installed (as in CI: `uv sync --frozen` has no extras).
Run locally with: uv run --extra model pytest -q tests/test_provider_sdk.py
"""

import json

import pytest

anthropic = pytest.importorskip("anthropic")
httpx = pytest.importorskip("httpx")

from agents.providers import (AnthropicProvider, ProviderConfigError,  # noqa: E402
                              classify_error)

REPLY = {
    "id": "msg_test", "type": "message", "role": "assistant",
    "model": "claude-haiku-4-5-20251001",
    "content": [{"type": "text", "text": '{"action": "WAIT", "reason": "test"}'}],
    "stop_reason": "end_turn", "stop_sequence": None,
    "usage": {"input_tokens": 123, "output_tokens": 9},
}


class _Offline(AnthropicProvider):
    def __init__(self, handler, **kw):
        self._handler = handler
        super().__init__(**kw)

    def _make_client(self, anthropic, timeout_s):
        client = super()._make_client(anthropic, timeout_s)    # the real settings
        return client.with_options(http_client=httpx.Client(
            transport=httpx.MockTransport(self._handler)))


def test_adapter_builds_one_request_and_reads_text_usage_and_request_id(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=REPLY, headers={"request-id": "req_test"})

    p = _Offline(handler, model="claude-haiku-4-5", timeout_s=15.0)
    assert p._client.max_retries == 0 and p._client.timeout == 15.0
    c = p.complete("system text", "user text")

    assert len(seen) == 1
    body = json.loads(seen[0].content)
    assert body["model"] == "claude-haiku-4-5" and body["max_tokens"] == 400
    assert body["system"] == "system text"
    assert body["messages"] == [{"role": "user", "content": "user text"}]
    assert not {"temperature", "top_p", "top_k"} & set(body)   # 400 on API 2026-10-21
    assert seen[0].headers["x-api-key"] == "test-key-not-real"  # from the environment
    assert (c.text, c.model, c.tokens_in, c.tokens_out, c.request_id) == (
        '{"action": "WAIT", "reason": "test"}', "claude-haiku-4-5-20251001", 123, 9, "req_test")


def test_adapter_does_not_retry_a_failed_request(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(529, json={"type": "error", "error": {
            "type": "overloaded_error", "message": "Overloaded"}})

    p = _Offline(handler, model="claude-haiku-4-5")
    with pytest.raises(anthropic.APIStatusError):
        p.complete("s", "u")
    assert len(seen) == 1            # one counted call is one HTTP request


def test_sdk_no_key_error_is_classified_and_the_adapter_now_stops_first(monkeypatch):
    """The SDK's own behaviour behind the 2026-10-26 failed live attempt: with
    an empty key the client builds, and the request raises TypeError without
    sending anything. The adapter now refuses to build instead."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    seen = []
    client = anthropic.Anthropic(max_retries=0, http_client=httpx.Client(
        transport=httpx.MockTransport(lambda r: seen.append(r) or httpx.Response(200, json=REPLY))))
    with pytest.raises(TypeError) as exc:
        client.messages.create(model="claude-haiku-4-5", max_tokens=1,
                               messages=[{"role": "user", "content": "x"}])
    assert seen == [] and classify_error(exc.value) == "auth_missing"
    with pytest.raises(ProviderConfigError):
        AnthropicProvider(model="claude-haiku-4-5")


@pytest.mark.parametrize("status,kind", [(401, "auth_rejected"), (404, "model_not_found"),
                                         (429, "rate_limited"), (529, "overloaded")])
def test_sdk_status_errors_get_their_kind(monkeypatch, status, kind):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    p = _Offline(lambda r: httpx.Response(status, json={"type": "error", "error": {
        "type": "x", "message": "m"}}), model="claude-haiku-4-5")
    with pytest.raises(anthropic.APIStatusError) as exc:
        p.complete("s", "u")
    assert classify_error(exc.value) == kind
