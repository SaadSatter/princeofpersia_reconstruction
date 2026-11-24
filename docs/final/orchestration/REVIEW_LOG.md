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
| 2026-11-24 | SMOKE-01 | brief (coordination commit) | orchestrator | claude-opus-5-5; verified: transcript (session 50115623) | 58ea6e7 on `main` | n/a | → `tasks/SMOKE-01.md`@58ea6e7 | dispatched tech-lead |
| 2026-11-24 | SMOKE-01 | implementation (read-only path check) | tech-lead (agent a9e1b3e1) | claude-sonnet-5-5 (verified: transcript) | fc16525 on `task/SMOKE-01` | n/a; 1 minor finding | `tasks/SMOKE-01.md`@58ea6e7 → `reports/SMOKE-01-tech-lead.md`@fc16525 | 435 passed, 12 skipped; to QA |
| 2026-11-24 | SMOKE-01 | Gate 1 | qa (agent a3224446) | claude-sonnet-5-5 (verified: transcript) | reviewed fc16525; report 3bb36f5 on `gate/SMOKE-01-qa` | ACCEPT WITH NOTES | `reports/SMOKE-01-tech-lead.md`@fc16525 → `reports/SMOKE-01-qa.md`@3bb36f5 | minor: `CLAUDE.md:76` names `agents/rl/` and `docs/final/RL_POLICY.md`, absent on `main` (present on `orch/preview`, T07). Routed to Saad |
| 2026-11-24 | SMOKE-01 | Gate 3 | orchestrator | claude-opus-5-5; verified: transcript (session 50115623) | 3bb36f5 (no integration; reports stay on their branches) | **closed** | brief@58ea6e7 → TL@fc16525 → QA@3bb36f5 → this row; chain unbroken | see Gate 3 note below |

**SMOKE-01 Gate 3 note (2026-11-24 13:28 ET).** (1) Reviewed commits fc16525 and
3bb36f5 are the ones recorded. Nothing was integrated (Saad: no merge). (2) Gate 1 report present,
ACCEPT WITH NOTES. Gate 2 not required (Saad: "Gate 2 does not apply (no AI or
boundary change)"). (3) No blocker or major finding. The one minor finding is
correct: I checked `git cat-file -e 58ea6e7:docs/final/RL_POLICY.md` (missing)
and `git ls-tree orch/preview` (present: `agents/rl/{__init__,encoder,policy}.py`,
`docs/final/RL_POLICY.md`). It needs no fix on this task. It clears when T07
reaches `main`, or when Saad approves a `CLAUDE.md` wording change.
(4) I ran `uv run pytest -q` on 3bb36f5 in a temporary detached worktree, now removed:
`435 passed, 12 skipped in 3.07s`. (5) Acceptance criteria 1 to 6 are met. I
independently re-checked every literal path and all six `.claude/agents/*.md`
procedure pointers at 58ea6e7. (6) The `consumed` chain is unbroken, and all three shas
exist. (7) No checklist row is claimed. (8) `git diff --name-only 58ea6e7..3bb36f5`
lists only `reports/SMOKE-01-tech-lead.md` and `reports/SMOKE-01-qa.md`.
Cosmetic: both reports write `source_commit` as a description ("the commit
adding this file"), because a commit cannot name its own sha. A template
clarification could follow. Models from `tools/orchestration/verify_models.py --latest`:
main `claude-opus-5-5`; subagent `type=tech-lead` and `type=qa`, both
`meta_model=claude-sonnet-5-5 responses=claude-sonnet-5-5`.
| 2026-11-24 | SMOKE-01 follow-up | configuration fixes from the chain (refactor session fb28fc89, Opus 5.5, not started as the orchestrator agent) | — | claude-opus-5-5 (verified: transcript) | see the commit after 44d02e2 | n/a | read `reports/SMOKE-01-tech-lead.md`@fc16525 and `reports/SMOKE-01-qa.md`@3bb36f5 | (1) agent commits now use `--author "Claude … (<role> …)"`, since worker commits showed Saad as author; (2) `source_commit` cannot be a report's own commit, which the template now says; (3) the QA minor finding was fixed in `CLAUDE.md`; (4) worktree test counts were documented (445 collected vs 459) |
| 2026-11-24 | T10a | brief | orchestrator (refactor session fb28fc89 acting as orchestrator; not started via the `orchestrator` agent) | claude-opus-5-5 (verified: transcript) | 96a334b on `main` | n/a | → `tasks/T10a.md`@96a334b; issue #5 | dispatched tech-lead |
| 2026-11-24 | T10a | implementation (docs) | tech-lead | claude-sonnet-5-5 (configured; verification at Gate 3) | 4b0f1ba, report 7faccc0 on `task/T10a` | n/a | `tasks/T10a.md`@96a334b → `reports/T10a-tech-lead.md`@7faccc0 | 435 passed, 12 skipped (worktree); to QA |
| 2026-11-24 | T10a | Gate 1 | qa | claude-sonnet-5-5 (configured; verification at Gate 3) | reviewed 7faccc0; report a6df4f4 on `gate/T10a-qa` | ACCEPT WITH NOTES | `reports/T10a-tech-lead.md`@7faccc0 → `reports/T10a-qa.md`@a6df4f4 | F1 (minor: GDD §6–7 says the browser never holds the GameState, which is false for the Pyodide build), F2 (minor: 19 vs 18 features), F3 (cosmetic). Returned as T10a-fix1 (attempt 1 of 2) |
| 2026-11-24 | T10a-fix1 | implementation (docs) | tech-lead | claude-sonnet-5-5 (configured; verification at Gate 3) | 562c634, report 5379d62 on `task/T10a-fix1` | n/a | `tasks/T10a-fix1.md`@9d942d3 + `reports/T10a-qa.md`@a6df4f4 → `reports/T10a-fix1-tech-lead.md`@5379d62 | F1–F3 addressed; to QA |
| 2026-11-24 | T10a-fix1 | Gate 1 | qa | claude-sonnet-5-5 (configured; verification at Gate 3) | reviewed 5379d62; report 2d88e03 on `gate/T10a-fix1-qa` | ACCEPT WITH NOTES | `reports/T10a-fix1-tech-lead.md`@5379d62 → `reports/T10a-fix1-qa.md`@2d88e03 | F1–F3 verified. New N1/N2 (minor): Section 4 labels understate what is on `main`. Root cause: STATUS.md did not list main's content (now fixed). Returned as T10a-fix2, attempt 2 of 2 |
| 2026-11-24 | T10a-fix2 | implementation (docs) | tech-lead | claude-sonnet-5-5 (verified: transcript) | 2d5bd95, report 675d149 on `task/T10a-fix2` | n/a | `tasks/T10a-fix2.md`@cf4dde2 + `reports/T10a-fix1-qa.md`@2d88e03 → `reports/T10a-fix2-tech-lead.md`@675d149 | N1, N2 fixed; §5.2/5.3 status notes |
| 2026-11-24 | T10a-fix2 | Gate 1 | qa | claude-sonnet-5-5 (verified: transcript) | reviewed 675d149; report 1c54bbe on `gate/T10a-fix2-qa` | ACCEPT WITH NOTES | `reports/T10a-fix2-tech-lead.md`@675d149 → `reports/T10a-fix2-qa.md`@1c54bbe | G1 cosmetic (`LINGER_AFTER` is in `pop/versus.py:77`); out-of-scope follow-ups: GDD §2, §6 |
| 2026-11-24 | T10a (+fix1, fix2) | **Gate 3** | orchestrator (refactor session fb28fc89 acting as orchestrator) | claude-opus-5-5 (verified: transcript); all 3 tech-lead + 3 qa runs claude-sonnet-5-5 (verified) | `orch/T10a` a1b9738 (task/T10a-fix2 + three gate branches) | **closed**; PR #6 awaiting Saad's merge | chain unbroken: brief@96a334b → TL@7faccc0 → QA@a6df4f4 → fix1 brief@9d942d3 → TL@5379d62 → QA@2d88e03 → fix2 brief@cf4dde2 → TL@675d149 → QA@1c54bbe | `uv run --extra play pytest -q` in the integration worktree: 451 passed, 9 skipped; merges cleanly into main; scope = 5 docs + 6 reports. Follow-ups → T10b |

Gate 3 note, T10a (2026-11-24). (1) Integrated commits are the ones the gates reviewed: 7faccc0, 5379d62, 675d149. (2) All three Gate 1 reports exist; none is REJECT. (3) No blocker or major finding; F1–F3 and N1–N2 were fixed and verified, and G1 (cosmetic) is deferred to T10b. (4) Suite re-run by the orchestrator: result line above. (5) All 7 T10a acceptance criteria were met at 7faccc0 (QA a6df4f4), with corrections verified at 2d88e03 and 1c54bbe. (6) Chain complete, as above. (7) The checklist rows the task touches link decisions. (8) Scope check passed, and the merge is clean. Lesson for the process: N1 came from an orchestrator record (STATUS.md did not list what `main` contains), not from the worker; fixed in cf4dde2.
