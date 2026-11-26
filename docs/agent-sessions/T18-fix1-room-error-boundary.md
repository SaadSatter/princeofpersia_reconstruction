# Session: T18-fix1, one room's error never stops the server

Tech Lead (Sonnet 5.5), 2026-11-24, base orch/reviewed fc02687, decision #63, finding EVAL-T18-1.

- Wrote `tests/test_online_rooms_fix1.py` first; it failed with the trace-dir `NotADirectoryError` escaping `pump()`.
- `server/app.py`: `pump()` catches an exception from one room's `advance` (which includes `on_finish`/`_record`), logs it with the room code through the `server` logger (traceback server-side only), marks that room ended, and carries on with the other rooms and HOME.
- `ONLINE_PLAY.md`: one sentence.
- Expected side effect: the strict xfail in `tests/test_eval_t18_rooms.py` now XPASSes; the Evaluation Specialist removes the mark at Gate 2.
- Tests need `uv run --extra online --extra train pytest -q` (websockets, numpy).
