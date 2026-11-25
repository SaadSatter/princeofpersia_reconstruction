# T20-fix2 session (tech-lead worker)

Base `5700c42` (`gate/T20-fix1-eval`), branch `task/T20-fix2`. Corrective attempt 2 of 2 for
T20, from Eval E2, E3 and the `moves` note.

Order: probe each summary mechanic through the real engine and recorder, then fix. Writes only in
`server/telemetry.py`, `tools/telemetry/summarize.py`, `docs/final/playtest/TELEMETRY.md` and the
new `tests/test_t20fix2_counts.py`. No `pop/` change, no existing test edited.

- E2: `flip` is one per started `JUMP_*`, `RUN_JUMP_*` or `_HOP_FLIP_*` move (the engine's own
  `started_move` name), or any start whose effect is `flipped`; a bumped standing jump is not.
- E3: the draw key toggles DRAW and SHEATHE, and up plus a direction is JUMP then RUN_JUMP while it
  is held. The recorder treats those as one held key, so the later starts carry `repeat`.
- `repeats` and `repeats_by_move` per seat in the summary.
- Item 4 found one more bug of the same class: `block` read 0 in schema 2, because a stance
  change starts no engine move (R-V03) and so never has a `move` row. It is now counted from the
  accepted STANCE_* `action` row, with `repeat` on the held ticks.

No paid calls, no training, no server left running.
Details and the result line: `docs/final/orchestration/reports/T20-fix2-tech-lead.md`.
