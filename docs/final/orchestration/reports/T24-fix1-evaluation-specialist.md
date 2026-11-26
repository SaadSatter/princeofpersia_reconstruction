---
handoff_id: HO-T24-fix1-evaluation-specialist
task_id: T24-fix1
date: 2026-11-26
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T24-fix1.md@773b955; reports/T24-evaluation-specialist.md@d187e1c; reports/T24-fix1-tech-lead.md@673f09f; reports/T24-fix1-qa.md@d91963a
source_branch: gate/T24-fix1-eval
source_commit: 3d94918 (code/tests; this report's own commit follows)
reviewed_commit: 673f09f (QA probes at d91963a)
verdict: ACCEPT
---

# T24-fix1: evaluation-specialist report (Gate 2)

Verdict: **ACCEPT.** No leak, no change to either macro rival, #101 behaves as specified at the boundary. Nothing required before Gate 3.
Not done, by instruction: no training, no `--live`, no H6 (`evaluation/heldout/` not opened). Tuning starts only.

## Paths
- `tests/test_eval_T24fix1_boundary.py` (new, 2 tests). No other file changed except this report.
- Scratch outputs (not committed): `old_*.json`, `new_*.json` in the session scratchpad.

## Before / after, tuning starts, seat-swapped
`evaluation/t24_compare.py`, `PYTHONPATH=. python evaluation/t24_compare.py <ppo|mirror|ppo_rand> 8 vary`. 32 combos x 8 engine seeds = 256 episodes per row, all counted. Weights `ppo-run-1.json`, unchanged.
Before: `git archive 1a515ca` in a scratch tree (`has_kneel_path: false`). After: 673f09f plus QA probes (`true`).

| Condition | Engine | W / D / L | Mean frames | Distinct final states | Seed-0 hashes (32) | Fallbacks | Aborted | DOWN-takes | DOWN sword pickups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PPO vs scripted baseline | 1a515ca | 240 / 16 / 0 | 859.2 | 30 | - | 0 | 0 | n/a | n/a |
| PPO vs scripted baseline | 673f09f | 240 / 16 / 0 | 859.2 | 30 | identical 32/32 | 0 | 0 | 0 | 0 |
| baseline mirror | 1a515ca | 128 / 0 / 128 | 738.4 | 14 | - | 0 | 0 | n/a | n/a |
| baseline mirror | 673f09f | 128 / 0 / 128 | 738.4 | 14 | identical 32/32 | 0 | 0 | 0 | 0 |
| PPO vs random-input seat | 1a515ca | 254 / 0 / 2 | 334.1 | 252 | - | 0 | 0 | n/a | n/a |
| PPO vs random-input seat | 673f09f | 254 / 0 / 2 | 334.1 | 252 | identical 32/32 | 0 | 0 | 3 | 22 |

Changed duels: **0** in every row (outcomes, by-seat W/D/L, reasons, means, distinct-state counts and seed-0 hashes all equal). Unintended disguises by a macro rival: **0** (DOWN-takes and DOWN sword pickups are 0 in both macro-only rows). The 3 DOWN-takes in the stress row are the random seat, the same count as at T24 (fix1 did not move it); they changed no outcome or hash. Fallbacks 0. Policy errors 0 (no aborted episode). Draws: 16 `time_up`, same two start pairs as T19/T24. Caveats unchanged: 32 distinct games vs the baseline, tuning starts the policy trained on, only seed-0 hashes per game compared (aggregates equal over all 768 episodes), no strength claim.

## Checks
- **F1 test pins "still hangs".** `tests/test_eval_T24_f1.py::test_down_at_a_ledge_edge_standing_over_a_body_still_hangs` asserts `_kneel_target() is None`, posture `hanging`, not disguised, `last_result.effect == "hanging"`. Passes. Only that test changed, as authorised.
- **R-V25 (same rule, no new knowledge).** `_would_hang_down` reads the rival's own `ahead()`, `blocks` and `geom.supported`, all of which `engine._down` already reads. It is on `Rival`, so both seats share it. My `test_edge_down_with_body_hangs_like_down_without_body_for_both_seats_keys` compares both seats' observation key sets every frame for 30 frames, body versus no body, at the edge: equal; plus effect `hanging`. QA's seat-B JSON equality probes (away from edges) also pass. No new observation key, legal action, log or error string.
- **R-V19 (suspicion).** A hang does not disguise, so suspicion is untouched. `TAKE` still takes the uniform at the edge (my `test_edge_take_still_takes_the_uniform`; QA's all-edge-cases test), and away from an edge DOWN still takes, so the T24 behaviour R-V19 covers is intact.
- **Macro layer.** `_hang_drop` plans DOWN at an edge; with the fix that DOWN now hangs even over a body, which is what the planner meant. Measured: 0 DOWN-takes in 512 macro-rival episodes.

## Findings
None. T24 Eval findings F1 and F2 are closed (F1 by the code and the test, F2 by the spec sentence QA confirmed). The T24 note (random seat disguises via DOWN over bodies) stands, intended by #94.

## Evidence affected?
No. Macro-rival behaviour is bit-identical to the pre-T24 base, so T08, T09 and `ppo-run-1.json` evidence stand. The single H6 run (decision #61) should name the engine commit.

## Leak findings, baseline fairness, runtime, reward and training, reproducibility, separation, live readiness
Not touched by T24-fix1 and not re-read; nothing changed in `agents/`, `tools/rl/`, `pop/observation.py` or the runner. The shipped weights test (`tests/test_rl_run1_shipped.py`) is in the suite. Fallbacks 0. Latency not re-measured (no inference change). Not applicable: live and training readiness.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q   (clean committed tree, 3d94918)
2046 passed, 11 skipped, 5 xfailed, 2 warnings in 428.53s (0:07:08)
uptime at finish: 0:11  up 11 days,  2:31, 2 users, load averages: 6.33 6.16 6.22
```
(1989 at 673f09f, plus QA's 55 probes and my 2.) `node --test web/` not run (no web file changed).

## Known limitations
No human, browser or online trial; tuning starts only; seed-0 hashes only per game.

## Before Gate 3
**None.**

## Requested next action
Orchestrator: Gate 3 on task/T24-fix1 with the QA and this report.

## Student decision required
none
