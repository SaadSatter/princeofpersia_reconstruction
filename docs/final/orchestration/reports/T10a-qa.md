---
handoff_id: HO-T10a-qa
task_id: T10a
date: 2026-11-24 ET
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T10a-tech-lead.md@7faccc0
source_branch: gate/T10a-qa
source_commit: 7faccc007223fbf2645496a863d9b13913665c90 (no tests added; docs-only task; this report is the only change)
reviewed_commit: 7faccc007223fbf2645496a863d9b13913665c90 (work commit 4b0f1ba)
verdict: ACCEPT WITH NOTES
---

# T10a: qa report

Status: done

## Work completed
Read the brief (96a334b), the Tech Lead report, the decisions #1-#30, STATUS.md, COURSE_ROLE_MAP.md and the full diff 96a334b..7faccc0. Fact-checked every Changes row, A0 and B0 row, OQ/CQ edit, checklist and plan edit against the decision files, `agent-config.json`, and `origin/orch/preview` (`RL_POLICY.md`, `MACROS.md`, `TRAPS_SPEC.md`, `RULE_SOURCE_MAP.md`, `agents/rl/encoder.py`). Ran the link check and the suite. No tests added (docs only).

## Paths
`docs/final/orchestration/reports/T10a-qa.md` only.

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Dated Changes section atop GDD and CONFIGURATION, one line per change with source, G1 text kept, inline markers | Met | Both files open with the section (GDD l.9, CONFIGURATION top). Every row cites a decision or commit. The diff deletes G1 text only where a marked replacement keeps it (OQ-3, OQ-6, OQ-11, CQ rows keep "G1 text"/"G1 proposal"; CQ "needed by" dates preserved in a paragraph). One G1 phrase lost: GDD Section 2 Session row "about 5 minutes (OQ-3)" became "5 minutes = 3,600 frames" with no marker (trivial) |
| 2 | Part A: PPO rival fully described, Haiku legacy, honest status | Met, one error inherited from the source doc (F2) | A0 rows match `RL_POLICY.md`, `MACROS.md` and `agent-config.json` (MLP 2x64 tanh, masked softmax, `sm-ppo-mlp-1`, SHA-256 `load_net`, 5,100 s cap, cadence 6/4, WAIT fallback, nearest-figure target, no weights, training not started). Status labels agree with STATUS.md (preview / WIP / none on main) |
| 3 | Part B current agents, links, no over-counting of formal roles | Met | B0 matches `COURSE_ROLE_MAP.md` (orchestrator No; evaluation-specialist No; requirements-auditor No; rules-reviewer part of QA check; tech/qa Yes once `agent-team/roles` exist). The six `.claude/agents/*.md` files exist on main. Models match `agent-config.json` and STATUS |
| 4 | Closed items marked with decision numbers; open ones stay open | Met | OQ-3 (#5), OQ-6 (#22), OQ-11 (#12, #25), CQ-1 (#23), CQ-7 (see ruling 1), CQ-3 partly (#24). OQ-7, OQ-9, OQ-10 (server), OQ-12, OQ-13, CQ-2, CQ-4, CQ-5, CQ-6 stay open; every STATUS "Waiting on Saad" design item (B2 threshold, D1 "on screen", trap 1 heart, cadence 4, nearest-figure target, reward defaults, CLIMB down, Student decision, official-repo move) is written as waiting, none chosen |
| 5 | Checklist decisions in force, no status raised; plan note and risk updates; README links | Met | Checklist: one row moved "not started" to "in progress" ("Update GDD and Configuration Document"), which is true of this very task and still pending QA/merge (not a raise on unevidenced work; see note N2). Plan: current-plan note points to PLAN-v2 and v3-delta, original rows kept, new risk table. README links orchestration and `agent-config.json`, "CLAUDE.md (implementation agent)" gone |
| 6 | No new design decision; nothing in Saad's voice | Met | No new numbers or choices found. The "+3 per frame", "12-frame kneel", "gate slam 1 heart" values are #22 plus `TRAPS_SPEC.md` ("the spec's other recommended options stand"). No sentence in Saad's voice |
| 7 | Every claim traceable; contradictions in the report | Met | Each row cites #n, a file or a commit. Tech Lead report lists ten unresolved items |

## Tests run
```
uv run pytest -q
435 passed, 12 skipped in 5.07s
```
Link check (script over the five files, every `](relative)` target resolved from `docs/final/`): `broken 0`. `git diff --name-only 96a334b..7faccc0`: the five permitted docs plus the Tech Lead report. `EVIDENCE_INDEX.md`, `AGENT-TEAM.md`, `README.md`, code and tests untouched.

## Rulings on the Tech Lead's judgment calls
1. **CQ-7 closed by commit 2d40972, no Saad decision.** Accept the wording. The question ("whether to add") is answered by fact, and the cell says no decision records Saad's confirmation. It does not pre-empt him. Keep it on the list for Saad to confirm in his next batch.
2. **OQ-6 closed by #22.** Accept. #22 ("Accept recommendations") adopts `TRAPS_SPEC.md`, whose recommended option is one-shot (section 4, "one-shot (recommended)"; header line 4 "one-shot"). The G1 number list is untouched.
3. **OQ-9 kept open.** Accept; only the 4 s figure is marked superseded.
4. **CQ-2 reframed, not closed.** Accept; consistent with `RL_POLICY.md` "Open items" (feature set approval).
5. **#19 and +48 per hop not re-verified in code.** Accept. #18 verbatim says "+6 per frame on each of the 8 hop frames; three hops ... break the disguise", and `RULE_SOURCE_MAP.md` R-V24 on `orch/preview` says +6 per frame. Eight times six is 48. The claim "three hops break" is the decision text, not re-run.
6. **No live URL.** Accept. Nothing on record; the wording is correct.
7. **959 passed not copied.** Accept.
8. **Engine-decision line unchanged.** Accept; no decision on it exists.
9. **EVIDENCE_INDEX.md untouched.** Accept (forbidden by the brief). Follow-up for the orchestrator after Saad commits his edits.
10. **GDD Sections 6 and 7 and Section 4 labels left unmarked.** Do not accept as is: see F1.

## Findings
Reproduced by reading the files; nothing here is a runtime failure.

- **F1 [minor] `docs/final/GDD.md` Sections 6 and 7 (l.147-160)** are not marked superseded. Section 6 says "each browser ... the server validates them"; Section 7 says "The browser never holds the `GameState`, the other seat's observation or the arena layout". Under #12 the engine runs in the browser through Pyodide, so for the hosted build the browser does hold the state (the Plan risk note and `agent-config.json` "limitations" say so, the GDD does not). Section 4 "Planned" labels (disguise, sword, traps, guard rule) are also stale against `orch/reviewed`. Expected: a one-line `[Superseded ... #1, #12]` marker on Sections 6 and 7, and the devtools exposure added to the Changes "Platform" row. Needed so a reader of Section 7 is not told something the decided design contradicts. Not a blocker for the doc task but should be fixed before the PR is merged.
- **F2 [minor] `docs/final/CONFIGURATION.md` A0 "Knowledge boundary"** repeats "251 features ... the seat's own state (19)". Group counts 150+2+19+2+4+60+15 sum to 252. The code (`agents/rl/encoder.py` `_names()` on `orch/preview`) gives me = 3+4+2+4+5 = 18, total 251. So 251 is right and "19" is wrong. The error is inherited from `RL_POLICY.md` (table "Me | 19"), which is not in T10a scope. Expected: write 18 (or drop the per-group counts), and tell the Tech Lead of T07 about the source doc.
- **F3 [cosmetic] GDD `Session` row** loses the G1 phrase "about 5 minutes (OQ-3)" without a marker (see criterion 1).

Unverified concerns: the claims about `orch/preview` heads and "review pending" follow STATUS.md, which I did not re-derive; I did not run any `orch/preview` code or tests.

## Notes (not findings)
- N1. The Changes tables are long; each row is one line and sourced, which meets the brief. Saad may want to read the "Where it lives" column first.
- N2. The checklist status "in progress" for the GDD update is true but self-referential; the orchestrator should keep it until the PR merges.
- N3. Nothing in the diff decides an item from STATUS "Waiting on Saad".

## Known limitations
No code or branch behaviour was executed except `uv run pytest -q` on the base-equivalent tree. I read `orch/preview` files with `git show`, not a checkout.

## Not checked
`EVIDENCE_INDEX.md` accuracy (out of scope). The official course repository. Whether `agent-config.json` content matches the course schema.

## Requested next action
Orchestrator: return F1 and F2 to the Tech Lead (T10a-fix1, docs only) or accept the notes and have Saad merge with them recorded; Gate 3 is yours. Gate 2 not required.

## Student decision required
None.
