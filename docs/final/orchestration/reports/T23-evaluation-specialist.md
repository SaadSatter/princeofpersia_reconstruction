---
handoff_id: HO-T23-evaluation-specialist
task_id: T23 (T23, T23-fix1, T23-fix2)
date: 2026-11-26
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T23-qa.md@c2f9517 (and reports/T23-fix2-tech-lead.md@444bd39)
source_branch: gate/T23-eval
source_commit: see the final message
reviewed_commit: c2f9517
verdict: ACCEPT
---

# T23: Evaluation Specialist report (Gate 2)

Status: done

## Work completed
Base c2f9517 on `gate/T23-eval`. Read the diff `dfe2d90..c2f9517` for `pop/`, `server/`, `web/`, `play.py` and `agents/` (28 added lines in five files, none in `agents/` or the encoder). Re-ran the T19 compare set on dfe2d90 (extracted copy) and on c2f9517, which QA did not repeat. Probed the AI-seat boundary, determinism, trace and replay, and what reaches clients. No production code, tests or success criteria were edited.

## Checks
| Area | Result | Evidence |
| --- | --- | --- |
| Engine input rule | Pass | `VersusEpisode.release(seat)` only sets `pending[seat] = None` after `_check_seat`; it logs nothing and changes no counter. Called only on the branch where a human seat has no legal action this tick (`web/bridge.py:296`, `play.py:310`) |
| AI seats never release | Pass | `grep -rn "release("` over `play.py web server pop agents tools` finds only those two callers plus `server/trace.py:28` (replay of recorded human releases). `web/bridge.py` calls it inside `if seat in self.humans`; `play.py` loops over `shown_seats`, which is `("A",)` against a rival, so the AI seat B is not in the loop. QA's spy test confirms on the server. The AI branch (`self.rival(...)`) has no release |
| Determinism | Pass | The added lines contain no `time`, `random`, `datetime` or new import (grep over the added diff lines, no match). The rule is per-tick, so tick counts only |
| Server trace | Pass | `Match._releases` gets one list per tick from `game.released`, and is reset on rematch with `_ticks`. Trace carries `"releases"` beside `"ticks"` |
| Replay | Pass | `server.trace.replay` applies steps then releases, then ticks. An older trace with no `releases` key replays (probe below). QA's `test_replay_depends_on_the_recorded_releases` shows a trace stripped of releases gives a different hash |
| Knowledge boundary | Pass | `released` and `releases` appear only in `web/bridge.py` (server-side attribute) and `server/match.py`/`server/trace.py`; no `.js` file or `server/app.py` references them, and `trace()` stays server-side. Observations, legal actions and payloads are unchanged: no new data to clients or seats |
| T19 compare set | Pass | Below |

## T19 compare set against dfe2d90
Command, run in each tree: `PYTHONPATH=. uv run --frozen --extra train python evaluation/t19_compare.py <kind> 1`, with kinds `ppo`, `mirror`, `ppo_rand`, `base_rand` (tuning starts only, 32 combos each, seats and start order swapped). The JSON was compared with `wall_s` removed.

| Condition | Identical to dfe2d90 | Episodes | Wins | Draws | Losses | Aborted | Fallbacks | Distinct final states |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ppo (PPO vs baseline) | Yes | 32 | 30 | 2 | 0 | 0 | 0 | 30 |
| mirror (baseline vs baseline) | Yes | 32 | 16 | 0 | 16 | 0 | 0 | 14 |
| ppo_rand (PPO vs random) | Yes | 32 | 31 | 0 | 1 | 0 | 0 | 32 |
| base_rand (baseline vs random) | Yes | 32 | 27 | 0 | 5 | 0 | 0 | 29 |

Every episode is counted; none aborted, none used the fallback. This confirms the rule changes no AI trace. It is a regression check on the tuning starts with one seed, not a strength claim; the held-out set was not touched and nothing was tuned.

## Old-trace probe
A trace with no `releases` key (120 ticks, seed 3) replays to the same state hash as the live episode, and the same trace with explicit empty `releases` gives the same hash. (Scratch script, not committed.)

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t23_release.py tests/test_t23fix1_release.py tests/test_t23_qa_release.py tests/test_server_match.py tests/test_trace_replay.py tests/test_t22fix2_overlap.py
116 passed in 207.33s (0:03:27)
```
The full suite was not re-run by me: QA ran it at 435ab28: `2360 passed, 11 skipped, 5 xfailed, 2 warnings in 766.95s`; c2f9517 adds only QA's report on top.

## Leak findings
None found. Probed: AI seats calling `release`, `released`/`releases` in client-facing code, new fields in observations or payloads, time or randomness in the new lines.
Baseline fairness: unchanged (same code, identical traces).
Reward and training method: not touched.
Checkpoint reproducibility: not touched; the shipped weights loaded with their recorded SHA-256 in the compare runs.
Train / held-out separation: not touched; compare used `TUNING_STARTS` only.
Evaluation validity and confounds: one engine seed, two tuning starts, nearest-figure targeting; a regression check only.
Local inference performance: not measured (no change to inference); the compare runs took 10.7 s for 32 episodes each for the PPO and mirror conditions (measured, wall time, four processes in parallel on one machine).
Replay and fallback: replay verified above; fallback counts were 0 in all 128 episodes.
Training-run readiness: not applicable to this task.

## Findings
No blocker or major finding.
- Minor: `server.trace.replay` zips `ticks` with `releases`, so a trace whose `releases` list is shorter than `ticks` silently stops early. Traces written by `Match` always have equal lengths (one append per tick), so this cannot happen from the server; a length check would make a corrupt trace fail loudly. Optional.
- Not checked: a live browser tab (QA's note); I relied on the bridge and server code paths.

## Unresolved findings
none

## Requested next action
Orchestrator, Gate 3.

## Student decision required
none
