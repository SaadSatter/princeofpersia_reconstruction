# Change summary for the independent reviewer — session 04 (R-D25)

For `.claude/agents/rules-reviewer.md`. Written by the implementation agent;
not a review.

**Trigger.** The first live attempt (`traces/live/20261026T162629Z-model-history-S1-0.jsonl`)
made 40 calls and all 40 failed with the `anthropic` SDK's `TypeError: Could
not resolve authentication method`: 0 tokens, 0.6 ms mean latency, 40 WAIT
fallbacks, `step_limit`. The SDK builds a client without a key and raises
this error inside each request when `ANTHROPIC_API_KEY` is unset or empty.
Nothing is sent.

**Change (R-D25).**
1. `agents/providers.py` `check_credentials`: rejects an unset, empty, or
   whitespace-padded key with `ProviderConfigError`, before the SDK is
   imported. It names the variable, never its value. `AnthropicProvider`
   calls it in `__init__`, and `evaluate.py` calls it before any episode
   (exit 2, no trace).
2. `classify_error`: maps an exception to a fixed category (HTTP status,
   SDK class name, or the SDK's no-key TypeError).
3. `ModelPlayer.decide` tags provider exceptions with `error_kind` and
   re-raises them. The runner records `error_kind` per step (`timeout`,
   `unparseable_reply`, `player_error` for untagged) and `failed_call_kinds`
   per episode.
4. `pop/runner.py` `safe_error_text`: redacts `sk-ant-…` and bearer tokens
   and caps error text at 300 characters.
5. `tools/smoke_provider.py`: new. Makes exactly one tiny call (max 8 output
   tokens) when given `--live`; `--check-only` makes no network call. It is
   **outside the runner**; see audit finding 1.

**Unchanged:** call counting, limits, timeouts, fallback labels, game rules,
the frozen suite, the baseline.

**Please check:** that the preflight cannot skip or hide a counted call;
that no trace field can carry a key; that the categories are correct for
the SDK's real exceptions; whether the smoke tool's exception to "every
call goes through the runner" is acceptable.

Tests: `tests/test_regressions.py` (the `test_regression_missing_api_key_*` and
`test_regression_failed_calls_had_no_error_category` tests failed before the
change), `tests/test_provider_sdk.py` (local, needs the `model` extra),
`tests/test_evaluate.py::test_smoke_tool_needs_live_and_a_key_and_sends_one_request`.
Audit: `docs/audits/AUDIT-2026-10-26-session04-live-attempt-fix.md` (same session).
