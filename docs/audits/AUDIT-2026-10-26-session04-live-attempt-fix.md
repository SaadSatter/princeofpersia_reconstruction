# Audit — 2026-10-26 — session 04 (failed live attempt, R-D25)

| Field | Value |
| --- | --- |
| Date | 2026-10-26 |
| Code audited | working tree on top of `b2a6e2a` (uncommitted at audit time; committed afterwards, see `docs/agent-sessions/04-live-attempt-diagnosis.md`) |
| Auditor | `/game-rules-audit` skill, run inside the implementation session that wrote the change. **Not an independent review.** Change summary for `.claude/agents/rules-reviewer.md`: `docs/reviews/CHANGE-SUMMARY-session04.md` |
| Scope | `pop/runner.py` (`error_kind`, `failed_call_kinds`, `safe_error_text`), `agents/providers.py` (`check_credentials`, `classify_error`), `agents/model_player.py` (exception tagging), `evaluate.py` (credential preflight, warning), `tools/smoke_provider.py` (new), `tests/test_regressions.py`, `tests/test_provider_sdk.py`, `tests/test_evaluate.py`, `docs/RULE_SOURCE_MAP.md` R-D25, `docs/GAME_SPEC.md` §7 |
| Files read | `docs/GAME_SPEC.md` §7, `docs/RULE_SOURCE_MAP.md`, `pop/runner.py`, `agents/model_player.py`, `agents/providers.py`, `evaluate.py`, `tools/smoke_provider.py`, the tests above, `traces/live/20261026T162629Z-model-history-S1-0.jsonl` |
| Commands | `uv run --extra model pytest -q` → 125 passed; `uv run --extra model pytest -q -k "leak or legal or limit or determin"` → 28 passed, 97 deselected; CI-like env without extras (`UV_PROJECT_ENVIRONMENT=<scratch> uv sync --frozen`, then `pytest -q`) → 118 passed, 1 skipped; `grep -rn "import pygame" pop/` → no output; `grep -rn "pop.engine\|pop.levels\|GameState\|open(" agents/` → no output |

Checks A, B1–B3, B6, C and E3–E4 concern code this change does not touch.
Their tests were re-run and pass; results are carried forward from
`AUDIT-2026-10-26-session03-audit-fixes.md`.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| A1–A3 | PASS (carried forward) | `pop/interface.py` unchanged |
| B1–B3 | PASS (carried forward) | `pop/observation.py` unchanged; leak tests pass |
| B4 step results reveal nothing hidden | PASS | new text is provider error text and a category (`pop/runner.py:180`); neither comes from the engine. `ModelPlayer.commit` writes only "WAIT (failed call)" to memory, so error text never reaches a prompt |
| B5 prompt from obs + legal + own history | PASS | `agents/model_player.py` gains only `classify_error` (`:22`); agents grep empty |
| B6 | PASS (carried forward) | `agents/baseline.py` unchanged |
| C1–C4 | PASS (carried forward) | unchanged |
| D1 step limit | PASS | `test_step_limit_through_runner`; the failed live attempt itself ended `step_limit` at 40 |
| D2 call limit, failed calls count | PASS | counting unchanged (`pop/runner.py:150-163`). The preflight (`evaluate.py:150-154`) runs before any episode and makes no call, so it neither counts nor skips one. `test_regression_missing_api_key_became_40_fallback_waits` (exit 2, no trace) |
| D3 timeout, labeled fallback | PASS | timeout path now also returns kind `"timeout"` (`pop/runner.py:88`); `test_runner` timeout tests unchanged and pass |
| D4 trace record fields | PASS with note | step gains `error_kind` (`pop/runner.py:180`), header gains `failed_call_kinds` (`:211`); error text redacted and capped (`:59-66`), `test_error_text_in_traces_never_contains_a_key`. Kinds tested: `test_regression_failed_calls_had_no_error_category`, `test_failed_call_kinds_cover_provider_errors_timeouts_and_bad_replies`, SDK-level `test_sdk_status_errors_get_their_kind` (local only) |
| D5 runner owns the Episode | PASS | unchanged |
| E1 | NOT IMPLEMENTED | `play.py` does not exist |
| E2 no pygame in pop/ | PASS | grep empty |
| E3, E4 | PASS (carried forward) | determinism tests pass |
| F1 touched rules agree | PASS | R-D25 ↔ `check_credentials` / `classify_error` / runner fields ↔ the regression tests above; GAME_SPEC §7 sentence added |
| F2 no label promoted | PASS | one new `design` row |

## Findings (most severe first)

- [should fix] `tools/smoke_provider.py:79` — calls the provider directly, outside the runner, which conflicts with CLAUDE.md "Every call goes through the runner" — the tool records model id, latency, tokens, cost and error kind itself and is not an episode, but the student must approve the exception (or ask for it to go through `run_episode`) before it is run.
- [note] `agents/providers.py:78` `classify_error` — `auth_missing` is detected by matching the SDK's TypeError text ("authentication method"); a future SDK wording change would turn it into `other`. Evidence: only the local SDK test (`tests/test_provider_sdk.py`) checks the real message; CI skips it. The preflight check does not depend on this.
- [note] `pop/runner.py:94` `_late_reply` — a late call that fails is logged `status: "failed"` without an `error_kind`. Minor; late failures carry no usage.
- [note] `pop/runner.py:150` — a rejected key (HTTP 401) still runs a full episode of counted, unbilled failed calls; only a missing/blank key is stopped before the run. Stopping early after repeated auth failures would change runner limits, which is the student's decision.
- [note] `agents/providers.py:50` — a whitespace-padded key is rejected, not trimmed. Conservative; the message tells the user what to fix without showing the value.

## Not checked

- Live behaviour: no live call made; the smoke test awaits the student's approval and key.
- Independent review of R-D25: pending (`rules-reviewer`).
- `play.py`: not implemented.
- Course workflow in `game-dev-f26`: not run.
