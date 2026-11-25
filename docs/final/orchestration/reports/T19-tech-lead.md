---
handoff_id: HO-T19-tech-lead
task_id: T19
date: 2026-11-24 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T19.md@447f298c44829e90e03ab55a69a7764eda809905
source_branch: task/T19
source_commit: 7bbab99770e5d17b22ccf1d78c58bfff50174baf
reviewed_commit: n/a
verdict: n/a
---

# T19: tech-lead report

Status: partial. The work is complete and committed, but **two existing tests fail** and the brief says to stop
and report when a test outside #53 breaks (section "Findings"). I did not edit them.

## Work completed
Tests first (commit `4eb0da4`, 45 Python tests failing on `fc02687`, plus new Node cases), then the changes:
- **#53 flip by default.** `Rival._jump_look` always answers `flipped`. Distances, landing, walls, claims, R-V23
  unchanged; a jump into a wall is still a bump; `UP` under a ledge still climbs; bare `UP` is still a hop.
- **#54 grace window, in the engine** (new row R-V35, `Duel._grace_jump`, `GRACE_TICKS = 2`). Chosen over an
  input-layer buffer because (a) a buffer must hold a lone direction for up to 2 ticks, adding latency to every
  move, and (b) it would need a copy in `play.py`, `web/bridge.py` and `server/match.py`. As an engine rule it is
  one implementation: the three front ends all end in `Duel.submit`/`tick`, and the scripted and trained rival
  seats get it too.
- **#55 either control set.** `WebGame` (human vs AI) reads both sets; `Match` (online) accepts either set and
  renames it into the seat's own (`bridge.to_seat_keys`); `keys.js` `gameKeys` and `online.js` send all 16 names;
  hints say both sets work. Local two-player keeps A = WASD, B = arrows.
- **Item 3 kneel.** `took_sword`, `took_uniform` (so also the `no_uniform` TAKE frames) and `kneeled` all draw the
  rival's `crouch` strip.

## Paths
Changed: `pop/versus.py`, `pop/engine.py` (two small helpers, `_climb_target`, `up_hops`; `_up` now calls
`_climb_target`, behaviour identical), `web/bridge.py`, `server/match.py`, `web/keys.js`, `web/online.js`,
`render/versus_view.py`, `play.py` (docstring only), `docs/RULE_SOURCE_MAP.md` (R-V22 amended, R-V35 new),
`docs/final/VERSUS_SPEC.md` (R-V22 sentences, either-set row), `docs/final/ONLINE_PLAY.md`,
`docs/agent-sessions/T19-gameplay-cleanup.md`. Tests: new `tests/test_t19_{flip,grace,kneel,controls}.py`,
`web/keys.test.js` (3 new cases). No `docs/final/GDD.md` change: it holds no sentence about the standing jump.
`web/draw.js` unchanged: it only blits the Python draw list, so the kneel lives in `render/versus_view.py`.
`web/main.js` unchanged: it already passes every held key to the bridge.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Both sets drive seat A (AI, online); local 2P splits | Yes | `tests/test_t19_controls.py` (bridge, `Match`, `Match` vs baseline); `web/keys.test.js` T19 cases |
| 2 | left→up and up→left at 0, 1, 2 ticks = one flip; 3 ticks = two inputs; late press buffered; lone-direction latency | Yes, with one caveat | `tests/test_t19_grace.py` (see caveat 1 below) |
| 3 | Kneel for `took_sword`, TAKE, `no_uniform`; other seat's view unchanged | Yes | `tests/test_t19_kneel.py` (the other-seat test passes on the base too: it is a guard) |
| 4 | Standing jump left and right flips with today's distances; climb and hop unchanged; rule map updated | Yes | `tests/test_t19_flip.py`; R-V22 and R-V35 rows |
| 5 | Determinism | Yes | `test_flips_are_deterministic`, `test_the_same_inputs_give_the_same_trace` |
| 6 | Suite green | **No** | two existing tests fail (below) |

**Latency.** A lone direction starts on the press tick exactly as before: added latency 0 ticks
(`test_a_lone_direction_starts_on_the_press_tick_with_no_added_latency`). The window costs nothing for a single
press; what it changes is that a jump pressed 1 or 2 ticks after a direction no longer waits for that move
(4 ticks for a run, 8 for a step) and starts on the press tick.

**Mechanism detail.** Direction then jump: while a plain `LEFT/RIGHT/STEP_*` move is in its first 2 frames and
began a fresh run (not a continuation of a run chain), a pending `JUMP_<same way>`, a `RUN_JUMP_<same way>` (the
front end sends that as soon as it sees the run) or a bare `UP` that would hop cancels it and starts a standing
jump that way at once. `UP` under a ledge, a continued run chain (the ordinary running jump) and the careful
step plus Shift run jump are left alone. Jump then direction is the existing hop turn.
The jump pressed with the opposite facing now faces and jumps with no separate 4-frame turn
(`Rival._directional`); without it a same-tick "left + jump" while facing right was a 4-tick turn, the worst case of
the lag. Runs and steps still turn first (R-D20).

## Tests run
```
base fc02687 (brief): 1380 passed, 12 skipped, 4 xfailed, 2 warnings
uv run --frozen --extra play --extra train --extra online pytest -q
2 failed, 1444 passed, 12 skipped, 4 xfailed, 2 warnings in 373.49s (0:06:13)
node web/keys.test.js
keys.test.js: 9 passed
```
(`tests/test_web_js.py` also runs the Node file inside pytest.) Failures: see Findings. No browser and no pygame
window were run by hand. `play.py --versus` is local two-player and was not touched beyond a docstring.

### Existing tests I changed (all decision #53, Saad 2026-11-24)
| Test | Old assertion | New assertion |
| --- | --- | --- |
| `tests/test_flip.py::test_a_standing_jump_with_nobody_to_pass_does_not_flip` (renamed `..._flips_too`) | `motion["effect"] == "jumped"` | `== "flipped"` |
| `tests/test_flip.py::test_a_jump_with_nobody_in_the_way_is_an_ordinary_jump` (renamed `..._is_a_flip_with_the_same_distance`) | `effect == "jumped"` and col 4 | `effect == "flipped"` and col 4 |
| `tests/test_flip.py::test_a_rival_in_the_next_room_does_not_stop_the_jump` | `effect == "jumped"`, `to is None` | `effect == "flipped"`, `to is None`; docstring says so |
| `tests/test_flip_review.py::test_last_result_names_the_same_effect_as_the_motion[JUMP_RIGHT-...]` | param `"jumped"` | param `"flipped"` |

## Findings
1. **[major] `tests/test_gate_t05_qa_probes.py::test_qa_baseline_never_needs_a_fallback_over_randomised_duels_in_every_room`
   fails** on `assert ... and decisions > 5000`: 4735 decisions in the 36 seeded games, 5357 on the base.
   Reproduced; the zero-fallback assertions in that test pass. I toggled the three T19 rules off one at a time
   (script in the session scratchpad, not committed): the whole drop comes from the jump-faces-first change
   (`Rival._directional`); the flip look and the grace window change nothing in these 36 games. So the baseline
   and the random controller now finish duels sooner. Proposed edit for the orchestrator or Saad to approve: lower
   the volume floor (the assertion is about coverage, not a rule), or drop the facing change if you would rather
   keep R-D20 for `JUMP_*` (then the 0-tick "left + jump while facing the other way" case is a 4-tick turn first).
2. **[major] `tests/test_server_ws.py::test_keys_move_your_own_rival_and_each_client_gets_only_its_own_payload`
   fails**: client B sends `["a"]` ("A's key: ignored") and asserts B's column is unchanged. Decision #55 makes
   WASD drive B's own seat online, so B now moves. This is the rule #55 reverses, not a regression. Proposed edit:
   have B send a name that belongs to no seat, or assert that `a` moves B and never A (`tests/test_t19_controls.py`
   already covers both).
3. [minor] Item 3 premise: the brief says "the existing kneel pose used for rigging". In `render/` nothing drew
   `kneeled` specially (it fell through to the idle stand), and sword and uniform used the `take` strip. I used one
   named strip, `render/versus_view.py` `KNEEL = "crouch"`, for all three, so rigging now also shows a crouch.
   Needs Saad's eye on the art (the crouch strip is 6 frames stretched over 6 or 12).
4. [minor] "3 ticks apart behaves as two separate inputs" holds for direction-then-jump. For jump-then-direction it
   does not: the existing hop turn (R-V22; `tests/test_flip.py`, `tests/test_flip_review.py` pin "any visible hop
   frame, including the last") turns the hop into a flip whenever the direction arrives during the 8 hop frames. I
   kept it as the brief says ("a direction during a hop still turns it into a flip").
5. [note] Behaviour a player may notice: a tap of a direction followed within 2 ticks by `UP` (on open floor) now
   jumps that way instead of running one cell and then hopping.

## Known limitations
- Nothing was run in a browser or pygame window; the page changes are Node-tested and Python-tested only.
- The macro planner (`agents/macros.py` `plan_path`) still prices a `JUMP_*` against the facing as a 4-frame turn
  plus the jump and its predictor models a reversal as a turn only; the engine now jumps at once. I did not change
  `agents/` (the brief allows it only if the flip change breaks it, and the flip change alone does not).
- The grace window uses the engine's frame count, so it is 2 ticks at 12 Hz (about 170 ms) as decided; the page's
  catch-up of up to 3 ticks after a stall can shorten it in wall time.

## Unresolved findings
Findings 1 and 2 (two existing tests that need an approved edit), finding 3 (art).

## Requested next action
Commit to review: 7bbab99770e5d17b22ccf1d78c58bfff50174baf on task/T19 (this report is committed after it)
What changed: every directional jump flips; a jump within 2 ticks after a direction (or a direction within a hop)
is one flip that way, in the engine for every seat; either key set drives the player's own seat in human vs AI
and online; sword pickup, uniform take and rigging draw the crouch strip; R-V22 amended, R-V35 added.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q`; `node web/keys.test.js`;
new tests `tests/test_t19_*.py`; for the grace rule, `Duel._grace_jump` in `pop/versus.py`; for the AI-facing
effect, the decision count probe in Finding 1.
What I am unsure about: whether dropping the turn-first rule for `JUMP_*` is acceptable for the AI seats (it is
the whole cause of Finding 1); the crouch strip as the kneel (Finding 3); the `UP`-after-direction conversion
(Finding 5); whether a stalled-tick catch-up on the page should count toward the window.
Touches the knowledge boundary or AI seat: yes (Gate 2 applies: action and macro behaviour change for every seat).

For Gate 2 specifically (no `agents/rl/**` or `tools/rl/**` file was touched):
- `agents/rl/encoder.py` lists `jumped` and `flipped` together in `LEAPS`, so the effect name does not change its
  features. `agents/versus_baseline.py` does the same. Nothing in `agents/macros.py` tests `jumped` or `flipped`.
- What can change the shipped rival (`ppo-run-1.json`) is the dynamics, not the names: a `JUMP_*` opposite the
  facing no longer turns first, and a jump within 2 ticks after a direction replaces that move. Whether it needs
  re-evaluation or retraining is for Gate 2 and Saad; I make no claim.
- R-V25 masking is unchanged: `LEAPS` and `JUMPS` still include both names and `GUARD_MOTIONS` is untouched.

## Student decision required
Finding 1 and 2: approve the two test edits (or tell me which rule to keep). Finding 3: approve the crouch strip
as the kneel look.
