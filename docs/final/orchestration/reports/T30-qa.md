---
handoff_id: HO-T30-qa
task_id: T30
date: 2026-11-27 13:15 ET
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T30-tech-lead.md@cb3799b (brief docs/final/orchestration/tasks/T30.md@a293773)
source_branch: gate/T30-qa
source_commit: cb3799be03e1713f705f60896635c15adb1c719b (no tests added; this report is the only change)
reviewed_commit: cb3799be03e1713f705f60896635c15adb1c719b
verdict: ACCEPT WITH NOTES
---

# T30: qa report

Status: done

## Work completed
Read SCOPE_LOCK.md at cb3799b against each of Saad's nine #123 rules (text from `DECISIONS-2026-11-26.md`@a293773). Checked every cited sha, run id and PR against git and GitHub (`gh`, repo SaadSatter/shadow_masque). Ran `tests/test_qa_T08_probes.py` on a clean tree at a293773 and at cb3799b. Diffed old and new SCOPE_LOCK to see what was removed.

## Paths
Only this report. No tests added (docs-only change; nothing to probe in code).

## Acceptance criteria → evidence
Scope: `git diff --name-only a293773 cb3799b` = `docs/final/SCOPE_LOCK.md` and `reports/T30-tech-lead.md`. Within the permitted paths.

| # | Rule (#123) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Stale lines updated with evidence; "only if gates close by Friday" removed | Met, one citation note (N1) | `grep -i friday` finds nothing. Removed rows: "T23-fix1 only if gates close", "CI red until PR #12", "not on main" (old rows in diff). New rows cite 4e20b83 (PR #12, MERGED per `gh pr view 12`), 41550f9 (ancestor of 4e20b83), 271d1ee (ancestor of a293773). Pages run 46040177615: success, push on main, head cb2702b, workflow "Web page (GitHub Pages)". `gh api pages`: build_type workflow, cname shadowmasque.com, status built. DNS: `dig` returns no A or NS records and curl gives 000, so "DNS pending" is true |
| 2 | External playtest pending until Saad conducts it | Met | Limitations row: "still pending until Saad conducts it" |
| 3 | LAN suffices, public server not required, not excluded forever | Met | In-scope LAN row and Out-of-scope row, both citing #123 |
| 4 | PPO retrain, AI RIG_TRAP, movement/scroll, other gameplay moved to "Deferred: may be reconsidered before Gold on external-playtest findings or evaluation evidence, with Saad's approval"; #118 freeze kept | Met | Section title matches verbatim. Four rows present. Removed from Out of scope (old rows gone from diff). Freeze section keeps #118 |
| 5 | Telemetry/BI agent as possible third G4 role | Met | Section "Possible third production role for G4"; old exclusion row removed |
| 6 | T09 result exactly; threshold unchanged | Met | Row reads "13 W, 2 D, 1 L of 16 held-out duels, bar 14, "NOT SUPPORTED" (#77)", plus "The threshold was not changed after the result (#123)". Numbers identical to the old row |
| 7 | Hosted frontend distinct from LAN server | Met | In-scope rows and the devtools limitation row state the static page runs the engine in the browser and the LAN server owns the only `GameState` |
| 8 | Header baseline line (`main` 271d1ee or later) | Met | "Scope baseline (decision #123)" paragraph. 271d1ee is on main (ancestor of a293773) |
| 9 | "Draft, not approved by Saad" and blank approval line kept; nothing in Saad's voice except quoting #123 | Met | Both lines present and unchanged. The text paraphrases #123 in the third person and does not quote him. The Deferred paragraph says "Decision #123: these are deferred, not excluded", a paraphrase attributed by number, not a quotation |
| – | Every line cites a decision or a commit; no claim without a source checked on main | Met with N1, N2 | See notes |

## Tests run
```
git switch --detach a293773 ; uv run --frozen --extra train --extra online pytest -q tests/test_qa_T08_probes.py
14 passed, 1 xfailed in 0.99s        (load average 2.3, clean tree)
git switch gate/T30-qa (cb3799b) ; same command
14 passed, 1 xfailed in 1.12s        (load average 2.3, clean tree)
uv run --frozen --extra train --extra online pytest -q tests/test_eval_*.py tests/test_qa_T08*.py tests/test_gate_w3_*.py
390 passed, 2 xfailed, 6 warnings in 175.65s (0:02:55)
```
Run sequentially. Another agent's `python -m server` process was idle on this machine; load average stayed 2.3 to 2.4. I did not run the full 8 minute suite.

## Findings
No blocker or major. Reproduced facts:

- [minor] N1. `docs/final/SCOPE_LOCK.md`, row "Deterministic CI green on `main`": it says "CI run 46038977033 succeeded on `main` 271d1ee". That run was `workflow_dispatch` on branch `orch/pr13-merge` (`headSha` 271d1ee), not a push on `main`. The sha is right, the branch is not. Push runs of "Deterministic checks (dev)" on `main`: 46040129893 success at 271d1ee, 46040177624 success at cb2702b, 1a9b513 run 46044444723 success. The push run for 4e20b83 itself (46038648957) was **cancelled**, so "green at the 4e20b83 merge" rests on the PR checks at 41550f9 (run 45802226460, success) and the later runs. Suggested fix: cite 46040129893. The Tech Lead copied the id from REVIEW_LOG line 270 and did not query it, as the handoff said. REVIEW_LOG itself says "CI 46038977033 success on 271d1ee", which is accurate.
- [cosmetic] N2. Current `main` runs: a293773 cancelled (46045212107), then 6f1b42b and acfc462 in progress when I looked. "CI green on main" is true at the last completed push run (1a9b513, 7c4fc1d). Say "green at 271d1ee and 1a9b513" if you want it exact.
- [cosmetic] N3. The Freeze row "T23-fix1 landed before the freeze (PR #12)": supported by #118 and REVIEW_LOG line 266 (T23 closed, 41550f9), and 41550f9 is an ancestor of 4e20b83. No change needed.

### The 3 failures in tests/test_qa_T08_probes.py
Not reproduced. The file passes (14 passed, 1 xfailed) at both a293773 and cb3799b, in a fresh `.venv`, on an otherwise idle tree, so the diff cannot be the cause (one markdown file, no import of it by any test I ran). Also passes alongside the other eval and gate tests (390 passed). The tests that failed for the Tech Lead (`cli.main` returned 2 where 0 was expected; "DID NOT RAISE KeyboardInterrupt") are the held-out ledger tests, which patch `manifest.LEDGER_PATH` to a tmp path. A return of 2 means the CLI refused the held-out run before trial one. My evidence does not say why. It is not caused by this change. The most likely causes are an order dependence inside the full suite, or load and state in the Tech Lead's fresh worktree. Classification: not reproducible here; not pre-existing in isolation and not caused by T30. If you want it settled, run the full suite once on main (about 8 minutes) and see whether it recurs.

## Known limitations
Only SCOPE_LOCK.md was reviewed for wording against #123. I did not re-verify every decision number (#35 to #57 and similar) against the decision files, only those #123 introduces or the changed rows rely on (#77, #118, #119, #123, #43, #69).

## Not checked
The full 8 minute suite (not meaningful for a docs-only diff); the playwright smoke test (no web change); decision numbers in rows that T30 did not touch.

## Unresolved findings
N1 (minor) and N2 (cosmetic) above, for the Tech Lead or orchestrator to fix before showing Saad. The 3 unreproduced failures.

## Requested next action
Orchestrator: have N1 corrected (cite run 46040129893) or accept as is, then show Saad `docs/final/SCOPE_LOCK.md` at the final sha. No PR and no copy into PR #2 until he approves.

## Student decision required
Saad's approval of the scope lock. Not answered here.
