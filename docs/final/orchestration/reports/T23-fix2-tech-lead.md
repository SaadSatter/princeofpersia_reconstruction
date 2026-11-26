---
handoff_id: HO-T23-fix2-tech-lead
task_id: T23-fix2
date: 2026-11-26
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T23-fix2.md@ed332cc
source_branch: task/T23-fix2
source_commit: see "Commit to review"
reviewed_commit: n/a
verdict: n/a
---

# T23-fix2: tech-lead report

Status: done (only QA's four #99 tests fail, as the brief allows)

## Work completed
New branch `task/T23-fix2` from `dfe2d90`, with these cherry-picked in order: 987a0ad, 455dfb0, 0c7d73a (T23), then b882931, 4cad17f, 5756e25 (T23-fix1). `git diff --name-only dfe2d90..HEAD` lists only T23 files: `docs/RULE_SOURCE_MAP.md`, `docs/agent-sessions/T23-release-after-landing.md`, the T23 and T23-fix1 reports, `play.py`, `pop/versus.py`, `server/match.py`, `server/trace.py`, `web/bridge.py`, `tests/test_t20fix1_recorder.py`, `tests/test_t23_release.py`, `tests/test_t23fix1_release.py`. Then the two approved test edits (below). `task/T23-fix1` is untouched.

## Test edits (old → new)
| Test | Old | New |
| --- | --- | --- |
| #113 `tests/test_server_match.py::test_the_input_trace_replays_to_the_same_outcome_and_state_hash` | own loop: `ep = arena_episode(seed)`; `ep.step` each tick input; `ep.tick()`; compare `ep.outcome()` and `digest(snapshot(ep))` | `outcome, h = replay(tr)` (`server.trace.replay`); `outcome == m.episode.outcome()`; `h == tr["state_hash"] == digest(snapshot(m.episode))` |
| #114 `tests/test_t22fix2_overlap.py::test_ai_room_logs_only_the_human_seat` | `rows[-1]["type"] == "duel_end"` | a `duel_end` row exists, and every row after it is `rematch` |
| #99 (T23-fix1) `tests/test_t20fix1_recorder.py::test_a_jump_then_three_left_ticks_is_one_flip` | `assert left and all(r["effect"] != "flipped" for r in left)` | `assert not left` |

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Clean branch, only T23 files | Yes | diff list above |
| 2-3 | #113 and #114 edits | Yes | table; both files pass |
| 4 | Edits listed old → new | Yes | table |
| 5 | Suite on committed clean tree | Yes, with the four QA tests failing | below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (committed clean tree)
4 failed, 2344 passed, 11 skipped, 5 xfailed, 2 warnings in 483.10s (0:08:03)
```
The four failures are QA's #99 tests: three in `tests/test_t20_qa_probes.py` (repeat marker, release then new press, held after a different move) and `tests/test_t20_qa_refused_mirror.py::test_refused_mirror_agrees_with_real_resolution[3-None]`.

## Findings
No new findings. T19 compare and AI-seat checks from `reports/T23-fix1-tech-lead.md` apply unchanged (same code).

## Known limitations
The cherry-picked T23 and T23-fix1 reports are kept as records; the T23 report's "blocked" status is superseded by this chain.

## Unresolved findings
none

## Requested next action
QA, Gate 1, then Gate 2 (input rule, server trace, replay): update the four #99 tests.

Commit to review: the commit after this report's parent (see the final message) on task/T23-fix2
What changed: the release rule (#93) now covers pygame and the server trace/replay, on a clean branch with the two approved test edits.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_t23_release.py tests/test_t23fix1_release.py tests/test_server_match.py tests/test_t22fix2_overlap.py`
What I am unsure about: nothing new.
Touches the knowledge boundary or AI seat: no (AI seats never release); Gate 2 applies for the input rule and server trace.

## Student decision required
none
