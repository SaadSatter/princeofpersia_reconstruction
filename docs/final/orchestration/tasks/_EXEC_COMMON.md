# Common setup for execution tasks (from 2026-11-24)

| What | Path |
| --- | --- |
| Development repo, bare, synced from Saad's local `main` by the orchestrator | `/home/claude/sm/dev.git` |
| Your worktree (create it; never share one) | `/home/claude/sm/wt/<TASK-ID>` |
| Orchestration files (also in the repo at `docs/final/orchestration/`) | in your clone |
| FINAL_REQUIREMENTS copy | `/home/claude/sm/inputs/FINAL_REQUIREMENTS.md` |

```
git clone -q /home/claude/sm/dev.git /home/claude/sm/wt/<TASK-ID>
cd /home/claude/sm/wt/<TASK-ID>
git checkout -q -b task/<TASK-ID> <base sha from the brief or your prompt>
git config user.name "Claude (<role> subagent)"; git config user.email "noreply@anthropic.com"
```

- Commit only on your `task/<TASK-ID>` branch, only inside your permitted write paths. Never push to `dev.git`; the orchestrator fetches your branch from your clone.
- Every commit message ends with the trailer below, naming the model you actually run on (for example `Claude Sonnet 5.5` for a Sonnet subagent):
  ```
  Co-Authored-By: Claude <your model> <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01DktSfuWQ416LWvPbT3AoAS
  ```
- Tests: `python3 -m pytest -q -p no:cacheprovider` (sandbox: Python 3.13, pytest 9.1, numpy present, pygame/anthropic absent). Paste the real result line.
- No network, no API keys, no paid calls.
- Saad's decisions in force: `docs/final/orchestration/DECISIONS-2026-11-23.md`. Plan: `PLAN-2026-11-23-v2.md`.
