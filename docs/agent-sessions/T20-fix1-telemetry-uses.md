# T20-fix1 session (tech-lead worker)

Base `a039283` (`gate/T20-eval`), branch `task/T20-fix1`. Corrective attempt 1 of 2 for T20,
from QA F1, F2, F3, Eval E1 and decisions #81 to #83.

Order: failing tests for `VersusEpisode.started_move` first, then the accessor in
`pop/versus.py`, then the recorder (`server/telemetry.py`: `move` rows, `started` and `grace`
on `action` rows, `effect` removed from `action` rows, pause end on forfeit), the summarizer
(counts from `move` rows, `repeat` skipped, grace-cancelled direction dropped from `moves`,
`REFUSED_RUN_MIN = 12`), `TELEMETRY.md` and the tests `tests/test_t20fix1_*.py` with a
schema 2 fixture in `tests/data/t20_telemetry/v2/`.

One step past "the accessor only": the accessor cannot say whether a jump was a grace cancel
from the move name alone (inferring it from the log history gave a false positive in a fuzz:
a jump queued behind a direction that had just finished). So `Duel._start` records which rule
rewrote the input (`kick`, `grace`, `hop_turn`) in a reporting-only dict, and the accessor
returns a `str` subclass with a `.rewrite` attribute. No rule reads it. See the report.

No paid calls, no training, no server left running.
Details and the result line: `docs/final/orchestration/reports/T20-fix1-tech-lead.md`.
