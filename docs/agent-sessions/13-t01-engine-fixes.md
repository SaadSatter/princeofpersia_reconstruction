# Session 13 — T01 engine fixes: disguise tells, R-V24 hop, 5-minute duel, input counts

| Field | Value |
| --- | --- |
| Tool / role | Claude Code, Tech Lead subagent (instructions: `docs/final/orchestration/agents/tech-lead.md`, `CLAUDE.md`, `AGENTS.md`), started by the orchestrator |
| Session | `https://claude.ai/code/session_01DktSfuWQ416LWvPbT3AoAS` (from the commit trailer the orchestrator supplied). The transcript id was not extracted: `tools/evidence/extract_sessions.py` was not run in this sandbox |
| Model | `claude-opus-5-5` |
| Date | 2026-11-23 |
| Branch | `task/T01` from `main` 721b3e6, in a sandbox clone of `/home/claude/sm/dev.git`; not pushed |
| Independence | Builder session. Not a review. QA (T02) reviews separately; this session wrote nothing in `docs/reviews/` |
| Brief | `docs/final/orchestration/tasks/T01.md` |

## Saad's instructions in force (quoted from `docs/final/orchestration/DECISIONS-2026-11-23.md`)

- #4: "Hopping should raise suspicion, what do you mean inputs that go stale?"
- #5: "Make the duel time limit 5min"
- #7: "Yes let this be my tech handoff"

## What was done

- **F1 (AUDIT-B, major):** a disguised rival's `WAIT` showed the other seat
  `motion.effect: "waited"`, which no guard shows. A probe over every
  disguised-legal input in every arena cell also found `bumped`, `edge`,
  a blocked jump in place (`bumped`, 8 frames) and a crouch (`none`,
  4 frames). Fix: a disguised figure shows a motion only if a guard can show
  it (`GUARD_MOTIONS`) or it raises suspicion by rule; otherwise
  `motion: null`, as for a paused guard. Proposed as rule-map row R-V25.
- **R-V24:** a hop straight up in a guard's sight raises suspicion +6/frame
  (the R-V19 jumping step; number proposed). `Duel.suspicious_rise` is used
  by both the meter and the observation.
- **OQ-3:** `DUEL_FRAMES = 3600` (5 min at 12 fps) is the default for `Duel`,
  `VersusEpisode`, `arena_episode` and so `play.py --versus`; a seat's
  `minutes_left` counts from the duel's own limit. Single-player clock
  unchanged.
- **F3 (awaiting Saad):** `outcome()` reports per-seat `stale_inputs` and
  `replaced_inputs`. Reporting only; in separate commits so it can be dropped.

## Commits (`git log --oneline 721b3e6..task/T01`)

| Commit | Message |
| --- | --- |
| a1100f6 | test(T01): failing tests for disguise tells, R-V24 hop and the 5-minute duel |
| 558ef6d | fix(T01): disguised rival observed as a guard on every input; R-V24 hop |
| 6160501 | feat(T01): arena duel lasts 5 minutes; minutes_left from the duel's limit |
| 1a838c1 | test(T01): failing tests for per-seat stale and replaced input counts |
| 7027536 | test(T01): read Duel.motion's own 'facing' key in the replaced-input test |
| 64d0c0e | feat(T01): report per-seat stale and replaced inputs in outcome() |

## Tests (run in this session)

`python3 -m pytest -q -p no:cacheprovider` (Python 3.13, pytest 9; pygame
and anthropic absent):

- base 721b3e6: `419 passed, 12 skipped`
- a1100f6 (new tests only): 27 failed, 61 passed in the two new files
- 1a838c1 (count tests only): 4 failed, 1 passed
- tip: `512 passed, 12 skipped`

## Not done / open

- Residual posture tells (not motion): a disguised rival can be seen
  `falling` (for example a careful step onto a loose floor), `hanging` or
  `dead`; no guard shows these, and a fall from a loose floor raises no
  suspicion. Needs a design decision.
- A disguised `WAIT` is shown as standing still but, as before T01, does not
  count as standing still for R-V19 lingering or R-V20's fall (the meter uses
  the move in progress). Not changed: a rule question for Saad.
- `docs/agent-sessions/README.md` and `docs/final/EVIDENCE_INDEX.md` not
  updated (outside this task's write paths).

## T01-fix1 (2026-11-23, tech-lead subagent, branch task/T01-fix1 from 83127cf)

Corrective work after the T01 gates (inputs: GATE-T01-qa, GATE-T01-eval,
decision 15).

- L1: R-V26, TAKE always legal over a downed guard; no uniform gives
  `last_result.effect = "no_uniform"` and nothing else. Marks removed:
  `GATE-T01-eval-L1` in `tests/test_gate_t01_eval_boundary.py`.
- L2: figure order sorts on every observed field. Mark removed:
  `GATE-T01-eval-L2`.
- QA1: a disguised move that ends in another room is masked (`motion: null`)
  under R-V25 unless it raises suspicion. Mark removed: `GATE-T01-QA1` in
  `tests/test_gate_t01_qa_disguise.py`.
- Left xfail for Saad: QA2 (postures), QA3 (WAIT and lingering). R-V24's amount
  untouched.
- `tests/test_disguise.py::test_take_needs_a_downed_uniformed_guard_ahead`
  asserts the pre-decision rule (no TAKE once the uniform is gone) and now
  fails; it is an existing test, so it was not edited (needs Saad's approval).
- Also updated VERSUS_SPEC section 2.2 (outcome keys added by T01) and the
  R-V26 row.
- QA3 (added by Saad 2026-11-23, "Yes, fix it"): a re-sent WAIT counts as
  standing still for R-V19 lingering. Mark removed: `GATE-T01-QA3` in
  `tests/test_gate_t01_qa_disguise.py`. QA2 stays xfail.
