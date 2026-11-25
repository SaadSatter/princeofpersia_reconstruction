# T20-fix2: a running jump is a flip; a held key is one use (corrective attempt 2 of 2, the last)

Handoff id: HO-T20-fix2-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3.
Findings: Eval E2 (major), E3 (minor) and the `moves` note, in `reports/T20-fix1-evaluation-specialist.md`@5700c42 (REJECT). Decisions in force: #53 (every directional jump is a flip), #81–#83, #85, #86. **If this attempt is rejected, the orchestrator stops and escalates to Saad; there is no fix3 without his answer.**
Base: `gate/T20-fix1-eval` 5700c42: `git switch -c task/T20-fix2 5700c42`. Suite there: `1635 passed, 12 skipped, 6 xfailed` (E2 and E3 as strict xfails).

## Fix

1. **E2 (major).** A running jump starts as a run and becomes the flip inside the same engine move. Count it as one flip. More generally, count one flip for every `JUMP_*`, `RUN_JUMP_*` and hop-turn flip start, whether or not the move's first frames read `moved`. Derive this from `started_move` and its `rewrite`, not from a second copy of the rule.
2. **E3 (minor).** Holding the draw key alternates DRAW and SHEATHE. Count a held key as one use (the F1 principle: a held key is not a new use), with a `repeat` marker on the toggles that follow.
3. **`moves` note.** Add a per-seat `repeats` count to the summary, so `moves` (raw engine starts) and `mechanics` (uses) reconcile.
4. Re-check every mechanic in the summary for the same class of bug: a move whose first frames read another effect (run → flip, lunge, kick, TAKE, RIG, sword pickup, block stances). List each mechanic and the evidence that a single use counts once.

## Permitted writes

`server/telemetry.py`, `tools/telemetry/**`, `docs/final/playtest/TELEMETRY.md`, new tests `tests/test_t20fix2_*.py`, new fixture files under `tests/data/t20_telemetry/`, `docs/agent-sessions/` (a new file), `docs/final/orchestration/reports/T20-fix2-tech-lead.md`. **No `pop/` change.** If one seems needed, stop and report. Do not edit any existing test: Eval's E2 and E3 strict xfails will XPASS, and their author removes the marks at Gate 2.

## Acceptance

1. A running jump (hold a direction 8 ticks, then direction + jump) gives `flip == 1`. So do a standing jump and a hop turned into a flip.
2. Holding `g` for 30 ticks gives one use (draw 1 or sheathe 1, per the first toggle), with the rest marked `repeat`.
3. `moves − repeats` reconciles with the summed uses where a mechanic maps one-to-one, and the report says where it does not.
4. The item 4 table is in the report, with a test per mechanic.
5. Determinism, leak and client-message identity tests still pass.
6. The suite is green except the expected Eval XPASS, with the real line pasted (`uv run --frozen --extra play --extra train --extra online pytest -q`).

Gates: QA (`gate/T20-fix2-qa`), Eval (`gate/T20-fix2-eval`), Gate 3.
