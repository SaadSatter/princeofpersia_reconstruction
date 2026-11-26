# T20-fix1: count uses once, log the move the engine started (corrective attempt 1 of 2)

Handoff id: HO-T20-fix1-orchestrator. Assigned: tech-lead; then qa (Gate 1), evaluation-specialist (Gate 2), Gate 3.
Findings: QA F1, F2, F3 (`reports/T20-qa.md`@8139bae, REJECT); Eval E1 and items 2–5 (`reports/T20-evaluation-specialist.md`@a039283). Decisions #81, #82, #83.
Base: `gate/T20-eval` a039283 (T20 + QA and Eval probes): `git switch -c task/T20-fix1 a039283`. Suite there: `1582 passed, 12 skipped, 7 xfailed`.

## Fix

1. **#81 accessor.** Add one public read-only method in `pop/versus.py` (or `VersusEpisode`), for example `started_move(seat)`: the action the engine actually started for that seat on the last tick, after the R-V10 kick swap, the R-V22 hop turn, the R-V35 grace cancel and stale-input drops, or `None`. Write the failing test first. It changes no rule and is not added to any observation. The recorder's resolved-action column and `effect` come only from it. Update the recorder's contract text, and tell Gate 2 that its `ast` source test must allow this one call.
2. **F1 + E1: count a use once, at the move's start.** A held key, or a queued direction during a running flip, is not a new use. Fix or document `action.effect` on every row.
3. **F2 / #82 grace.** The jump row carries `"grace": true`. The summarizer drops the superseded direction. The log stays append-only.
4. **#83 thresholds.** `REFUSED_RUN_MIN = 12` ticks; idle 3 s and stuck 60 s stay.
5. **F3.** Log `pause` end when a paused duel ends by forfeit.
6. **Docs.** Fix TELEMETRY.md per Gate 2:
   - Never hand a seat's file back to its player (it carries the seed).
   - The host JSON has per-seat counts.
   - Idle means "no input".
   - Stuck means "stayed in the room".
   - "Accepted" is not "executed".
   - AI duels summarize the human seat only.

## Permitted writes

`pop/versus.py` (the accessor only), `server/telemetry.py`, `server/match.py`, `server/app.py` (pause/forfeit hook only), `tools/telemetry/**`, `docs/final/playtest/TELEMETRY.md`, new tests `tests/test_t20fix1_*.py`, new fixture files under `tests/data/t20_telemetry/`, `docs/agent-sessions/` (a new file), `docs/final/orchestration/reports/T20-fix1-tech-lead.md`. Do not edit any existing test. QA's and Eval's strict xfails (F1, F2, E1) will XPASS or need their form changed. Report each one; their authors change them at their gates.

## Acceptance

1. One held flip gives `flip: 1`. A jump then 3 LEFT ticks gives one flip.
2. A grace cancel gives a jump row with `grace: true`, and the summary does not count the direction.
3. A kick that replaced a jump, and a hop that turned into a flip, log as the move the engine started.
4. Determinism holds: the 8-combination test, the trace, the state hash and client messages are identical with and without `--playtest`.
5. Leak tests still pass.
6. The suite is green except the expected XPASS/xfail-form items, with the real line pasted (brief command: `uv run --frozen --extra play --extra train --extra online pytest -q`).

Gates: QA (`gate/T20-fix1-qa`), Eval (`gate/T20-fix1-eval`), Gate 3. **If this attempt is rejected, T20-fix2 is the last before escalation to Saad.**
