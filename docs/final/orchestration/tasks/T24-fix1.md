# T24-fix1: hang wins at a ledge edge (decision #101), and the R-V17 spec sentence (#98)

Handoff id: HO-T24-fix1-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3. Corrective attempt 1 of 2 for T24.
Read first: `tasks/T24.md`@b1514bc; `reports/T24-qa.md`@48176a5 (F1, F2); `reports/T24-evaluation-specialist.md`@d187e1c (findings 2 and 3, the recommended fix and wording); decisions #94, #98, #101.
Base: `gate/T24-eval` d187e1c. `git switch -c task/T24-fix1 d187e1c`.

1. **#101 (F1):** in `pop/versus.py`, `_kneel_target`'s uniform branch returns nothing when this `DOWN` would start a hang-down (the cell ahead is not blocked and not supported, the same test as `engine._down`), so `DOWN` hangs as before; `TAKE` still takes the uniform there. Failing test first. Update R-V17 in `docs/RULE_SOURCE_MAP.md` (cite #101).
2. **#98 (F2):** `docs/final/VERSUS_SPEC.md` R-V17: after a kneel picks up a sword, the sword is drawn, so the uniform needs SHEATHE then DOWN, or TAKE (Eval's suggested wording).
3. **Authorised test edit:** the third test in `tests/test_eval_T24_f1.py` (it pins the pre-#101 take at a ledge edge) changes only to "still hangs". List old and new. No other existing-test edit.

Permitted writes: `pop/versus.py` (the kneel path only), `docs/RULE_SOURCE_MAP.md` (R-V17), `docs/final/VERSUS_SPEC.md` (R-V17), the one test edit, new tests `tests/test_t24fix1_*.py`, `docs/agent-sessions/` (one new file), `docs/final/orchestration/reports/T24-fix1-tech-lead.md`. No training, no `--live`, no H6 run.
Suite on a clean committed tree; paste the real line. Gates: QA, Eval (re-run the before/after A/B: zero change expected), Gate 3.
