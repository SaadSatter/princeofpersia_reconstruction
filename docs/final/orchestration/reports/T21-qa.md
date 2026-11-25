---
handoff_id: HO-T21-qa
task_id: T21
date: 2026-11-25
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T21-tech-lead.md@f603c57 (work 2081398)
coordination_commit: 71bc3fb47b9bcfb3b215b220d8b01754a96191ad (origin/main tip, brief tasks/T21.md)
source_branch: gate/T21-qa
source_commit: the commit that holds this file
reviewed_commit: f603c57eb6c11431bd3de2bd5265b53e54c677f6
verdict: ACCEPT WITH NOTES
---

# T21: QA report (Gate 1: facts, paths, permissions)

Status: done. No tests added: the change is docs and agent definitions, and the
checks are file and number comparisons. No production code touched.

## Verdict
ACCEPT WITH NOTES. Every acceptance criterion is met. No blocker or major
finding. Three minor and two cosmetic notes below.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Definition loads: frontmatter valid, name, model pinned, no Agent tool | yes (parsed; not loaded by a live agent) | `.claude/agents/telemetry-analyst.md` keys: name, description, model, tools, isolation, color. `name: telemetry-analyst`, `model: claude-sonnet-5-5`, `tools: Read, Grep, Glob, Bash, Write`. Same key set and body shape as `qa.md` and `requirements-auditor.md` on main. It has no `Edit` (qa has it), which suits a report-only worker |
| 2 | Write permission is its own report only | met by instruction only | Definition: "You write nothing else". Procedure section 4: "Your write permission is your report path only"; section 5 scope check. See "Permission assessment" |
| 3 | All role tables agree | yes | "Role tables" below |
| 4 | Suite green | yes | `uv run --frozen --extra play --extra train --extra online pytest -q` on the clean tree at f603c57: `1952 passed, 11 skipped, 5 xfailed, 2 warnings in 476.97s (0:07:56)` |
| 5 | Procedure carries the four T20-fix2 reading notes | yes | Procedure section 2, "How to read the summary": flip counts jump starts; zero-gap DRAW then SHEATHE reads as one hold; pre-fix2 logs undercount block/flip/draw/sheathe and are never pooled; AI duels summarize the human seat only. Matches `reports/T20-fix2-evaluation-specialist.md` |
| 6 | Finding fields, label, bans | yes | Section 3 table: kind, what, where, how many, evidence (file:lines), confidence. "counted from logs" required on every number. Section 4 bans: interpreting for Saad, LOG.md section 6 and Saad-voiced files, game code/tests/tools, re-identification (player codes only from Saad's sheet), plus handing logs back, quoting consent, pooling seats' hidden info, paid calls |
| 7 | Dry run matches the summarizer | yes, with notes | "Dry run" below |
| 8 | Paths and links | yes, with a note | "Paths and links" below |

## Permission assessment (item 2)
`Write` and `Bash` cannot be confined to one path by the tool list. Worktree
isolation sets the default cwd; it does not stop Bash writing to an absolute
path. So the limit rests on the definition, the procedure (stated twice, plus a
`git diff --name-only <base>..HEAD` self-check) and the orchestrator.
That is adequate for a worker whose only output is reviewed before use, but the
orchestrator link is weak as written: the "Analyst findings" paragraph
(orchestrator.md section 5) checks findings against the Playtest Log and does
not check scope. Tighten, in this order:

1. (recommended) In that paragraph, before relaying, run
   `git diff --name-only <base>..audit/<ID>-telemetry` and require exactly
   `docs/final/orchestration/reports/<ID>-telemetry-analyst.md`. Any other path
   is rejected. This is the one control that does not depend on the analyst
   obeying text.
2. (optional) Also require an empty `git status --short` in its worktree after
   the commit, and that nothing under `docs/final/playtest/` changed during the
   run.
3. (optional) The `*-host.json` and LOG.md section 6 bans are instruction-only
   (Read and Bash can open them). Keep the host file out of the log directory
   named in the brief.

Not a reason to reject: the tool list is as tight as the tasks allow (Bash is
needed for the summarizer and git).

## Role tables (item 4)
`git diff origin/main f603c57 -- <file>` for each of the five files shows only
new rows or inserted names:
- `CLAUDE.md`: `telemetry-analyst` in the named-worker list, and a new
  "Telemetry Analyst" row in the Roles table. Nothing else.
- `docs/final/orchestration/README.md`: one agents-table row.
- `docs/final/orchestration/agents/orchestrator.md`: a routing row, a worker-table
  row, a branch-table row (`audit/<ID>-telemetry`) and the "Analyst findings"
  paragraph in section 5 (Gates).
- `.claude/agents/orchestrator.md`: the name in `description`, in the `Agent(...)`
  list and in the spawnable list.
- `docs/final/orchestration/COURSE_ROLE_MAP.md`: one row ("not a formal
  production agent (decision #69)") and the name in the `team-` collision note.
Names, paths and model agree across the five files and the two new files. The
brief said "section 4 or 5" for the not-confirmed rule; it is in section 5 and
the analyst procedure's pointer ("section 5") is correct.
The whole-tree `git diff origin/main f603c57` is large because `task/T21` is
based on `orch/reviewed` (72066f1), which differs widely from main. Only these
five files were taken from main. Expected.

## Dry run (item 5)
Regenerated with `python3 tools/telemetry/summarize.py tests/data/t20_telemetry
--out <scratchpad>` twice: `summary.json` byte-identical (`cmp`). Compared every
number and cited line with the summary and the raw files (counted from logs).
5 seat logs, 3 duels, all schema 1, build `fixture`, rival human: correct.
`v2/` is not read by the summarizer (not recursive): correct.
- S1 7.167 s idle, `ABCD-001-A:9-11`, ticks 14 to 100: correct.
- S2 83.333 s (002-A), 83.333 s (002-B), 66.667 s (001-B), lines 2-5, 2-5, 2-9;
  3 of 5 seat logs, 2 of 3 duels: correct.
- Q1 disconnect tick 500, forfeit tick 1000, `002-B:3-5`, `002-A:4-5`: correct.
- Q2 disconnect 400, reconnect 430 (line 7), rematch false at 800, A true at
  `001-A:17`: correct.
- Q3 abandoned at tick 100, `EFGH-001-A:3`: correct.
- M1 to M3 counts (TAKE, RIG, flip, block, draw 1 each; sheathe, sword_pickup,
  throw, kick, sweep 0; two seats with no mechanic): correct.
No numeric error. N1 and N2 below concern citation quality.

## Paths and links (item 6)
All 9 paths changed by 2081398 exist at f603c57, and so does the tech-lead
report. Backticked paths in the new docs resolve, with one note: the
procedure's `../HANDOFF_PROTOCOL.md` and `../reports/_TEMPLATE.md` exist on
`main` but not on this base (`orch/reviewed` also lacks `agents/qa.md`). They
resolve once merged into a tree with main's records. `docs/final/playtest/LOG.md`
(facts sections 2 to 5, section 6 Saad's), `TELEMETRY.md`,
`tools/telemetry/summarize.py`, `tests/data/t20_telemetry/` and
`reports/T20-fix2-evaluation-specialist.md` exist and the LOG.md headings match
the procedure's reading of them.

## Findings
| ID | Sev | Where | What | Reproduce | Expected vs actual |
| --- | --- | --- | --- | --- | --- |
| N1 | minor | `reports/T21-dryrun-telemetry-analyst.md` M1 | Cites the summary's "Never used" line for "sheathe, sword pickup, throw, kick, sweep". That line lists only sheathe and sword_pickup; throw, kick, sweep are 0 only in the mechanics table. M1 gives no file:line, which the procedure requires | `python3 tools/telemetry/summarize.py tests/data/t20_telemetry --out <dir>`; read `summary.md` | cite the table rows for throw, kick, sweep |
| N2 | minor | same file, M2 | Lines given for TAKE (`001-A:10`) and RIG (`002-A:3`) only. flip (`001-B:3`), block (`001-B:4`) and draw (`001-A:8`) have none | `cat -n tests/data/t20_telemetry/*.jsonl` | exact lines for each of the five |
| N3 | minor | orchestrator.md section 5 | The analyst check has no scope check (see Permission assessment) | n/a | add the `git diff --name-only` check |
| N4 | cosmetic | `.claude/agents/orchestrator.md`, `COURSE_ROLE_MAP.md` | Inserted names push two lines past the usual wrap | read the diff | rewrap |
| N5 | cosmetic | dry-run S2 | The ABCD-002 disconnect is in `002-B.jsonl:3`; `002-A.jsonl` shows only the forfeit. The row is duel-level, so it is right, but name the file | `002-A.jsonl:4` | say "disconnect in 002-B" |

Unverified (not reproduced): (a) a restarted session accepts the new `Agent(...)`
entry; (b) the definition loads in a live spawn. The first real run is the test.

## Not checked
- A live spawn of the agent (the type exists only after a session restart).
- Playwright and CI workflows: nothing under `.github/` or `ci/` changed in T21.
  Differences to `origin/main` there come from the base branch.
- Gate 2 does not apply (no game or AI code).

## Requested next action
Orchestrator: Gate 3. Ask for N1 to N3 as a short Tech Lead fix, or accept the
notes. When merging `task/T21` into a branch based on `orch/reviewed`, check
that only the new analyst files and the rows above enter.

## Student decision required
None.
