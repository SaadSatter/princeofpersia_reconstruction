---
handoff_id: HO-GATE-wave3-qa
task_id: GATE-wave3
date: 2026-11-24
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/wave2-batch.md@f2c25e8 (sections T07, T06b, T14-fix1; condensed summaries, these tasks predate per-task reports); docs/final/orchestration/tasks/T06b.md@f2c25e8; docs/final/orchestration/tasks/T07.md@f2c25e8; docs/final/orchestration/tasks/T14-fix1.md@f2c25e8; docs/final/orchestration/tasks/GATE-wave3.md@f2c25e8
source_branch: gate/wave3-qa
source_commit: see the commit that adds this file (tests and report are committed together)
reviewed_commit: T06b 9af96a9 (record 4e9121b); T07 1e34cf2; T14-fix1 ca3667b; all run on the combined line ae90c8c
verdict: T06b ACCEPT WITH NOTES; T07 REJECT (one failing test, trivial test-side fix; no product defect found); T14-fix1 ACCEPT WITH NOTES
---

# GATE-wave3: QA (Gate 1) report

Status: done. Branch `gate/wave3-qa` from `ae90c8c` (`git rev-parse HEAD` confirmed).
Run with `uv run --frozen --extra play --extra train pytest -q`.

## Paths
New tests (all pass, none xfailed):
- `tests/test_gate_w3_qa_T06b_traps.py` (12)
- `tests/test_gate_w3_qa_T07_rl.py` (10)
- `tests/test_gate_w3_qa_T14fix1_web.py` (9)

No production code or existing test was edited.

## Tests run
```
uv run --frozen --extra play --extra train pytest -q          (ae90c8c, before my tests)
1 failed, 1109 passed, 11 skipped, 2 xfailed in 114.76s
FAILED tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations
uv run --frozen --extra play --extra train pytest -q tests/test_gate_w3_qa_*   -> 12 + 10 + 9 passed
node web/keys.test.js -> keys.test.js: 6 passed
```
Full run with my 31 tests added: see the final line in "Full suite" at the end.

## Scope
`git diff --name-only <base>..<commit>`: T06b touched `pop/versus.py`, `docs/RULE_SOURCE_MAP.md`, `docs/final/TRAPS_SPEC.md`, `docs/final/VERSUS_SPEC.md`, `tests/test_traps*.py`, plus the session record (4e9121b). All permitted. T07 touched only `agents/rl/**`, `tools/rl/**`, `tests/test_rl_*.py`, `docs/final/RL_POLICY.md`, one session record. Permitted. T14-fix1 touched `web/**`, `tools/web/**`, `tests/test_web_*.py`, the copied `tests/test_gate_t14_*`, `docs/final/WEB_BUILD.md`. Permitted; workflows untouched. The three edited existing web tests are justified (the allowed import set gains `agents`; the archive may hold `agents/`, still banning tests/tools/traces/docs; keys.test.js defaults change to the baseline and gain `neutral`). Each edit is minimal and tied to a brief item.

---

## Verdict block: T06b (rival-rigged loose floor), reviewed_commit 9af96a9 (+4e9121b)
**ACCEPT WITH NOTES**

| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | 8 leak tests of spec section 6 | Met | `tests/test_traps_leaks.py` passes; mine add a sweep: B at 3 rows x 10 cols x 2 facings, A rigging from 2 columns (over 50 cases): B's `legal_actions` and tiles/state/edges/swords/suspicion/kid/me equal the unrigged control |
| 2 | Owner-harm | Met | existing test; lethal case in mine (`test_lethal_spring_leaks_nothing_to_the_victim`: 1-heart victim, no trap/rig/owner word and no seat id in B's view at any frame) |
| 3 | Guard springs a trap, guard downed | Met | `test_a_guard_springing_a_rig_...`; mine: a downed guard lying on a rig does not spring it |
| 4 | One-shot | Met | `test_a_rig_is_one_shot_and_frees_no_trap` |
| 5 | Cancel by hit or knockdown spends the trap | Met | existing tests |
| 6 | Double rig consumed by first body | Met | existing; mine: both seats rig the same cell from opposite sides at the same time, both succeed, both budgets drop to 3, one fall |
| 7 | Suspicion while rigging disguised | Met | 36 total (3 x 12) for seat A (existing) and seat B (mine) |
| 8 | Determinism | Met | existing trace test; mine: scripted two-seat rigging duel, snapshot trace equal across two runs |
| 9 | Frozen suite unchanged, full suite green | Met | `test_frozen_suite.py` passes; whole suite green apart from the T07 test below |
| 10 | Same observation keys both seats | Met | existing key tests; mine: rival adapter sees exactly `OBSERVATION_KEYS` |
| Extra | Spring timing | Met | shake to fall is the existing `LOOSE_DELAY` (within 2 frames, mine) |
| Extra | Illegal RIG | Met | at the room edge, with no traps left, while knocked down or hanging: refused (`accepted: False`), counted invalid, no free kneel, `traps_left` unchanged |
| Extra | Scratch merge with T05 and T07 | Met | `ae90c8c` already holds T05, T05-fix1, T04-fix3, T06b and T07; suite green except the T07 test |
| Extra | Gate plate | Not built | stated by the implementer and the brief ("if time allows"); spec section 11 explains why |

Findings (none reproduced as a blocker or major):
- [minor] `agents/macros.py:36` (`RESERVED = ("RIG_TRAP",)`) and `agents/macros.py:262`: no agent can issue `RIG` yet. RIG_TRAP is not mapped to the engine input, and the PPO mask keeps the slot False. Expected by the briefs (T05/T07 own it); it is the open task before the rival can rig. Reproduce: `grep -rn RIG agents/`.
- [minor] `pop/versus.py:356-366` (`_rig`): the cell is re-checked for floor only at the end of the kneel, not for bodies. If the other rival steps onto X during the 12-frame kneel, the rig is placed under it (verified: no spring while standing, `test_a_body_walking_onto_the_cell_during_the_kneel_...`). Not a leak. It leaves the rig live for the next arrival. The spec is silent; Saad may want "cancelled if a body is there".
- [minor, design, for Saad] "1 heart in all" (`_land`) adds a heart on short falls (implementer flagged; spec section 11 item 2). Behaves as documented.
- [minor, design] Legality is stricter than the spec (bottom row and holes opening to rooms below are refused; section 11 item 1). No leak; it shrinks the cells a rival may rig.
- [note] A disguised kneel is masked as standing still (R-V25), by design. No leak found.
- Not reproduced, unverified: gate-plate rig, a spring by a body that lands on the cell (no start position in the arena rooms gives a clean landing onto a cell on the same room's rows; not constructed).

---

## Verdict block: T07 (PPO stack), reviewed_commit 1e34cf2
**REJECT** (the brief's "full suite green" is not met on `ae90c8c`; the cause is in the test, the fix is small. I found no defect in the product code, and no major finding.)

| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Encoder leak test (disguised = guard) | Met | `tests/test_rl_encoder.py` passes; features read only observed fields; `minutes_left`, outcome, ids not read |
| 2 | Order invariance | Met | existing test passes |
| 3 | Mask correctness | Met | existing; RIG_TRAP always False; with no legal input only WAIT; my masked-probability test: a masked macro stays at probability under 1e-12 after 5 updates with entropy bonus |
| 4 | Deterministic rollouts for a seed | Met | existing; mine: same seed twice gives identical weights, and 1 worker equals 2 workers (`max_iters=2`, `max_frames=240`; the weights SHA matches) |
| 5 | Inference parity to 1e-9 over 200 observations | **Not met on `ae90c8c`** | see finding T07-QA-1. Mine passes with the corrected collection (200+ observations over 6 seeds, worst difference under 1e-9) |
| 6 | Weight hash checked at load | Met | wrong, tampered, missing hash all raise `WeightsError` (existing) |
| 7 | Smoke training run, 60 s or less | Met | existing smoke test passes in the suite |
| 8 | Full training run logged | Not applicable | training not started, as instructed |
| 9 | Full suite green | **Not met** | 1 failed, 1109 passed, 11 skipped, 2 xfailed |
| Extra | GAE, clipping, advantage normalisation | Met | hand-computed GAE with gamma 0.9 / lam 0.5 / bootstrap matches; a sample outside the clip range with positive advantage gives zero actor change (entropy off); batch advantages have mean 0 and std 1; the policy-gradient, entropy and Adam-time derivations read correct |
| Extra | `tools/rl/env.py` uses `on_frame` true state for reward only | Met | the only `.snapshot()` call is in `_Shaper.__call__`; running the same seed with shaping on and off gives identical features, actions and log-probs (`test_shaping_credit_never_changes_...`) |
| Extra | No held-out access | Met | no path to `evaluation/` or held-out starts in `env`, `train`, `ppo`; `TUNING_STARTS` holds the two tuning starts |

Findings:
- **[major, reproduced] T07-QA-1** `tests/test_rl_policy.py:46` (`_record`) asserts `len(rec.seen) >= 200` from one baseline-vs-baseline duel (`.run(3)`, `arena.STARTS`). Since T05-fix1 ended the mirror deadlock, that duel ends after 145 decisions. Reproduce: `uv run --frozen --extra play --extra train pytest -q tests/test_rl_policy.py::test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations` gives `assert 145 >= 200`. Cause confirmed: the product is fine and the test's data source shrank. Minimal correct fix (T07-fix1): collect across several seeds (6 seeds give over 200), and give each duel its own `Encoder` so history from a previous duel does not carry over. My `test_parity_holds_over_200_observations_collected_across_several_seeds` shows it. The other test using `_record(60)` still passes.
- [minor] `docs/agent-sessions/11-*`: the T07 record number collides with another record (the implementer noted it). Rename in the fix.
- [observation for Gate 2, not a defect] the target rule `nearest_target` (`agents/rl/policy.py:120`) is a fixed rule over observed positions; it counts a rival figure and a guard alike. Whether it helps or hurts I3 is the Evaluation Specialist's call.
- [observation] `final_check` and `train` use `copy_mode="json"`, `threaded=False`, `clock=lambda: 0.0`; the 85-minute cap and the 2-start tuning set are as the implementer reports. Not run (training is not approved).
- Not checked: wall-clock throughput of a full run, and whether a policy trained on 2 starts overfits (Gate 2).

---

## Verdict block: T14-fix1 (web corrections), reviewed_commit ca3667b
**ACCEPT WITH NOTES**

| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | `SeatControllerRival(controller, every=6)`: cadence, WAIT to None, tuple legal, fallback label, one controller per game | Met | `tests/test_web_rival.py` passes; mine: two `make_game` calls never share a controller and play identical 200-tick traces; rematch resets the controller and replays the same duel exactly (300 ticks) |
| 2 | Default AI rival is the baseline, idle and random kept as labelled options | Met | `make_game` and `parseOptions` (Node test: 6 passed); unknown name falls back to the baseline; the page links to all three |
| 3 | `agents/` in game.zip, stdlib only | Met | `AGENT_MODULES` is four files; archive-runs-alone test passes |
| 4 | `WebGame(rival=SeatControllerRival(make_baseline()))` plays 600 ticks, 0 invalid inputs | Met | mine: 600 ticks, a rematch, 600 more, both seats: `invalid_inputs == {A: 0, B: 0}`, 0 fallbacks |
| 5 | Smoke proves input reaches the engine | Met in logic, not run | `tools/web/smoke.cjs` compares `window.__smLast` position and canvas bytes before and after holding D, and fails if either is missing or unchanged. Playwright and a browser are not installed here, and the workflow has not run on CI, so it is text-tested only (as the implementer says) |
| 6 | Key hints for the human's seat | Met | Node test and Python page test |
| 7 | Neutral label, no other field differs | Met | mine: 40 ticks, payloads equal with `rival` removed; `rival == "Rival"`; the default label is not "Rival" |
| 8 | Build hash from the manifest on the page | Met | mine: `build` is 8 hex, reproducible across two builds, changes when a file hash changes, no local path in the manifest |
| 9 | WEB_BUILD.md notes | Met | adapter, public zip, editable query string, devtools closed, rematch keeps the seed, and "not verified in a browser" all present (sections "Playtest notes", "What has not been verified") |
| 10 | Node contract test passes; suite green | Met | `node web/keys.test.js`: 6 passed; suite green apart from the T07 test |
| Extra | Rival gets only its own view | Met | a hostile controller that wipes its observation cannot change the duel (the observation is a copy); the keys it sees equal `OBSERVATION_KEYS` |
| Extra | Duel over | Met | the adapter keeps being called after the end with no new invalid inputs |

Findings:
- [minor, T13 inherits] `web/main.js:89` (`exposeForTests`) always publishes `window.__smLast` (human seat position) on the live page, not only in a test mode. It is harmless for the human's own seat, but T13 online play must not put a remote seat's or the full state there. Gate it or keep it to the own seat.
- [minor, T13 inherits] The adapter calls the controller synchronously on the page's tick (`web/bridge.py` `SeatControllerRival.__call__`) with no time limit and no runner; a slower controller (PPO in pure Python every 6 ticks) stalls a frame, and a hang stalls the page. Fine for the baseline. T13's server runs the AI seat and should keep the runner's timeout.
- [minor, T13 inherits] The rival's label is built from the controller's name and kind (`AI rival: ... (scripted)`), so without `?label=neutral` a blind session shows what the opponent is. Neutral mode must be the default for Session B on any T13 page. The query string is editable by the player (documented).
- [note] Not verified in a browser: no Playwright or Chromium here, and CI has not run `web-smoke.yml`. The page, Pyodide import of `agents/` and the screenshots are unchecked.
- [note] Rematch keeps the seed (decision #25), so a replay of the baseline is identical; recorded in WEB_BUILD.md as a learning confound.

---

## Not checked
- A real browser, screenshots, the Playwright smoke run (not installed here).
- A paid or `--live` model call (not allowed).
- The full PPO training run and its quality.
- Gate-plate traps (not built).
- The Evaluation Specialist's items (ownership leak boundary through guards' reactions, H6 overfitting, neutral-label equivalence beyond the payload) are left to Gate 2; I checked only the payload and observation level.

## Full suite
`uv run --frozen --extra play --extra train pytest -q` with my 31 tests: 1 failed, 1140 passed, 11 skipped, 2 xfailed in 187.83s. The one failure is T07-QA-1.
