# Week 7 pair audit preparation — October 26, 2026

README-only rehearsal used a fresh archive of committed development source plus
only the new README, audit CLI and its tests, with a new Python 3.12.14 virtual
environment and `uv sync --frozen --extra model --python 3.12`. No graphics or
artwork were needed. README shell blocks were extracted and executed directly.
The timed command portion took 4.56 seconds excluding installation, browser CI
inspection and the blocked credential entry. This is a simulated timed audit,
not evidence of an actual classmate playtest or a completed live-model audit.

| Checklist row | Result | Evidence |
| --- | --- | --- |
| Reset declared S1 seed 0 | Ran | initial observation returned |
| Observe without hidden information | Ran | current-room observation; existing leakage tests pass |
| Legal list, illegal action, unchanged world | Ran | false/unknown action; unchanged observation and frames; test snapshots entire Game; refusal counter intentionally increments |
| Step one legal action | Ran | RIGHT accepted |
| Explicit terminal outcome | Ran | won, score 1, 12 actions, one invalid action |
| Complete heuristic baseline | Ran | won, 8 actions, 0 model calls; new audit JSONL |
| Live Anthropic episode and trace | Did not run | no ANTHROPIC_API_KEY in execution environment; exit 2 before episode; trace reader correctly reports no live trace |
| Latest course midterm CI | Ran | GitHub API: PR-head 85b8fdbe8b77c86ba5fb4027974e38cffd51fb75; midterm run 40409664334 successful before this transfer; README explains checking newest run against head |

Fresh-environment targeted checks: 34 passed. Full suite: 199 passed, 4 skipped
(optional graphics/assets absent). No failed call or historical trace is
presented as a successful live model run. The student must securely configure
credentials and run the two documented live blocks before calling that row done.

The transfer also includes the pre-existing S3 crash fix f9c2c14 and its
regression/replay tests, already committed before this session. No frozen
scenario, existing result, prompt, baseline or artwork was changed for the audit.
CI status after transfer is reported in the chat with the new commit/run links.
