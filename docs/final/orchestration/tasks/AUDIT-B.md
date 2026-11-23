# AUDIT-B: Independent verification, tests and CI (read-only)
Assigned agent: `agents/qa.md` (audit mode)
Setup: `tasks/_AUDIT_COMMON.md`
Requirements: FINAL_REQUIREMENTS §2 CI [R], §5 deterministic tests [R]/[+], AGENTS.md "Checks".
Permitted write paths: none (scratch checkouts under /home/claude/sm/wt/AUDIT-B only).

Determine:
1. Test results on `final/versus-engine` (13c7488), `main`, and any branch with a different tests tree: pass/fail/skip counts; list each skip with its reason.
2. Determinism: run the suite twice on versus-engine; check that same seed + same actions gives identical traces for two-seat play (find or describe the test).
3. Coverage against the required categories, for the **versus** game (not the midterm single-player engine): rule/state invariants; valid path to a terminal outcome (win, draw, time limit); invalid/malformed action rejection with no state change and counting, for both seats; observed-regression tests; combat, disguise, guards, traps; both seats; observation isolation (disguise identity, trap ownership, other rooms, ids/ordering/counts); deterministic replay; per-seat step / model-call / timeout limits and fallback. Mark each present (test name), weak (would pass with the feature removed — explain), or missing.
4. Known regressions or open findings: read `docs/reviews/`, `docs/audits/` (latest first) and check whether each finding is fixed (test name/commit) or still open.
5. CI readiness: `.github/workflows/ci.yml`, `ci/midterm-saadsatter.yml`, official repo `/home/claude/final-saadsatter/.github/workflows/final.yml` — what each runs; what has to change so the official repo runs the game tests on every PR plus `team validate`/`render`; whether "passing checks required to merge" (branch protection) can be verified here (likely not).
6. Integration risks QA would want tested before and after merging branches.
Propose missing tests (name + one-line behaviour), do not write them.
