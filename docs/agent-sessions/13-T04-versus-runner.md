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

## Follow-up: T04-fix1 (corrective work on the gate findings), 2026-11-23

| Field | Value |
| --- | --- |
| Tool / role | Claude Code subagent, Tech Lead; brief `docs/final/orchestration/tasks/T04-fix1.md`, findings `docs/final/orchestration/reports/GATE-T04.md` |
| Session | Same orchestrator session trailer as above; the subagent's own transcript id is not known to it |
| Model | `claude-opus-5-5` |
| Branch / base | `task/T04-fix1` from `task/T04` at `af76c30` |
| Independence | Builder. Not a review. The gates have not re-run on this branch |

### Instructions (quoted, truncated)

- "Read …/agents/tech-lead.md and follow it. Your task brief is …/tasks/T04-fix1.md … Do not push."

### What happened

- **Failing tests first** (`f1bd7c7`, `2fb60ff`): the two gate test files
  copied unchanged except that the `xfail` marks were removed for QA-1, QA-2,
  QA-3, QA-4, eval-2, eval-3 and eval-4. QA-5 (Saad's decision) and eval-1
  (default left unkeyed, see below) stay `xfail`. New tests in
  `tests/test_versus_runner.py` and `tests/test_seats.py`. The isolation test
  `test_controller_gets_only_plain_copies_of_its_own_seat` now builds its
  comparison episode with the run's duel limit (it failed on a merge with
  T01, `minutes_left` 0 vs 5).
- **Fix** (`93c8cc6`): plain-`str` normalisation of answers; safe text for
  refused answers and for exceptions whose `__str__` raises; bounded
  `reset`; busy controllers get a `busy` fallback and are never called
  concurrently; `BaseException` is an `error`; `VersusLimits` validation;
  optional `seed_key` (HMAC) for `controller_seed`; `on_frame` hook with a
  read-only `EpisodeView`; `copy_mode="json"` / `threaded=False` fast path,
  defaults unchanged and recorded in the result.
- **Docs:** `docs/final/VERSUS_RUNNER.md` (the above, plus the section on
  in-process isolation being by convention).
- **Not decided here:** QA-5, the default for `seed_key`, cadence/timeout,
  aborted vs forfeit, exact-name validation (listed for Saad in the note).

### Tests (verified, run in this session)

- Gate tests copied with marks removed, before the fix: `45 failed, 477 passed, 12 skipped, 2 xfailed`.
- After the fix, on `task/T04-fix1`: `python3 -m pytest -q -p no:cacheprovider` -> `524 passed, 12 skipped, 2 xfailed`.
- Scratch merge of `task/T04-fix1` with `task/T01` (`83127cf`), not committed to the branch: the same command -> `617 passed, 12 skipped, 2 xfailed`.
