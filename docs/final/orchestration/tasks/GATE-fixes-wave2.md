# GATE-fixes-wave2: re-review of T01-fix1 + T01-fix2 and T04-fix2 on the integrated branch
Gate 1: `agents/qa.md`. Gate 2: `agents/evaluation-specialist.md`. These are separate subagents.
Commit: `cd5c4aa` on `int/wave2` (integrates T01, T04-fix1, T11-fix1, T02, T02-close, T01-fix2 [contains T01-fix1 dc43978 + a76b3a7], T04-fix2 0f73e82): `git clone -q /home/claude/sm/wt/INT /home/claude/sm/wt/<gate-id> && cd ... && git checkout -q cd5c4aa`. The orchestrator measured `775 passed, 12 skipped, 3 xfailed`.
Inputs: `/home/claude/sm/orch/tasks/T01-fix1.md`, `T01-fix2.md`, `T04-fix2.md`; `/home/claude/sm/orch/reports/GATE-T01-qa.md`, `GATE-T01-eval.md`, `GATE-T04-fix1.md`; DECISIONS #15, #17–#21, #24.
Check:
1. T01-fix1 and fix2:
   - **L1 / R-V26:** TAKE is legal over any downed guard and is a no-op without a uniform. The other seat's view is identical either way.
   - **L2:** figure order.
   - **QA1:** the next-room step is masked.
   - **QA3:** lingering with repeated WAIT.
   - **Stale test:** only that one assertion changed.
   - The fuzz hash change is explained only by R-V26 and QA3.
   - Re-run your exhaustive disguise probe (QA) or boundary probe (Eval).
2. T04-fix2:
   - The `__class__` spoof is handled.
   - Busy is shared across runner instances.
   - `decision_every` type is checked.
   - Docs.
   - **The implementer edited one Eval probe** (`test_busy_state_is_per_runner_instance` → `test_busy_state_is_shared_across_runner_instances`, `max_active == 1`). Eval: confirm or reject that edit of your test.
3. No regression in the integrated branch.
Permitted writes: new tests `tests/test_gate_w2_<qa|eval>_*.py` on `gate/w2-<qa|eval>` (failing ones xfail strict).
Return the verdict block per change (T01-fix1/2, T04-fix2). Be concise.
