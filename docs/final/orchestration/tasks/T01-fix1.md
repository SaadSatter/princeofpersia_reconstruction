# T01-fix1: corrective work after the T01 gates
Assigned agent: `agents/tech-lead.md`
Setup: `_EXEC_COMMON.md`. Base: `83127cf` (task/T01): `git clone -q /home/claude/sm/wt/T01 /home/claude/sm/wt/T01-fix1 && cd /home/claude/sm/wt/T01-fix1 && git checkout -q -b task/T01-fix1 83127cf`.
Inputs: `/home/claude/sm/orch/reports/GATE-T01-qa.md`, `/home/claude/sm/orch/reports/GATE-T01-eval.md`, `/home/claude/sm/orch/DECISIONS-2026-11-23.md` (#15: "TAKE always legal").
Gate tests: copy `git -C /home/claude/sm/wt/GATE-T01-qa show gate/T01-qa:tests/test_gate_t01_qa_disguise.py` and `git -C /home/claude/sm/wt/GATE-T01-eval show gate/T01-eval:tests/test_gate_t01_eval_boundary.py` into your branch unchanged, except that you remove the xfail mark of each finding you fix. Say exactly which marks you removed.
Fix:
1. **L1 (decision 15):** TAKE is legal over any downed guard in front, whether or not its uniform remains. If the uniform is gone, the input is accepted, plays the TAKE animation or no-op the same way, changes nothing else, and reports a `last_result` effect the acting seat can see (for example `no_uniform`). Add a new rule row R-V26 (`design`, Saad 2026-11-23, with rationale and the alternative rejected: "show taken uniforms"). The other seat must not learn anything from it beyond what is on screen.
2. **L2:** same-cell figure order must not depend on rival or guard; sort on every observed field.
3. **QA1:** a disguised step into the next room must not show `motion.to: null` to an observer, if this can be masked under R-V25 without hiding the arrival. Otherwise leave it xfail and explain why.
Leave as xfail, as design questions for Saad: QA2 (postures), QA3 (repeated WAIT and lingering), and anything about R-V24's amount.
Permitted write paths: `pop/versus.py`, the two gate test files, new `tests/test_t01fix1_*.py`, new rows in `docs/RULE_SOURCE_MAP.md`, `docs/final/VERSUS_SPEC.md` (R-V26 row, and the §2.2 outcome keys added by T01), `docs/agent-sessions/` (append to the T01 record).
Acceptance: failing tests first; full suite green; frozen suite unchanged; report the result line; Handoff to QA block.
