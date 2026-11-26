# AUDIT-G23: G2/G3 readiness audit (read-only)

- Task id: AUDIT-G23
- Assigned agent: `requirements-auditor` (`agents/requirements-auditor.md`)
- Requested by: Saad, 2026-11-26: "I want to focus on getting this ready for saturday, make sure everything is done and ready for that"
- Deadline audited: G2/G3, Sat 2026-11-28, 11:59 p.m.
- Requirements: `inputs/FINAL_REQUIREMENTS.md` §6 "G2/G3" (all six lines) and every §2–§5 line labelled [R] that G2/G3 depends on; `COURSE_ROLE_MAP.md` "G2/G3".
- Base: `main` at this coordination commit, plus `orch/reviewed` dfe2d90 (the graded gameplay once PR #12 is merged; PR #6 T10a docs is also open and unmerged).
- Official repository: `columbia-university-ai-games/final-saadsatter`. Inspect read-only with `gh api` / `gh repo view` (template contents, `team/`, `.github/workflows/final.yml`, open issues incl. the Gate decisions issue, discussions if visible). Do not push, comment or open anything there.
- Permitted write paths: `docs/final/orchestration/reports/AUDIT-G23-requirements-auditor.md` only, on branch `audit/AUDIT-G23`.
- Gates: none (read-only audit). The orchestrator reads the report.

## Deliver
1. A table: each G2/G3 requirement → PASS / PARTIAL / MISSING / BLOCKED / N/A, the evidence (commit, path, PR, test line), and what is left.
2. For each gap: **who** can close it (Saad only — e.g. recording, playtest, Student decision, coverage-map calls, discussion post; or an agent under a brief), the smallest concrete step, and dependencies between steps (e.g. T03 migration must follow PR #6 and PR #12 merges).
3. A concrete plan for T03 (official-repository move, decision #6): what must be copied, what template files must be preserved, `python -m team init` and `render` steps, where the T02 handoff draft and `other-roles.md` go, README/tracker links required, and the old course-repository PR to close. Name risks (private assets on the course branch, original-asset rules in `AGENTS.md`, CI in `final.yml`).
4. Status of: deterministic CI (does CI run and pass on `main`?), "live evaluation evidence appropriate to gate" for a PPO rival (decision #3), scope lock and dated "Changes since the last gate" in GDD/configuration, the T10b follow-ups listed in `STATUS.md`, and the session-record numbering clash noted in `STATUS.md`.
5. An ordered checklist for the next 48 hours.

Never claim something passed without a citation you checked in this session.
