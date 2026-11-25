# Versus evaluation protocol (task T08)

Status: built on `orch/reviewed` fc02687 by the Tech Lead; not yet through
Gate 1 (QA), Gate 2 (Evaluation Specialist) or Gate 3. No held-out result
exists. T09 runs H6 once, after T19, on the post-T19 engine.

Code: `evaluation/` (scenarios, monitors, controllers, freeze check, analysis)
and `tools/eval/` (`run_versus_suite.py`, `analyze_results.py`). Tests:
`tests/test_eval_*.py`.

## 1. What is compared, and the hypotheses

The AI rival is the PPO policy (`agents/rl/`, shipped weights
`agents/rl/weights/ppo-run-1.json`, SHA-256 in `agents/rl/policy.py`
`SHIPPED_SHA256`). The comparison is against the scripted baseline
(`agents/versus_baseline.py`), on the same controller interface, labelled
`scripted`. The PPO rival has no provider, token or cost: those fields are
**N/A** in every row (as in PR #64).

Hypotheses (stated before any held-out run; they are claims to test, not
results):

| # | Hypothesis | Measured by |
| --- | --- | --- |
| H-a | In full duels from the held-out starts the PPO rival wins more often than it loses against the scripted baseline, in both seats | H6, win/draw/loss per controller and per seat, Wilson intervals |
| H-b | The PPO rival does not do worse than the baseline on the four approved scenarios (D1, B2, I3, F5) | tuning split, per-scenario success rates, M against S as the subject |
| H-c | Neither rival is pushed to its fallback: fallbacks, invalid inputs and stale inputs stay at 0 for both | the rows' `seats.*.fallbacks`, `invalid_inputs`, `stale_inputs` |

H-a is the headline. A draw (time up) is not a win; an aborted round is not a
win. If the intervals overlap the report says so and makes no strength claim.

## 2. What counts as success (Saad's words, decisions #9, #58, #59)

Computed from the true state after every frame (the runner's `on_frame`
view), never shown to a controller. Subject = seat A.

| Id | Saad's words (decision #9) | Reading in force | Predicate |
| --- | --- | --- | --- |
| D1 | "Success if the agent kills a guard and picks up the disguise when no other player is on screen." | #59: "on screen" = the other rival is in the agent's room at **no frame** of the scenario | a guard is downed, its uniform is taken by the agent, and the other rival shares the agent's room at no frame. Seat B is forced to WAIT |
| B2 | "Blend if another guard doesn't notice it or keeps low suspicion." | #58: "low" = suspicion **below 50 of 100** for the whole scenario (`monitors.B2_LOW_THRESHOLD`, a named parameter) | the disguised agent is never targeted by a guard and its suspicion meter stays below 50 at every frame. The row also stores `success_active` (at least 6 distinct cells visited) because a seat that stands still is never noticed; that is an extra, not the flag |
| I3 | "Identify if the agent can distinguish between player guard and real guard." | no reading was open | the first thing the agent strikes is the disguised rival (its hearts drop), not a real guard (downed or knocked down); a same-frame strike on both is not a success. Seat B is a scripted `decoy` that paces like a patrol (stated confound: its stride is not calibrated to a real patrol) |
| F5 | "Fight or retreat if it wins a duel against a player or guard." | no reading was open | the agent is alive when a guard is downed, or when the other rival dies (`win_against: either`). F5-a, F5-b: guard with seat B idle in another room; F5-c: rival against rival |
| H6 | (decision #9: held out) | not applicable | full duel, 3,600 frames (5 minutes, decision #5); **no success flag**: the outcome by controller slot is the measurement |

Retreating is not scored separately: "fight or retreat" succeeds when the duel
is won, however it was won.

## 3. Splits

| Split | File | Contents | Who may read it |
| --- | --- | --- | --- |
| tuning | `evaluation/scenarios/tuning.json` | D1, B2, I3, F5 with three starts each (12 starts) | anyone; used for dry runs, tuning and tests |
| held-out | `evaluation/heldout/H6.json` | H6: four full-duel starts, eight guard posts | **only the CLI, through the hash check.** OFF LIMITS to training, tuning, reward and prompt design |

Frozen file: `evaluation/heldout/H6.json`, SHA-256
`44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847`.

Disjointness, enforced by tests (`tests/test_eval_registry.py`):

- no H6 start cell (room, row, column, any seat) is a start cell of the eight
  `TUNING_STARTS` in `tools/rl/env.py`, of any tuning scenario, or of the
  default arena starts;
- no H6 guard post is a tuning-scenario post or a default arena post;
- no H6 rival starts inside the patrol of a guard of its own start;
- `agents/rl/**` and `tools/rl/**` never mention `heldout` or `evaluation/` and
  never import `evaluation`; neither do `pop/`, `agents/`, `render/`, `server/`.

**H6-4's B start (decision #60).** The candidate in `orch/wip-T08` put B at
(1,2,3,+1), which is the A start of tuning pair 2. The rule, written before the
cell was chosen and independent of any policy result: keep B's room and row,
scan right from the old column, and take the first floor cell that no tuning
start, no other H6 start and no H6-4 guard patrol uses. Column 3 is a tuning
cell; column 4 is free, so B starts at (1,2,4,+1). The tuning scenarios'
cells were chosen the same way against the H6 cells.

## 4. Freeze rule

1. `H6.json` is committed once and never edited. The CLI recomputes its
   SHA-256 and refuses to run on any difference (a missing file also refuses).
2. A change needs a new hash, a new commit and a note here, and voids every
   earlier held-out result.
3. **Run once per frozen policy.** A real held-out run first appends a line to
   `evaluation/heldout/ledger.jsonl` (keyed by the weights SHA-256, or by the
   scripted source hash for scripted-only runs), then runs. A second run for the
   same key is refused. An aborted run still used its claim.
4. A held-out dry run (`--dry-run --split heldout`) uses WAIT seats on both
   seats, writes no ledger line and refuses any policy configuration.
5. MvM is test only and is refused on the held-out split.
6. T08 itself ran no policy on H6. T09 runs it once, after T19.

## 5. Runner policy (decision #24) and result rows

- **Fresh controllers per trial**, built for that trial only. One controller
  per worker and seat; seats never share an instance (the runner refuses it).
  A controller reported busy (an earlier call timed out and has not returned)
  makes the row a **harness error**: `harness_error: true`, `aborted: true`,
  `abort_reason: "harness_error:busy"`. It is not a quiet result.
- **Secret `seed_key`**: `--make-seed-key PATH` writes
  `secrets.token_bytes(32)` as 64 hex characters, mode 0600, never overwrites.
  A real run needs `--seed-key-file`; keys under 32 bytes are refused. The key
  is never written to a result or trace, only a short id. A dry run uses a
  public key and says so (`seed_key_id: dry-run-public`).
- **Aborted runs are reported**, never dropped: a runner cap (`max_frames`,
  `max_fallbacks`), a harness error or an exception each give a row with
  `aborted: true` and the reason. They count in the denominator as "not a
  success, not a win".
- **Row fields**: scenario, start id, seed, commit (and `dirty`), controller
  names, versions and weights hash, seat (`controllers.A/B`, `outcome.result_A/B`),
  outcome, termination, success flag and reason, metrics, invalid, stale,
  replaced and fallback/busy/timeout counts, decisions, measured latency
  (`time.perf_counter`), trace paths, forced stand-ins, `seed_key_id`.
- **Two-seat traces**: `traces/<scenario>/<start>/<config>-t<n>/` holds
  `seat-A.jsonl`, `seat-B.jsonl` (one line per decision, with the seat's
  observation and legal-list hashes) and `meta.json`. `--replay DIR` re-feeds
  the recorded inputs and compares the final snapshot hash with the trace and
  the meta file (exit 0 equal, 1 different).

### Configurations and seat swap

A configuration names the seat A and seat B controllers: SvS, MvS, SvM, MvM
(S scripted baseline, M PPO). MvS against SvM is the seat swap for a duel.
A scenario start that forces seat B to a stand-in (`wait`, `decoy`) runs only
configurations whose B letter is S: SvM would repeat SvS and MvM would repeat
MvS exactly. In those scenarios the subject is always seat A, so "M against S"
means the PPO rival as the subject (MvS) against the baseline as the subject
(SvS), each against the same stand-in. Seat B as a subject is covered only in
the rival-against-rival starts (F5-c and H6).

## 6. Comparison plan

1. Tuning dry run: `--dry-run`, SvS, every scenario. Plumbing only; the rows are
   labelled and are not evidence of play strength.
2. Tuning comparison: MvS and SvS on D1, B2, I3, F5; F5-c also SvM. At least 3 trials per start and configuration.
3. Held-out (T09, once): `--split heldout --configs MvS,SvM`, seed key from
   `--make-seed-key`, at least 3 trials per start and configuration.
4. Analysis: `tools/eval/analyze_results.py results.json`.

### Seeds are not independent trials

T07-run1 Evaluation E3 found that duels of one start pair gave identical results
across seeds: the baseline and the argmax policy are deterministic, and the
engine's RNG is rarely consulted. The analysis therefore reports, per condition
(scenario, start, configuration), the **rows run** and the **distinct final
snapshots**, and computes its rates and intervals over the distinct outcomes
(`n`), not over the rows (`n_rows`). Three trials of one start with one final
state are one trial. Independent evidence comes from distinct starts and the two
seats, not from seed repeats. With fewer than 3 distinct outcomes an interval is
printed but flagged `n<3`. A study that wants more independent trials adds
starts, which for H6 means a new frozen set.

### Win, draw, loss and mirrors

Win/draw/loss are reported per controller (M or S) over both seats, with the
split by seat A and seat B, 95 % Wilson intervals, and aborted rounds in the
denominator. A mirror match (the same kind of controller in both seats: SvS,
MvM) is **one trial**, reported as seat A wins, seat B wins and draws, never as
two controllers.

## 7. Plumbing requests (not done here; `pop/` is not ours to edit)

1. `ScenarioEpisode` (`evaluation/spec.py`) sets `kid.hp` and `disguised` on the
   duel's private rivals after every `reset`, and reads `_duel`. A public set-up
   hook on `VersusEpisode` (hearts, disguise, no change of rules) would remove
   that. T19 changes the engine now; the tests in `tests/test_eval_*.py` fail
   loudly if it moves.
2. `pop.versus_runner.snapshot` reads `_duel.snapshot()` when the episode has no
   public `snapshot`; the same request.

## 8. Not in this protocol

Playtests, reflections, balance numbers and any Student decision are Saad's.
This document changes no rule, number or approved criterion.
