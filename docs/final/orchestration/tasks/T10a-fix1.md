# T10a-fix1: correct the T10a docs per QA Gate 1 findings F1–F3
Handoff id: HO-T10a-fix1-orchestrator
Assigned agent: `tech-lead` (procedure: `agents/tech-lead.md`). Setup: `tasks/_EXEC_COMMON.md`.
Why: Gate 1 on T10a (`reports/T10a-qa.md` @ a6df4f4, branch `gate/T10a-qa`) gave ACCEPT WITH NOTES. F1 leaves a false statement in the GDD, so the orchestrator returns F1–F3 before the PR rather than merging known-wrong text. This is the first corrective attempt (of at most two).
Consume first: `docs/final/orchestration/reports/T10a-qa.md` at a6df4f4.
Base: `task/T10a` at 7faccc0. Branch: `task/T10a-fix1`. The fix stacks on T10a, and one PR will carry both.
Permitted write paths: `docs/final/GDD.md`, `docs/final/CONFIGURATION.md`, your report. Nothing else. In particular, not `RL_POLICY.md`: it is on `orch/preview`, outside scope, and is flagged for T07 in your report.
Acceptance criteria:
1. F1: GDD Sections 6 and 7 carry a one-line `[Superseded …]` marker citing decisions #1 and #12, with the G1 text kept. The hosted-build fact is stated: the engine runs in the browser through Pyodide, so devtools can read hidden state, which is acceptable for human vs AI but not for online human vs human (`PLAN-2026-11-23-v3-delta.md`, "Known limitation"). The GDD "Changes since the last gate" Platform row says the same. Mark the stale Section 4 "Planned" labels only where `STATUS.md` shows the work exists, and say on which branch.
2. F2: CONFIGURATION A0 says the seat's own state is 18 features, matching `agents/rl/encoder.py` on `orch/preview`, and the groups sum to 251. Your report flags the 19 in `RL_POLICY.md` as a T07 follow-up.
3. F3: the GDD Session row keeps the G1 phrase with a marker, next to the new value (5 minutes, decision #5).
4. Nothing else changes. `git diff --name-only 7faccc0..HEAD` shows only the permitted paths.
Required tests: `uv run pytest -q` (unchanged), the link check on the two files.
Required gates: Gate 1 QA (re-check F1–F3 only, plus a regression scan of the diff). Gate 2 not required. Gate 3 orchestrator.
