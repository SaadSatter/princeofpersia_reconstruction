# Audit: flip (R-V22), two-seat versus engine

- **Date:** 2026-11-18
- **Commit:** `05fe136` (branch `final/versus-engine`, in sync with `origin`)
- **Scope:** commits `8c2d9bd` (flips over rivals, guards, holes and spikes) and
  `05fe136` (flip from a run or a hop), against base `339cbdb`. Commits
  `fa086fe` (guard art) and `dfc8ade` (TAKE from the rival's own cell) are in
  the same range but outside this scope and were not audited.
- **Auditor:** Claude Code, `game-rules-audit` skill, run in a session
  separate from the one that built the flip. This session did not write or
  change any of the audited code.
- **Files read:** `AGENTS.md`, `CLAUDE.md`, `docs/final/README.md`,
  `docs/final/REQUIREMENTS_CHECKLIST.md`, `docs/final/EVIDENCE_INDEX.md`,
  `docs/RULE_SOURCE_MAP.md` (row R-V22), `docs/final/VERSUS_SPEC.md` (R-V22,
  §10), the diff `339cbdb..05fe136` for `pop/engine.py`, `pop/versus.py`,
  `play.py`, `tests/test_disguise.py`; `pop/versus.py` (rival blocks, duel
  queries, `legal_actions`, `submit`, `tick`, `_advance`, `_hop_turn`,
  `_start`, `_separate`, `observe`, `VersusEpisode`); `pop/physics.py`
  constants; `tests/test_flip.py`.
- **Not read this session:** `docs/MIDTERM_GUIDELINES.md`, `docs/GAME_SPEC.md`,
  `docs/final/GDD.md`, `docs/final/CONFIGURATION.md`, `pop/interface.py`,
  `pop/observation.py`, `pop/runner.py`, `agents/`, `evaluate.py`. None of
  them changed in the audited commits (`git diff --stat 339cbdb..05fe136`
  lists no file under `agents/`, `pop/interface.py`, `pop/observation.py`,
  `pop/runner.py` or `pop/situations.py`).

## Commands run

| Command | Result |
| --- | --- |
| `uv run pytest -q` | 417 passed, 1 skipped |
| `uv run pytest -q tests/test_flip.py` | 21 passed |
| `uv run pytest -q -k "leak or legal or limit or determin"` | 35 passed, 1 skipped, 382 deselected |
| `grep -rn "import pygame" pop/` | no matches |
| `grep -rn "pop.engine\|pop.levels\|GameState\|open(" agents/` | no matches |
| `ls server web` | neither exists |
| Probe scripts in the session scratchpad (not committed) driving `VersusEpisode` on arena A | results quoted in the findings |

## Checks

Result values: PASS, FAIL, NOT IMPLEMENTED, and NOT CHECKED (not checked
again this session because the audited commits do not touch it; see
"Not checked").

| Check | Result | Evidence |
| --- | --- | --- |
| A1 Five operations | PASS (versus) | `VersusEpisode.reset/observe/legal_actions/step/outcome`, `pop/versus.py` (`class VersusEpisode`, line 861) |
| A2 Unknown player id rejected | PASS | `ep.step("C", "UP")` raises `ValueError: unknown seat` (`_check_seat`) |
| A3 `outcome()` fields | NOT CHECKED | Versus `outcome()` returns status, reason, frames, inputs, invalid_inputs; it has no score or call count. Model calls are not wired to versus seats yet (G4/G6) |
| B1 Observation keys | PASS for the flip | The flip adds only the value `flipped` to the existing `motion.effect` key (`FIGURE_KEYS`, `ME_EXTRA_KEYS` unchanged). `motion.to` is `None` when the landing cell is in another room (`_motion_view`) |
| B2 Nothing from other rooms | PASS, with a note (F3, F6) | Figures and their motion are listed only for the observer's room. `_can_vault` refuses to vault a body outside the jumper's room |
| B3 `legal_actions` from posture only | PASS for the flip | No new legal action: `_HOP_FLIP_LEFT/RIGHT` are internal and refused from a seat (`step("A", "_HOP_FLIP_LEFT")` gives `unknown action`). Mid-hop list equals the standing list |
| B4 Step results leak nothing | PASS | `step` returns accepted/action/queued_at_frame or an error string; unchanged |
| B5 Model prompt from observations only | NOT CHECKED | `agents/` unchanged; grep clean |
| B6 Baseline same inputs | NOT CHECKED | `agents/` unchanged |
| C1 Out-of-vocabulary action refused | PASS | `_HOP_FLIP_LEFT` refused with `unknown action` |
| C2 Malformed actions | PASS | `step("A", None)`, `step("A", 7)` give `action must be a string` |
| C3 Terminal refuses actions | NOT CHECKED | `legal_actions` returns `()` when terminal; not changed |
| C4 Consecutive-invalid limit | NOT CHECKED | unchanged |
| D1-D5 Episode limits, traces | NOT CHECKED | runner unchanged; per-seat limits are "not started" in the final checklist |
| E1 Human and agent share `step` | PASS | `play.py` maps keys to `RUN_JUMP_*`/`JUMP_*`/`LEFT`/`RIGHT`, all in the seat vocabulary, and submits them through `ep.step` after `ep.legal_actions`. The hop-to-flip runs inside the engine (`Duel._hop_turn`) for any seat, so an AI seat sending a direction mid-hop gets the same flip |
| E2 No pygame in `pop/` | PASS | grep clean |
| E3 Macro frame counts | PASS for the flip | Flip uses the jump's own spans and frames (`P.JUMP` 12, `P.RUN_JUMP_FLIGHT` 8); `motion.frame` now counts from take-off (`test_regression_running_jump_flight_counts_its_own_frames`) |
| E4 Determinism | PASS | Probe: two runs of a script with a hop-flip by A and a running flip plus hop-flip by B over 40 frames give identical observations for both seats |
| F1 Rule, test and map agree | FAIL in one case (F1 below) | R-V22 row and VERSUS_SPEC agree with the code for guards; the landing claim does not cover the other rival |
| F2 No label promotion | PASS | R-V22 is `design`, cites VERSUS_SPEC §3 and Saad 2026-11-17 |
| G1 Seat id checked | PASS | `_check_seat`; internal hop-flip action cannot be sent by a seat |
| G2 Disguise identity | PASS for observation fields; behaviour note F2 | Probe: B disguised beside a real guard, A's figures are `['guard', 'guard']`. Flip effect and vault rules are the same for a disguised rival and a guard (`standing_at` / `guard_at` both block and both may be vaulted) |
| G3 Trap ownership | NOT IMPLEMENTED | Traps not built |
| G4 Per-seat history and model session | NOT IMPLEMENTED | Versus model seat not built |
| G5 Simultaneity | FAIL (finding 1a) | Corrected later in this session: the first version said PASS, based only on a mutual flip from standing, which mirrors correctly when the seats are swapped. The independent reviewer then pointed to the arrival frame, and a sweep probe confirmed that the seat id changes the result there |
| G6 Per-seat limits | NOT IMPLEMENTED | Final checklist: "per-seat limits not started" |
| H1-H7 Online server boundary | NOT IMPLEMENTED | `server/` and `web/` do not exist |

## Findings

Most severe first.

1. `[should fix] pop/versus.py:341-346 (Duel.landings), pop/versus.py:573-582 (Duel._separate)` — A jump's landing cell is claimed only against guards. The other rival may step into it during the flight; when the jumper lands, `_separate` sends whichever rival moved that frame back to where it was, so the jumper ends on its **take-off** cell after a full 12-frame flight shown heading for `motion.to`. R-V22 says the flip "lands beyond (never on anyone)"; it does not land on anyone, but it silently snaps back 3 cells. — Probe, arena A room 2 row 0, no guards: A at col 3 `JUMP_RIGHT` (`motion.to = [0, 6]`), B at col 7 `STEP_LEFT` reaches col 6 at frame 10; at frame 13 A stands at col 3 and B at col 6. The same happens to a plain jump (existing behaviour), but a flip lands right beside the body it passed, which makes this much more likely. No test covers a rival entering the landing cell.
1a. `[should fix] pop/versus.py:479-480 (Duel.tick, seats advanced in SEATS order)` — Whether a jump flips depends on the seat id when the other rival's run reaches a new cell on the frame the jump starts. Each seat plans its jump inside its own `_advance`, so seat A plans before B has moved that frame and seat B plans after A has. Added after the independent review raised it. — Probe: jumper at room 2 col 2 facing right, runner at col 5 running left, `JUMP_RIGHT` sent after k ticks. For k = 4: when the jumper is seat A it plans a plain jump to col 4, the runner arrives there, and A snaps back to col 2. When the jumper is seat B it sees the runner already at col 4, flips to col 5 and lands there. Every other k gives the same result for both seats. No swap-seat test covers it.
2. `[note] pop/versus.py:333-339 (cell_free_for_guard), 341-346` — Disguise behaviour tell caused by finding 1: a real guard never steps into a jumper's landing cell, but a disguised rival can. A seat that sees a "guard" walk into its landing cell knows that figure is the other rival. The observation fields do not differ (G2 passes); the difference is in behaviour. Fixing finding 1 the same way for both rivals and guards would remove it.
3. `[note] pop/versus.py:345` — `landings()` includes landing cells in any room, so a guard in room X refuses to step into a cell that a rival flying in from room Y will land in. A seat in room X could see the guard hold its position just before the jumper appears (at most one flight, 8-12 frames, early). Small, but it is a reaction to something outside that seat's room.
4. `[note] tests/test_flip.py:114-119; pop/versus.py (guard sight and strike, R-V14/R-V15)` — Flipping over a guard that **faces** the jumper fails: the jumper keeps its cell until it lands, so the guard sees and stabs it in mid-air. Probe: guard posted at col 4 facing left, A at col 3 `JUMP_RIGHT` (`flipped`, to col 6). At flight frame 5 A loses a heart and ends at col 2. VERSUS_SPEC accepts that "a lunge into that cell still hits it", and the guard test deliberately uses a guard facing away. Whether "guards can be flipped over" (Saad's playtest) is meant to include an alert guard facing the rival is a design question for Saad, not a code defect.
5. `[note] docs/final/VERSUS_SPEC.md:103, tests/test_flip.py:140-149` — The spec says a body in another room "still blocks, as before, so a jump never reveals someone out of sight", and the test is named `..._is_not_revealed`. The block itself is visible: with B at room 3 col 0, A's jump from room 2 col 8 shows `motion.to = [0, 9]` at take-off and stays in room 2, while with nobody there the jump would cross into room 3 (`to = None`). The flip neither adds nor removes this channel (it comes from the existing cross-room blocking rule), but the wording overstates what the test shows.
6. `[note] tests/test_flip.py` — Missing tests: a rival entering a jumper's landing cell (finding 1); a swap test for G2 (flip over a disguised rival compared with a flip over a real guard in the same cell, both seats' observations equal apart from the known `me` fields); a determinism test that includes a hop-flip (the probe above shows determinism holds; there is no committed test).

## Not checked

- A3, B5, B6, C3, C4, D1-D5: the runner, interface, observation module and
  agents did not change in the audited commits; not checked again this session.
- G3, G4, G6, H1-H7: features not built (traps, versus model seat, per-seat
  limits, server and web client).
- The flip picture (`render/versus_view.flip`, `render/dungeon.py`,
  `render/draw.py`): only the headless pose test was run; no window was
  opened, so the somersault was not checked by eye on macOS.
- Commits `fa086fe` and `dfc8ade`: outside the requested scope.
- The reference source: R-V22 is a `design` rule with no `code` locator to
  verify.

This audit does not decide whether the flip is ready to merge; Saad decides
what to do with each finding.
