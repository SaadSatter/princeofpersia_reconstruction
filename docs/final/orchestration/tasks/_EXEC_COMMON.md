# Common setup for execution tasks (native agents, from 2026-11-24)

This replaces the claude.ai sandbox setup of 2026-11-23/24 (bare repository at
`/home/claude/sm/dev.git`, one clone per worker). That version is in git
history at `87606b9`. Briefs written before this date still name it, and they
are historical records.

## Where a worker works

Each worker subagent runs in its **own temporary git worktree**, created by
Claude Code (`isolation: worktree` in its native definition). The worktree
shares the repository's objects, so every branch and commit is reachable.
It starts from the default branch, so make your branch first:

| Role | Branch | Command |
| --- | --- | --- |
| tech-lead | `task/<TASK-ID>` | `git switch -c task/<TASK-ID> <base-sha>` |
| qa | `gate/<TASK-ID>-qa` | `git switch -c gate/<TASK-ID>-qa <reviewed-sha>` |
| evaluation-specialist | `gate/<TASK-ID>-eval` | `git switch -c gate/<TASK-ID>-eval <reviewed-sha>` |
| requirements-auditor | `audit/<TASK-ID>` | `git switch -c audit/<TASK-ID> <base-sha>` |

Then check with `git rev-parse HEAD` and `pwd` (a path under
`.claude/worktrees/`). Never `cd` into the main checkout and never write there.
Saad's own uncommitted work lives in it.

Read files from the commits your prompt names, not from whatever the
worktree happens to hold:

```
git show <coordination-sha>:docs/final/orchestration/tasks/<TASK-ID>.md
git show <coordination-sha>:docs/final/orchestration/agents/<role>.md
git show <handoff-sha>:docs/final/orchestration/reports/<prev>.md
```

## Commits

- Commit only on your own branch, only inside your permitted write paths,
  and stage explicit paths (`git add <path>`).
- Your report goes in `docs/final/orchestration/reports/<TASK-ID>-<role>.md`
  on the same branch (`../HANDOFF_PROTOCOL.md`).
- Commit as the agent, so `git log` shows who did the work. (SMOKE-01 found
  worker commits authored as Saad, because the worktree inherits his git
  identity.) Use:
  ```
  git commit --author "Claude Sonnet 5.5 (<role> worker) <noreply@anthropic.com>" -m "..."
  ```
  and end the message with the trailer naming the **configured** model (the
  verified one goes in the review log):
  ```
  Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
  ```
- Never push, merge, rebase, force-push or delete a branch. The orchestrator
  reads your branch directly; the worktree's branch stays in the repository
  after the worktree is removed.

## Tests

`uv run pytest -q` (Saad's Mac: `uv` present). Where `uv` is missing:
`python3 -m pytest -q -p no:cacheprovider`. Say which one you used, and paste
the real result line.

Expect more skips in a worker worktree than in Saad's checkout. A fresh
worktree has no gitignored data (original Level 1, bundled images), and its
new `uv` environment has no pygame. Some tests are generated from local
files, so a worktree also *collects* fewer tests: on 2026-11-24 a worktree
collected 445 (SMOKE-01: 435 passed, 12 skipped) where the main checkout
collected 459 (459 passed, 1 skipped). Report skips as skips. Gate 3 re-runs the suite in the main
checkout or the integration worktree, and says which.

No network for tests, no API keys, no paid calls, and no training run
longer than 10 minutes without Saad's approval quoted in the brief.

## Decisions and plan in force

`docs/final/orchestration/DECISIONS-2026-11-23.md` (#1 to #25),
`PLAN-2026-11-23-v2.md`, `PLAN-2026-11-23-v3-delta.md`, and `STATUS.md`
("Waiting on Saad" lists what is still open).
