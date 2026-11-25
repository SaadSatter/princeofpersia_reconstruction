# T10a-fix2: correct the GDD Section 4 status labels (QA N1, N2). Last corrective attempt
Handoff id: HO-T10a-fix2-orchestrator
Assigned agent: `tech-lead` (procedure: `agents/tech-lead.md`). Setup: `tasks/_EXEC_COMMON.md`.
Why: Gate 1 on T10a-fix1 (`reports/T10a-fix1-qa.md` @ 2d88e03, branch `gate/T10a-fix1-qa`) gave ACCEPT WITH NOTES. F1–F3 are fixed, but the new Section 4 labels say disguise and the lingering rule are not on `main`. They are, so N1 and N2 are new minor findings. The root cause was the orchestrator's `STATUS.md`, which did not list what `main` contains. That is now fixed in `STATUS.md` ("What `main` already contains") at the coordination commit. **This is attempt 2 of 2.** If it fails, the orchestrator escalates to Saad.
Consume first: `docs/final/orchestration/reports/T10a-fix1-qa.md` at 2d88e03.
Base: `task/T10a-fix1` at 5379d62. Branch: `task/T10a-fix2`.
Permitted write paths: `docs/final/GDD.md`, your report.
Expected result (verify each against `main` before writing; do not copy blindly):
1. GDD Section 4 **Act**: movement [Implemented]; take a uniform / disguise [Implemented on `main`; the T01 fixes (R-V24 hop, R-V25, R-V26) on `orch/reviewed`]; sword [Implemented on `main`]; rig a trap [Planned; loose floor on `orch/preview`].
2. **Respond**: guard rule [Implemented on `main` (`pop/guards.py`, R-V19 `LINGER_AFTER`); the WAIT-lingering fix on `orch/reviewed`]; traps as in 1; loose floors and gates [Implemented as level hazards] (unchanged).
3. **Interpret**: HUD [Implemented on `main` in the pygame frontend (hearts in `render/draw.py`, suspicion eye/bar and DISGUISED marker in `play.py`); the browser HUD is on `orch/preview`].
4. Any other row in Sections 4, 5.2 or 5.3 whose `[Planned]` label contradicts the `STATUS.md` list: fix it the same way, and name each one in your report.
5. Nothing else changes. `git diff --name-only 5379d62..HEAD` shows only `docs/final/GDD.md` and the report.
Required tests: `uv run pytest -q`; link check on GDD.md.
Required gates: Gate 1 QA (N1, N2 and the rows changed under 4). Gate 2 not required. Gate 3 orchestrator.
