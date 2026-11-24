# Saad's decisions: 2026-11-24

Saad gave these in chat on Tue 2026-11-24, about 13:40 ET, after reading the
orchestration refactor report. His words are copied **verbatim**. Numbering
continues from `DECISIONS-2026-11-23.md`.

> "Push to github I agree with the smoke and origin main. You don't need approval for every push, for issues and PRs for handoffs you don't need approval. Allow to commit to main follow the new rules. Update the outdated docs."

| # | Topic | Saad's answer (verbatim excerpt) | Orchestrator's reading and effect |
|---|---|---|---|
| 26 | Publish the refactor | "Push to github I agree with the smoke and origin main" | Push `main` (including `inputs/FINAL_REQUIREMENTS.md`, which becomes public) and the SMOKE-01 branches `task/SMOKE-01` and `gate/SMOKE-01-qa` |
| 27 | Pushing | "You don't need approval for every push" | Standing approval: the orchestrator pushes branches without asking each time. Never force-push, never delete or rewrite a branch. Workers still do not push; the orchestrator does. `AGENTS.md` item 6 updated to match |
| 28 | GitHub handoffs | "for issues and PRs for handoffs you don't need approval" | The orchestrator opens issues and PRs, and posts reports as PR or issue comments, without asking (extends decision #14). **Merging** a PR is still Saad's |
| 29 | Committing to `main` | "Allow to commit to main follow the new rules" | The orchestrator commits to `main` under the new rules: orchestration records (`docs/final/orchestration/**`) directly; gameplay, engine, tests and other docs reach `main` only through a PR Saad merges |
| 30 | Outdated docs | "Update the outdated docs" | Task T10: bring `GDD.md`, `CONFIGURATION.md`, `REQUIREMENTS_CHECKLIST.md`, `PROJECT_PLAN.md` and `docs/final/README.md` in line with decisions #1 to #29, with dated "Changes since the last gate" sections and no rewritten history. It runs through the chain: Tech Lead, QA, Gate 3, then a PR |

## Addendum: Tue 2026-11-24, about 14:19 ET

Saad answered two questions put to him by the orchestrator session (AskUserQuestion) before T05-fix1 was dispatched again. His choices are quoted verbatim.

| # | Question (short) | Saad's answer (verbatim choice) | Orchestrator's reading and effect |
|---|---|---|---|
| 31 | CLIMB down (T05-fix1; was listed under "Waiting on Saad") | "CLIMB both ways (Recommended)" | `CLIMB` climbs up an edge, and also goes down safely: hang and drop, or a drop into a pit the engine lets you survive. `SEARCH` and `FLEE` may also use survivable drops. No new macro name (decision #23 stands). G1's "climb" is read as covering both directions. `MACROS.md` records it as confirmed by Saad, not pending |
| 32 | Parallel work alongside T05-fix1 | "T05-fix1 only (Recommended)" | Only one task chain runs at a time for now. T04-fix3 and GATE-wave3 wait until the T05-fix1 chain is finished |
