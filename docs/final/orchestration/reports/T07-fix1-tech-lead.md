---
handoff_id: HO-T07-fix1-tech-lead
task_id: T07-fix1
date: 2026-11-24
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T07-fix1.md@e51dd12
source_branch: task/T07-fix1
source_commit: fa0c840
reviewed_commit: n/a
verdict: n/a
---

# T07-fix1: tech-lead report

Status: done

## Work completed
Failing tests first (commit before the fix), then the six brief items. Parity test now gathers over 6 seeds with a fresh Encoder per duel (#42). Policy and encoder errors are counted, logged, written to `summary.json`, and stop the training run (proposed). Six tuning starts added (#44), disjoint from the held-out lists. `RL_POLICY.md` states #43 and the starts. Session record renumbered 11 to 16. No full training run, no push.

## Paths
- `agents/rl/policy.py`: `make_rl_rival` exposes `policy_macro` and `policy_errors()` on the controller.
- `tools/rl/env.py`: 8 `TUNING_STARTS`; `TrainPolicy.errors` (try/except around `choose`, answers WAIT); `play_episode` returns `policy_errors` (learner plus a snapshot opponent's `PolicyMacro.errors`); empty-episode arrays no longer crash.
- `tools/rl/train.py`: `TrainingError`, `TrainConfig.fail_on_policy_error` (default True), `policy_errors` in every log row and in `summary.json`, exit status 2 with a stderr message from `main()`.
- `tests/test_rl_policy.py`: `_record` edit (#42). `tests/test_rl_train.py`: the "only two starts" test now expects 8 (the midterm two first); this was forced by #44 and is inside `tests/test_rl_*.py`. New: `tests/test_rl_fix1_errors.py` (5), `tests/test_rl_fix1_starts.py` (5).
- `docs/final/RL_POLICY.md`; `docs/agent-sessions/16-t07-ppo-rival.md` (renamed with `git mv`; no links to the old name existed), `docs/agent-sessions/17-T07-fix1-ppo-corrections.md`.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Parity over at least 200 observations, several seeds | Met | `test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations` passes, asserts `n >= 200`, 1e-9 kept |
| 2 | Injected error counted, in log.jsonl, summary.json, smoke; stops run | Met | `tests/test_rl_fix1_errors.py`: episode count, log row, summary (`stopped: policy_error`, `weights_sha256: null`), CLI exit non-zero, clean run shows 0 |
| 3 | About 8 starts incl. lower floors, disjointness test | Met | `tests/test_rl_fix1_starts.py`; pairs 3 to 8 reach rooms 4, 5, 6 |
| 4 | RL_POLICY.md states #43, the starts, labelled numbers | Met | sections "Actions", "Held-out starts and tuning starts", "Speed (estimate...)" |
| 5 | Smoke run under 60 s, deterministic | Met | `test_smoke_training_...` and `test_training_is_reproducible_...` pass |
| 6 | Full suite | Met | below |
| 7 | No full training run | Met | not started |

## Tests run
```
uv run --frozen --extra play --extra train pytest -q
1120 passed, 11 skipped, 2 xfailed in 163.15s (0:02:43)
```
Scope: `git diff --name-only ae90c8c..fa0c840` lists only agents/rl, tools/rl, tests/test_rl_*.py, RL_POLICY.md, docs/agent-sessions (the report is added in the next commit).

## Findings
- [note for T08] The existing midterm tuning start `(1, 2, 3, +1)` equals the A cell of candidate H6-4 (`25e4587`). My new starts avoid all held-out and candidate H6 cells. The H6 cells are written into the test as facts; T08 must re-check against the frozen H6.
- [note] Per-update evaluation and `final_check` use `_combo(k)` for k < 8, i.e. only the two midterm starts, so the new starts are trained on but not evaluated in the loop.
- [note] In-loop errors from the baseline opponent are not counted (it is not a PolicyMacro); runner fallbacks of the learner stay in `fallbacks`.
- Not run: the full training run, any browser, any live call.

## Known limitations
Disjointness is by cell (room, row, col) ignoring facing, stricter than pair-level. Eight starts are still few; expect some over-fitting.

## Unresolved findings
None of mine. E2 (H6 freeze) and E5 to E9 are T08 or later, as the brief says.

## Requested next action
Commit to review: fa0c840 on task/T07-fix1 (plus the report commit above it)
What changed: parity test fixed; training errors are visible and fatal; 8 tuning starts; docs and session numbering corrected.
How to check it: `uv run --frozen --extra play --extra train pytest -q tests/test_rl_*.py`; to see the failure path, run `tests/test_rl_fix1_errors.py`; read `RL_POLICY.md` "Held-out starts and tuning starts".
What I am unsure about: whether the stop-on-first-error should skip the whole update (it does: the errored rollout is not trained on); whether the 6 hand-picked starts are balanced enough (not tested for balance); the edit to `tests/test_rl_train.py` (covered by #44 and the brief's path list, but it is an existing test).
Touches the knowledge boundary or AI seat: yes (Gate 2 applies): training starts and the AI seat's error accounting.

## Student decision required
For Saad: approve or reject the **proposed** rule that the full training run stops with a non-zero exit on the first policy or encoder error (`fail_on_policy_error`, default on).
