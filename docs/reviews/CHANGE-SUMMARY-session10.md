# Change summary for the independent reviewer — session 10 (Level 1 stabilization)

For `.claude/agents/rules-reviewer.md`. Written by the implementation agent;
not a review. Branch `level1-reconstruction` (local; not synced to PR #57).
Responds to the independent review of session 08's work (findings as
relayed by the student; that review's report is not in this repository).

**Not changed.** Frozen suite definitions, seeds, limits, prompts;
`agents/`, `evaluate.py`, `traces/`, `EVALUATION.md`. `docs/EVALUATION_SUITE.md`
gains only a change-log row.

**Change.**
1. `pop/engine.py`: `Game._phase` — one movement resolver for run, step,
   standing/running jump, climb up, climb down to hang, climb up from
   hanging, drink, sword pickup. Before a departure frame (`pop/physics.py`
   `*_DEPART`) a falling floor interrupts the move and the kid falls from
   where he stands; after it he is `_airborne` (no fall or crush from the
   floor he left) and arrives with support checked by `_enter`. Replaces
   the session-08 ad-hoc checks in `_up`/`_down` (R-D33).
2. `pop/mechanics.py`: any plate kind opens a linked exit (R-C09).
3. `pop/levels.py`: gate spec must be 1 (up) or 2 (down) (R-C29); a loose
   floor with the required bit is refused (R-C35).
4. Tests: `tests/consistency.py`; movement regression tests and two exact S3
   sequences in `tests/test_regressions.py`; `tests/test_trace_replay.py`
   now compares complete-state fingerprints with golden ones made by the
   engines that recorded each trace (`tests/trace_state.py`,
   `tests/data/trace_states.json`); new L1 route checked at every frame;
   exit/gate/required-bit tests; the always-true assertion in
   `tests/test_level1.py` replaced.
5. `tools/solve_level1.py`: the search key now includes exit position (it
   pruned waiting for an opening exit).

6. Documentation: `docs/RULE_SOURCE_MAP.md` (R-D33, R-C35; R-C09, R-C29,
   R-A03 corrected), `docs/GAME_SPEC.md` §5, `docs/EVALUATION_SUITE.md`
   (change-log row only), `docs/LEVEL1.md`, `docs/REQUIREMENTS_CHECKLIST.md`,
   `docs/IMPLEMENTATION_PLAN.md`, `docs/agent-sessions/10-level1-stabilization.md`.

**Commits.** `b061194` (movement fix), `e999181` (trace replay), `a2b49ae`
(rule findings), `04cf17f` (docs, solver), then a documentation-only
handoff commit. Base for the diff: `8e68e56`.

**Results claimed (verify).** `uv run pytest -q`: 281 passed, 1 skipped
(with the local Level 1 file); 16/16 traces identical in complete state;
fresh baseline final suite 12/12 identical; new L1 route won in 87
actions, 0 invalid, sword, 1 HP; fresh clone without the level file 272
passed, 10 skipped.

**Please check in particular.**
- Is `_phase`'s interruption rule right for every caller, and are the
  departure frames reasonable (R-D33 rationale)? Any move still placing the
  kid without a support check?
- `_airborne` is reset in `finally`; can it leak into a later frame?
- Are the golden fingerprints a sound guard (made with old engines, not
  the new one)? Is anything in the state missing from `trace_state.canonical`?
- R-C29, R-A03 (now `code`), R-C09, R-C35 locators.
