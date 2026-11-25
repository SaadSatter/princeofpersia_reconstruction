# T07-fix1: PPO stack corrections before the full training run

Handoff id: HO-T07-fix1-orchestrator
Assigned agent: tech-lead (`agents/tech-lead.md`); then qa, then evaluation-specialist
Why: GATE-wave3 rejected T07 at Gate 1 (T07-QA-1), and Gate 2 listed must-fix items before training. This is **corrective attempt 1 of 2**; a second rejected fix escalates to Saad.
Findings: `docs/final/orchestration/reports/GATE-wave3-qa.md` @ e50a846 (`gate/wave3-qa`, T07 block); `docs/final/orchestration/reports/GATE-wave3-evaluation-specialist.md` @ f02314b (`gate/wave3-eval`, T07 block). Original brief: `tasks/T07.md`. Implementer summary: `reports/wave2-batch.md` (T07).
Decisions in force (`DECISIONS-2026-11-24.md`): #42 "Allow the fix (Recommended)"; #43 "Train without traps"; #44 "Add tuning starts (Recommended)"; #34/#40 (numpy is the `train` extra). Also #3 (PPO rival), #23 (vocabulary), #24 (runner policy).
Setup: `tasks/_EXEC_COMMON.md`.

## Base

`ae90c8c` (`int/T13-base`, the preview line): `git switch -c task/T07-fix1 ae90c8c`. Run with `uv run --frozen --extra play --extra train pytest -q`. On this base the one failure is the T07-QA-1 test you fix.

## Fix

1. **T07-QA-1 (#42).** In `tests/test_rl_policy.py`, `_record` must gather its observations over several seeds (QA found that 6 give more than 200), with a fresh `Encoder` for each duel. Keep the assertion and the 1e-9 tolerance. QA's `tests/test_gate_w3_qa_T07_rl.py::test_parity_holds_over_200_observations_collected_across_several_seeds` (on `gate/wave3-qa`) shows the approach. Do not weaken the test.
2. **T07-E4 (errors must be visible).**
   - `PolicyMacro.errors` and any exception in `TrainPolicy.choose` must reach the runner's fallback accounting, or be counted in a field that `tools/rl/train.py` writes to `log.jsonl` and `summary.json` and the smoke test asserts.
   - **Proposed** (flag it for Saad in your report): the full training run stops with a non-zero exit and a clear message on the first policy or encoder error, rather than training on silent WAITs.
   - Add tests: inject an encoder error, and check that it is counted and visible and that the run fails loudly.
3. **T07-E1 (#43).** Keep `RIG_TRAP` reserved and masked. In `docs/final/RL_POLICY.md`, state plainly that the PPO rival does not set traps in G2/G3, and that traps are human-only, by Saad's decision #43.
4. **T07-E3 (#44).**
   - Add about 6 tuning starts to `tools/rl/env.py` `TUNING_STARTS`, including lower-floor rooms.
   - Each start must be **disjoint** from:
     - every held-out list on the base: `LOWER_HELD_OUT_STARTS` and the held-out starts in `tests/test_versus_baseline.py`;
     - the candidate H6 in the unreviewed WIP `orch/wip-T08` @ 25e4587 (`evaluation/heldout/H6.json`). Read it with `git show 25e4587:evaluation/heldout/H6.json`; do not copy it into your branch.
   - Add a test that checks disjointness from the lists on your base.
   - Record the new starts and how you picked them in `RL_POLICY.md`, before any training.
5. **Session record.** `docs/agent-sessions/11-t07-ppo-rival.md` shares number 11 with `11-free-dungeon-art-download.md`. Rename it to the next free number with `git mv`, and fix any links to it inside your permitted paths.
6. **Stale numbers.** Update the speed estimate in `RL_POLICY.md` (Gate 2 measured 8 untrained duels in 2.7 s on an Apple M4). Label it as an estimate.

Not in scope (T08 or later): the nearest-target confound for I3/F5, E5–E9, freezing H6.

## Permitted write paths

`agents/rl/**`, `tools/rl/**`, `tests/test_rl_*.py` (including the `_record` edit under #42), new tests `tests/test_rl_fix1_*.py`, `docs/final/RL_POLICY.md`, `docs/agent-sessions/` (the rename and a new record), `docs/final/orchestration/reports/T07-fix1-tech-lead.md`. **Not** `agents/macros.py`, `agents/versus_baseline.py`, `pop/`, `evaluation/`, or other existing tests.

## Acceptance criteria (failing tests first)

1. The parity test passes with at least 200 observations from several seeds.
2. An injected policy or encoder error is counted, appears in `log.jsonl`, `summary.json` and the smoke output, and (as proposed) stops a training run.
3. `TUNING_STARTS` has about 8 starts, including lower floors, with a passing disjointness test.
4. `RL_POLICY.md` states #43 and the new starts, and its numbers are labelled measured or estimate.
5. The smoke training run (under 60 s) still passes and is deterministic.
6. Suite: `uv run --frozen --extra play --extra train pytest -q` passes, and the result line is pasted.
7. **No full training run** (Saad's go-ahead is still needed).

## Gates

Gate 1 `qa` (`gate/T07-fix1-qa`); Gate 2 `evaluation-specialist` (`gate/T07-fix1-eval`); then Gate 3.
