# T18-fix1: one room's error never stops the server (decision #63)

Handoff id: HO-T18-fix1-orchestrator. Assigned: tech-lead; then qa (Gate 1), then evaluation-specialist (Gate 2: online server), then Gate 3.
Decision: #63, Saad: "let's add the server crash fix". Finding: EVAL-T18-1 in `reports/T18-evaluation-specialist.md`@f4dc475: an exception from one room's `on_finish` (for example `write_trace` on an unwritable `--trace-dir`) escapes `pump()`, ends `run_ticks`, and stops every room.
Base: `orch/reviewed` fc02687: `git switch -c task/T18-fix1 fc02687`. Suite there: `1380 passed, 12 skipped, 4 xfailed, 2 warnings`. T19 is in progress on its own branch; do not touch its paths.

## What to build

An error raised while finishing or recording one room's duel (`on_finish`, the trace write, `_record`) is caught at the room boundary, logged server-side with the room code and the exception (never sent to any client), and that room is handled as finished. Every other room, including HOME, keeps ticking. The tick loop never ends because of one room. No error text reaches a client.

## Permitted writes

`server/app.py`, `server/__main__.py` (only if the trace write needs it), new tests `tests/test_online_rooms_fix1*.py`, `docs/final/ONLINE_PLAY.md` (one sentence), `docs/agent-sessions/` (a new file), `docs/final/orchestration/reports/T18-fix1-tech-lead.md`. Do not edit existing tests: the strict xfail `tests/test_eval_t18_rooms.py` EVAL-T18-1 test will start to pass (XPASS fails the suite); report it, and its author (the Evaluation Specialist) removes the mark at Gate 2.

## Acceptance (failing test first)

1. An unwritable trace dir in room 1: room 1's error is logged, room 2 and HOME keep ticking and finish normally, and the server keeps running.
2. No client receives the exception text.
3. The suite is green except for the expected XPASS of EVAL-T18-1, with the real line pasted.

Gates: QA (`gate/T18-fix1-qa`), Eval (`gate/T18-fix1-eval`, removes its xfail mark), Gate 3.
