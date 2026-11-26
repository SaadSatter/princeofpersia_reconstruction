---
handoff_id: HO-T08-fix1-qa
task_id: T08-fix1
date: 2026-11-25
from: qa
to: evaluation-specialist
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T08-fix1-tech-lead.md@ea9c786 (brief tasks/T08-fix1.md@49d7840, decisions #64-#66, #74-#78)
source_branch: gate/T08-fix1-qa
source_commit: 0f57d8c
reviewed_commit: ea9c786
verdict: ACCEPT WITH NOTES
---

# T08-fix1: QA report (Gate 1)

Status: done. Reviewed exactly ea9c786 (base 059aea5). No policy ran on H6, the real ledger was never written (none exists after the full suite; `git status` clean), no training, no `--live`, no production edit.

## Work completed
Re-derived the H6-5..H6-8 selection from the written rule with an independent implementation, checked the freeze, disjointness, the #64 ledger and dirty-tree logic (throwaway git repos, CLI with a temp ledger), F-1, F-2, F-4, #65, #76, #77, #75. Added 28 probes (`tests/test_qa_T08fix1_probes.py`, all pass) and made the #78 pin edit.

## Paths
`tests/test_qa_T08fix1_probes.py` (new), `tests/test_qa_T08_probes.py` (one assertion, #78), this report.

## #78 edit (QA's test only)
`tests/test_qa_T08_probes.py::test_a_one_byte_change_is_refused_and_the_real_file_hash_is_the_recorded_one`: old `startswith("44da40ec") and endswith("0847")`, new `startswith("d013152a") and endswith("5266")` (full new H6 SHA-256 `d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266`; the full-hash equality line below it is unchanged and passes). Nothing else touched.

## Acceptance criteria
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Rule committed before starts | met | `1f6fe1e` 00:05:22 precedes `632fc95` 00:13:12; probe `test_the_rule_commit_precedes...`; `select_heldout_starts.py` first appears in 632fc95. Its source reads only the arena, TUNING_STARTS and the scenario files, not results |
| 2 | Starts reproduced from cell lists alone | met | my own re-implementation from the PROTOCOL 3.1 text (not importing the Tech Lead's script) gives H6-5..8 exactly (`test_an_independent_reading...`) |
| 3 | H6-1..4 byte-identical to first freeze | met | `git show 059aea5:H6.json` hashes to `44da40ec...0847`; first four starts equal (probe) |
| 4 | New hash in all three places | met | file, `manifest.HELDOUT_SHA256`, README, PROTOCOL (also named in the superseded note) all `d013152a...5266` |
| 5 | Disjointness | met | cells disjoint from TUNING_STARTS, every tuning start (mirrors included), `arena.STARTS`, H6-1..4, each other; rivals in different rooms; 16 post tuples distinct and not in default or tuning posts; no H6 configuration (either seat order, guard layout) equals a tuning one (3 probes) |
| 6 | #64 key and refusals | met | key is (policy key, commit); second run with changed configs, scenario subset, trials or seed-base is refused and recorded; unknown commit, dirty True and dirty None refused with nothing in the ledger and a later clean run still claims (CLI probes) |
| 7 | F-1 | met | agent fighting in the guard's room credited; other rival downs it while agent is elsewhere not credited (probe). Room presence is an approximation, see N-1 |
| 8 | F-2, F-4 | met | un-xfailed QA probes pass; unknown split, bad JSON, missing dir give exit 2 |
| 9 | #65 mirrors and per-seat analysis | met | each of 11 mirrors is the exact seat swap of its original (rivals, hearts, disguise, guards, forced controller), planned only as SvS/SvM, analysis keeps seats as separate lines (probes); dry run of D1,B2 shows the mirrored rows |
| 10 | #76 B2 | met | disguise on last frame required (`disguise_lost`); no frames is not a success. A mid-way loss regained by the end succeeds (documented "end state decides"); see N-3 |
| 11 | #77 bar, #75 wording | met | PROTOCOL: 14 of 16 and no aborted duel, else "not supported"; "unseen start pairs and guard layouts"; I recomputed the Wilson bounds (16/16 0.806, 14/16 0.64, 13/16 0.57, 12/16 0.505 printed 0.51, 11/16 0.444, 6/6 0.61, 5/6 0.436, 3/3 0.438, 2/3 0.208) and they match |
| 12 | Tests failed first | met | per the brief, tests committed in 4b08daa before the fix 25475a3; the five new files' commit order verified in the log |
| 13 | Scope | met | `git diff --name-only 059aea5..ea9c786`: 23 paths, all permitted; existing-test edits are only the three #78 tests (pinned values) and the three xfail removals |

## Tests run
```
uv run --frozen --extra play --extra train --extra online pytest -q      (on 0f57d8c, clean committed tree)
2 failed, 1601 passed, 11 skipped, 5 xfailed, 2 warnings in 393.95s (0:06:33)
```
The 2 failures are the Evaluation Specialist's, expected under #78 and not touched by me:
`tests/test_eval_T08_gate2.py::test_f3_exposure_of_h6_guard_posts_to_training` (pins exposure (2,1,5) for 4 starts; now 8 starts, 16 posts: 5,1,10) and `::test_h6_has_four_starts_and_two_seat_orders_give_eight_outcomes` (`len == 4`). Skips are the same 11 as the base; xfails are 4 pre-existing plus the QA F-3 strict xfail (still true).

## Findings
| ID | Sev | Finding | Reproduction | Expected |
| --- | --- | --- | --- | --- |
| N-1 | minor | D1 attribution is room presence at the first knocked-down or downed frame, so a trap fall or bystander fall in the agent's room is credited to the agent. Accepted approximation (no striker field); pinned by `test_known_gap_a_guard_downed_by_a_trap...` | probe | note it in the protocol's D1 reading; Eval to judge |
| N-2 | minor | The dirty-tree check counts untracked files only under `evaluation/` and `tools/eval/` (as briefed). Untracked files under `agents/`, `pop/`, and gitignored or skip-worktree files hide a change; an edited `ledger.jsonl`/`refusals.jsonl` is ignored by design. A run can therefore name a commit that is not exactly the engine it ran | `test_known_gap_*` in `tests/test_qa_T08fix1_probes.py` | T09 operator checks `git status --ignored` by hand, or widen to all untracked non-ignored files |
| N-3 | minor | Tests that call the real `git_state` (`test_eval_suite.py::test_a_real_heldout_run_is_claimed_once_per_frozen_policy`, `test_qa_T08_probes.py` ledger-bypass and ledger-line-before-trial) fail on any dirty tracked tree, e.g. `echo >> README.md` then `pytest tests/test_qa_T08_probes.py tests/test_eval_suite.py` gives 3 failed. They are green on a clean checkout (CI) and the suite run left no ledger or refusals file. Fragile for developers; a fix is a monkeypatched `git_state` in those tests (their authors) | as stated | acceptable for gates; note for the orchestrator |
| N-4 | cosmetic | B2 regained disguise counts as success (documented), and a dry-run/aborted B2 row can show `success=True` (e.g. B2-a SvS at a 40-frame cap); analysis counts aborted rows as aborted, so unaffected | dry-run D1,B2 | none |
| N-5 | cosmetic | Wilson 12/16 is 0.505, printed 0.51 | arithmetic | none |
| N-6 | note (documented) | Run-once is a convention: deleting `ledger.jsonl` resets it, no lock, `refusals.jsonl` and `ledger.jsonl` are not gitignored (they are excluded from the dirty check by name, so a refusal cannot block a later run) | n/a | T09 should commit the ledger line before reporting |

No blocker or major. The H6 rule, hash, disjointness and key logic held under every attack I tried.

## For Gate 2 (Evaluation Specialist)
Update your two pinned tests (listed above). Judge the rule's free choices (span widths 2-4, SHA-256 order, facing toward middle); my independent reimplementation confirms they are fully specified by the text. The new rival cells concentrate in rooms 2 and 6 (13 free corridor cells existed), none in rooms 1 or 3.

## Requested next action
Gate 2 on `gate/T08-fix1-qa` (0f57d8c) plus this report's commit.

## Student decision required
none
