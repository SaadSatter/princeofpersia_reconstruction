# Versus runner and seat controllers (task T04)

Status: implemented on branch `task/T04`; gate findings (`GATE-T04`) fixed
on `task/T04-fix1`, awaiting the gates again. Values marked *proposed* need
Saad's approval.

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
SHA-256 hash of the episode seed and the seat. That hash is one-way but not
secret: a controller can find a small episode seed by hashing candidates
(GATE-T04-eval-1). `VersusRunner(seed_key=...)` switches to HMAC-SHA-256 with
a key the controllers never see; the key is not written to the result or the
traces, so whoever keeps it can reproduce the controllers' seeds. The default
stays unkeyed so that runs repeat without a key (*proposed*; see below).

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
  current legal list (`"wait"` is refused). It is first copied to a plain
  `str` (`str.__str__`), so a `str` subclass cannot pass the check with its
  own `__eq__` or play something else through its own `strip`; the plain
  text is what is checked, submitted and traced (GATE-T04-QA-1, QA-2), and a
  `numpy.str_` answer still works. Refused answers never reach `step`, so
  they change no state. A refused answer whose `repr` raises is recorded as
  `<unprintable TYPE>` (QA-3).
- **Fallback.** Exception (any `BaseException`, `SystemExit` included,
  eval-4), timeout, busy controller, illegal answer or malformed answer is
  replaced by `WAIT` with `source: "fallback"` and a `fallback_reason`
  (`error`, `timeout`, `busy`, `illegal`, `malformed`). Counted per seat
  (`errors`, `timeouts`, `busy`, `refused`). The other seat's cadence is
  unaffected. A fallback `WAIT` plays exactly like a controller `WAIT`
  (tested). `KeyboardInterrupt` in an inline call (below) still stops the run.
- **Timeout.** `timeout_s` defaults to 5 s (*proposed*) and must be a finite
  number above 0 (`VersusLimits` refuses `None`, booleans, strings, 0,
  negative, NaN and infinity; the counts must be non-negative ints or
  `None`). Latency is measured with the injectable clock; by default the call
  also runs in a daemon worker thread bounded by `timeout_s` of real time. A
  late reply is discarded.
- **Busy.** A timed-out call cannot be killed. Until it returns, its
  controller is *busy*: the runner does not call it again (not `decide`, not
  `reset`, also in a later run of the same runner) and its seat gets
  `fallback_reason: "busy"` at each decision (eval-2). So a controller is
  never called concurrently with itself.
- **Reset.** `reset(seed)` is bounded the same way (QA-4 / eval-3). A reset
  that raises, times out or finds the controller busy is recorded in
  `seats[seat].reset_error` (`"timeout"`, `"busy"` or the redacted error) and
  the seat still plays.
- **Limits** (`VersusLimits`, per seat, all off by default, values to be
  approved): `max_decisions` (the run stops when a seat would need one more),
  `max_fallbacks` (the run stops when a seat exceeds it), `max_frames`
  (safety cap). The duel limit comes from the episode. A runner stop gives
  `status: "aborted:<reason>:<seats>"`; it is not scored as a win or loss
  (*proposed*; see below).
- **Result.** `seating` (seat to controller slot), `runner` (`copy_mode`,
  `threaded`), per-seat `seats` stats (`decisions`, `fallbacks`, `refused`,
  `errors`, `timeouts`, `busy`, `reset_error`), the episode
  `outcome`, `status`, `winner_seat` and `winner_slot`, the final snapshot and
  its SHA-256, and per-seat `traces`.
- **Seat swap.** `swap_seats=True` puts controller slot A in seat B and slot
  B in seat A; `seating`, `seats[*].slot` and `winner_slot` show it.

## Runner-side hooks (for T05/T08)

- **`on_frame(frame, view)`** (keyword argument). Called after every tick
  with the number of frames played (1, 2, ...) and an `EpisodeView` with
  `observe(seat)`, `legal_actions(seat)`, `outcome()` and `snapshot()`, each
  returning a copy. The view has no `step`, `tick` or `reset`. It is built by
  the runner and never passed to a controller; it is for scenario metrics in
  trusted evaluator code. Adding a hook does not change traces or the final
  snapshot (tested). An exception in the hook propagates (it is our code).
- **Trusted fast path for training.** `copy_mode="json"` copies the
  observation with a JSON round trip instead of `copy.deepcopy` (the current
  observation survives it unchanged; tuples would become lists).
  `threaded=False` calls the controller on the runner's thread: no thread
  start per call, but also **no real-time bound**, so a hanging controller
  hangs the run; latency over `timeout_s` on the injected clock is still a
  `timeout` fallback, after the call returns. Use both only for our own
  controllers (PPO self-play). The defaults (`deepcopy`, threaded) are
  unchanged and every result says which were used. Measured in the sandbox
  (5 seeds, 2,000-frame duels, two `RandomController`s, cadence 6): default
  about 3,800 decisions/s, `threaded=False` about 6,300, both options about
  6,400; the JSON copy alone gains little with the current small observation.

## In-process isolation is by convention

A controller in the runner's process gets only copies and never a reference
to the episode, but Python does not enforce that boundary: `gc.get_objects()`,
`sys._current_frames()` and closures reach the episode, the other seat's
controller and the runner (both gate reviewers showed this). The copies stop
accidents and honest mistakes, not a hostile controller. A controller that is
not ours (a student's or a third party's agent, a model with tool access)
must run in another process, talking to the runner only through its own
observation and its answer, as the online server will (deferred). Our own
scripted, PPO and Claude-backed controllers run in-process by this
convention, and the leak tests check what they are handed.

## Traces and replay

Each decision record has: `frame`, `seat`, `slot`, `controller`, `kind`,
`obs_sha256`, `legal_sha256`, `input` (what was submitted), `source`
(`controller` | `fallback`), `fallback_reason`, `answer` (the refused answer,
truncated to 80 characters), `error`, `latency_ms`.

`save_traces(result, dir)` writes `seat-A.jsonl` and `seat-B.jsonl` (run
header with `runner`, decisions, end line with the outcome and the final
snapshot hash).
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
- One controller instance may still fill both seats (GATE-T04-QA-5, test
  kept `xfail` pending Saad's decision). The busy rule keys on the instance,
  so such a controller is at least never called concurrently.
- A controller whose `name` or `kind` attribute raises is not guarded (they
  are read when the run starts).

## Decisions for Saad

1. Decision cadence of 6 frames (0.5 s) and a 5 s timeout.
2. Whether a seat that exceeds `max_fallbacks` forfeits (scored as a loss)
   or the run is reported as aborted (current behaviour), and default values
   for `max_decisions` and `max_fallbacks` in evaluation.
3. Exact-name validation (lowercase or padded answers are refused, although
   `VersusEpisode.step` would accept them).
4. GATE-T04-QA-5: refuse one controller instance in both seats with
   `ValueError` (both reviewers recommend it), or allow it.
5. GATE-T04-eval-1: keep the unkeyed `controller_seed` as the default
   (reproducible without a secret; reversible for small seeds), or make
   evaluation runs pass a `seed_key` (and decide who keeps it). The gate test
   stays `xfail` until this is decided.
