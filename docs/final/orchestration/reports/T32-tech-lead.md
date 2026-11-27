---
handoff_id: HO-T32-tech-lead
task_id: T32
date: 2026-11-27
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T32.md@04a2849
source_branch: task/T32
source_commit: 2fc9097
reviewed_commit: n/a
verdict: n/a
---

# T32: tech-lead report

Status: done (one scope note and 3 unrelated suite failures, below)

## Work completed
Replaced the draft/unapproved status lines in PROTOCOL.md, CONSENT.md, LOG.md and TELEMETRY.md with "Approved by Saad 2026-11-27 (decision #126); frozen from this date — a change is a new version". Moved the telemetry sentence from CONSENT.md's "Draft addition for option (b)" section (drafted in T20, TELEMETRY.md "Draft for CONSENT.md") into the read-aloud option (b) text, and replaced the draft section with a short note giving the source. TELEMETRY.md's closing pointer now says the sentence is in the consent text.

## Paths
docs/final/playtest/{PROTOCOL,CONSENT,LOG,TELEMETRY}.md

## Acceptance criteria → evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | git diff shows only status lines and the one consent-sentence move | Yes | `git diff 04a2849..2fc9097 --stat`: 4 files under docs/final/playtest |

## Tests run
```
uv run pytest -q   -> 13 collection errors (No module named numpy; train extra not installed)
uv run --all-extras pytest -q -rf
3 failed, 2380 passed, 10 skipped, 5 xfailed, 2 warnings in 501.96s (0:08:21)
```
Failures: tests/test_eval_suite.py::test_a_real_heldout_run_is_claimed_once_per_frozen_policy, tests/test_qa_T08_probes.py::test_the_ledger_is_not_bypassed_by_seed_key_scenario_subset_trials_or_seed_base, tests/test_qa_T08_probes.py::test_the_ledger_line_is_written_before_the_first_trial. All three are held-out ledger tests (the CLI returns exit 2 where 0 is expected). My diff touches only docs/final/playtest. I did not run them on the base to confirm they fail there (unverified; likely environment). Playtest/consent/telemetry tests (-k filter) passed: 63 passed.

## Findings
- Judgement calls: (1) LOG.md protocol-versions row "Approved by Saad: not yet" now reads "2026-11-27 (decision #126)" and "0 (draft, T11)" is "0 (T11)"; it is a status cell, QA may check. (2) The consent sentence is appended to option (b) without the leading "(b) ..." ellipsis, otherwise word for word. (3) Section heading renamed "Telemetry sentence for option (b)".
- Scope: QUESTIONNAIRE.md and OBSERVATION_TEMPLATE.md also carry "Status: draft kit (T11)" lines, but they are not in the permitted paths, so I left them. They need a follow-up task or permission.

## Known limitations
See the scope note above.

## Unresolved findings
The 3 failing tests above.

## Requested next action
Commit to review: 2fc9097 on task/T32
What changed: status lines now say approved and frozen; the telemetry sentence is now in the read-aloud consent text. No hypothesis, definition, script, question or other consent wording changed.
How to check it: `git diff 04a2849..2fc9097 -- docs/final/playtest`
What I am unsure about: the LOG.md version-table cell; the two out-of-scope status lines; the 3 unrelated failures.
Touches the knowledge boundary or AI seat: no (Gate 2 does not apply)

## Student decision required
none
