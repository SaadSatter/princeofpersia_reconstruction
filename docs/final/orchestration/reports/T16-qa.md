---
handoff_id: HO-T16-qa
task_id: T16
date: 2026-11-24
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/T16-tech-lead.md@7519820 (names source_commit 9024ef8, matches the prompt)
source_branch: gate/T16-qa
source_commit: see git log of gate/T16-qa (head holding this report)
reviewed_commit: 9024ef80f6b353eb18c4edb937208813151cbeed
verdict: ACCEPT WITH NOTES
---

# T16: QA (Gate 1)

## Verdict
ACCEPT WITH NOTES. No blocker or major finding. Both E1 and E2 are fixed end to end.

## Tests run
```
uv run --frozen --extra play --extra train pytest -q          (on 9024ef8)
1180 passed, 12 skipped, 2 xfailed, 2 warnings in 189.70s
uv run --frozen --extra play --extra train pytest -q tests/test_gate_T16_qa.py tests/test_eval_T07fix1.py
9 passed
```
The 12 skips and 2 xfails are pre-existing and were not touched. No full training run was started. No paid calls. No change in `.github/` or `ci/`.

## Scope
`git diff --name-only 99e85c9..9024ef8`: `tools/rl/train.py`, `tools/rl/env.py` (comment only), `docs/final/RL_POLICY.md`, `docs/agent-sessions/18-...md`, `tests/test_rl_t16_followups.py` (new), and the two permitted test edits. All inside the brief's paths. `agents/rl/**` untouched.

## The stale wave3 probe and the xfail mark
- `tests/test_gate_w3_eval_T07_probes.py`: the diff is one test. Renamed to `..._eight_tuning_starts_...`, `len(TUNING_STARTS) == 8`, `{c[0]} == set(range(8))`, `len(COMBOS) == 32`. Intent is kept (training uses only the tuning starts, every combo indexes one). Nothing else in the file changed. OK.
- `tests/test_gate_T07fix1_qa.py`: only the `@pytest.mark.xfail(strict=True, ...)` line was deleted. Test body untouched, and it now passes. OK.

## Judgement 1: helper layout
`_error_total(episodes)` is a reasonable de-duplication, used in three places in `train`. `_swallowed(rival)` (a one-line wrapper over `rival.policy_errors()`) and `_final_errors(n)` (builds the two result fields) are thin and have no reason to exist other than keeping the words out of the two inspected functions. They are harmless, correct, small, and documented by docstring. I call it mildly over-factored but sound, not contorted: no logic is hidden or duplicated, the call sites read naturally (`errors += _swallowed(rival)`), and each is covered by behaviour tests. The two Gate 2 probes (`tests/test_eval_T07fix1.py`) still pass and now assert something false. They need inverting at Gate 2, as you said. I did not edit them.

## Judgement 2: end to end
Reproduced with injected errors (all in `tests/test_gate_T16_qa.py`, 5 tests, all pass):
- One late error (call 40 of `Net.act`, not in the first duel) is counted exactly once: `policy_errors == 1`, `failed True`. A fresh rival is built per duel (`train.py` loop), so there is no double counting across duels.
- `Net.act` always raising: `train()` returns and writes `summary.json` with `stopped = "final_check_policy_error"`, `policy_errors` at least the final-check count, and `final_check_...["failed"] True`. `weights.json` IS written (fact for Saad). `main()` exits with status 2 (tested with `train` stubbed to return that summary). A clean summary does not exit 2.
- In-loop evaluation error (greedy episodes only) with fail-fast on: `TrainingError` raised, `summary.json` has `stopped = "policy_error"`, `policy_errors > 0`, `weights_sha256 None`, no `weights.json`. `log.jsonl` last row has `eval_policy_errors > 0`.
- Same error with fail-fast off: the run continues, `stopped == "max_iters"`, and `summary.policy_errors` equals the sum of the row values (greater than 0).
- Empty batch: `_batch([])` and a batch of all-empty episodes return `None`; the QA-1 test passes.

## Acceptance criteria to evidence
| # | Criterion | Met | Evidence |
| --- | --- | --- | --- |
| 1 | Suite green | Yes | 1180 passed, 12 skipped, 2 xfailed (above) |
| 2 | Exported-policy error counted and fails the check | Yes | `test_one_late_error...`, `test_final_check_error_keeps_weights...`, tech-lead's two tests |
| 3 | Per-update eval errors in `log.jsonl` | Yes | `eval_policy_errors` in the row, `train.py` row dict; QA and TL tests |
| 4 | Empty batch with switch off does not crash | Yes | `_batch` returns None, `train` skips `ppo.update`; test passes unmarked |
| 5 | Doc statements correct | Yes | `RL_POLICY.md:123` (8x2x2 = 32), `:126-127` (`final_check` loops `range(len(env.COMBOS))`, 128 duels), `:125` (in-loop pairs 0 and 1: `_combo(k)` for k < `eval_episodes` = 8 covers combos 0 to 7 = pair 0 and 1), `:133` (H6-4 B slot: `((3,2,5,-1),(1,2,3,1))` at `tests/test_rl_fix1_starts.py:39`), `:156,:196` (#47 decided); `env.py` COMBOS comment says 32 |
| 6 | Smoke under 60 s, no full run | Yes | `tests/test_rl_train.py` smoke runs inside the suite; no full run |

## Findings
No blocker or major.
- Minor (F1, behaviour for Saad): under the tech-lead's reading of #47, a `final_check` error does not withhold the weights. `summary.stopped = "final_check_policy_error"` and exit 2 are the only signals; `weights.json` and its sha stay on disk. A script that only checks `weights.json` would ship a policy that fell back to WAIT. Reproduced by `test_final_check_error_keeps_weights_marks_summary_and_main_exits_2`. Saad confirms whether weights should be withheld.
- Minor (F2, behaviour for Saad): an eval-only error also stops the run under #47 (reading confirmed in code and test). In that path the per-update row is written and counted, but the snapshot pool update and the stop happen after the PPO update has trained on that rollout; the weights are not exported. Fine, but it is a reading, not a decision.
- Note (F3): `tests/test_eval_T07fix1.py::test_final_check_does_not_read_rival_error_counts` and `::test_in_loop_eval_errors_are_not_summed` are now false statements held green by the helper layout. Invert at Gate 2.
- Note (F4): `stopped == "max_iters"` is the normal-finish value, not `None`; any consumer testing `stopped is None` is wrong (my first draft made this mistake).

## Not checked
- A full or even a long training run (excluded by the brief).
- Multi-process worker behaviour with injected errors (my injections ran with `workers=1`; the multiprocess identity test is in the existing suite and passed).
- Playwright/browser build: not relevant to this change.

## Student decision required
None.

## Requested next action
Gate 2: invert the two probes in F3; confirm F1 and F2 with Saad.
Touches the knowledge boundary or AI seat: yes (AI rival training and error accounting; no observation, action or hidden-information change).
