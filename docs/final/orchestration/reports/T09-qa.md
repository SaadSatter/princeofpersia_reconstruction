---
task: T09
from: qa
to: rules-reviewer
consumed: docs/final/orchestration/reports/T09-evaluation-specialist.md@874c5e0 and docs/final/evaluation/RESULTS-T09.md@874c5e0
reviewed_commit: 874c5e0
source_commit: gate/T09-qa head (this report's commit)
verdict: ACCEPT WITH NOTES
---

# T09 QA (Gate 1): the one held-out comparison (H6)

**Verdict: ACCEPT WITH NOTES.** The evidence is complete, reproducible and the report matches it. The pre-registered verdict "NOT SUPPORTED" (13 W / 2 D / 1 L of 16, bar 14) follows decision #77 literally. No blocker or major finding. I did not run the held-out split and did not write `ledger.jsonl` or `refusals.jsonl`; `--replay` only.

## Suite

`uv run --frozen --extra play --extra train --extra online pytest -q` on the clean tree at 874c5e0 (before adding my test file; `git status --porcelain --ignored` showed only `.venv/` and `__pycache__/`):
**1767 passed, 11 skipped, 5 xfailed, 2 warnings in 282.96s (0:04:42)**.
My probe: `tests/test_qa_T09_evidence.py`, 11 passed (read-only on committed evidence).

## Acceptance criteria to evidence

| criterion | met | evidence |
| --- | --- | --- |
| Only permitted paths changed | yes | `git diff --name-only 0ea8d73..874c5e0`: only `evaluation/heldout/ledger.jsonl`, `evaluation/results/T09/**`, `RESULTS-T09.md`, the evaluation report. No code, test, weights, H6 or PROTOCOL change. No `refusals.jsonl`. `docs/agent-sessions/` file not added (permitted, optional; see note N5) |
| Code at run commit equals 0ea8d73 | yes | `git diff --name-only 0ea8d73 77bc2f7` lists only `docs/final/orchestration/reports/T09-evaluation-specialist.md` |
| H6 and weights unchanged | yes | H6.json sha256 d013152a...5266; ppo-run-1.json 80e4a110...ba4c (test `test_frozen_inputs_hash`) |
| Ledger: exactly one claim, key and commit | yes | one line, status `claimed`, policy_key = weights hash, heldout_sha256 = H6 hash, commit 77bc2f7d..., `dirty: false`, run id 20261125T085558Z equals every row's run id. Claim time 08:55:59Z, one second after the run id; `run_versus_suite.py` line 172 claims before the trial loop. No per-trial timestamps exist, so "before the first trial" rests on the code order plus the 1 s gap, not on a timestamp inside a trace |
| 48 rows, nothing missing | yes | 8 starts x 2 configs x 3 trials, all unique; 0 aborted, 0 harness errors; 0 fallbacks, refused, errors, timeouts, busy, invalid on both seats in all rows |
| `analyze_results.py` reproduces the counts | yes | rerun on the committed JSON: `analysis.json` byte-identical (`cmp`), `analysis.txt` identical apart from uv's install chatter. 13/2/1; seat A 7W 1D 0L, seat B 6W 1D 1L |
| Per start, sweep, Wilson, robustness | yes | independent recount: sweeps H6-3 to H6-7 = 5 of 8; hearts per cell match (SvM hearts mapped through the seat, A is the baseline there); Wilson 13/16 = 0.57 to 0.93, 12/14 = 0.60 to 0.96 recomputed; rooms, exposure labels (`exposure_table.py`) and the hazard flags agree with H6.json and the table |
| `--replay` reproduces snapshots | yes | all 16 trial-0 cells replayed, 16 of 16 `"ok": true`, expected = replayed sha. Nothing written to `evaluation/heldout/` (still only H6.json, ledger.jsonl, README.md) |
| Verdict follows #77 literally | yes | 13 < 14, so not supported; aborted = 0. PROTOCOL section 6 text matches #77 |
| Counting rule (step 4) | yes | every cell has one distinct (snapshot, termination, frames) over its 3 trials, so "win only if all 3 win" changes nothing. Test `test_trials_agree_per_cell` |
| Stale and fall numbers | stale yes, falls not re-derived | stale recomputed per controller: PPO 21, baseline 18, per-cell table identical to the report. Falls (25 vs 37) rest on a replay count by posture; I did not re-derive them (see Not checked) |
| Latency | yes | 7500 PPO-seat decisions, mean 0.27 ms, max 10.8 ms (H6-3 SvM t2) |
| No seed key in committed files | yes | ledger and results carry only `seed_key_id` `5b5c7582` (a prefix); trial seeds are the literals 0, 1, 2; every 64-hex string in ledger, results, analysis, RESULTS and trace metas is a known digest; no `seed*key*` file under `evaluation/` |
| Honest wording | yes | first line "NOT SUPPORTED", "does not mean the rival is worse"; no strength claim; confounds listed (nearest-figure targeting, deterministic single outcome, patrol overlap, hazard-ahead, no guard in room 2, duels-only training, seat/position confound, stale/falls, effective n near 8) |

## Findings

No blocker, no major. None reproduced as a failure.

- **N1 (minor, wording)** `RESULTS-T09.md` "Stale inputs and falls": PROTOCOL H-c (line 29) says fallbacks, invalid and stale stay at 0 for **both** seats. On H6 the stale counts are 21 PPO and 18 baseline, so H-c is literally not met on H6. Decision #80 relaxed H-c for step 1 only and says to "report it" for H6; the report does report the numbers and flags it in the handoff, but RESULTS does not say in one line "H-c as written is not met on H6; #80 reading applied". Suggest one sentence. The verdict is unaffected (13 < 14 either way; the report says so).
- **N2 (minor, interpretation)** The reported PPO-seat stale inputs on H6 (21) differ from the "0 PPO stale" in the tuning step. The report's explanation (a queued move stranded when the previous move ends in a fall) was shown on the tuning split for the baseline only; it was not shown for the PPO-seat stale on H6. The stale-cause sentence in RESULTS is stated as general mechanism, which is fair, but the rules reviewer should not read it as verified for those four PPO cells.
- **N3 (minor, interpretation)** The "fall" counts are counts of entries into posture `falling`, "descriptive". The sentence "which may favour the PPO rival" is a hypothesis, labelled as such; keep it unpromoted. The one loss (H6-8 SvM) shows 3 falls each, so falls do not explain it.
- **N4 (note, confound strength)** The draws/loss are all in the two cells with PPO as the *later-moving or right-side* position is not testable here: seat order is confounded with start position (stated). Seat B record is 6W 1D 1L, seat A 7W 1D 0L; with n = 8 each this is not evidence of a seat effect either way.
- **N5 (note, process)** No `docs/agent-sessions/` record was added. The brief lists it as a permitted write, and AGENTS.md asks for a session record after substantial work; the orchestrator may want one before closing.
- **N6 (note, process)** The report header says `to: qa`; the QA role file names the final recipient as the orchestrator or the next gate. This is only a routing label; my `to:` is `rules-reviewer` as instructed.

## For the rules reviewer

Read-only points worth an independent look: (1) whether "13 of 16" should be quoted anywhere as more than "not shown at this bar" (it must not be called "better" or "worse"); (2) the H-c wording gap in N1; (3) the seat/position confound and PPO stale on H6 in the final summary; (4) that cells are not independent (effective n near 8), so the Wilson intervals must stay marked optimistic.

## Not checked

- The fall counts (25 vs 37): not re-derived by a posture-replay script; descriptive only.
- That no earlier H6 run happened outside this repository (the ledger is local; a prior private run cannot be excluded from the files alone, only the repo's ledger and git history, which show one claim).
- Trace content beyond meta and ledger for hidden facts (the T08/T19 reviews cover the boundary).
- Order of ledger write against first trial by timestamp (none recorded).
