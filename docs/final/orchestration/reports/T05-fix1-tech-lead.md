---
handoff_id: HO-T05-fix1-tech-lead
task_id: T05-fix1
date: 2026-11-24 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T05-fix1.md@38aca15
source_branch: task/T05-fix1
source_commit: ce8c8c07f1d77e2f800f331f6716b1fed5862f25
reviewed_commit: n/a
verdict: n/a
---

# T05-fix1: tech-lead report

Status: done

## Work completed
Fixed the Gate 1 and Gate 2 findings on `agents/macros.py` and `agents/versus_baseline.py` (no `pop/` change). Base `0846a16` (diff to `6692771` was exactly the four test files the brief names). Decision #31 recorded in `MACROS.md`: CLIMB down is confirmed by Saad, not pending. I reused ideas from the untested WIP `ab78522` (read, not cherry-picked), ran everything, and fixed what traces showed.

Starting state at `0846a16`: 15 failed, 825 passed, 12 skipped, 18 xfailed. The 15: 6 new macro tests and 8 new baseline tests (the brief's failing-tests), plus `test_gate_t04fix1_qa_probes::test_numpy_str_answer_still_works` (numpy not installed in this worktree; unrelated, still failing).

Changes: CLIMB up and down (hang and drop saves the heart of a two-row fall, pit in the bottom row leaves the room, shaft up tried per column and facing); the planner treats survivable drops as moves; SEARCH visits every room including lower floors; FLEE can leave by a pit; DISGUISE reads `last_result.effect == "no_uniform"`; rule 5 only fights a lone guard at full hearts when it is knocked down or unarmed with its back turned, otherwise flees (more than 2 cells), fights (closer), waits for a patrol to turn, or climbs down to its row; a knocked-down figure is finished at once (lunge queued during the sweep); a malformed policy tuple is a reported failure. Bugs found while tracing: a finished wait keeps a stale `motion.to`; an input queued while a move leaves the room turned a hop into a flip and sent a seat over the edge onto spikes; an unarmed rival was fled from at one heart.

## Paths
`agents/macros.py`, `agents/versus_baseline.py`, `docs/final/MACROS.md`, `tests/test_macros.py`, `tests/test_versus_baseline.py`, `tests/test_gate_t05_eval_baseline.py`, `tests/test_gate_t05_qa_probes.py`, `docs/agent-sessions/15-T05-fix1-macros-baseline.md`, this report. Scope check `git diff --name-only 0846a16..HEAD`: all permitted.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Default start: reaches rooms 4 and 5, gets a uniform in most seeds | yes | seeds 0-3, both seats: rooms 4 and 5 in 8/8, uniform 8/8 |
| 2 | Finds a WAIT rival in rooms 4-6 | yes | Gate 2 probe, 3 cases (rival at room 4 col 3, room 6 col 5, room 5 col 7), seeds 0,1, both seats, all pass |
| 3 | Does not die to a lone guard 8/8 | yes | rooms 4 and 5, seeds 0,1, both seats: 0 deaths; Gate 2 `survives_a_guard_room_start` 4 and 5 pass |
| 4 | Every input legal; determinism | yes | existing QA probes (illegal inputs, fallbacks 0, two fresh baselines identical, replay) pass |
| 5 | Competence table, tuning and new held-out lower starts | yes | below |
| 6 | Baseline vs baseline not 10/10 no-hit draws, at least 12 swapped duels | yes | 12 duels (seeds 0-5, both swap): 0 draws, 12 `won:B`. Note: every duel is the same trace and seat B wins (seat A resolves first), so this is an order asymmetry, not a draw. Random starts, 24 duels (sampler seed 5): 10 W, 7 L, 7 T. No symmetry-breaking from identity or seed was added |
| 7 | Memory disclosed | yes | `MACROS.md`, "What the baseline remembers" |

Competence table (fixed starts, seats swapped, `tests/test_versus_baseline.py`; held-out lists frozen at `0846a16`, unchanged):

| Set | vs WAIT | vs Random |
| --- | --- | --- |
| tuning (2 starts, top row) | 8/8 | 8/8 |
| held-out (4 starts, top row) | 16/16 | 16/16 |
| lower tuning (2 starts) | 8/8 | 8/8 |
| lower held-out (7 starts, frozen) | 28/28 | 27/28 |

Random starts in every room (40 duels, 3,600 frames, alternating seats, fast path): sampler seed 99 vs WAIT: 39 W, 0 L, 1 T (QA's sweep before: 22 W, 8 L, 10 T). Sampler seed 7 vs Random: 37 W, 3 L, 0 T. These samplers are mine (scripts not committed), not QA's seed, so treat as indicative.

## Tests run
```
uv run pytest -q
FAILED tests/test_gate_t04fix1_qa_probes.py::test_numpy_str_answer_still_works
1 failed, 860 passed, 12 skipped, 3 xfailed in 63.77s (0:01:03)
```
Used `uv run`, not the fallback. The one failure is `ModuleNotFoundError: No module named 'numpy'`, present at the base too; not touched.

## Findings
xfail marks removed (each fixed): GATE-T05-eval-1, eval-2, qa-1, qa-2, qa-3; all xfails of this task are gone (3 remaining xfails are other tasks'). Minor (decide crash on a None or malformed tuple): fixed, tested. Test changes, each explained:
- `tests/test_macros.py`: the six failing-test commit tests used `drive(...)` and then asserted the final state, but the test policy `Fixed` re-asks the same macro after it is done, so the end state kept moving. I adopted the WIP's `drive_one` (stops at the first macro event) and assert the event reason instead. The scenarios, starts and expected outcomes are unchanged.
- Added tests: no input queued while a move leaves the room; stale `to` after a wait; malformed policy; finishing a felled guard; climb down to a guard's row; 12-duel mirror match.
- I did not change `LOWER_HELD_OUT_STARTS` or any start list.

## Known limitations
- A lone armed guard adjacent at the start still costs one to two hearts (seed 16 case passes but loses hearts); the shaft-up search is blind and slow; baseline vs baseline on random starts is not good play (7 T of 24); mirror match is decided by seat order.
- The uniform result relies on a guard patrol and my STRIKE sweep-then-lunge working; only passive rivals were tested. The `T` rows above can be a rival hiding behind the up-shaft search.
- Brief's one-step assumption "pit down lands in a room below with floor at the top" is an assumption (the view cannot see it); a wrong guess is a death by `leave_down` planned as blind cost 4.

## Unresolved findings
None of the brief's items left open. The orchestrator should note that the baseline now uses `CLIMB` (macro vocabulary unchanged, #23).

## Requested next action
Commit to review: ce8c8c07f1d77e2f800f331f6716b1fed5862f25 on task/T05-fix1
What changed: the baseline can descend, search all floors, flee vertically, get a uniform from the default start, survive lone guards, and is not deadlocked against itself.
How to check it: `uv run pytest -q`; `uv run pytest -q -s tests/test_versus_baseline.py` prints the competence numbers; Gate 2 probes in `tests/test_gate_t05_eval_baseline.py`; read `docs/final/MACROS.md`.
What I am unsure about: the random-start sweeps are my own samplers; rule 5 thresholds (ENGAGED 2, DANGER_RANGE 3, wait 40, danger memory 120) were set while looking at the failing duels, so held-out numbers for the old top-row set are the only unseen ones; seed 99 sweep leaves one timeout (start (4,2,9,+1) vs (2,2,0,+1)).
Touches the knowledge boundary or AI seat: yes (baseline and macro layer change, Gate 2 applies)

## Student decision required
none
