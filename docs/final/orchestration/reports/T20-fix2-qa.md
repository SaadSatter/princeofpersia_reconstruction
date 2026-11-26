---
handoff_id: HO-T20-fix2-qa
task_id: T20-fix2
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T20-fix2-tech-lead.md@ed64a01
source_branch: gate/T20-fix2-qa
source_commit: see the commit that holds this file (git log -1 gate/T20-fix2-qa)
reviewed_commit: ed64a01d589632424372d798f0e669f7b260b9e6
verdict: ACCEPT
---

# T20-fix2: QA report (Gate 1)

Verdict: ACCEPT. No blocker, major or minor finding reproduced.

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q
2 failed, 1681 passed, 12 skipped, 4 xfailed, 2 warnings in 303.97s (0:05:03)
```
The 2 failures are the expected strict XPASS in `tests/test_eval_t20_probes.py`
(`test_a_running_jump_is_counted_as_a_flip`, `test_a_held_draw_key_is_one_use`). That file is untouched.
1681 = the Tech Lead's 1668 plus my 13 new tests. `tests/test_t20fix2_counts.py` + my file: 46 passed.

## Acceptance criteria -> evidence
| # | Criterion | Met | Evidence |
| --- | --- | --- | --- |
| 1 | Running, standing, hop-turned jump: flip == 1 | yes | Probed through the web Match: d x8 then d+w gives `{RIGHT, RUN_JUMP_RIGHT}` flip 1; standing flip 1; hop (d, gap, a+w) `JUMP_LEFT` flip 1; shift running jump 1; two separate jumps 2; held d+w 20 ticks (armed or not) 1 |
| 2 | `g` held 30 ticks: one use, rest `repeat` | yes | `test_held_draw_key_marks_every_later_toggle_repeat`: draw 1, sheathe 0, first row unmarked, all later `repeat` |
| 3 | `moves - repeats` reconciles; says where not | yes | `test_repeats_reconcile_for_a_held_draw`; Tech Lead's lunge/draw reconcile test; flip/block/events documented as non-reconciling (checked: flip and block map from names or action rows, not 1:1) |
| 4 | Item-4 table, test per mechanic | yes | Table rows checked against `tests/test_t20fix2_counts.py`: TAKE, RIG, flip, block, draw/sheathe, sword_pickup, lunge/throw/kick, sweep, disguise each have a one-press and held-20 case |
| 5 | Determinism, leak, client-message identity pass | yes | full suite: no failure other than the two Eval XPASS |
| 6 | Suite green except Eval XPASS, line pasted | yes | line above |

## Focus checks (exactly-once under realistic play)
Reproduced with my own scripts and the committed `tests/test_t20fix2_qa_probes.py`:
- Flip: run-up jump with d kept held afterwards = 1; two run-up jumps in a row = 2; hop-turn = 1; held w+d 20 ticks, armed and unarmed = 1 (later JUMP starts carry `repeat`). Run-up lengths 6 to 39 ticks: flip 1 whenever a jump started; the cases where no jump started (lengths 18, 21, 39) count 0, correctly, because no `move` row exists.
- Jump that bumps: standing jump into a wall (left wall) gives `JUMP_LEFT` with a bumped effect, flip 0. Documented limit stands: a run-up jump that bumps after starting cannot be told apart at its start and counts 1. I could not make the engine produce that case in these rooms.
- Holds: held `g` 30 ticks 1; held w+a / w+d 1 flip; held stance w or s 20 ticks block 1; w then s then w = block 3 (three presses); armed w+f held = throw 1, no extra block.
- New block count: counted from accepted `STANCE_*` action rows, `repeat` skipped; was 0 before. Verified 1 per hold, N per N changes.
- Old logs: schema-1 (accepted action, effect flipped) and an early schema-2 log (move row with no `effect`, stance rows with no `repeat`) summarize without error, counts as expected; committed fixtures (root and `v2/`) summarize with rc 0.

## Findings
None reproduced.

Unverified, minor, noted for Eval (not blocking):
- Tapping jump every other tick while running: the engine starts one jump and later taps are dropped, so flip 1. If Eval judges that repeated taps should count more than one, the recorder cannot tell. Observed, not a defect.
- Documented limit confirmed: DRAW then SHEATHE on separate presses with zero gap ticks reads as one hold.

## Scope
`git diff --name-only 5700c42..ed64a01`: `docs/agent-sessions/T20-fix2-telemetry-flip-hold.md`, the Tech Lead report, `docs/final/playtest/TELEMETRY.md`, `server/telemetry.py`, `tests/test_t20fix2_counts.py`, `tools/telemetry/summarize.py`. All permitted; no `pop/` change, no existing test edited. CI files not changed.

## Not checked
Browser/Playwright smoke (no browser change). Gate 2 measurement validity and removal of the Eval xfail marks are left to Eval.

## Requested next action
Gate 2 (Eval) on `gate/T20-fix2-qa`.
