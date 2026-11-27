---
handoff_id: HO-T22-fix2-evaluation-specialist
task_id: T22-fix2
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T22-fix2-qa.md@b188161 (and docs/final/orchestration/reports/T22-fix2-tech-lead.md@9b59677; brief docs/final/orchestration/tasks/T22-fix2.md@d35fe93; my T22-fix1 report@967db26; T20 Gate 2 report on orch/reviewed 1a515ca)
source_branch: gate/T22-fix2-eval
source_commit: see the branch head (test commit e142f51; this report is committed after it)
reviewed_commit: 9b59677 (with QA's work at b188161)
verdict: ACCEPT
---

# T22-fix2: Evaluation Specialist report (Gate 2)

Status: done. No training, no `--live`, no H6 run. Only `tests/test_eval_T22fix2_boundary.py` (new) and this report were written. No gameplay, encoder, trainer or other author's test was touched.

## Verdict
**ACCEPT.** The AI seat boundary holds in AI rooms with telemetry on, parity holds after the merge, telemetry never touches the duel, and the weights cache is sound. Nothing blocks Gate 3 from a Gate 2 view. Two wall-clock tests are load-sensitive (details below); that is a test-hardening matter, not a product defect.

## Work completed
Read the brief, my T22-fix1 report, the T20 Gate 2 report, the Tech Lead and QA reports. Read `server/match.py` (`_tick`, `_start_rec`, `_note_fallbacks`), `server/telemetry.py` (recorder seats), `agents/modes.py` (`_shared_net`, `step_ai_seat`). Wrote 18 tests (all pass, 15 s).

## Acceptance criteria to evidence (Gate 2 scope)
| # | Item | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Telemetry in an AI room holds only the human seat's facts | yes | `test_ai_room_logs_hold_only_seat_a_even_with_many_fallbacks`: budget 0 forces fallbacks (non-vacuous, asserted in the trace). The directory holds exactly `...-A.jsonl` and `...-host.json`. Neither contains "fallback", "source", "policy", "ppo", "macro", "weights", the shipped SHA-256, "seat b" or `"b"`. Every `seat` field is A. No client message contains "fallback". |
| 2 | Recorder ignores seat B's inputs | yes | `test_recorder_ignores_seat_b_inputs_even_when_handed_them`: `after_tick` is fed extra `("B", ...)` accepted inputs on every tick; A's log is byte-identical to the unfed run. (The recorder filters by its own `seats`, which for an AI room is `("A",)`.) |
| 3 | Human rooms still log both seats, each in its own file | yes | `test_human_room_still_logs_each_seat_in_its_own_file_only`; T20's `test_a_log_is_identical_whatever_b_hides` passes in the full suite. |
| 4 | Parity: game hook == runner | yes | `test_game_hook_equals_runner_after_the_merge`, seeds 0, 1, 2, 5, 7, 11 (720 frames, ARENA, baseline A, shipped rival B): equal final snapshots, 0 fallbacks, 0 policy errors. My T22-fix1 test (seeds 0, 3) also passes. |
| 5 | Parity: server `Match` == game hook, telemetry on | yes | `test_server_match_equals_game_hook_with_telemetry_on`, same 6 seeds, idle A: equal snapshots, fallback counters `(0,0,0)`, only the A log written. By transitivity the server equals the runner. |
| 6 | Telemetry never changes the duel | yes | `test_telemetry_changes_nothing_in_an_ai_room_with_a_busy_human`: seeds 3 and 9, 900 ticks of random keys, with and without telemetry: trace, `state_hash`, every client message and the final snapshot are equal. T20's four-seed human/baseline test and TL/QA's local-run tests (screenshots equal in ai, baseline, human) also pass. |
| 7 | Weights cache on (path, digest) | yes | `test_weights_cache_keyed_on_path_and_digest_and_refuses_a_wrong_hash`: a warm hit returns the same net; the key is `(path, digest)`; a wrong hash is refused with the cache warm; a same-path edited file is refused (the QA-T22fix1-1 hole is closed). |

## Findings

**Cache (item 3 of the brief): sound.** The bytes are hashed on every call. Only a file whose digest equals the expected hash right now can be a hit, so a cache can never serve a net for a file that no longer matches. A mismatch goes to `load_net`, which raises `WeightsError`. The path stays in the key (the existing test requires it). The cost is a read plus SHA-256, about 0.3 ms (my T22-fix1 figure; not re-measured here). On a miss the file is read twice; `load_net` re-checks the hash, so a race cannot yield a wrong net.

**Boundary in AI rooms.** The recorder is built with `human_seats` only. `_tick` hands it `accepted` including seat B's inputs, and the recorder drops them by its own seats (probe 2). Fallbacks go to `Match._fallbacks` and the trace, never to the recorder (probe 1). The host JSON lists only A. The header carries `rival` = mode id (`ai` or `baseline`), no weights hash or path. No client message gains a field.

**One disclosure, carried from T20 and unchanged.** The header `rival` field says "ai" or "baseline" in the host-side file. That is the mode the human chose and was shown, so it is not a hidden fact. The seed is in the header, so a seat's file must not be handed back to its player (T20 note; still not in TELEMETRY.md).

**Telemetry and determinism.** The server AI seat has a wall-clock budget (0.04 s) and so is the one place where added CPU could in principle change a trace (T20 residual risk). Measured here: with a 5 s budget the traces are equal, and with the default budget the shipped rival never fell back in the parity runs. In a heavily loaded process a late answer would be a labelled fallback, as it is without telemetry.

**Flakiness.** Two wall-clock tests failed under load in QA's runs. Neither is touched by the merge, and I did not edit either.
1. `tests/test_qa_T22_probes.py::test_server_ai_seat_gets_only_seat_b_and_a_slow_policy_is_a_logged_fallback_never_sent[ai|baseline]` (QA's, T22). QA already widened the `worst` bound to half the injected delay (0.15 s); one later run still failed (run A) and could not be reproduced. The probable remaining cause is the line `assert m.trace()["fallbacks"] == []` after the 30-tick warm-up. The match uses the default rival budget (0.04 s), so on a loaded machine a normal tick that takes longer than 0.04 s becomes a legitimate `slow_answer_replaced_by_wait` fallback and the assertion fails. This is an inference from the code, not a captured failure. **Owner: QA (author).** **How:** build the room with a generous budget for the warm-up (`smodes.make_match(mode, seed=7, rival_budget_s=2.0)` as other tests do), then set `m.game.rival.budget_s = 0.04` just before injecting the 0.30 s delay; or keep the warm-up and assert only that no fallback has `reason != "slow_answer_replaced_by_wait"`. The injected 0.30 s delay then still exceeds the budget by 7.5 times.
2. `tests/test_rl_train.py::test_smoke_training_runs_logs_exports_and_loads_back` (Tech Lead's T07-fix1 test, line 76, `time.time() - t0 < 60`). It trains for real for `max_iters=2`, so the bound is a smoke bound, not a property. Under load it can run past 60 s. It is an older test unrelated to T22-fix2. **Owner: Tech Lead (author), as a separate small task, or Gate 3 can run it on an idle machine.** **How:** raise the bound to a generous value (for example 300 s, the training itself is capped by `total_seconds=40` and `max_iters=2`), or drop the elapsed assertion; correctness is covered by the log, hash and load-back assertions after it.
Neither blocks the merge: both pass on an idle machine and in isolation. My own suite run below passed all tests at a load average that rose from 4.6 to about 18 during the run, so I did not reproduce either failure.

**No strength claim, no leak.** Nothing here measures strength; my parity runs compare traces.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_eval_T22fix2_boundary.py
18 passed in 15.40s

uv run --frozen --extra play --extra train --extra online pytest -q      (clean committed tree e142f51)
2191 passed, 11 skipped, 5 xfailed, 2 warnings in 539.49s (0:08:59)
```
Machine load (`uptime`): 4.58 8.32 11.46 at the start (23:31); 18.37 11.77 11.19 at the end (23:40). The 5 xfails are the earlier strict ones (T20 F1/F2 and E1, and two older); none passed unexpectedly. 2191 = QA's 2173 plus my 18.

## Eval-specific headings
Leak findings: none. Probed: log, host JSON and client messages in an AI room under forced fallbacks; recorder fed seat B inputs; header content.
Baseline fairness: unchanged. Reward, training, reproducibility, held-out separation: untouched (nothing under `agents/rl/`, `tools/rl/`, `evaluation/`, `pop/` changed; the shipped weights hash is still checked by `load_net` on every call).
Evaluation validity: no comparative evidence produced.
Local inference latency: not re-measured (T22 report: median 0.04 ms, p99 1.2 ms).
Replay fidelity: server trace and game parity checked above; WAIT-input replay test from T22-fix1 passes.
Fallback: labelled `"source": "fallback"`, kept in the server trace and stdout, never in a telemetry file or client message.
Training-run readiness: not applicable.

## Known limitations / Not checked
- No real browser or WebSocket client; the server path is tested through `Match` and `make_match`, as in T22-fix1.
- `play.py --mode ai --playtest` R-key restart: covered by QA's probes, not re-run by me.
- The two flaky tests were not reproduced; the diagnosis of item 1 is by reading.
- `docs/final/playtest/TELEMETRY.md` still lacks the `--mode ... --playtest` line and the "do not return a seat's file to its player" note (QA note; a docs task).

## Unresolved findings
None blocking.

## Requested next action
**Before Gate 3: none.** Optional, in any order, none required to merge: (1) QA hardens its warm-up check as above; (2) Tech Lead raises the 60 s smoke bound in a small task; (3) a docs task for `TELEMETRY.md`. For the Gate 3 full-suite run, use an idle machine.

## Student decision required
None.
