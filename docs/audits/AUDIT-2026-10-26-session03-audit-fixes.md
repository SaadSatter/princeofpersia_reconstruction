# Audit — 2026-10-26 — session 03 (fixes for session-02 findings F-1, F-2)

| Field | Value |
| --- | --- |
| Date | 2026-10-26 |
| Code audited | working tree on top of `06ff044` (uncommitted at audit time; committed afterwards in this session, see `docs/agent-sessions/03-audit-fixes-live-prep.md`) |
| Auditor | `/game-rules-audit` skill, run inside the implementation session that wrote the fix. **Not an independent review.** The change summary for `.claude/agents/rules-reviewer.md` is in `docs/reviews/CHANGE-SUMMARY-session03.md` |
| Scope | `pop/runner.py`, `agents/model_player.py`, `agents/providers.py`, `evaluate.py`, `tests/test_regressions.py`, `tests/test_provider_sdk.py`, `docs/RULE_SOURCE_MAP.md` (R-D23, R-D24), `docs/GAME_SPEC.md` §7 |
| Files read | `docs/MIDTERM_GUIDELINES.md`, `docs/GAME_SPEC.md` §7, `docs/RULE_SOURCE_MAP.md`, `docs/REQUIREMENTS_CHECKLIST.md`, `pop/runner.py`, `agents/model_player.py`, `agents/providers.py`, `agents/baseline.py`, `evaluate.py`, `tests/test_runner.py`, `tests/test_model_player.py`, `tests/test_regressions.py`, `tests/test_evaluate.py` |
| Commands | `uv run --frozen pytest -q` → 111 passed, 1 skipped; `uv run --frozen pytest -q -k "leak or legal or limit or determin"` → 27 passed, 1 skipped, 84 deselected; `uv run --extra model pytest -q tests/test_provider_sdk.py` → 2 passed; `grep -rn "import pygame" pop/` → no output; `grep -rn "pop.engine\|pop.levels\|GameState\|open(" agents/` → no output |

Checks A, B, C and E concern code this change does not touch; they were not
re-read line by line. Their tests were re-run and pass; results are carried
forward from `AUDIT-2026-10-26-session02-agents.md`.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| A1–A3 | PASS (carried forward) | unchanged files; `tests/test_interface.py` passes |
| B1–B4 | PASS (carried forward) | unchanged files; leak tests pass |
| B5 prompt from obs + legal + own history only | PASS | `agents/model_player.py` imports still only `pop.runner.Decision`, `pop.tiles.LEGEND`, `.providers.estimate_cost` (+ stdlib `threading`). History now comes from `_memory_after` (`agents/model_player.py:110`), a copy of committed memory plus the current observation; same text as before (`test_history_is_bounded_and_obs_only_has_none`, `test_seen_rooms_come_only_from_rooms_already_visited` pass unchanged) |
| B6 baseline same inputs | PASS (carried forward) | `agents/baseline.py` unchanged |
| C1–C4 | PASS (carried forward) | unchanged; tests pass |
| D1 step limit | PASS | `test_step_limit_through_runner` |
| D2 call limit, failed calls count | PASS | `test_call_limit_counts_every_call`, `test_failed_calls_count_and_fallbacks_are_labeled`; SDK makes exactly one HTTP request per call even on 529 (`tests/test_provider_sdk.py::test_adapter_does_not_retry_a_failed_request`) |
| D3 per-call timeout in code, labeled fallback | PASS (F-1 fixed) | `pop/runner.py:53` returns the abandoned `(thread, box)`; `run_episode` never reads it during the episode (`pop/runner.py:125-129`), only at the end in `_late_reply` (`pop/runner.py:76`). Player memory is written only in `ModelPlayer.commit` (`agents/model_player.py:124`), called by the runner after `ep.step` (`pop/runner.py:151`). `test_regression_late_reply_after_timeout_rewrote_player_memory` failed before the change (prompt 3 contained `RUN_JUMP_RIGHT ->`), passes after; 5/5 repeat runs passed |
| D4 trace record fields | PASS with note | step fields unchanged; header gains `late_replies` (`i`, `status`, tokens, cost). Unknown cost is `null` (F-2 fixed): `agents/model_player.py:173`, `pop/runner.py:95` `_sum_cost`, `evaluate.py` `_sum_cost` / `table_md` prints `unknown`. `test_regression_unknown_model_price_reported_as_free` failed before (`0.0 is None`), passes after |
| D5 runner owns the Episode | PASS | unchanged; `commit` receives `copy.deepcopy(obs)` |
| E1 human/agent same step | NOT IMPLEMENTED | `play.py` does not exist |
| E2 no pygame in pop/ | PASS | grep empty |
| E3, E4 | PASS (carried forward) | determinism tests pass |
| F1 touched rules agree | PASS | R-D23 ↔ `pop/runner.py` + `ModelPlayer.commit` ↔ regression test; R-D24 ↔ `_sum_cost` ×2 + `cost_usd: None` ↔ regression test + `test_late_reply_still_pending_at_episode_end_has_unknown_cost`; GAME_SPEC §7 text added |
| F2 no label promoted | PASS | only `design` rows R-D23, R-D24 appended |

## Findings (most severe first)

- [note] `agents/baseline.py:240-245` — the baseline still updates its memory inside `decide`, so the R-D23 guarantee holds only for players that use `commit`. Evidence: the baseline decides in ≈0.2 ms against a 20 s timeout, so it has never timed out; the runner docstring (`pop/runner.py:14-18`) states the contract. Moving the baseline to `commit` would change the baseline, which the student ruled out.
- [note] `pop/runner.py:76` — a late reply still `pending` at episode end makes the episode cost `null`. This is accurate (the call may be billed) but one hung call hides the cost of the whole episode; the tokens of the other calls stay visible.
- [note] `tests/test_provider_sdk.py` — skipped in CI because CI installs no extras (`uv sync --frozen`). It verifies the adapter against SDK 0.125.0 locally only.
- [note] `agents/providers.py` `PRICE_DATE` — price re-verified 2026-10-26 ($1 / $5 per MTok for Claude Haiku 4.5, platform.claude.com pricing page). The deprecations page lists `claude-haiku-4-5-20251001` as Active with "not sooner than October 15, 2026" as its tentative retirement date, which has passed; re-check before each trial day.

## Not checked

- Live model behavior: no `ANTHROPIC_API_KEY` in this session's environment; no live call made by this session.
- Independent review of this change: pending (`rules-reviewer`).
- `play.py`: not implemented.
- Course workflow in `game-dev-f26`: not run.
