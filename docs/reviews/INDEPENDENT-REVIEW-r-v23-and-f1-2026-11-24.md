# Independent review: R-V23 fixes (13c7488) and disguise leak F1

- **Date:** 2026-11-24
- **Reviewer:** QA subagent (`docs/final/orchestration/agents/qa.md`), task
  `docs/final/orchestration/tasks/T02.md`. The QA subagent did not write the
  flip, the R-V23 fixes or the 2026-11-18 audit and review. It also had no
  instruction to approve them.
- **Commit reviewed:** `13c748875c4e61ecda7526489d31d4dfd2d5d645`. The worktree
  was at `721b3e6` (`main`). `git diff --stat 13c7488 721b3e6 -- pop render
  agents tests` is empty, so the code and tests under review are the same as
  in 13c7488.
- **Why this review exists:** the session that ran the 2026-11-18 audit also
  wrote the 13c7488 fixes. Its own record says the fixes are "not independent"
  and "have not been reviewed" (`sm-untracked-13.md`, the uncommitted session-13
  record. `docs/agent-sessions/13-flip-audit-review-fixes.md` is not in the
  repository at 721b3e6).
- **Environment:** orchestrator sandbox, Python 3.13.18, pytest 9.1.1. pygame
  and anthropic are not installed. Command: `python3 -m pytest -q -p no:cacheprovider`.
- **Read:** `AGENTS.md`, `CLAUDE.md`, orchestration `README.md`,
  `DECISIONS-2026-11-23.md`, `reports/AUDIT-B-qa.md`, the brief,
  `.claude/agents/rules-reviewer.md` (checklist only),
  `docs/audits/AUDIT-2026-11-18-flip-r-v22.md`,
  `docs/reviews/INDEPENDENT-REVIEW-flip-r-v22.md`, `git show 13c7488` (all of
  it), `pop/versus.py` (`Rival` and `Duel` queries, tick, advance, settle,
  observe, `VersusEpisode`), `pop/guards.py`, `pop/engine.py` (`_run`,
  `_step`, `_jump`), `pop/arena.py`, `pop/mechanics.py` (gates),
  `tests/test_flip_review.py`, `tests/test_flip.py` (header and first tests),
  and the R-V22/R-V23 rows of `docs/final/VERSUS_SPEC.md` and
  `docs/RULE_SOURCE_MAP.md`.

## Commands and results

| Command | Result |
| --- | --- |
| `python3 -m pytest -q -p no:cacheprovider` at 721b3e6 before QA's tests | `419 passed, 12 skipped in 3.13s` |
| same, on `task/T02` with QA's two new files | `447 passed, 12 skipped, 5 xfailed in 2.80s` |
| `pytest tests/test_flip_review.py tests/test_flip.py` | `47 passed` |
| `tests/test_flip_review.py` run on the pre-fix tree `7b38b65` (`git archive` into `/tmp`) | `12 failed, 14 passed`. The 12 failures match the commit message's "12 fail on the old engine" |
| `tests/test_qa_t02_r_v23.py` run on the pre-fix tree `7b38b65` | `8 failed, 10 passed`. Those 8 tests detect R-V23 itself. The other 10 cover behaviour the old engine already had |
| `pytest tests/test_qa_t02_disguise_tells.py --runxfail` | Each of the 5 xfails fails on its stated assertion (output quoted under F1/F2) |

All 12 skips are environmental: no pygame, no anthropic, images not bundled, and
the original Level 1 not fetched. They are the same skips AUDIT-B listed.

## 1. 2026-11-18 findings against 13c7488

| Source finding | Verdict | Evidence |
| --- | --- | --- |
| Audit 1 / review should-fix: the other rival could step into the landing cell, and the jumper snapped back to its take-off cell | **Closed** | `test_the_other_rival_cannot_step_into_a_landing_cell_in_sight[False/True]` fails on 7b38b65 and passes on 13c7488. A landing cell reached from another room is settled (`test_a_jumper_landing_on_someone_from_another_room_settles_beside_them`). See also finding T02-F7 (wording) |
| Audit 1a / review should-fix: the seat id changed where a jump landed | **Closed** | `test_where_a_jump_goes_does_not_depend_on_the_seat_id[4]` fails on 7b38b65 and passes now. QA's `test_qa_t02_settling_does_not_depend_on_the_seat_id` (5 settle cases, both seats' full observations, every frame) passes |
| Audit 2 / review note: a disguised rival was the only "guard" that could step into a landing cell | **Closed** | The same parametrized test with `disguised=True` |
| Audit 3 / review should-fix: landing cells were claimed in every room, so a guard reacted to an unseen jump | **Closed** (test is narrow) | `test_a_landing_cell_in_another_room_is_not_claimed` checks `cell_free_for_guard`, not the guard's observed behaviour. That is enough because `Guard._decide` only asks `cell_free_for_guard` (pop/guards.py:151-189) |
| Audit 4 / review note: an alert guard facing the jumper stabs it mid-flip | **Kept by Saad** (2026-11-23), now tested | `test_an_alert_guard_facing_the_jumper_stabs_it_mid_flip` |
| Audit 5 / review **blocking**: a body in another room blocked the jump, which revealed it | **Closed**, with one residual edge case (T02-F3) | `test_a_body_out_of_sight_does_not_change_the_jump` fails on 7b38b65 and passes now. QA's `test_qa_t02_a_move_into_a_doorway_does_not_reveal_who_stands_there[RIGHT/STEP_RIGHT]` gives the same result for runs and steps |
| Audit 6 / review should-fix: missing tests (flip over a disguised rival vs over a guard, observer in another room, hop-flip refused from a seat, determinism with a hop-flip) | **Closed** | `test_flipping_over_a_disguised_rival_looks_like_flipping_over_a_guard`, `test_a_seat_in_another_room_never_sees_the_flip`, `test_a_seat_cannot_send_the_internal_hop_flip`, `test_flips_and_hop_flips_are_deterministic`. Determinism is checked only in one process, run twice. A cross-process or replay-from-log test is still missing (AUDIT-B §2) |
| Review should-fix: the R-V22 rule-map row had no rationale or rejected alternatives and repeated the false guarantee | **Closed** | `docs/RULE_SOURCE_MAP.md` R-V22 and R-V23 rows now have **Why** and **Alternatives rejected** |
| Review note: the hop window's last frame | **Kept by Saad**, now tested | `test_a_direction_on_the_last_hop_frame_still_flips` |
| Review note: `RUN_JUMP_*` sent mid-hop becomes a 3-cell flip | **Partially closed** | VERSUS_SPEC R-V22 now says so. The AI seat's action description does not exist yet (T05), so it cannot be checked |
| Review note: `last_result.effect` disagreed with `motion.effect` | **Closed** | `test_last_result_names_the_same_effect_as_the_motion[RUN_JUMP_RIGHT-flipped]` and `test_a_hop_flip_reports_a_flip_when_it_ends` fail on 7b38b65 and pass now |
| Review note: the running flip's picture stayed on the floor for about 20% of the flight | **Closed** (headless pose only) | `test_a_running_flip_leaves_the_floor_on_its_first_frame`. Not checked by eye |
| Review note: a stray sentence in the VERSUS_SPEC table | **Closed** | VERSUS_SPEC.md:112 is now a paragraph after the table |

## 2. Findings

Findings are listed most severe first. "Observed" means QA reproduced it in this
session. "Suspected" means QA did not reproduce it.

**T02-F1 `[major]` pop/versus.py:888-898 (`_motion_view`), 919-920 (disguised figure) — observed.**
This is AUDIT-B F1, still open at 13c7488. When a disguised, sheathed rival
sends `WAIT`, the other seat sees a `kind: "guard"` figure with `motion:
{"effect": "waited", "frames": 6, ...}`. A real guard never shows `waited`:
`Guard.motion` returns None while it pauses and otherwise only moved, turned,
drew, sheathed or lunge (pop/guards.py:85-96, 140-189). The figure's fields
alone reveal which "guard" is the rival, and the leak costs the rival no
suspicion. This contradicts R-V18 and the checklist's "disguise identity …
done".
- Reproduction: `test_qa_t02_disguised_wait_matches_paused_guard` (xfail
  strict). Disguised A at (2,0,4) facing left sends WAIT. The observer B is at
  (2,1,0). The control game has a held guard at (2,0,4) instead. B's
  observations differ from frame 1.
- Same failure in `test_qa_t02_disguised_motion_is_a_guard_motion_or_costs_the_disguise[WAIT]`:
  `WAIT: shown [(False, 'waited', 6, 'standing')] with suspicion 0 and the disguise kept`.
- Expected: the same as a paused guard (`motion: None`). Actual: `waited`/6.

**T02-F2 `[major]` pop/versus.py:79 (`LEAPS`), 407-436 (`_suspect`) — observed. This is
AUDIT-B F2 under the decision now in force (R-V24).**
Saad's decision of 2026-11-23 says "Hopping should raise suspicion". At
13c7488 a disguised `UP` hop shows the other seat `effect "none"` over 8
frames, a motion no guard makes, and the watching guard's suspicion stays at 0.
`"none"` is not in `LEAPS`.
- Reproduction: `test_qa_t02_disguised_hop_in_a_guards_sight_raises_suspicion`
  (xfail strict: `assert 0 > 0`) and
  `..._costs_the_disguise[UP]`: `UP: shown [(False, 'none', 8, 'standing')] with suspicion 0 and the disguise kept`.
- Expected: suspicion rises (R-V24, +6 proposed in T01). Actual: 0.
- Routed to T01, which already owns R-V24.

**T02-F2b `[minor/design]` same lines — observed, and not covered by any decision.**
A disguised `DOWN` shows `effect "none"` over 4 frames and raises no suspicion.
That makes it the same kind of tell as the hop.
- Reproduction: `..._costs_the_disguise[DOWN]` (xfail strict):
  `DOWN: shown [(False, 'none', 4, 'standing')] with suspicion 0 and the disguise kept`.
- T01's acceptance criterion 1 lists DOWN, so T01 has to choose: make it look
  like a guard, or make it raise suspicion. That choice needs Saad.
- The same test passes for running, jumps and running jumps. Each shows a
  motion no sheathed guard makes (a sheathed "guard" running at 4 frames per
  cell, `jumped`, `flipped`), but each raises suspicion under R-V19, which is
  the intended cost.
- Walking, turning, DRAW and SWEEP pass: they either match a guard or break the
  disguise.

**T02-F3 `[minor]` pop/versus.py:645-654 (`_nearest_free` returns `came_from`), 611-631, 619-621 (docstring) — observed.**
R-V23 sometimes sends a mover back into the room it came from, after the move
was shown as entering the next room. The mover learns that bodies it never saw
fill the row. The docstring says "It never goes back to a room it has left, so
a body out of sight is only found by entering its room and seeing it", and the
code does not do that in two cases:
- (a) The row has no free cell. In arena A, the gate at (2,1,5) is closed,
  guards are held at (2,1,7) and (2,1,6), and B is at (2,1,9). A runs `LEFT`
  from (3,1,0). A's motion shows `moved`, then A is back at (3,1,0) and sees
  nothing. With room 2 empty, A would have been in room 2.
- (b) Two jumpers' settle cells would be the same. A jumps from (1,0,9) and B
  from (3,0,0) into room 2, which is full of guards except col 3. Both go back
  to rooms 1 and 3 after a 12-frame flight
  (`test_qa_t02_two_jumpers_whose_settle_cells_coincide_both_go_back`, which
  pins the current behaviour).
- VERSUS_SPEC R-V23 allows both cases ("Only a row with no free cell sends it
  back where it was"; "so do two whose settle cells would be the same"). The
  spec and the code agree with each other. The docstring is wrong, and the
  residual leak is not listed anywhere.
- Expected (per the docstring): the mover never goes back to a room it left.
  Actual: it does, in these two cases.
- Rare in play. Saad decides whether it matters.

**T02-F4 `[minor]` pop/versus.py:661-670 (`_replan`) with pop/engine.py:331-345 (running jump enters its run-up cell inside the same macro) — observed.**
A `RUN_JUMP_RIGHT` from (1,0,9) has its run-up cell at (2,0,0). B stands there,
out of sight. The run-up arrives at (2,0,0) and the flight is planned on that
frame. R-V23 then settles A at (2,0,1) and `_replan` **cancels** the move
instead of planning it again, because `_started` is the frame the run-up began.
A's motion goes from `moved 4/4` straight to `None`, and `last_result` stays
`None`: this input never reports a result. With B parked elsewhere, the same
input flips to (2,0,4) and reports `flipped`.
- R-V23 says "a move it had just started from the cell it was moved off is
  planned again". Here the flight began on that frame, but it is dropped.
- No leak: A is in room 2 and sees B. The problems are an input that silently
  vanishes and a missing result, which matter for the AI seat and for counting
  stale inputs.
- Reproduction script: `/tmp/t02probe/p6.py` in the QA sandbox. The steps are
  as above, 16 ticks.
- Expected: either the flight is planned again from (2,0,1), or the move ends
  with a `last_result`. Actual: cancelled with no result.
- Not committed as a test, because the right behaviour is a design choice.

**T02-F5 `[minor/design]` pop/versus.py:128-141 (`Rival.blocks`), 611-631 — observed.**
Two rivals in a doorway now pass through each other. A is at (1,0,9) and runs
`RIGHT`. B is at (2,0,0) and runs `LEFT` on the same frame. Neither sees the
other, neither move is blocked, and after 5 frames A is at (2,0,0) and B at
(1,0,9). The settle step only handles ending on the same cell, not crossing.
Before 13c7488 both moves were blocked. R-V00 now says "cannot pass through
each other **in sight**", so this case is allowed by the letter of the rule but
not stated. The result is the same with the seats swapped
(`test_qa_t02_settling_does_not_depend_on_the_seat_id` case 2).

**T02-F6 `[minor/design]` pop/versus.py:645-659 (`_nearest_free`, `_settles_in`) — observed.**
When the mover settles, it is moved to the "nearest free cell" across holes,
spikes and standing guards. The spec forbids ending **on** spikes or a hole,
or **past** a wall or closed gate, but says nothing about crossing them.
Observed cases:
- A runs into (2,1,0) onto B and settles at (2,1,2), across the hole at col 1.
  It could not have walked there.
- From room 3 onto B at (2,1,9), A settles at (2,1,7) across the hole at col 8
  and onto a drop plate.
- With B at (2,2,0) and a guard at (2,2,1), A settles at (2,2,3), across the
  guard and the spikes at col 2.
- With guards at cols 6 and 7 and the gate open, A settles at (2,1,5), four
  cells from where it arrived.

The spec's "puts the mover just past them" describes only the one-body case.
Saad decides whether a settle may cross a gap, spikes or a second body.

**T02-F7 `[cosmetic]` docs/final/VERSUS_SPEC.md:109 (R-V22 row) — observed.**
The row says "neither a guard nor the other rival (disguised or not) can step
into it [the claimed landing cell]". A rival coming from the next room can step
in, by design, and the jumper then settles. `test_a_jumper_landing_on_someone_from_another_room_settles_beside_them`
expects exactly that. The rule is right; the sentence should say "from inside
the room".

**T02-F8 `[cosmetic]` stale comments — observed.**
- pop/versus.py:143-147: the `_can_vault` docstring still says a body in the
  next room "still stops the jump as before". Under R-V23 it does not.
- tests/test_flip.py:5-7: the module docstring still says "a body in another
  room still blocks (the jumper cannot see it, so the jump must not reveal it)".
  Editing this is an edit to an existing test file, so it needs Saad.

**T02-F9 `[minor]` pop/versus.py:479-488 (`submit`), 562-566 (`_advance`) — observed. This is AUDIT-B F3, restated.**
A newer pending input replaces an older one, and a queued input that is no
longer legal when it would start is dropped. Neither is counted or reported.
- Reproduction: A at (2,0,3) facing right. `step("A","RIGHT")` and
  `step("A","STEP_LEFT")` are both accepted at frame 0. After 12 ticks,
  `outcome()["inputs"]["A"] == 2`, `log` holds both, `invalid_inputs` is 0, and
  only the second input ran (`last_result.effect == "turned"`).
- The decision is still pending. Saad asked "what do you mean inputs that go
  stale?" (DECISIONS #4). T01 criterion 4 proposes reporting-only counts in a
  separate commit.
- No QA test is committed, because the expected behaviour is not decided.

**Suspected, not reproduced.** Swords dropped (R-V07) near a settle cell are
not considered by `_settles_in`. QA did not find a case where this matters.

## 3. Tests added (QA commit on `task/T02`)

- `tests/test_qa_t02_r_v23.py` has 18 tests, all passing at 13c7488. Eight of
  them fail on 7b38b65. They cover:
  - both rivals arriving in one doorway cell, with either seat
  - two jumpers whose settle cells coincide
  - a settle that skips a hole, spikes and a closed gate
  - a settle at both room edges
  - runs and steps into a doorway that do not reveal the body there
  - settling on a disguised rival observed exactly like settling on a guard
  - settling that keeps the disguise and adds no suspicion
  - seat-swap symmetry of the full observations over 5 settle scenarios,
    including the running jump of T02-F4
- `tests/test_qa_t02_disguise_tells.py` has 15 tests: 10 pass and 5 are
  `xfail(strict=True)`. The xfails are:
  - `test_qa_t02_disguised_wait_matches_paused_guard` (T02-F1)
  - the motion-set test for `WAIT` (T02-F1), `UP` (T02-F2 / R-V24) and `DOWN`
    (T02-F2b)
  - `test_qa_t02_disguised_hop_in_a_guards_sight_raises_suspicion` (T02-F2)

  When T01 fixes these, the strict xfails will XPASS and fail the suite, so
  their marks must then be removed. Removing a mark is an edit to an existing
  test and needs Saad's approval.

## Not checked

- Rendering by eye: no window was opened, because pygame is absent.
- Dev CI on GitHub for 13c7488: QA had no network or GitHub access. The
  workflow (`.github/workflows/ci.yml`) is unchanged since AUDIT-B.
- The official repository's `final.yml`: not in this sandbox.
- Climbing onto a body (`UP` from (6,0,4) under the shaft did not climb in
  QA's probe, so the climb arrival path of R-V23 was not exercised).
- Pushes (`_push`) cannot cross rooms (`_free` requires the same room), so they
  cannot trigger a settle. This was confirmed by reading the code, not tested.
- Cross-process determinism and replay from `ep.log` were not re-run (AUDIT-B
  §2 did this at the same commit).
- Pinned pytest < 9 (`uv run`).
- The AI seat, runner limits, traps and server: not built.

## Verdict

```
Verdict: ACCEPT WITH NOTES (R-V23 fixes); F1 and F2 remain open and are routed to T01
Commit reviewed: 13c748875c4e61ecda7526489d31d4dfd2d5d645
Acceptance criteria:
 1 Each R-V23 fix checked against the 2026-11-18 findings -> met -> table in §1, old/new runs
 2 New probes of R-V23 -> met -> tests/test_qa_t02_r_v23.py; findings T02-F3..F6
 3 F1 as a failing test plus the motion-effect-set test; F2 and F3 restated -> met -> tests/test_qa_t02_disguise_tells.py; T02-F2, T02-F9
 4 Review in qa.md format -> met -> this file
 5 Handoff draft, Student decision empty -> met -> docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md
 6 Full suite line -> met -> 447 passed, 12 skipped, 5 xfailed
Findings: T02-F1 major, T02-F2 major, T02-F2b minor/design, T02-F3 minor, T02-F4 minor,
          T02-F5 minor/design, T02-F6 minor/design, T02-F9 minor, T02-F7 cosmetic, T02-F8 cosmetic
Not checked: see above
```

This review does not decide what happens to any finding. Saad decides.
