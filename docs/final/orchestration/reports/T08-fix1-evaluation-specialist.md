---
handoff_id: HO-T08-fix1-evaluation-specialist
task_id: T08-fix1
date: 2026-11-25
from: evaluation-specialist
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T08-fix1-qa.md@72e3467 (QA ACCEPT WITH NOTES, N-1 to N-6); docs/final/orchestration/reports/T08-fix1-tech-lead.md@ea9c786; docs/final/orchestration/tasks/T08-fix1.md@49d7840 (with the #78 amendment); DECISIONS-2026-11-24.md@49d7840 (#64-#66, #74-#78); docs/final/orchestration/reports/T08-evaluation-specialist.md@059aea5
source_branch: gate/T08-fix1-eval
source_commit: see the commit that adds this file (the final message names it)
reviewed_commit: ea9c786 (code) plus QA's work at 72e3467
verdict: ACCEPT WITH NOTES
---

# T08-fix1: Evaluation Specialist (Gate 2) report

Status: done. Verdict: **ACCEPT WITH NOTES**. No leak, H6 still unreachable from training, the new starts follow a
rule that was written first and that I and QA can both regenerate, nothing in the rule needs Saad. **T09 may run once
T19 closes, under the conditions in "T09 readiness"**, none of which needs new code. The two points worth Saad's eyes
are about wording, not decisions (see "Items for Saad").

## Suite
```
uv run --frozen --extra play --extra train --extra online pytest -q      (on da05992, clean committed tree)
1611 passed, 11 skipped, 5 xfailed, 2 warnings in 396.66s (0:06:36)
```
Run on `gate/T08-fix1-eval` at da05992 (72e3467 plus my test commit). QA's line at 0f57d8c had 2 failures, which were my two
tests; they pass now. My new file alone: `8 passed`. No policy ran on H6, the real ledger and refusals file were never
written (neither exists), no training, no `--live`. I did run PPO and baseline on the **tuning** split only (below).

## #78 edit: my two tests in `tests/test_eval_T08_gate2.py` (pinned values only)
| Test | Old | New |
| --- | --- | --- |
| `test_f3_exposure_of_h6_guard_posts_to_training` | `(full, partial, none) == (2, 1, 5)` over every H6 start | `(2, 1, 5)` over the first four starts (the superseded freeze) **and** `(5, 1, 10)` over all eight, plus the same totals from `tools/eval/exposure_table.exposure` (`posts == 16`) |
| `test_h6_has_four_starts_and_two_seat_orders_give_eight_outcomes` | `len(_h6_starts()) == 4` | `len == 8` (16 duels with seats swapped), and the first four ids are H6-1 to H6-4 |
Test names are kept (only pinned values changed, as #78 says). Every other assertion in the file is unchanged and passes
(`test_power_of_an_eight_outcome_heldout_run` is the arithmetic for the superseded 4-start set and stays true).

## What I checked
- **Rule and starts.** Read `PROTOCOL.md` 3.1, `tools/eval/select_heldout_starts.py`, `H6.json`; QA's independent
  reimplementation (from the text alone) reproduces H6-5 to H6-8; the rule commit `1f6fe1e` precedes `632fc95`; H6-1 to H6-4
  are byte-identical to the first freeze. Hash `d013152a...5266` is in `manifest.py`, the README and PROTOCOL (test pinned).
- **Tuning smoke (plumbing, not strength).** `--split tuning --configs SvS,MvS,SvM --trials 1`, fresh seed key and `--out`
  in a scratch directory (not the repo): 47 rows, 0 aborted. The analysis shows the #65 per-seat lines: B2, D1, I3 each
  report subject seat A and subject seat B separately for S and M; F5 shows SvM by seat. Every condition again has 1 distinct
  outcome (seeds add nothing; mirrors add the seat, not a layout). Counts are 1 to 3 distinct outcomes per cell, so every
  scenario interval is wide (3 of 3 gives 0.44 to 1.00). Not strength evidence; not tuned against.
- **Ledger code read** (`manifest.claim_heldout_run`, `require_known_clean_tree`, `record_refusal`, `suite._dirty`, the CLI
  order: verify hash, then clean-tree check, then claim, refusals to `refusals.jsonl`). The claim is written before any trial.

## Findings
| id | severity | finding |
| --- | --- | --- |
| G-1 | **moderate (for the T09 brief)** | **A new commit reopens a claim.** The key is (weights, commit), as Saad chose. Committing T09's own report (or the ledger line) creates a new HEAD, so the tool would accept a second held-out run for the same weights. Both lines would stay visible, as #64 intends, but the tool is not a barrier to a second run. T09's brief must therefore state the one-run rule itself (pinned by `test_a_new_commit_reopens_a_claim...`). No code change needed |
| G-2 | minor | **Three new starts open with a hazard one step ahead of a rival** (the facing rule, toward the room's middle): H6-5 A faces a pit (room 2 shaft, col 4), H6-6 B and H6-8 A face spikes. H6-7 A faces the open gate. None of H6-1 to H6-4 does. This is a property of the pre-written rule, not an error, and the seat swap gives each controller each seat, so it cancels per start. T09 must report it beside the per-start rows so a result is not misread as "hazard handling" in aggregate (pinned by test) |
| G-3 | minor | **Clustering.** New rival cells: room 2 x3, room 6 x3, room 4 x1, room 5 x1, rooms 1 and 3 none. All 16 rival cells: rooms 1 to 6 get 2, 3, 2, 3, 3, 3. Balanced overall. **Guards over all 8 starts**: room 1 six posts, room 3 three, rooms 4 and 5 three each, room 6 one, **room 2 none**. So no held-out duel has a guard in the Gatehouse. Every start has its rivals one or two room hops apart (pinned), so none is unreachable and the bar is attainable. Rooms 2 and 6 hold 6 of the 8 new rival cells because only 13 free corridor cells existed |
| G-4 | minor | **Effective n is below 16.** The two seat orders of one start share geometry, and both controllers are deterministic, so seeds add nothing. See "The #77 bar". The Wilson interval treats the 16 as independent and so is optimistic; the bar is strict enough that this does not matter for the decision rule, but the report must not call the interval exact |
| G-5 | minor | **Dirty-tree check is narrower than the claim in the key** (QA N-2): untracked files outside `evaluation/` and `tools/eval/`, and ignored files, are not seen. Acceptable for T09 if the operator checks by hand (below) |
| E-6, QA F-3 | accepted | H-b wording, #75 wording and "unseen start pairs and guard layouts" are in PROTOCOL 1 and 3 as decided. The F-3 strict xfail stays true |

No leak found: `agents/rl/**` and `tools/rl/**` still do not mention `heldout` or import `evaluation` (existing source-scan
test passes); seed key and seed are not written to rows; the held-out dry run uses WAIT seats and refuses a policy.

## Judgments requested
**Is H6-5 to H6-8 and the selection rule sound, and does it need Saad?** Sound; **nothing for Saad.** It is fully specified
(QA reproduced it from the text; `select_heldout_starts.py` regenerates it and a test compares with the file), it reads only
the map and the used-cell lists (a test greps the source for any policy, baseline or run-data reference), it fails the build
rather than adjusting, and the free choices (spans 2 to 4, facing toward the middle, SHA-256 order) are arbitrary but not
outcome-aware, which is what matters for a held-out set. They are the Tech Lead's mechanical choices inside a decision Saad
made (#74: "chosen by a rule written down before any cell is picked and never from policy results"). The consequences
(G-2, G-3) are disclosures. I would not re-draw the starts: doing so after seeing the geometry is allowed (H6 has never run)
but would only trade one partial pattern for another and add a fourth hash.

**What T09 reports per start.** For each of H6-1 to H6-8: result of MvS and of SvM (win/draw/loss, termination, hearts at end),
a label from `tools/eval/exposure_table.py` (H6-1 training-like; H6-3, H6-6, H6-7, H6-8 partly; H6-2, H6-4, H6-5 unseen
layouts), the two rival rooms and whether a hazard opens within one step (G-2: H6-5, H6-6, H6-8), and a **sweep count**
(starts where the PPO rival won both orders). Then the overall 16-duel line with Wilson, and the same split to the most
training-like starts excluded (H6-1) as a robustness line, stated as descriptive.

**The #77 bar (at least 14 of 16, no aborted duel) and its power.** Computed, and pinned in `tests/test_eval_T08fix1_gate2.py`:
- Independent duels: a rival that wins half of them passes **0.2 %** of the time (so a pass is hard to get by luck); one that
  wins 80 % passes **35 %**, 90 % passes **79 %**.
- With the seat orders of a start treated as a cluster (a start gives 2, 1 or 0 wins): a coin-flip rival passes under 1 %; a rival
  that sweeps 70 % of starts and splits 25 % passes **46 %**; one that sweeps 90 % passes **96 %**.
- Wilson lower bounds (16 duels): 16/16 0.81, 14/16 0.64, 12/16 0.51, 11/16 0.44. So the bar is stricter than the point where
  the lower bound clears 0.5 (12 of 16).
- The bar is **conservative**: low risk of calling a weak rival better, moderate chance of calling a good rival "not supported".
  That is a reasonable pre-registration. A result below it is "not supported", and the report must say that is not evidence the
  rival is worse. Effective n is nearer 8 starts than 16 duels, so a pass is a claim about these 8 start pairs and guard layouts
  (#75 wording), not about the arena in general. Nothing to change; the bar is Saad's and is not moved after the run.

**#64 ledger and QA N-2, N-3, N-6: acceptable for T09, no code change before the run**, provided the brief carries G-1 and
these operator steps. N-2 (narrow dirty check): T09 runs `git status --porcelain --ignored` on the exact commit and requires it
empty except for the seed key outside the repo; this closes the gap by hand. N-3 (real-ledger tests fail on a dirty tracked
tree) affects developers only; it does not touch the one run, but the gate suite must be run on a clean committed tree (as I
did). N-6 (ledger is a convention; no lock; deleting the file resets it): T09 commits `ledger.jsonl` and `refusals.jsonl` together
with the results and its report, and the brief forbids a second run by rule (G-1). The ledger line is written before the first
trial, so a crash after the claim burns the claim: the brief must say that is reported as an aborted run and never re-run without
Saad.

**QA N-1 (D1 credit approximation): accept.** Room presence at the first knocked-down or downed frame can credit a trap fall in
the agent's room. D1 forces seat B to WAIT, so no other rival can down a guard; only a trap or fall can. D1 is a tuning scenario
in H-b, not part of H6 or the T09 bar, and the protocol already says "was in the guard's room". Nothing to fix.

**#65 per-seat analysis: works.** The tuning smoke shows seat A and seat B as separate subject-seat lines for S and M, and F5 by
seat; 11 mirrors are exact swaps (QA). Caveats to state in T09: mirrors repeat geometry, so each scenario has 3 layouts, not 6;
seat-B rows run SvS and SvM only. n per cell is 3 or less, so scenario rates are descriptive.

**#76 B2: built as decided.** The subject must be disguised on the last frame (`disguise_lost`), threshold 50 stays a named
parameter, `success_active` is reported and never scored. The "end state decides" reading (a loss regained by the end succeeds) is
documented and QA N-4 notes a dry-run row can show `success=True`; analysis counts aborted rows as failures, so unaffected.
B2 is an H-b scenario, not part of the bar.

**#75 wording: accepted.** PROTOCOL 3 says start cells and post tuples are disjoint, patrol ranges are not, "unseen start pairs
and guard layouts", and the numbers come from the generated table (16 posts: 5 full, 1 partial, 10 none). One small request,
not a blocker: add the G-2 hazard line to the H6 README or PROTOCOL 3 in T09's analysis, not as a spec change.

## T09 readiness
**T09 may run once T19 closes**, as a single held-out run, if its brief contains all of these:
1. **Base**: the commit that includes T19, T08-fix1 and the shipped weights, closed at Gate 3 (name the sha). T09 does not edit
   code, `agents/rl/weights/`, `H6.json`, `PROTOCOL.md` or the bar.
2. **Re-check first, on the tuning split, after T19**: the shipped weights still equal `SHIPPED_SHA256` and the checkpoint loads;
   the tuning dry run and a tuning comparison (`--split tuning --configs SvS,MvS,SvM --trials 3`) complete with 0 aborted, 0
   fallbacks, 0 invalid, 0 stale for both seats, and the observation or action schema is unchanged (T19 changes the engine; the
   policy has fixed input and mask sizes). If any of these fails, stop and report; do not retrain or tune, and do not run H6.
   This is a health check, not a selection of weights.
3. **Clean committed tree**: `git status --porcelain --ignored` shows nothing but the seed key (kept outside the repo, mode 0600,
   from `--make-seed-key`); the full suite line pasted from that tree.
4. **The exact command** (one invocation, from the project root):
   `uv run --frozen --extra play --extra train --extra online python tools/eval/run_versus_suite.py --split heldout --configs MvS,SvM --trials 3 --seed-key-file <KEY> --out <results dir>`
   (a real run, no `--dry-run`, no `--live`, never MvM, default limits). Run it **once**; no second invocation for any reason
   other than a refusal that wrote nothing to the ledger.
5. **One-run rule by words** (G-1): committing the report or ledger does not reopen it. A crash or abort after the claim is
   reported as is and escalated to Saad; the aborted duels count in the denominator.
6. **Commit the evidence**: `evaluation/heldout/ledger.jsonl`, `refusals.jsonl` (if any), `results.json`, traces, the analysis
   output, in the same commit as the report.
7. **Report**: the pre-registered verdict line first ("supported" only with at least 14 of 16 and no aborted duel; otherwise "not
   supported"), then the per-start table above, per seat and per controller, Wilson intervals marked as optimistic (G-4),
   confounds (nearest-figure targeting, one distinct outcome per condition, patrol overlap, hazard-ahead starts, PPO trained for
   duels only), measured latency from the rows, replay of one trace (a replay is never new evidence), and failed or odd rows in
   full.
8. No tuning, no re-seeding, no choosing of weights or starts after seeing a result.

## Evaluation-specialist headings (Gate 2)
Leak findings: none found. Probed: `agents/rl/**` and `tools/rl/**` source scan (no `heldout`, no `evaluation` import), seed key
and seed in rows, held-out dry run uses WAIT seats and refuses a policy, the new `select_heldout_starts.py` reads no run data
(grepped by the Tech Lead's test; I read it), refusals file holds no key.
Baseline fairness: same observation and macros as the policy; scripted baseline runs the same runner. Nearest-figure targeting
confound (D1, I3) stays disclosed. Not changed by this task.
Reward and training method: not in scope (no training); T07 gates cover it.
Checkpoint reproducibility: weights hash in every smoke row equals the shipped hash; T09 re-checks after T19 (item 2).
Train / held-out separation: start cells and post tuples disjoint (tests); patrol ranges overlap training patrols for 6 of the 16
posts (5 full, 1 partial), disclosed (#75); no training or tuning configuration repeated; H6 never run with a policy.
Evaluation validity and confounds: 8 starts, 16 duels, effective n nearer 8; one distinct outcome per condition; hazard-ahead starts
(G-2); guards absent from room 2 (G-3); H-b skills untrained; decoy uncalibrated; three layouts per tuning skill scenario.
Local inference performance: not re-measured here (T08 measured 0.2 ms mean, 0.5 ms max per decision on this machine, tuning start
F5-c, `time.perf_counter`); T09's rows carry the measured latency again. Browser not measured.
Replay and fallback: tuning smoke 47 rows, 0 aborted; replay not re-run here (QA verified F-4). Labelled WAIT fallback and aborted
rows are counted as before.
Training-run readiness: not applicable (no training); held-out run readiness is above.

## Paths
`tests/test_eval_T08_gate2.py` (two pinned values, #78), `tests/test_eval_T08fix1_gate2.py` (new, 8 tests), this report.

## Items for Saad
1. **Nothing blocks.** The selection rule and starts need no decision from you.
2. For awareness (your call whether it matters): the new starts include three that face a pit or spikes on the first step and
   the Gatehouse (room 2) has no guard in any held-out duel. I recommend accepting both and reporting them (G-2, G-3); changing
   them now would mean a new frozen file and a new hash and would not change the claim.
3. For awareness: the run-once tool lets a new commit through (G-1). The T09 brief will carry the one-run rule in words. If you
   want the tool to enforce it (key on the weights alone, as originally refused), that is a new decision and a code change.

## Not checked
H6 with the policy (forbidden); browser latency; concurrent ledger claims; behaviour of the shipped weights on the post-T19
engine (T09 item 2); the real-engine hazard behaviour at the three hazard starts (no run permitted).

## Unresolved findings
G-1 to G-5 above; none blocks Gate 3 on the build. G-1 and G-5 are carried into the T09 brief.

## Requested next action
Orchestrator: Gate 3 on T08-fix1; carry the T09 readiness list into the T09 brief once T19 closes.

## Student decision required
none
