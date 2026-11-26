---
handoff_id: HO-T04-fix3-tech-lead
task_id: T04-fix3
date: 2026-11-24
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T04-fix3.md@5a2db64
source_branch: task/T04-fix3
source_commit: 60ef7d54a478143b54b26ddd6335e9a26278bab8
reviewed_commit: n/a
verdict: n/a
---

# T04-fix3: tech-lead report

Status: done (amended per decision #33; the two numpy failures remain, numpy is T15 per #34)

## Work completed
Base 7fe2e9c checked: `git diff --name-only cd5c4aa 7fe2e9c` lists only the four gate files, and their edits match items 1 to 3 (QA-5 xfail removed; eval-1 xfail turned into a keyed test that must pass plus an unkeyed test documenting the default; the two GATE-w2 probe files copied in with no xfail marks). Before my change: `5 failed, 842 passed, 12 skipped, 1 xfailed`. The failures were QA-5, the two concurrency tests, and two numpy tests (see below).

1. QA-5: `VersusRunner.__init__` raises `ValueError` if `controllers["A"] is controllers["B"]`.
2. Eval-1: the code needed no change (`seed_key` was already opt-in and keyed seeds were already unrecoverable). VERSUS_RUNNER.md now says evaluation runs must pass a `seed_key`, names the two tests, and marks the decision as made.
3. Race: `_call` now claims the controller under `_LATE_LOCK` (`_claim`) before the call, storing an `_IN_FLIGHT` sentinel in `_LATE`. A runner that finds the sentinel or a live late thread gives a `busy` fallback. After the call the entry is replaced by the late thread (timeout) or removed, in a `finally`. I did not use the WIP snapshot 76de25c.
4. Session note: the base file had no "R-V26 and QA3" sentence to correct, so I added a short "Effect on traces" bullet to `13-t01-engine-fixes.md` that says "R-V26, QA3 and L2". Check that this is what you wanted.

## Paths
`pop/versus_runner.py`, `tests/test_versus_runner.py` (one new test), `docs/final/VERSUS_RUNNER.md`, `docs/agent-sessions/13-T04-versus-runner.md`, `docs/agent-sessions/13-t01-engine-fixes.md`. No gate-file edits by me.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | QA-5 refused, xfail gone | yes | `test_qa5_one_instance_cannot_play_both_seats` passes |
| 2 | eval-1 keyed test passes, unkeyed documented | yes | both tests in `tests/test_gate_t04_eval_boundary.py` pass; doc text added |
| 3 | no concurrent calls; busy fallback | yes | new `test_concurrent_runners_never_call_one_controller_at_once_forced_overlap` (events, no sleeps) failed on 7fe2e9c code (`1 failed`, after the 5 s timeout) and passes now; both GATE-w2 probes pass |
| 4 | session wording | yes, see above | |
| - | no flakiness | yes | 57 runs of the 7 concurrency/busy tests across `test_versus_runner.py` and the two w2 probe files: 57 of 57 passed |

## Test changes
Amendment (decision #33, Saad: "Flip to ValueError"): `tests/test_gate_t04fix1_eval_probes.py::test_same_instance_in_both_seats_busy_blocks_both` is renamed `test_same_instance_in_both_seats_is_refused` and now asserts that `VersusRunner(..., {"A": s, "B": s}, ...)` raises `ValueError`. No other test in the file changed. No other gate file was edited by me.

## Tests run
```
uv run pytest -q
2 failed, 846 passed, 12 skipped, 1 xfailed
```
The 2 failures are `test_numpy_str_answer_still_works` (t04fix1 qa probes) and `test_numpy_str_answers_still_work` (w2 qa probes): `ModuleNotFoundError: numpy`, environmental, present before this task (T15, #34).

## Findings
No open findings from this task. The earlier stale-test finding is resolved by the edit above.

## Known limitations
The in-flight mark also covers inline (`threaded=False`) calls, so two threads sharing a controller in fast-path mode also get `busy` rather than a concurrent call. This matches the decision's intent but is new behaviour for that mode.

## Unresolved findings
none (numpy failures are environmental).

## Requested next action
Commit to review: 60ef7d54a478143b54b26ddd6335e9a26278bab8 on task/T04-fix3
What changed: one controller object cannot fill both seats; a controller call is marked in flight at its start under the registry lock, so concurrent runners give a `busy` fallback instead of calling it twice; docs say evaluation runs must pass a `seed_key`.
How to check it: `uv run pytest -q tests/test_versus_runner.py tests/test_gate_t04_qa_adversarial.py tests/test_gate_t04_eval_boundary.py tests/test_gate_w2_qa_probes.py tests/test_gate_w2_eval_probes.py`; the only failure should be the numpy test. Revert `pop/versus_runner.py` to 7fe2e9c to see the new overlap test fail.
What I am unsure about: the session-note wording; the inline-mode behaviour above.
Touches the knowledge boundary or AI seat: yes (runner, seat isolation: one controller across both seats). Gate 2 applies.

## Student decision required
none
