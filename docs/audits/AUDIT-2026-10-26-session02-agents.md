# Audit — 2026-10-26 — session 02 (agents, runner R-D22, evaluator)

| Field | Value |
| --- | --- |
| Date | 2026-10-26 |
| Commit audited | `e91e9b0` |
| Auditor | `/game-rules-audit` skill, run inside implementation session `159ae00b-e523-4413-a369-e4a064ef34a7` (the same session that wrote the code — **this is not an independent review**; see `.claude/agents/rules-reviewer.md` for that) |
| Scope | `pop/runner.py` (R-D22), `agents/baseline.py`, `agents/model_player.py`, `agents/providers.py`, `evaluate.py`; commits `8a1fbf0..e91e9b0` |
| Files read | `docs/MIDTERM_GUIDELINES.md`, `docs/GAME_SPEC.md`, `docs/RULE_SOURCE_MAP.md`, `docs/REQUIREMENTS_CHECKLIST.md`, `pop/interface.py`, `pop/observation.py`, `pop/runner.py`, `pop/engine.py`, `agents/*.py`, `evaluate.py`, `tests/` |
| Commands | `uv run pytest -q` → 108 passed; `uv run pytest -q -k "leak or legal or limit or determin"` → 27 passed, 81 deselected; `grep -rn "import pygame" pop/` → no output; `grep -rn "pop.engine\|pop.levels\|GameState\|open(" agents/` → no output |

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| A1 five operations | PASS | `pop/interface.py:41,52,58,65,87`; `tests/test_interface.py::test_five_operations_exist` |
| A2 unknown player rejected | PASS | `pop/interface.py:117`; `test_unknown_player_is_rejected` |
| A3 outcome fields | PASS with note | `outcome()` (`pop/interface.py:87`) returns status, reason, score, actions, invalid_actions, frames. Calls are in the runner result (`model_calls`, `failed_calls`), not in `outcome()`; see note N3 |
| B1 observation keys | PASS | `pop/observation.py` `OBSERVATION_KEYS`; `test_observation_has_exactly_the_allowed_keys`. Runner adds only `calls_left` (`pop/runner.py`, GAME_SPEC §8 "calls left") |
| B2 no other rooms / links / timers | PASS | `test_observation_shows_only_the_current_room`, `test_observation_hides_links_ids_and_held_out_status`, `test_gate_state_shows_openness_not_timers` |
| B3 legal list by posture only | PASS | `pop/engine.py` `LEGAL_BY_POSTURE`; `test_legal_actions_depend_only_on_posture` |
| B4 step results reveal nothing hidden | PASS | `test_step_result_reveals_nothing_beyond_the_observation`; R-D22 error text is the fixed string `"unparseable reply"` |
| B5 prompt built from obs + legal + own history only | PASS | `agents/model_player.py` imports only `pop.runner.Decision`, `pop.tiles.LEGEND`; `tests/test_architecture.py::test_players_cannot_import_the_engine_situations_or_solutions`; `tests/test_model_player.py::test_prompts_reveal_no_situation_ids_links_or_routes`, `::test_seen_rooms_come_only_from_rooms_already_visited` |
| B6 baseline uses same inputs | PASS with note | `agents/baseline.py` has no imports beyond stdlib; reads only `observation` keys. Asymmetry (disclose): its rules knowledge is hand-coded search, the model's is prompt text; baseline compute is unbounded per decision (sub-ms in practice). See N1 |
| C1 unknown action rejected, no state change | PASS | `test_invalid_actions_are_refused_counted_and_change_nothing` compares `snapshot()` before/after |
| C2 non-string action invalid | PASS | same parametrized test; `INVALID_NOT_TEXT` |
| C3 actions after terminal refused | PASS | `test_terminal_episode_refuses_actions_without_counting` |
| C4 consecutive-invalid limit | PASS | `test_five_consecutive_invalid_actions_end_the_episode`; `tests/test_model_player.py::test_illegal_model_action_counts_invalid_not_fallback` |
| D1 step limit | PASS | `pop/interface.py` `step_limit`; `test_step_limit_through_runner` |
| D2 call limit, failed calls count | PASS | `test_call_limit_counts_every_call`, `test_failed_calls_count_and_fallbacks_are_labeled`, `test_provider_error_counts_as_failed_call_and_falls_back`; SDK retries off (`agents/providers.py` `max_retries=0`) |
| D3 per-call timeout in code, labeled fallback | PASS with finding | `pop/runner.py:_call_with_timeout` (thread join); `test_timeout_produces_labeled_fallback`. See F-1 (abandoned thread) |
| D4 trace record fields | PASS with note | `pop/runner.py:112-121`: i, action, source, accepted, error, effect, frames, latency_ms, meta (tokens_in/out, cost_usd, model, raw, parsed_action for the model). Baseline steps have empty `meta` (no tokens) — summary treats as 0 |
| D5 runner owns the Episode | PASS | `pop/runner.py:run_episode` creates `Episode`; players get `copy.deepcopy(obs)` and `list(legal)`; `test_player_gets_copies_not_the_episode_state` |
| E1 human and agent use the same step | NOT IMPLEMENTED (play.py) | `play.py` does not exist. Interim `play_text.py` calls `Episode.step` like the runner |
| E2 no pygame in pop/ | PASS | grep empty; `test_engine_never_imports_pygame` |
| E3 macro frames ≤ 12 | PASS | `pop/engine.py:perform` asserts `frames <= MAX_FRAMES` |
| E4 determinism | PASS | `tests/test_determinism.py` (2 tests), `tests/test_baseline.py::test_baseline_is_deterministic` |
| F1 touched rules agree | PASS | R-D22 row (`docs/RULE_SOURCE_MAP.md`), `pop/runner.py` (Decision.fallback_reason), tests `test_unparseable_reply_is_a_labeled_fallback_that_keeps_its_metadata`, `test_parseable_but_illegal_model_action_is_submitted_and_counted_invalid` (written first; 2 failed before the change) |
| F2 no label promoted | PASS | This session's map diff (`git diff 86a1111 -- docs/RULE_SOURCE_MAP.md`) only appends R-D22 |

## Findings (most severe first)

- [should fix] `pop/runner.py:_call_with_timeout` — a timed-out decision thread keeps running; a `ModelPlayer` reply that arrives late can still update the player's `_pending`/history while the next decision runs, and its tokens are never recorded — evidence: thread is a daemon and is not cancelled; the provider's own timeout (15 s, `agents/providers.py`) is below the runner's 20 s, which makes this unlikely but not impossible.
- [should fix] `evaluate.py:summarize` — cost sums `cost_usd` and treats unknown-price models as 0.0 without flagging them in the table — evidence: `agents/model_player.py` sets `cost_known`, but `summarize` ignores it. Only affects a non-Haiku `--model`.
- [note] N1 `agents/baseline.py` — the baseline is a planner with a hand-coded rules model; it won 12/12 on the final suite. Ceiling effect: the suite cannot show the model beating the baseline, only matching or trailing it. Disclose in EVALUATION.md.
- [note] N2 `agents/providers.py:PRICES` — price is from a reference cached 2026-10-06, not verified against the live pricing page on the run day.
- [note] N3 `pop/interface.py:outcome` — call counts live in the runner result, not `outcome()`. Acceptable because the runner, not the Episode, owns calls; document in README.
- [note] N4 `agents/providers.py:VertexProvider` — never run (no credentials); labeled untested in code.

## Not checked

- Live model behavior: no `ANTHROPIC_API_KEY` in this environment; no live call was made.
- `play.py` (Pygame frontend): not implemented yet (plan item 9).
- The course-repo workflow on GitHub: `ci/midterm-saadsatter.yml` has only been checked statically (`tests/test_ci_workflow.py`) and its commands rehearsed locally in a copy at `midterms/saadsatter/`; it has not run in `game-dev-f26`.
