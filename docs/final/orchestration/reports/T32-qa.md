---
handoff_id: HO-T32-qa
task_id: T32
date: 2026-11-27
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/T32-tech-lead.md@04f6eb8
source_branch: gate/T32-qa
source_commit: see git log (this report's commit)
reviewed_commit: 04f6eb8
verdict: ACCEPT WITH NOTES
---

# T32: QA report

Note: the Tech Lead report's own header says `source_commit: 2fc9097`; the
reviewed head 04f6eb8 is 2fc9097 plus the report file only
(`git diff 2fc9097 04f6eb8 --stat`: one file, the report). Playtest diff is identical.

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | `git diff` shows only status lines and the one consent-sentence move | Yes | `git diff 04a2849 04f6eb8 --name-only`: the four permitted playtest files plus the T32 report. Hunks read in full: PROTOCOL.md, LOG.md header and version row, TELEMETRY.md header and closing pointer, CONSENT.md status line, option (b) text, and the draft section. No hypothesis, definition, script or question text changed. |

## Facts you asked me to verify
- Only status lines: yes, with two caveats below.
  - PROTOCOL.md: the old status paragraph also said "Saad approves ... before any session. After approval the definitions are frozen: a change after a session is a new protocol version, recorded in LOG.md". The new status line keeps the freeze and the "new version recorded in LOG.md with its date and reason" rule; the "approves ... before any session" clause is dropped, which is correct now. Still status text.
  - LOG.md: the "Proposal for Saad ... not approved" sentence in the header blockquote is now "Status: Approved ...". The rest of the blockquote ("Saad decides the format, writes or approves the hypotheses...") is kept.
  - TELEMETRY.md: header status and the closing "Draft for CONSENT.md" pointer only (the heading "Draft for CONSENT.md" itself was left as is; cosmetic).
- LOG.md version-table cell: "0 (draft, T11)" -> "0 (T11)" and "Approved by Saad (date)" cell "not yet" -> "2026-11-27 (decision #126)". Both are status cells (version label and approval date), not a hypothesis, definition or question. Acceptable. The "Change" cell ("Initial kit") and "Sessions run under it" ("none") are unchanged.
- Consent sentence move: the sentence now at the end of option (b) in CONSENT.md ("The file lists each game action you take, which room you are in, when you are hurt, when you pause or leave, and how the round ended, with the time of each. It does not contain your name, any address or anything about the other player that your own screen did not show you.") is word for word the draft at 04a2849 (read both; only the leading "**(b)** ..." was dropped and the line wrapping changed). The original sentence "It contains no name and no audio or video." stays in place, so option (b) now says "no name" twice. This is the Tech Lead's append choice and matches "exactly as drafted"; Saad may want to know the redundancy. Source is noted in the replaced section.

## Held-out ledger failures (tests/test_eval_suite.py, tests/test_qa_T08_probes.py)
Clean tree, `uv run --all-extras pytest -q -rf tests/test_eval_suite.py tests/test_qa_T08_probes.py`:
- 04a2849: `39 passed, 1 xfailed in 10.85s`
- 04f6eb8: `39 passed, 1 xfailed in 11.21s`
Not reproduced at either commit; identical results. The three failures the Tech Lead saw are not caused by this diff (docs only). Likely cause is state in their working tree (an existing held-out ledger/claim file, or a long full run), not verified; I did not have their tree.

## Other checks
- `uv run --all-extras pytest -q -k "playtest or consent or telemetry"` at 04f6eb8: `46 passed, 1 skipped, 2351 deselected in 39.24s`.
- I did not run the full suite (docs-only diff; the two named files and the playtest tests cover it).

## Findings
- minor (scope, already raised by Tech Lead): `docs/final/playtest/QUESTIONNAIRE.md` and `OBSERVATION_TEMPLATE.md` still carry "draft kit (T11)" status lines (not in T32's permitted paths), so the kit now reads as partly draft. Needs a follow-up task or permission. Confirmed they were not touched.
- cosmetic: TELEMETRY.md still has the heading "Draft for CONSENT.md" above the approved text.
- cosmetic: "no name" appears twice in option (b) of the read-aloud text.

## Not checked
Full suite, CI files (no change), Gate 2 (n/a). Cause of the Tech Lead's three failures.

## Student decision required
none
