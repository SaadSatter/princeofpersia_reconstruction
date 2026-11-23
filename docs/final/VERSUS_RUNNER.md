# Versus runner and seat controllers (task T04)

Status: implemented on branch `task/T04`, awaiting QA (Gate 1) and the
Evaluation Specialist (Gate 2). Values marked *proposed* need Saad's approval.

Code: `pop/seats.py`, `pop/versus_runner.py`. Tests: `tests/test_seats.py`,
`tests/test_versus_runner.py`.

## Seat controllers (`pop/seats.py`)

A controller has `name`, `kind` and `decide(observation, legal) -> str`, and
may have `reset(seed)`.

| Kind | Class | Behaviour |
| --- | --- | --- |
| `human` | `HumanController` | Returns the latest input the frontend queued with `queue()`, else `WAIT` |
| `scripted` | `ScriptedController`, `RandomController` | A fixed list then `WAIT`; a seeded random legal input (test baseline, not the T05 baseline) |
| `policy` | `PolicyController` | Wraps a policy function, for example the PPO rival behind the macro layer |
| `fallback` | `WaitController` | Always `WAIT` |

A controller receives deep copies of **its own seat's** observation and a
tuple of its legal inputs. It never receives the episode, the duel, the other
seat or the episode seed. `reset` receives `controller_seed(seed, seat)`, a
one-way hash of the episode seed and the seat.

## Runner (`pop/versus_runner.py`)

`VersusRunner(episode_factory, {"A": ..., "B": ...}, decision_every=6,
limits=VersusLimits(...), swap_seats=False, clock=time.perf_counter).run(seed)`

- **Cadence.** Both seats are asked at frames 0, 6, 12, ... (*proposed*:
  every 6 ticks = 0.5 s at 12 fps). Both observations are taken before either
  answer is submitted, so seat order never matters. A seat with no legal
  input (knocked down, dead) is not asked and is not charged a decision.
- **Lockstep.** Frames do not advance while a controller thinks. A real-time
  server (online play, deferred on 2026-11-23) would need its own loop.
- **Validation.** An answer must be a string that is exactly in the seat's
  current legal list (`"wait"` is refused). Refused answers never reach
  `step`, so they change no state.
- **Fallback.** Exception, timeout, illegal answer or malformed answer is
  replaced by `WAIT` with `source: "fallback"` and a `fallback_reason`
  (`error`, `timeout`, `illegal`, `malformed`). Counted per seat. The other
  seat's cadence is unaffected. A fallback `WAIT` plays exactly like a
  controller `WAIT` (tested).
- **Timeout.** `timeout_s` defaults to 5 s (*proposed*). Latency is measured
  with the injectable clock; the call also runs in a worker thread
  (`pop/runner.py` `_call_with_timeout`) bounded by `timeout_s` of real time.
  A late reply is discarded.
- **Limits** (`VersusLimits`, per seat, all off by default, values to be
  approved): `max_decisions` (the run stops when a seat would need one more),
  `max_fallbacks` (the run stops when a seat exceeds it), `max_frames`
  (safety cap). The duel limit comes from the episode. A runner stop gives
  `status: "aborted:<reason>:<seats>"`; it is not scored as a win or loss
  (*proposed*; see below).
- **Result.** `seating` (seat to controller slot), per-seat `seats` stats
  (`decisions`, `fallbacks`, `refused`, `errors`, `timeouts`), the episode
  `outcome`, `status`, `winner_seat` and `winner_slot`, the final snapshot and
  its SHA-256, and per-seat `traces`.
- **Seat swap.** `swap_seats=True` puts controller slot A in seat B and slot
  B in seat A; `seating`, `seats[*].slot` and `winner_slot` show it.

## Traces and replay

Each decision record has: `frame`, `seat`, `slot`, `controller`, `kind`,
`obs_sha256`, `legal_sha256`, `input` (what was submitted), `source`
(`controller` | `fallback`), `fallback_reason`, `answer` (the refused answer,
truncated to 80 characters), `error`, `latency_ms`.

`save_traces(result, dir)` writes `seat-A.jsonl` and `seat-B.jsonl` (run
header, decisions, end line with the outcome and the final snapshot hash).
`load_traces(paths)` reads them back. `replay(factory, result_or_loaded)`
re-feeds every recorded input at its frame and returns the final snapshot,
which tests compare with the run's.

## Known gaps

- `VersusEpisode` has no public `snapshot()`; the runner reads the duel's
  snapshot through `episode._duel` (runner side only). A public method in
  `pop/versus.py` (owned by T01 at the time of writing) would remove that.
- `HumanController` returns `WAIT` when nothing is queued, and a submitted
  `WAIT` is a 6-frame move. `play.py` will need a "no input" answer, or a
  different human cadence, before it uses the runner (not in this task).
- Trace records are not rule changes, so no `docs/RULE_SOURCE_MAP.md` row was
  added.

## Decisions for Saad

1. Decision cadence of 6 frames (0.5 s) and a 5 s timeout.
2. Whether a seat that exceeds `max_fallbacks` forfeits (scored as a loss)
   or the run is reported as aborted (current behaviour), and default values
   for `max_decisions` and `max_fallbacks` in evaluation.
3. Exact-name validation (lowercase or padded answers are refused, although
   `VersusEpisode.step` would accept them).
