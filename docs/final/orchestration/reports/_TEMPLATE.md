---
handoff_id: HO-<TASK-ID>-<role>
task_id: <TASK-ID>
date: <YYYY-MM-DD HH:MM ET>
from: <tech-lead | qa | evaluation-specialist | requirements-auditor>
to: <qa | evaluation-specialist | orchestrator>
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: <docs/final/orchestration/tasks/<TASK-ID>.md@<sha> | reports/<prev>.md@<sha>>
source_branch: <task/<ID> | gate/<ID>-qa | gate/<ID>-eval | audit/<ID>>
source_commit: <sha holding your work; report-only tasks: the base sha. Not this report's own commit (the receiver records that under consumed)>
reviewed_commit: <reviewers: exact sha under review; producers: n/a>
verdict: <ACCEPT | ACCEPT WITH NOTES | REJECT | n/a>
---

# <TASK-ID>: <role> report

Status: <done | partial | blocked>

## Work completed
<3-6 lines. What you did with the consumed handoff.>

## Paths
<files created or changed; evidence files>

## Acceptance criteria → evidence
| # | Criterion (from the brief) | Met? | Evidence |
| --- | --- | --- | --- |

## Tests run
```
<exact command>
<actual result line, copied>
```

## Findings
<[blocker | major | minor | cosmetic] path:line, what is wrong, reproduction, expected vs actual.
Separate reproduced failures from unverified concerns. "No findings" plus what you checked.>

## Known limitations

## Unresolved findings

## Requested next action
<who should do what next, with the path and sha they should read>

## Student decision required
<none, or the question for Saad. Never answer it here.>
