---
handoff_id: HO-T07-run1-qa
task_id: T07-run1
date: 2026-11-24 ET
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
consumed: docs/final/orchestration/reports/T07-run1-tech-lead.md@8c1a3af
source_branch: task/T07-run1
source_commit: 8c1a3af (tests 1e09afe, work 21efc5d, base f08c1a8)
verdict: ACCEPT
---

# T07-run1: QA report (Gate 1)

Verdict: **ACCEPT**. No findings above cosmetic; two notes below.

## Acceptance criteria
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Byte copies of weights and evidence | met | `cmp` of ppo-run-1.json vs source `run-1/weights.json`, and of config.json, summary.json, log.jsonl, run-1.meta, run-1.stdout vs the source folder: all identical. Source folder untouched (read only). |
| 2 | Hash chain file / constant / summary | met | `shasum -a 256` of source and copy = 80e4a110...5aba4c = `SHIPPED_SHA256` = `summary.json` `weights_sha256`. |
| 3 | policy.py: two constants only | met | `git diff f08c1a8 8c1a3af -- agents/rl/policy.py` is +4 lines (comment, two constants, spacing). |
| 4 | Tests fail without the files | met | Removing the weights file: 4 failed, 2 passed. Removing `tools/rl/runs/run-1/`: 2 failed, 4 passed. Files restored by `git checkout`; tree clean. (Constants-absent case fails by AttributeError on the base.) |
| 5 | Scope | met | `git diff --name-only f08c1a8..8c1a3af` = policy.py, the weights, `tools/rl/runs/run-1/*` (5 files), RL_POLICY.md, `docs/agent-sessions/T07-run1.md`, the TL report, `tests/test_rl_run1_shipped.py`. All permitted. No encoder, tools/rl code, existing test, play.py, web, server change. |
| 6 | RL_POLICY.md labels | met | Results paragraph says "tuning starts, 128 duels, seat-swapped; not held-out"; numbers (1568 updates, 25,088 episodes, 1,487,955 steps, 4812.6 s, 120/8/0) match summary.json. |
| 7 | Full suite | met | `uv run --frozen --extra play --extra train --extra online pytest -q` on gate/T07-run1-qa (adds my 3 probes): `1339 passed, 12 skipped, 2 xfailed, 2 warnings in 254.98s (0:04:14)`. TL's line on 8c1a3af: 1336 passed; difference is my 3 probes. |

## My probes
`tests/test_qa_T07run1_probe.py` (3 tests, 0.05 s, all pass): all weights finite and numerous; log steps strictly increasing; summary commit appears in run-1.meta; wall >= 4800 and `stopped: time_cap`; constant equals SHA-256 of the file bytes; no duplicate `weights.json` in the evidence folder; stdout non-empty.

## Findings
- N1 (cosmetic) `docs/final/RL_POLICY.md` "Command as first written" line keeps `--out tools/rl/logs/run-0 --seconds 5100`, while run 1 used seed 0, 4,800 s, `logs/run-1`. The prose says so, so it is accurate but easy to misread.
- N2 (note, for Eval and Saad, not a defect) `run-1.stderr` (empty) is not committed; the brief did not list it. The 120/8/0 is a tuning-start smoke check copied from summary.json; I did not rerun it (Eval's job). Win rate is on trained-on starts only, not a strength claim.

## Not checked
No rerun of the final check, no training, no `--live`, no H6.

Requested next action: Evaluation Specialist (`gate/T07-run1-eval`).
