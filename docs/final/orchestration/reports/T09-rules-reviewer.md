---
handoff_id: HO-T09-rules-reviewer
task_id: T09
date: 2026-11-25
from: rules-reviewer (read-only; returned its findings as text)
to: orchestrator
configured_model: see `.claude/agents/rules-reviewer.md`; runtime model recorded in REVIEW_LOG.md
reviewed_commit: gate/T09-qa 25df2ca (contains the run commit 874c5e0)
recorded_by: orchestrator (session 8edb65a6). The reviewer cannot write files; its reply is reproduced below verbatim, unedited.
---

# T09: independent review (rules reviewer), verbatim

T09 independent review (read-only). I changed no files, ran nothing and ran no tests. Judged at `gate/T09-qa` 25df2ca. Brief, decisions and the report-listed files were read at the paths named below.

**Verdict on the five questions**
1. The claim is honest and within #77 and #75.
2. I found no hidden-information leak from reading the code.
3. H6 separation holds as far as static checks can show.
4. The confounds are mostly complete. Three points are missing or understated (items 3 to 6).
5. I found a few things QA missed (items 1, 2, 7, 8). None changes the verdict.

No blocker. No major.

**Findings, most serious first**

1. [minor, but the only evidence gap that touches the integrity claim] `docs/final/evaluation/RESULTS-T09.md:42` and `T09-evaluation-specialist.md:29` say "no ... errored ... decision" and "0 errors". Those counts are the runner's `seats.*.errors`. The PPO controller swallows its own inference exceptions and answers WAIT (`agents/rl/policy.py:119-121`). It counts them in `pm.errors`, exposed as `ctrl.policy_errors()` (`policy.py:143-144`). No evaluation code reads it: grep for `policy_errors` finds nothing under `evaluation/` or `tools/eval/`, and the H6 rows have no such field.
   - A silent inference failure would look like a passive WAIT seat, not a fallback, and would not appear in any H6 row.
   - T07-fix1 flagged this gap itself: "The in-play counter still has to be written into game results by whoever runs the seat (T08/T13)". It was never closed.
   - Why it matters here: two of the three non-wins are draws, which is what a stuck seat would produce.
   - Not a verdict risk, because the run cannot be redone and 13 < 14.
   - Fix: either rebuild the PPO controller in a read-only replay of the 8 PPO-seat trace-0 cells and report `policy_errors()`, or reword line 42 to "no runner-level error; PPO inference errors were not recorded in H6 rows".

2. [minor] `RESULTS-T09.md:44-61`. PROTOCOL H-c (`PROTOCOL.md:29`) requires stale inputs to be 0 for both seats. On H6 they are 21 PPO and 18 baseline. Decision #80 relaxed H-c only for step 1 (the tuning health check) and said to "report" stale inputs on H6. RESULTS reports the counts but never says that H-c is not met as written on H6. QA N1 noted this. It is still open and should get one sentence.

3. [minor] `RESULTS-T09.md:61`. The stale mechanism ("only WAIT is legal after a fall, so the drop costs nothing extra") was probed on the baseline only, in the tuning split (`T09-evaluation-specialist.md:59-61`). It is asserted for the PPO-seat stale inputs in H6-2 MvS, H6-5 MvS, H6-6 SvM and H6-7 SvM without evidence. QA N2 noted this too. It should read "not verified for the PPO seat".

4. [minor] `RESULTS-T09.md:61`. The sentence "13 wins is below 14 either way" does not support "stale counts do not change the verdict". It only says the outcome as recorded is below 14.
   - The stronger fact, which I checked against the stale table (lines 47-59), is that none of the three non-wins has any stale input on either seat: H6-1 MvS, H6-2 SvM and H6-8 SvM all show 0/0. Stale inputs therefore do not explain the shortfall. State that instead.
   - Also say that the claim stays "not shown", not "would have reached 14".

5. [minor] The fall counts (25 vs 37, `RESULTS-T09.md:61`) have no committed tool or artifact. The posture-replay script is not in `tools/eval/` or `evaluation/` (grep for `falling` finds only engine tests), and QA did not re-derive them. I summed the per-cell numbers myself: 25 and 37 are arithmetically right. The "may favour the PPO rival" sentence is hedged, which is acceptable. Either commit the script or label the table "not independently reproduced". The loss cell H6-8 SvM is 3 falls against 3, so falls do not explain it.

6. [minor, omission] `RESULTS-T09.md` does not state the status of PROTOCOL H-a, "wins more than it loses". The Wilson lower bound of 0.57 sits above 0.5, and a reader may take that as a de facto win. State plainly that H-a is not the pre-registered criterion, that no strength claim is made, and that the interval is optimistic with effective n near 8. The text does say "optimistic", but only after the table. The baseline line in `analysis.txt:40` (1W 2D 13L, 0.01-0.28) is also not mirrored in RESULTS. That is fine, but it shows the interval is the complement of the PPO line, not independent evidence.

7. [note, stale doc] `PROTOCOL.md:5-6` still reads "No held-out result exists. T09 runs H6 once", and §4.6 is in the future tense. The brief forbids the evaluator from editing PROTOCOL, so this is for Gate 3. `evaluation/heldout/README.md:33` is still correct.

8. [note] The two draws (H6-1 MvS, H6-2 SvM) are 3600-frame time-ups with hearts 3/3 and 3/2. RESULTS says "no hit decided" but not whether it was a mutual stand-off or avoidance. In H6-1 MvS the metrics show 3566 co-present frames and only 10 distinct cells. This is an interpretation gap, not an error. It would be fairer to say "stalemate; cause not analysed".

9. [note, boundary and separation, no finding]
   - Boundary: the PPO seat sees only the observation (`policy.py:106-122`, `encoder.py:141-199`). A disguised rival appears as `"guard"` in `figures` (`pop/versus.py:1146`), so the `kind == "rival"` feature cannot reveal it. `PolicyMacro.reset(seed)` ignores the seed. The seed key appears in files only as the id `5b5c7582` (ledger, results, `analysis.txt`). On H6 all starts have `disguised` false and hearts 3 (`test_eval_registry.py:206`), so disguise is moot at the start.
   - Separation: `tests/test_eval_registry.py:210-220` asserts that `agents/rl` and `tools/rl` contain neither "heldout", "evaluation/" nor an `evaluation` import. It is a text check only. It cannot show what the weights learned, and no training log is checkable from this tree. `tools/rl/env.py:15` mentions "H6" in a docstring. This is harmless and passes the test, which looks for "heldout" only. The disjointness argument (training starts chosen to avoid H6-1 to H6-4 per #44; H6-5 to H6-8 chosen by a rule that excludes `TUNING_STARTS`) is written in PROTOCOL §3.1. I did not independently re-run it.
   - Ledger: one row, key and commit as stated, `dirty: false`. A claim in the ledger before the first trial rests on code order only, not a timestamp (QA agrees).

**What I checked and found consistent with the evidence**
- Counts and tables against `analysis.txt`: 13W 2D 1L; seat A 7W 1D 0L; seat B 6W 1D 1L; baseline 1W 2D 13L. Sweeps are 5 of 8. The table matches the H6-1 to H6-8 rows. Hearts at the end are plausible, including H6-8 SvM at 0/1 for PPO/baseline.
- Stale per-cell figures sum to 21 PPO (7 per trial) and 18 baseline (6 per trial). I recomputed them from the table.
- The first line of RESULTS gives the verdict and the "does not mean worse" clause as #77 and the brief require. There is no strength claim.
- Each cell has one distinct outcome over its 3 trials, so the conservative counting rule changed nothing.
- Seat/position confound and nearest-figure targeting are stated (lines 65 and 68). Hazard-ahead starts, no guard in room 2 and patrol overlap are stated (lines 66-67). Effective n near 8 is stated (lines 20 and 71).
- The seed-key leak risk is covered: QA checked the files and I saw only the 8-hex id.

**Not checked:** trace-level hidden facts in `seat-*.jsonl` (only that they hold hashes); the full `pop/observation.py` and `pop/versus_runner.py` boundary (relied on T08/T19 reviews; spot-checked `pop/versus.py:1146`); whether `H6.json` was ever read by any training run; fall counts, latency, any H6 run outside this repository's ledger; replay and the suite (cannot run commands; relied on QA); decisions #67 to #73, as instructed.
