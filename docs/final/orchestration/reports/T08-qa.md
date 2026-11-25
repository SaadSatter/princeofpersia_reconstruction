---
handoff_id: HO-T08-qa
task_id: T08
date: 2026-11-24
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T08-tech-lead.md@deb8718 (brief docs/final/orchestration/tasks/T08.md@0bba440, amended 2026-11-24 late night; decisions #58 to #61 in DECISIONS-2026-11-24.md@0bba440)
source_branch: gate/T08-qa
source_commit: see the commit that adds this file (the final message names it)
reviewed_commit: deb8718ac912436f71c4ac6e24085e0112adbd81
verdict: ACCEPT WITH NOTES
---

# T08: QA (Gate 1) report

Status: done. Verdict: **ACCEPT WITH NOTES**. No blocker or major finding was
reproduced; four minor findings (F-1 to F-4) are reproduced by strict xfail
probes, and nothing in them blocks Gate 2.

## Suite
```
uv run --frozen --extra play --extra train --extra online pytest -q
1468 passed, 11 skipped, 4 xfailed, 2 warnings in 380.91s (0:06:20)
```
(Run on the reviewed tree deb8718, before my probe file existed; the 4 xfailed are the repository's existing ones, same count as the Tech Lead's line.)
```
```
Probes alone: `11 passed, 4 xfailed in 0.83s` (`tests/test_qa_T08_probes.py`).
No PPO policy was run on H6; the real ledger was never written (probes patch a
temp ledger); no `--live`, no training.

## Scope (checked)
`git diff --name-only fc02687..deb8718` lists 23 files, all inside the brief's
permitted paths: `evaluation/**` (new), `tools/eval/{__init__,run_versus_suite,analyze_results}.py`
(new; `git ls-tree` confirms exactly these three, no stray file from the glob
staging), four new `tests/test_eval_*.py`, `docs/final/evaluation/PROTOCOL.md`,
one `docs/agent-sessions/` file, the tech-lead report. No edit under `pop/`,
`agents/`, `tools/rl/`, `play.py`, `render/`, `web/`, `server/`, `.github/`, `ci/`,
and no existing test touched. `git diff f9609ae deb8718 -- tests` is empty, so
the tests were not weakened after the failing commit.

Tests failed first: checking out f9609ae (tests only, on the base) gives
`ModuleNotFoundError: No module named 'evaluation'`, 4 collection errors. That
is an import failure, so it shows the tests could not pass without the work, not
that each assertion discriminates; I covered discrimination with the probes below.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Dry runs of every scenario, baseline vs baseline, write complete rows | met | `tests/test_eval_suite.py` dry-run tests pass; the module fixture runs the CLI over every tuning start, and my probes ran the CLI on H6 with `--dry-run` (rows written, none aborted) |
| 2 | Replay test | met | TL tests pass; probe `test_replaying_a_heldout_trace_with_the_heldout_split_reproduces_the_snapshot` passes. Caveat F-4 |
| 3 | Success predicates unit-tested on constructed states (D1 #59, B2 #58, I3, F5) | met with a gap | 29 monitor tests pass; B2 49 passes, 50 fails, threshold is `M.B2_LOW_THRESHOLD` and an overridable keyword. Gap F-1 (D1 attribution) |
| 4 | Held-out hash checked by the CLI | met | file SHA-256 recomputed: `44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847`; it matches `evaluation/manifest.py:28`, `evaluation/heldout/README.md:13` and `docs/final/evaluation/PROTOCOL.md:56`. A non-JSON file and a one-byte change are refused by hash before parsing (probe) |
| 5 | H6 disjoint from the 8 `TUNING_STARTS`; `agents/rl/**`, `tools/rl/**` never read H6 | met for start cells; see F-3 for guard patrols | rival start cells disjoint from `tools.rl.env.TUNING_STARTS`, from every tuning-scenario start and from `arena.STARTS` (test and my cell scan); H6-4 B is `(1,2,4,+1)` per #60. The rl text and import lint passes; probe adds that no rl file imports `tools.eval` either |
| 6 | Seat swap, fresh controllers, secret seed_key, aborted rows reported | met with F-2 | fresh controllers per `Trial.build_controllers`; key from `secrets.token_bytes(32)`, 0600, never in results or traces (TL test, and `seed_key_id` is a salted hash prefix); busy gives `harness_error` and `aborted`; exception rows are written. Analysis cannot summarise an exception row (F-2) |
| 7 | Analysis: Wilson, per-scenario success, distinct outcomes, mirror = one trial, per seat | met with F-2 | `tests/test_eval_analysis.py` 13 pass; read `evaluation/analysis.py` (aborted rows are their own trial and a failure in the denominator; mirror branch reports seat A and seat B wins) |
| 8 | PROTOCOL.md | met | present; states the freeze, splits, N/A provider fields |
| 9 | Full suite green | met | line above |
| 10 | Open questions for Saad reported | met | TL report lists three; see my notes below |

## Findings (all reproduced; none blocks Gate 2)
Probes live in `tests/test_qa_T08_probes.py`; each finding is a strict xfail,
so it turns into a failure the day it is fixed.

**F-1 (minor) `evaluation/monitors.py:DisguiseMonitor` (class docstring and `_observe`)** credits the agent with a guard the *other rival* downed earlier.
The docstring says "with the other rival out of the room only the agent can have
downed the guard". That holds only while the other rival cannot have visited the
guard's room before the agent. Repro: probe `test_d1_does_not_credit_a_guard_the_other_rival_downed_before_leaving`
(rival B downs the guard in room 4 while A is in room 3, B walks to room 5, A
enters room 4 and takes the uniform: `success` is True, expected False). It is
latent today because every D1 start forces seat B to WAIT. It matters if D1 is
ever run with an active seat B (TL open question 2). Suggested fix: record
`downed_frame` only while the subject is in the guard's room, or require the
subject to have struck the guard.

**F-2 (minor) `evaluation/analysis.py:114` (`duel_results`)** raises `KeyError: 'A'` on any aborted fight/duel row whose `controllers` is `{}`.
`run_trial` writes `controllers: {}` when the exception happens while building
controllers (for example the shipped weights failing to load, which is the
expected failure for an M seat). So the aborted-run reporting required by #24 works
in the runner, but `analyze_results.py` then crashes on exactly those rows and
reports nothing. Repro: probe `test_analysis_summarises_a_run_where_every_row_aborted_before_controllers_existed`
(`analysis.render` on two such rows). Expected: the "Aborted rounds" section lists
them; actual: `KeyError`. `success_by_scenario` already guards with `r.get("controllers")`;
`duel_results` does not.

**F-3 (minor) H6 "guard posts that appear nowhere else" is true for the exact post tuples only.**
Patrols are corridor ranges on row 2, so they overlap. Measured on the committed
files: 15 H6 guard cells are also tuning-scenario guard cells, 8 are default arena
patrol cells (`barracks (4,2,1..8)`, `pit_hall (5,2,1..8)`), and 6 `TUNING_STARTS`
cells (the PPO training starts) lie inside H6 patrols (`(3,2,6) (3,2,7) (4,2,4) (1,2,3) (1,2,2) (4,2,9)`).
The registry test compares `(room, row, (c0, c1))` tuples, so a patrol of
`(1, 9)` instead of `(1, 8)` would pass it. PROTOCOL.md line 63 states only the
tuple claim, so no claim is false, but the brief's intent ("start configurations
and guard posts not used anywhere else") is only partly met. The training set
itself used the default posts, so a trained policy has seen guards on most of
these cells; this softens how "held out" H6's guard layout is. Probe:
`test_h6_guard_patrol_cells_are_disjoint_from_every_other_split` (xfail). It may
be impossible to satisfy fully in a ten-column corridor; the Evaluation
Specialist should decide whether the protocol should say "start cells and post
tuples, not patrol cells".

**F-4 (minor) `tools/eval/run_versus_suite.py` (`--replay`)** replays only against the split named by `--split` (default tuning).
A held-out trace replayed without `--split heldout` dies with a `KeyError: 'H6'`
traceback although `meta.json` records `"split"`. With `--split heldout` it
replays and matches (probe passes). Probe: `test_replaying_a_heldout_trace_without_the_heldout_split_fails_cleanly`.

## Checks that passed (adversarial, with evidence)
- **Run-once ledger** (`evaluation/manifest.py:claim_heldout_run`): a second real
  held-out run for the same policy key is refused (exit 2) whatever the seed key,
  `--scenarios`, `--trials` or `--seed-base` (probe). A run with no seed key is
  refused and claims nothing. The ledger line is written before the first trial
  (probe aborts at trial one, the claim is already there and a rerun is refused).
  A held-out dry run builds only `wait` controllers and never a policy (probe spies on `C.build`).
  Residual weaknesses, none a finding against the build: the ledger is a plain local
  file (deleting it, or a different weights hash, resets it; it is not gitignored, so
  a commit would record it); claim is check-then-append with no lock; `HELDOUT_SHA256`
  is a source constant, so editing both the file and the constant passes (that is what the
  three recorded places and the commit history are for).
- **Predicates in the evaluator only.** The monitor is built in `run_trial` and fed from
  `on_frame` through `view.snapshot()`; controllers get `observe`/`legal_actions` only.
  Probe: an I3 observation for seat A contains none of `monitor, success, scenario, i3,
  decoy, start_id, seed_key`, and the disguised rival appears as `kind: guard`.
- **`ScenarioEpisode` and the private `_duel`.** `reset` sets only `kid.hp` and
  `disguised` after `super().reset`. Probe: a default start (3 hearts, no disguise)
  produces observations identical, frame by frame for 300 frames and both seats, to a
  plain `VersusEpisode` with the same situation, starts, seed and guards; hearts do not
  leak between episodes. Residual: `hp` is lowered but `max_hp` stays 3 (a 2-heart start
  shows `hp 2 / max_hp 3`), which is a faithful "wounded" start, not an altered rule.
  The `_duel` coupling is a known limitation (PROTOCOL.md section 7).
- **D1, B2, I3, F5 readings.** Read each class against #58 and #59: B2 uses
  `max suspicion < low` over every frame plus no guard targeting or full meter; D1 needs
  copresence of zero frames over the whole scenario including after the take (#59 as
  decided). Notes, not findings: B2 also succeeds if the agent drops its disguise by
  attacking without any guard noticing (the disguise loss is recorded, not scored); the
  initial frame (frame 0) is never passed to the monitors, which is harmless for every
  committed start since no D1 start puts the rivals in one room.
- **Secret key.** Dry runs use a public key and are labelled; a weak or non-hex key file is refused.
- **Distinct outcomes.** `_distinct` keys on `final_snapshot_sha256` per condition, aborted rows
  never merge, so seeds are not counted as independent trials unless the final states differ.

## Notes for the Evaluation Specialist (Gate 2)
1. F-3 and the training-start overlap decide how much weight H6 carries as "held out".
2. The `n<3` flag is the expected output for most conditions (one start gives one distinct outcome).
3. TL question 1 (ledger key includes the engine commit): as built, any later run of the same
   weights on a changed engine is refused, and a changed weights hash is accepted. Both are
   defensible; T09's run should state which it relies on.
4. Baseline dry-run success rates (D1 1/3, B2 1/3, I3 3/3, F5 2/3) are plumbing output only.

## Not checked
- The PPO policy on any split (forbidden here; T09 owns the single H6 run).
- Cost, tokens and provider fields: N/A by design, only checked that rows say so.
- Whether the I3 decoy resembles a real patrol (stated confound).
- Windows paths, concurrent claims of the ledger from two processes.
- `docs/agent-sessions/T08-versus-evaluation-suite.md` content (not part of any criterion).
- Browser build and Playwright: not applicable (no web change).

## Unresolved findings
F-1 to F-4, all minor, for the orchestrator to route (suggested: one Tech Lead
fix for F-1, F-2, F-4; F-3 is a protocol decision for the Evaluation Specialist
and Saad).

## Requested next action
Gate 2: Evaluation Specialist on `task/T08` deb8718 with this report. Run
`uv run --frozen --extra play --extra train --extra online pytest -q tests/test_qa_T08_probes.py`
to see the four strict xfails.
