# Session 14 (T05) — Macro layer and scripted versus baseline

Number provisional (parallel wave-1 records); the index was not edited
(outside this task's write paths).

| Field | Value |
| --- | --- |
| Tool / role | Claude Code subagent, Tech Lead; brief `docs/final/orchestration/tasks/T05.md` |
| Session | Subagent of the orchestrator session `https://claude.ai/code/session_01DktSfuWQ416LWvPbT3AoAS`; own transcript id unknown |
| Date | 2026-11-23 |
| Branch / base | `task/T05` from `03856b9` (`int/wave1`) |
| Independence | Builder, not a review. QA and Evaluation gates not yet run |

## What happened

- Failing tests first (`tests/test_macros.py`, `tests/test_versus_baseline.py`), then `agents/macros.py` and `agents/versus_baseline.py`, then `docs/final/MACROS.md`.
- Bugs found by running the baseline on the default start: an empty plan treated as "unreachable"; a seat's own WAIT counted as moving; a target across a pit unreachable (fixed by letting jumps fly over bodies); test setups lost by the runner's reset (fixed with a test subclass).
- Not done: no `pop/` change, no rule-map row (no rule added), no PPO, no traps.
- Base had 5 failing tests in `tests/test_qa_t02_disguise_tells.py` before this task (written for the pending T01-fix1); unchanged here.
