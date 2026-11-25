# GATE-T04: independent review of T04 (seat controllers and versus runner)
Gate 1 reviewer: `agents/qa.md`. Gate 2 reviewer: `agents/evaluation-specialist.md`. They are run as two separate subagents; neither sees the other's report.
Commit under review: `af76c30` on branch `task/T04`. Get it with `git clone -q /home/claude/sm/wt/T04 /home/claude/sm/wt/<your-gate-id> && git -C ... checkout -q af76c30`, and leave /home/claude/sm/wt/T04 itself untouched.
Inputs: `docs/final/orchestration/tasks/T04.md` (brief and acceptance criteria), `docs/final/orchestration/reports/T04-tech-lead.md` (implementer report and handoff), `docs/final/VERSUS_RUNNER.md`.
Permitted write paths: new tests only, as `tests/test_gate_t04_<qa|eval>_*.py`, committed on a branch `gate/T04-<qa|eval>` in your own clone. A new test that fails against af76c30 is a finding (mark it `xfail(strict=True, reason="GATE-T04-<id>")`).

QA focus: every acceptance criterion in T04.md, tested adversarially (controllers that keep references, raise in reset, return non-strings, decision_every=1, swap_seats with limits, a real won duel and the winner mapping, aborted runs and replay).
Evaluation Specialist focus: knowledge boundary (what a controller can reach: copies, the derived seed, legal-list hashing, trace contents, exception text), baseline fairness readiness (both seats on identical terms, simultaneous decisions), fallback and limit semantics for evaluation, determinism and replay fidelity, suitability for PPO training (speed: decisions per second with RandomController in both seats) and for seat-swapped comparisons.
Return the verdict block from your role file.
