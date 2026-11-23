# Session 13 (T04) — Seat-controller protocol and versus runner

Number 13 is provisional: other wave-1 tasks ran in parallel, and the
orchestrator may renumber this record when it merges them. The index
(`docs/agent-sessions/README.md`) was not edited: it is outside this task's
write paths.

| Field | Value |
| --- | --- |
| Tool / role | Claude Code subagent, Tech Lead (instructions: `docs/final/orchestration/agents/tech-lead.md`, `CLAUDE.md`, `AGENTS.md`); brief `docs/final/orchestration/tasks/T04.md` |
| Session | Subagent of the orchestrator session whose commit trailer is `Claude-Session: https://claude.ai/code/session_01DktSfuWQ416LWvPbT3AoAS`. The subagent's own transcript id is not known to it |
| Model | `claude-opus-5-5` |
| Date | 2026-11-23 (America/New_York) |
| Branch / base | `task/T04` in a private clone of the orchestrator's development repository, from `main` at `721b3e6` |
| Independence | Builder. Not a review. QA (Gate 1) and the Evaluation Specialist (Gate 2) have not yet run |
| Session URL | None. No shareable URL was created for this subagent |

## Instructions (from the orchestrator, quoted, truncated)

- "Read docs/final/orchestration/agents/tech-lead.md and follow it. Your task brief is docs/final/orchestration/tasks/T04.md …"
- "Another worker (T01) is editing pop/versus.py in parallel: do not edit it. … Do not push anywhere."

## What happened

- **Asked:** a `SeatController` protocol and a `VersusRunner` with copies-only
  observations, a fixed cadence, validated answers, labelled `WAIT` fallback
  on error, timeout, illegal or malformed answers, per-seat limits and JSONL
  traces, replay and seat swap (brief T04).
- **Done:** failing tests committed first (`tests/test_seats.py`,
  `tests/test_versus_runner.py`), then `pop/seats.py` and
  `pop/versus_runner.py`, then the design note `docs/final/VERSUS_RUNNER.md`.
- **Not done:** no `play.py` integration (out of scope); no public
  `VersusEpisode.snapshot()` (would need `pop/versus.py`, owned by T01); no
  rule-map row (no game rule changed).
- **Proposed, not decided:** 6-frame cadence, 5 s timeout, "aborted" (not
  forfeit) on a runner limit, exact-name validation. Listed for Saad in the
  design note.

## Commits (verified with `git log` in the clone)

| Commit | Message |
| --- | --- |
| `2dfa651` | test: failing tests for seat controllers and versus runner (T04) |
| `3e33b39` | feat: seat-controller protocol and versus runner (T04) |

The documentation commit that adds this record follows them on the same
branch.

## Tests (verified, run in this session)

- Before the implementation: `python3 -m pytest -q -p no:cacheprovider tests/test_seats.py tests/test_versus_runner.py` -> `2 errors in 0.15s` (collection: modules missing).
- After: the same files -> `38 passed in 0.36s`; full suite `python3 -m pytest -q -p no:cacheprovider` -> `457 passed, 12 skipped in 3.02s` (sandbox Python 3.13; pygame absent, so frontend tests skip).
