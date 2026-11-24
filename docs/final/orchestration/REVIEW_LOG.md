# Review log

One line per review gate (see `README.md`, "The feature cycle and its review gates").
A task is closed only when its Gate 3 line says `closed`.

| Date | Task | Gate | Reviewer | Commit | Verdict | Evidence | Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-23 | T11 | Gate 3 (pre) | orchestrator | e47c996 | paths OK | `git diff --name-only` only docs/final/playtest/ | awaits Gate 1 fact-check (GATE-T01-qa) |
| 2026-11-23 | T04 | Gate 3 (pre) | orchestrator | af76c30 | tests reproduce | 457 passed, 12 skipped; only new files | awaits GATE-T04 qa + eval |
| 2026-11-23 | T01+T04+T11 | integration trial | orchestrator | 83127cf + af76c30 + e47c996 | 1 failure | `tests/test_versus_runner.py::test_controller_gets_only_plain_copies_of_its_own_seat`: `minutes_left` 0 vs 5 — the test's comparison episode uses a different duel limit; exposed by T01's per-duel clock. F1 probe EQUAL on merge | corrective T04-fix1 (Tech Lead) after gate reports |
| 2026-11-23 | T02 | Gate 3 | orchestrator | f8583d6 | accepted as review | 447 passed, 12 skipped, 5 xfailed reproduced in merge trial; handoff draft has empty Student decision | Saad writes decision; QA removes xfails after T01 Gate 1 |
| 2026-11-23 | T01 vs T02 | cross-check | orchestrator | 83127cf + f8583d6 | T01 closes F1, F2, F2b | 5 T02 strict xfails XPASS on merge | close loop after GATE-T01 |
| 2026-11-23 | T04 | Gate 1 | QA (GATE-T04-qa) | af76c30 | ACCEPT WITH NOTES | gate/T04-qa ea165f3; 468 passed, 12 skipped, 5 xfailed | T04-fix1 |
| 2026-11-23 | T04 | Gate 2 | Evaluation Specialist (GATE-T04-eval) | af76c30 | ACCEPT WITH NOTES | gate/T04-eval eab92a5; 465 passed, 12 skipped, 4 xfailed | T04-fix1 |
| 2026-11-23 | T01 | Gate 1 | QA (GATE-T01-qa) | 83127cf | ACCEPT WITH NOTES | gate/T01-qa 68f58dc; 520 passed, 12 skipped, 3 xfailed; T02 xfails XPASS | T01-fix1 |
| 2026-11-23 | T01 | Gate 2 | Evaluation Specialist (GATE-T01-eval) | 83127cf | ACCEPT WITH NOTES | gate/T01-eval 865f597; 518 passed, 12 skipped, 2 xfailed; L1, L2 | T01-fix1 |
| 2026-11-23 | T11 | Gate 1 | QA (GATE-T01-qa) | e47c996 | ACCEPT WITH NOTES | consent promises a log the build does not write | T11-fix1 |
| 2026-11-23 | T11-fix1 | Gate 3 (pre) | orchestrator | 046599d | paths OK | docs/final/playtest only | Gate 1 batched with T01-fix1 |
| 2026-11-23 | T14 | Gate 2 | Evaluation Specialist (Sonnet) | e6c274d | ACCEPT WITH NOTES | gate/T14-eval 8de230a; no payload leak | T14-fix1 after QA gate |
| 2026-11-23 | T05 | Gate 2 | Evaluation Specialist (Sonnet) | 19b5da2 | ACCEPT WITH NOTES (blocking gap for evaluation) | no descent macro; lone-guard rule | T05-fix1; T07 full training paused |
| 2026-11-23 | T14 | Gate 1 | QA (Sonnet) | e6c274d | ACCEPT WITH NOTES | gate/T14-qa 9499a4e; adapter missing | T14-fix1 |
| 2026-11-24 | T01 chain (T01, T01-fix1, T01-fix2) | Gate 1+2 | QA / Eval (Sonnet) | cd5c4aa | ACCEPT WITH NOTES / ACCEPT | gate/w2-qa b56e573, gate/w2-eval d2e7a00 | closed at Gate 3 (orchestrator re-ran int/wave2: 775 passed, 12 skipped, 3 xfailed); note wording fix |
| 2026-11-24 | T04 chain (T04, fix1, fix2) | Gate 1+2 | QA / Eval (Sonnet) | cd5c4aa | ACCEPT WITH NOTES | concurrent-start busy race (minor) | T04-fix3 (QA-5 refuse, in-flight flag); otherwise closed |
| 2026-11-24 | T05 | Gate 1 | QA (Sonnet) | 19b5da2 | ACCEPT WITH NOTES | gate/T05-qa dec85c8; 3 majors | folded into T05-fix1 |
| 2026-11-24 | T02 handoff | closed | QA (T02-close) | 72f6552 | ACCEPT | 650 passed; Student decision empty | Saad writes decision |

## From 2026-11-24: native agents and file-based handoffs

Rows now name the **model** (configured, and verified from transcript
metadata with `tools/orchestration/verify_models.py`) and the **handoff
files** read and written (`HANDOFF_PROTOCOL.md`).

| Date | Task | Gate / event | Agent | Model (configured; verified) | Commit | Verdict | Handoff consumed → produced | Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-11-24 | config probe | delegation probe (headless `claude -p`, session 197da38f) | orchestrator → tech-lead | opus-5-5 → sonnet-5-5; verified: transcript (main `claude-opus-5-5`, subagent `agentType: tech-lead`, `claude-sonnet-5-5`) | 721b3e6 | `general-purpose` spawn refused; `tech-lead` spawned | — | allowlist kept; `disallowedTools: Agent(...)` removes the whole Agent tool on 2.1.331 |
