---
handoff_id: HO-T07-run1-tech-lead
task_id: T07-run1
date: 2026-11-24 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T07-run1.md@ef621a5
source_branch: task/T07-run1
source_commit: 21efc5d
reviewed_commit: n/a
verdict: n/a
---

# T07-run1: tech-lead report

Status: done

## Work completed
Copied the run-1 weights and evidence byte for byte (checked with `cmp` against the read-only
source folder and `shasum -a 256`). Added two constants to `agents/rl/policy.py`. Updated
`docs/final/RL_POLICY.md` (status, weights row, Results paragraph labelled "tuning starts, 128
duels, seat-swapped; not held-out", stale "Command (to run later)" line). The T07-fix1 QA N2
correction (`final_check` covers all 32 combos) was already correct on the base; no change.
Failing tests were committed first (all 6 failed), then the files made them pass.

## Paths
- `tests/test_rl_run1_shipped.py` (new, 6 tests, 0.1 s total)
- `agents/rl/weights/ppo-run-1.json` (new, SHA-256 80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c)
- `tools/rl/runs/run-1/{config.json,summary.json,log.jsonl,run-1.meta,run-1.stdout}` (new)
- `agents/rl/policy.py`: `SHIPPED_WEIGHTS` (Path to the file), `SHIPPED_SHA256`; nothing else
- `docs/final/RL_POLICY.md`, `docs/agent-sessions/T07-run1.md`

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Byte copies, hashes checked | yes | `cmp` ok on all 6 files; `shasum -a 256` of the copy = source = summary |
| 2 | Two constants in policy.py only | yes | diff is +4 lines |
| 3 | RL_POLICY.md status, row, Results, N2 | yes | N2 already correct |
| 4 | Tests: hash, load_net, format/sizes, summary agreement, deterministic duel with 0 fallbacks | yes | `tests/test_rl_run1_shipped.py` |
| 5 | New tests under 30 s | yes | 0.1 s |
| 6 | No change to encoder, tools/rl code, existing tests, play.py, web/, server/ | yes | scope check below |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
1336 passed, 12 skipped, 2 xfailed, 2 warnings in 284.82s (0:04:44)
```
(Base was 1330 passed; +6 new.) Scope: `git diff --name-only f08c1a8..HEAD` lists only the paths above, all permitted.

## Findings
No findings. Not checked: the summary's 120/8/0 result was copied, not rerun (Eval gate does that).

## Known limitations
The file is not wired into play.py, web or server (T19 follows). The determinism test uses a
WAIT opponent and 600 frames, so it checks the loader and runner path, not strength.

## Unresolved findings
None.

## Requested next action
QA (`gate/T07-run1-qa`): byte equality against the source folder, hash chain, and that the
tests fail without the files (they did on commit 1e09afe).

Commit to review: 21efc5d on task/T07-run1
What changed: the trained weights and run evidence are committed and named by two constants; docs state the results as tuning-start only.
How to check it: `uv run --frozen --extra play --extra train --extra online pytest -q tests/test_rl_run1_shipped.py`; `cmp` each file against `.../worktrees/train/tools/rl/logs/`.
What I am unsure about: nothing material. The hash constant is a literal in policy.py, duplicated in the tests by design.
Touches the knowledge boundary or AI seat: yes (ships AI rival weights; Gate 2 applies, already planned as `gate/T07-run1-eval`)

## Student decision required
None.
