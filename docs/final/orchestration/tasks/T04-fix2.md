# T04-fix2: second correction round on the versus runner
Assigned agent: `agents/tech-lead.md`. Base: `616ba8d` on task/T04-fix1: `git clone -q /home/claude/sm/wt/T04-fix1 /home/claude/sm/wt/T04-fix2 && cd ... && git checkout -q -b task/T04-fix2 616ba8d`.
Findings (GATE-T04-fix1 QA and Eval, both ACCEPT WITH NOTES; reports summarised in /home/claude/sm/orch/reports/GATE-T04-fix1.md):
1. [major] An answer whose `__class__` property returns `str` passes `isinstance`. Then `str.__str__(value)` raises TypeError in `_decide` (pop/versus_runner.py:107, 258), and the whole run crashes. Fix: check `type(value) is str` or a str subclass via `type()`, and guard normalisation so any failure is a `malformed` fallback.
2. [major] Busy tracking is per runner instance. Two runners sharing a controller can call it concurrently (the seat-swapped pair). Track busy on the controller itself (an attribute or a module-level weak map), so it holds across runner instances.
3. [minor] `decision_every` accepts 1.5 and True. Accept only int ≥ 1, not bool.
4. [note] VERSUS_RUNNER.md must state explicitly that:
   - traces from real-timeout runs are not reproducible (replay still is);
   - a controller still busy at the next run is not reset (`reset_error: "busy"`), so evaluation must treat that trial as invalid or use fresh controllers;
   - inline mode has no real-time bound.
Gate tests: copy `tests/test_gate_t04fix1_qa_probes.py` from `git -C /home/claude/sm/wt/GATE-T04-fix1-qa show gate/T04-fix1-qa:...` and `tests/test_gate_t04fix1_eval_probes.py` from `git -C /home/claude/sm/wt/GATE-T04-fix1-eval show gate/T04-fix1-eval:...`. Remove the xfail marks only for the findings you fix; say which.
Permitted writes: `pop/versus_runner.py`, `pop/seats.py`, `tests/test_versus_runner.py`, the copied gate files, `docs/final/VERSUS_RUNNER.md`, `docs/agent-sessions/13-T04-versus-runner.md`.
Acceptance: failing tests first; full suite green; report the result line; Handoff to QA block.
