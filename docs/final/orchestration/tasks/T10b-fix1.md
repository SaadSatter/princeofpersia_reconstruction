# T10b-fix1: QA minors on the G2/G3 docs; keep main's orchestration records

- Assigned: tech-lead; then qa (Gate 1); Gate 3. Corrective attempt 1 of 2.
- Requested: decision #117 (T10b), findings `reports/T10b-qa.md`@fd68e66 on `gate/T10b-qa`.
- Base: `task/T10b` 6c96c90. Branch `task/T10b-fix1`.
- Permitted write paths: as `tasks/T10b.md`, plus `docs/final/ENGINE_DECISION.md`, `agent-config.json`, and `docs/final/orchestration/**` **only** to restore files to `origin/main` (step 1).
- Do:
  1. Merge `origin/main` into the branch. For every path under `docs/final/orchestration/` take `origin/main`'s copy (main's records are authoritative, decision #11/#29), except keep the T10b reports. After this step `git diff origin/main -- docs/final/orchestration` must list only `reports/T10b-*`.
  2. Fix QA F1 (GDD:37: CI fix is T29), F2 (telemetry-analyst already on main), F3 (#108 chose T27 option (b); only T26 tap size is open, #112), F4 (TRACKER: T29 closed at Gate 3, 2f3e493, reaches main with PR #12; T23 at T23-fix2 with Gate 1 ACCEPT 94ec401; T23 decisions include #113, #114; refresh any other row against main's STATUS and REVIEW_LOG), F5 (PROJECT_PLAN.md:97 and ENGINE_DECISION.md:33: G2/G3 is Sat 2026-11-28).
  3. `agent-config.json`: correct the stale "no weights" statement to the shipped run-1 weights (SHA-256 80e4a110…ba4c), nothing else.
- Acceptance: suite green (`uv run --frozen --extra play --extra train --extra online pytest -q`); diff vs `origin/main` limited to permitted paths.
