# Session 08 — Original Level 1 as a separate scenario (P0–P4)

| Field | Value |
| --- | --- |
| Agent | Claude Code (CLI), model Claude Opus 5.5 (`claude-opus-5-5`) |
| Role | Implementation agent (instructions: `CLAUDE.md`) |
| Session ID | `d4e6718b-405e-4e8f-9665-d314679d5fa9` |
| Date | 2026-10-26 |
| Branch | `level1-reconstruction` in the development repository, **local commits only**; nothing pushed by this session, nothing synced to course PR #57 |
| Transcript | Local only, not committed |

## Student instructions and decisions

1. Investigate the original Level 1 and plan a faithful reconstruction; no
   code until approval. The agent presented a plan with findings: the
   original layout conflicted with R-D13; a guard in room 3 blocks the only
   way to the exit; an S3 crash was reachable.
2. Approved with D1 (data stays outside Git, pinned and checksummed, local
   setup), D2 (simplified combat as final phase P5), D3 (fix the crash now,
   replay all traces), D4 (placeholders now; original sword/guard/animation
   art bundled on the course branch before completion). Proceed P0–P4, stop
   before P5. Keep the six frozen scenarios and their results unchanged,
   keep L1 out of the suite, leak no original data through the interface,
   document every deviation, and record evidence here.

## Research (before code)

- Fetched into the git-ignored `vendor/` only: Apple II `LEVEL1`
  (historicalsource `2b4ddb5`), DOS `res2001.bin` (SDLPoP `3c5add5`),
  source files for reading. Decoded with scratch scripts outside the repository.
- Found: the two files agree on everything the game uses; 24 slots, 21
  reachable (corrects the plan's "23"); the start faces right (corrects
  R-C06); the gate behind the start slams by script; guards in rooms 3 and 21.
- A search over legal actions with the unmodified engine on the original
  layout found the crash (step 7 of an S3 sequence).

## Work and commits (branch `level1-reconstruction`)

| Commit | Content |
| --- | --- |
| `f9c2c14` | P0: loose ledge falling during a climb up or down; 2 regression tests; `tests/test_trace_replay.py` |
| `d5f6bda` | **Not this session:** the student's Week 7 pair-audit commit (session 09), which arrived on this branch between P0 and P1; left untouched |
| `f23efa9` | P1+P2: reader, registry, fetch and solve tools, Level 1 rules, frozen-suite guard tests, rule map, CLAUDE.md |
| `78422ee` | P3: frontend |
| `83892fc` | Audit finding 1 fix (effect named only if the floor is in view) + audit report |
| (this commit) | P4: `docs/LEVEL1.md`, GAME_SPEC, plan, change summary, this log, screenshot budget in `play.py` |

## Evidence

| Check | Command | Result |
| --- | --- | --- |
| Baseline before work | `uv run pytest -q` | 173 passed, 1 skipped |
| P0 regression tests fail before the fix | `uv run pytest -q tests/test_regressions.py` | `TypeError` (climb), `'hanging'` (climb-down); pass after |
| Crash and impossible-state search, all six scenarios, after P0 | scratch breadth-first search with the real engine | no crash; no "hanging from no floor" or "standing on air" |
| Committed traces | `tests/test_trace_replay.py` | 16 of 16 replay identically (after P0 and at the end) |
| Fresh baseline final suite vs `traces/eval/` | `uv run python evaluate.py --suite final --players baseline --out <scratch>` | 12 of 12 identical apart from timing fields (after P0 and at the end) |
| Frozen definitions, first observations, model prompt | `tests/test_frozen_suite.py` | hashes pinned before any Level 1 code; unchanged |
| Data | `uv run python tools/fetch_level1.py` then `--check` | both SHA-256s match; layouts identical; L1 loads |
| Full tests with the local file | `uv run pytest -q` | 251 passed, 1 skipped |
| Fresh clone, no level file, no pygame | `git clone` of the branch to scratch, `UV_OFFLINE=1 uv run pytest -q` | 242 passed, 10 skipped; `play.py L1` prints the setup instructions |
| L1 route, engine | `uv run python tools/solve_level1.py` | start → sword (room 15) → exit (room 9): won, 87 actions, 798 frames, 0 invalid, 1 HP left; about 20 s |
| L1 route, frontend | `play.py L1 --keys <route> --screenshot` (original art, headless) | "ESCAPED! (actions 87, invalid 0)" |
| Baseline on L1 (exhibition) | `run_episode(baseline, "L1", 100/101)` | `step_limit` at 600, stayed in room 1; traces kept in scratch, not committed |
| Rules audit | `/game-rules-audit` | `docs/audits/AUDIT-2026-10-26-session08-level1.md`: 1 should-fix leak (fixed, `83892fc`), 1 doc gap (fixed here), 2 notes |

## Not done

- No independent review yet: `docs/reviews/CHANGE-SUMMARY-session08.md` is
  ready for the `rules-reviewer` in a separate session.
- No observed play of an original build; checklist in `docs/LEVEL1.md`.
- No live model run on L1 (refused by `play.py`; legend lacks `S`, `k`).
- Art milestone (D4) and P5 not started. Dev CI not run for this branch
  (not pushed); course CI not run (not synced, by instruction).
