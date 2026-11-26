---
handoff_id: HO-GATE-wave3-evaluation-specialist
task_id: GATE-wave3
date: 2026-11-24
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/GATE-wave3-qa.md@e50a846 (gate/wave3-qa); brief docs/final/orchestration/tasks/GATE-wave3.md@54890b6
source_branch: gate/wave3-eval
source_commit: see the commit that adds this file (tests and report are committed together)
reviewed_commit: T06b 9af96a9 (record 4e9121b); T07 1e34cf2; T14-fix1 ca3667b; all run on the combined line ae90c8c
verdict: T06b ACCEPT WITH NOTES; T07 ACCEPT WITH NOTES (must-fix list below; QA's T07-QA-1 stays a blocker); T14-fix1 ACCEPT WITH NOTES
---

# GATE-wave3: Evaluation Specialist (Gate 2) report

Status: done. Branch `gate/wave3-eval` from `e50a846`. No training run, no paid call.
Full-suite line and my new tests are at the end.

## Paths
New tests (all pass; one skips by design):
- `tests/test_gate_w3_eval_T07_probes.py` (6 tests, 1 skip until `evaluation/heldout` exists)
- `tests/test_gate_w3_eval_T06b_probes.py` (2)
- `tests/test_gate_w3_eval_T14fix1_probes.py` (2)
No production code, encoder, trainer, existing test or criterion was edited. Scratch probes ran from the session scratchpad.

## Leak findings
none found. Probed:
- **T07 feature boundary.** Read `agents/rl/encoder.py` line by line. It reads `room, tiles, edges, me, figures, swords, suspicion` and the seat's own `status`; never `minutes_left`, outcome, ids, the seed, the other seat's hearts, or the figure list order (figures are sorted by an observed-field key). A disguised rival has `kind "guard"` and its motion masked (R-V18), so it encodes like a guard (QA's engine test confirms). The reward-shaping view (`on_frame`, `snapshot()`) is used only in `_Shaper`; QA's shaping-on/off identical-features test holds.
- **T07 inference path.** `PolicyMacro` calls only `encoder.update/features`, `nearest_target`, `macro_mask` on the seat's own observation, legal tuple and status. No clock, no runner state.
- **T06b ownership boundary** (beyond QA's sweep). (a) The tile never changes while rigged (probe: B's tiles equal before and 20 frames after A's rig). (b) RIG legality reads the other seat's *landing cell* (`claimed`), not its rigs. A disguised B jumping into the cell ahead of A flips A's RIG legality mid-flight. I checked whether that tells a disguised rival from a guard: over 8 B columns x 2 jump types x 8 A columns, every mid-flight legality difference came with a visible `motion` on B (jumps and flips are always shown, R-V19 `suspicious_rise`), so legality adds no tell. Test: `test_a_disguised_jump_that_changes_the_others_rig_legality_is_visible_in_that_view`. (c) `claims()` covers only the jumper's own room, so no cross-room legality leak. (d) Guards springing a rig is a visible event and reveals only that a rig existed there afterwards; no owner.
- **T06b kneel.** An undisguised kneeling rival is shown to the other seat with `motion.effect == "kneeled"` and its facing, so the cell ahead is readable by a human. TRAPS_SPEC section 2 says the other seat "does not see which cell"; that holds only up to facing. A disguised kneel is shown as a paused guard (R-V25). Not a leak of ownership or of the rig's existence after the kneel; a design note (T06b-E1).
- **Could a PPO encoder learn the other seat's rigs?** No. The encoder has no `my_traps`, `traps_left`, or motion-effect field except a binary `moving` and a leap flag. Kneel reads as "moving". The rig itself is invisible in tiles, legal actions, `last_result`, suspicion and guard behaviour until it springs.
- **T14-fix1.** `WebGame.tick` passes `ep.observe(seat)` and `ep.legal_actions(seat)` for the AI seat only (a spy rival sees exactly `OBSERVATION_KEYS`, and `me` is its own). Neutral payload text contains none of: baseline, scripted, fallback, placeholder, idle, random, ppo, policy, for all three rival kinds (my test; QA's test compares the whole payload minus `rival`). The build hash comes from the manifest and holds no path (QA).

## Baseline fairness
Unchanged since GATE-T05-fix1 eval: same observation and macros as the PPO rival (the baseline keeps tracker memory; the PPO encoder keeps its own short history; disclosed in `MACROS.md`). One fairness difference remains: the baseline chooses its own strike target from tells, while the PPO rival is limited to the nearest-figure target (see T07, N-target). Per-seat reporting for any baseline comparison is required (decision #31) and the trainer's `final_check` and training eval report only totals; T08's comparative run must report per seat.

## Reward and training method (T07)
- Terminal +1 / -1 / 0; shaping +0.1 per heart dealt, -0.1 per heart taken, +0.05 on becoming disguised. Hearts are 3 at most (episodes with random weights: shaping totals measured over 32 episodes were within -0.2 to +0.2 against terminal +-1), so the terminal reward dominates. My test asserts |shaping| <= 0.5 in 6 episodes.
- **Shaping exploits.** (1) Disguise bonus: it fires only on false-to-true, and re-disguise needs another downed guard's uniform (R-V26 gives `no_uniform` for a stripped body), so it is bounded by the number of guards (a few hundredths). A loop of disguise, lose it, disguise is not available without new bodies. (2) Hearts dealt count any heart the opponent loses (guards, falls, trap spring), so the learner is paid when a guard or a fall hurts the opponent. That is mild and not exploitable by the learner. (3) `-0.1` per heart taken plus a `-1` loss can teach avoidance. Untrained policies lost 30 of 32 duels to the baseline (2 wins, 0 draws, all duels end by a win), so there is no time-up draw attractor yet, but a trained policy could learn to flee to a draw (0 beats -1). Watch `draws` in `log.jsonl`. (4) `RewardConfig` credits go to the previous macro (off by one decision); harmless.
- PPO maths: QA verified GAE, clipping, advantage normalisation, masking. I read `_adam` (the step counter advances once per actor update and the critic reuses it: correct) and `update` (gradient norm clip 0.5 as documented). Truncated episodes bootstrap with 0 (only matters if `max_frames` is set; the full run leaves it `None`).
- **Last weights are exported once, after the loop** (my source test); `summary.json` writes `checkpoint_chosen_by_score: false`. Snapshots in the opponent pool are only opponents, not outputs.
- Hyperparameters, seed, commit, steps and wall time are in `config.json` and `summary.json`.

## Checkpoint reproducibility
`load_net(path, sha256)` refuses a missing, wrong or tampered hash and a mismatched encoder (QA). Same seed and 1 worker, and 1 against 2 workers, give identical weights SHA (QA, `max_iters=2`). Pure-Python against numpy parity holds to 1e-9 once the 200 observations are collected over several seeds (QA). Not reproduced here: the full 85-minute run (not approved). The RL_POLICY.md weights table is empty ("waiting for T05-fix1"); it must be filled with the real hash, commit, steps and wall time after the run.

## Train / held-out separation
- Training starts: exactly `env.TUNING_STARTS` (2 pairs; COMBOS = 8 combinations of pair, seat, which start). Test: `test_training_starts_are_exactly_the_two_tuning_starts_...`.
- No path to the held-out set: a source scan (AST imports and text) of `tools/rl` and `agents/rl` finds no `evaluation` import, no "heldout", "held_out", "evaluation/" or "H6" in code. Test: `test_training_code_cannot_reach_the_heldout_set`.
- **`evaluation/heldout/` does not exist on this line** (`ls evaluation` fails), and T08 has not frozen H6, so I cannot check disjointness, the file hash, or run-once-per-frozen-policy. My disjointness test skips until the directory exists. See finding T07-E2.
- Training-time numbers (`win_rate_vs_baseline_tuning`, `final_check`) are on the tuning starts and are tuning numbers, never evidence of strength. They also use fixed engine seeds (900000+, 10000+) that must stay out of the T08 secret `seed_key` space (#24); T08 should draw its seeds from the key.
- Overfit risk is high: two starts, one arena, fixed guard posts, a fixed 8-combination cycle. Enough for a policy to memorise routes. Whether H6 detects that depends on H6 being a different set of starts in the same arena; it cannot show generalisation to other layouts.

## Evaluation validity and confounds
Not run (no comparative evaluation is in scope). Confounds to carry into T08's report: (1) two tuning starts only; (2) the nearest-figure target rule; (3) argmax at inference against sampled actions in training; (4) baseline memory against PPO history; (5) fixed arena and fixed guard posts; (6) untrained policy loses about 94 % (30 of 32) to the baseline, so a trained policy that does not beat it is an expected, reportable outcome and must be reported as such, with Wilson intervals, per seat, every round including aborted ones.

## Local inference performance
**Measured** on this machine (Apple M4, 10 cores, CPython 3.13.5 at the repo, pure Python, random-initialised 251-64-64-9 net): `PolicyMacro.choose` mean 0.12 ms, p99 0.65 ms, max 2.9 ms over 660 calls (4 duels vs the baseline); `Net.logits` mean 0.28 ms, max 2.9 ms over 256 calls. The cadence is 6 frames (100 ms at 60 fps) and the policy decides at most every 4th decision. My test asserts mean < 10 ms and max < 100 ms. **Not measured**: Pyodide (browser) latency, and a trained net (same shape, so same cost). **Estimated** only: Pyodide runs CPython roughly 3 to 10 times slower, so about 1 to 3 ms mean, still far under one cadence. The browser build does not ship `agents/rl` or weights yet (T14-fix1 ships four agent files), so the PPO rival cannot run in the page.

## Replay and fallback
- A trained-rival duel replays the same as any duel: the controllers are deterministic given the seed (argmax, no RNG at inference), and the runner trace is the existing mechanism. I did not re-run a PPO trace replay because there are no trained weights; QA's smoke covers the train-export-reload path. Replay is never counted as new evidence.
- Fallback: `PolicyMacro.choose` catches any exception, counts it in `errors` and returns `WAIT`. That `errors` count is a controller field; the runner's labelled `"source": "fallback"` path covers runner-level failures. Gap: `PolicyMacro.errors` is not copied into the runner's per-seat fallback count or the result, so a policy that errors on every call would produce a seat that always waits with **zero** reported fallbacks (T07-E4). In training, `play_episode` reports `fallbacks` from the runner only, so the same gap hides encoder exceptions during the 85-minute run (they would look like a learner that likes WAIT).
- T14-fix1 adapter fallbacks (`fallbacks` counter) appear only in the non-neutral label; the neutral label hides them and nothing logs them (T14-E3).

## Training-run readiness
**Not ready: five items to settle first** (full run estimate below). Measured throughput on this M4: 8 full untrained duels in 2.7 s with shaping on, about 50 macro decisions per episode. At 2 workers one update (16 training and 8 greedy evaluation episodes) is about 2 to 4 s once duels are longer, so 85 minutes is about 1,300 to 2,500 updates and well under 2 M decisions. Estimated, not measured with a trained policy. The "6 s per update" in RL_POLICY.md is a sandbox figure. Needs Saad's go-ahead (not requested here).

---

## Verdict block: T06b (rival-rigged loose floor), reviewed_commit 9af96a9 (+4e9121b)
**ACCEPT WITH NOTES**

| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Ownership never reaches the other seat (tiles, `my_traps`, legal actions, outcome, `last_result`, guards, suspicion) | Met | QA sweep over 50+ placements plus my channel list above |
| 2 | RIG legality does not reveal the other seat's rig | Met | `rig_target` tests only own rigs and `claimed` landing cells (visible motion) |
| 3 | A PPO encoder cannot learn the other seat's rigs | Met | no trap or motion-effect fields in the 251 features |
| 4 | Kneel masking for a disguised rival | Met | probe: guard-like figure, `motion None`, tile unchanged |

Findings:
- [minor] **T06b-E1** Undisguised kneel plus facing identifies the rigged cell to anyone in sight (`motion.effect "kneeled"`). TRAPS_SPEC section 2 ("does not see which cell") is slightly stronger than the engine. Either soften the sentence or accept; no code change needed. Saad's call (balance).
- [minor] **T06b-E2** The PPO rival cannot rig at all (`RIG_TRAP` is `RESERVED` in `agents/macros.py:36` and False in `macro_mask`), so the rival never uses the trap feature the game now has. Wiring is a T05/T07 follow-up, and it changes the action vocabulary (CQ-1, Saad). See T07-E1.

## Verdict block: T07 (PPO stack), reviewed_commit 1e34cf2
**ACCEPT WITH NOTES** (no leak, no reachable held-out path, no criterion of mine failed; QA's reject on T07-QA-1 stands and must be fixed with the items marked "before training")

| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Feature boundary | Met | no hidden field read; figure order by observed fields; no clock, id or seed |
| 2 | Shaping reads only training-time data and is dominated by terminal | Met | `_Shaper` only; |shaping| <= 0.2 in 32 episodes |
| 3 | Last weights exported, none chosen by score | Met | source test |
| 4 | Held-out unreachable from `tools/rl` | Met | AST and text scan test |
| 5 | Held-out frozen, disjoint and hashed | Not checkable | `evaluation/heldout/` absent (T08) |
| 6 | Local inference well inside a cadence | Met (measured) | mean 0.12 ms |
| 7 | Fallback counted and labelled | **Partly met** | T07-E4 |
| 8 | Ready for the full run | Not yet | items below |

### Must be fixed before training (T07-fix1 and the decisions that gate the run)
1. **T07-QA-1** (QA, major): `tests/test_rl_policy.py::_record` collects from one duel that now ends after 145 decisions. Collect over several seeds with a fresh `Encoder` per duel. Rename the colliding session record number.
2. **T07-E4** (major for training honesty): count `PolicyMacro.errors` (inference exceptions) into the seat's fallback count that `play_episode` and the evaluation harness report, and have the trainer fail or log loudly when any learner `errors` is non-zero. Today an encoder bug during the 85-minute run shows up as a policy that likes WAIT, with `fallbacks: 0`. Suggested minimal fix: have `TrainPolicy.choose` and `PolicyMacro.choose` expose `errors` to the controller wrapper, and add `errors` to each `log.jsonl` row and to `summary.json`; assert zero in the smoke test. (The training `TrainPolicy.choose` has no try/except at all, so an exception there would crash an episode rather than fall back; decide which is wanted, but it must be visible.)
3. **T07-E1** (decision, Saad, before the run): train with `RIG_TRAP` masked (disclose "this rival cannot rig traps", consistent with the baseline, which does not rig either) or wire RIG first. Training now and wiring later throws the 85-minute run away, because the mask, the action meaning and the feature set (`my_traps`, `traps_left`) change.
4. **T07-E2** (T08, before the run): freeze H6 starts and record their hash, and confirm they share no start with `TUNING_STARTS` (my skipped test then enforces it). Without it, "tuning starts only" cannot be shown.
5. **T07-E3** (decision, Saad, before the run): two tuning starts will be memorised. Either accept and report it, or add tuning starts disjoint from H6 (RL_POLICY.md "Open items"). Do not tune on H6.

### Can wait (after the run, or never)
- **N-target (nearest-target rule vs I3).** Reproduced as a characterisation test (`test_nearest_target_rule_...`): the target is the nearest non-downed figure by `4*|row| + |col|`, ties to the lower column, and counts a guard and a rival alike. In I3 ("strike the disguised rival, not a real guard") the policy cannot pick the farther one, so a real guard nearer than the disguised rival is struck or followed instead of the rival, and the only correct policy is to withhold STRIKE until the rival is nearest. The rule also uses no observed tells to choose (the baseline does). It cannot create a leak, since it reads only observed positions, and it cannot help identify. Effect: it caps I3 and F5 performance, and T08 must report it as a named confound (it is in `RL_POLICY.md` as a known limit). Fixing it (a learned target slot over the K=3 figures) changes the action space (CQ-1), so it is Saad's call and is not a pre-training fix.
- **T07-E5** (minor): `Encoder` figure slots include downed bodies, so three bodies can crowd out a live figure (K=3 by distance). Rare in the arena; note only.
- **T07-E6** (minor): inference is argmax, training samples; the final check reports argmax. Expected; disclose in the results.
- **T07-E7** (minor): shaping rewards "heart dealt" for any opponent heart loss (guard, fall, trap). Disclose.
- **T07-E8** (minor): `docs/final/RL_POLICY.md` weights table and "Results" stay empty until the run; per-seat results are required (decision #31) in T08's report; fill the real hash and wall time then.
- **T07-E9** (minor): `tools/rl/train.py` `final_check` and the in-loop eval use fixed seeds (10000+, 900000+), outside T08's secret `seed_key`; keep T08's seeds from the key.

## Verdict block: T14-fix1 (web corrections), reviewed_commit ca3667b
**ACCEPT WITH NOTES**

| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | AI seat gets only its own view | Met | spy rival sees `OBSERVATION_KEYS` of its own seat; a mutating rival cannot change the duel (QA) |
| 2 | Neutral label really neutral | Met for the label | payload text has no kind, fallback or controller word in all three rivals |
| 3 | Build hash reveals nothing | Met | 8 hex from the manifest, no path (QA) |
| 4 | Fallback labelled and counted | **Partly** | counted; visible only in the non-neutral label |

Findings (T13 inherits where marked):
- [minor, **T13 inherits**] **T14-E1** The neutral label is neutral only on the page. The rival kind is in the URL (`?rival=baseline`, `?label=neutral`) and editable, and `agents/` in `game.zip` is readable, so a blind session leaks what the opponent is to anyone who looks (documented in WEB_BUILD.md). T13's online page must pick the opponent server-side, show no query option for it, and ship no `agents/` to the client.
- [minor, **T13 inherits**] **T14-E2** (QA's finding, restated) `window.__smLast` is published on the live page for the human seat's own position; T13 must not publish a remote seat's or the full state there.
- [minor, **T13 inherits**] **T14-E3** Adapter fallbacks are never logged or returned; neutral mode hides the count. T13's server must log the AI seat's fallbacks per seat (`"source": "fallback"`) and abort over the limit, as the runner does.
- [minor, **T13 inherits**] **T14-E4** (QA's finding, restated) the adapter calls the controller synchronously with no time limit and bypasses the T04 runner. The server-run AI seat in T13 should use the runner's timeout path.
- [note] The PPO rival is not wired into the page (no `agents/rl`, no weights, no hash in the build). That is out of scope for T14-fix1 but is a task before any browser claim about the trained rival.
- [note] Not verified in a browser (no Playwright here); I measured nothing about Pyodide.

## Not checked
A real browser; Pyodide latency; a full PPO run or trained-policy replay; H6 (absent); T08's comparative scenarios; paid calls; gate-plate rigs (not built).

## Tests run
`uv run --frozen --extra play --extra train pytest -q tests/test_gate_w3_eval_*`: 9 passed, 1 skipped (heldout not present).
Full suite: see final line below.

Full suite (`uv run --frozen --extra play --extra train pytest -q`, with QA tests and mine): 1 failed, 1150 passed, 12 skipped, 2 xfailed in 217.90s. The one failure is T07-QA-1 (`test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations`).
