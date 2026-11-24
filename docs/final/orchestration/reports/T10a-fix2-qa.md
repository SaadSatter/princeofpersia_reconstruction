---
handoff_id: HO-T10a-fix2-qa
task_id: T10a-fix2
date: 2026-11-24 ET
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id)
consumed: docs/final/orchestration/reports/T10a-fix2-tech-lead.md@675d149; docs/final/orchestration/tasks/T10a-fix2.md@cf4dde2
reviewed_commit: 675d14977b6e7e2a0c7987af20a68465206bfc7e
source_commit: see git log of gate/T10a-fix2-qa (report only; no new tests, docs-only change)
verdict: ACCEPT WITH NOTES
---

# T10a-fix2: QA report

## Verdict
ACCEPT WITH NOTES. N1 and N2 are fixed. No blocker or major. One cosmetic file-locator nit (G1).

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Act row | Met | Checked on `main`: `pop/versus.py` has TAKE (`_take`, R-V17), swords R-V01..R-V12 in `docs/RULE_SOURCE_MAP.md`; `HOP_FLIPS`/R-V22 present but R-V24/25/26 appear only on `orch/reviewed` (`git grep` on its rule map). Player-rigging: on `main` `pop/versus.py` has no rig action; `RIG_KIND = "loose"` is on `orch/preview` only. |
| 2 | Respond row | Met | `pop/guards.py` (Guard) and `LINGER_AFTER = 24` (`pop/versus.py:77`, R-V19) on `main`; `Rival.still` lingering counter on `orch/reviewed`. See G1 for the locator. |
| 3 | Interpret row | Met | `main:play.py` draws suspicion and `DISGUISED`; `main:render/draw.py` draws hearts. Browser HUD not on `main`. |
| 4 | Other contradicting rows | Met | 5.2 and 5.3 now carry a status note. Verified: hearts to 0, both-died draw (`draw:both_died`) and time-up draw (`draw:time_up`, `pop/versus.py:855-862`, `tests/test_versus.py:138`) on `main`; `main` default limit is `GAME_FRAMES` (60 minutes), 5-minute `DUEL_FRAMES` only on `orch/reviewed` (`pop/versus.py:49`), matching the note. Traps, online, disconnect, mode wiring correctly Planned. The notes (not per-row labels) are acceptable. |
| 5 | Scope | Met | `git diff --name-only 5379d62..675d149` = `docs/final/GDD.md` and `reports/T10a-fix2-tech-lead.md`. |

Tests: `uv run pytest -q` -> `435 passed, 12 skipped`. Link check on GDD.md (relative targets from docs/final/): none missing.

## Regression scan (5379d62..2d5bd95)
Diff is 3 table rows in Section 4 and two header edits (5.2, 5.3) in `docs/final/GDD.md`. No other line touched; the Section 5.2/5.3 tables are unchanged. Remaining `[Planned]` strings are at lines 15, 76-80 (Section 2 and the decision table) and 151 (Section 6), all outside this brief.

## Findings
- N1 (disguise on main): resolved. N2 (lingering rule on main): resolved.
- G1 (cosmetic) `docs/final/GDD.md:105` — "Guard rule [Implemented on `main` (`pop/guards.py`; R-V19 `LINGER_AFTER`)]" puts `LINGER_AFTER` under `pop/guards.py`. It is defined in `pop/versus.py:77` (guards.py has the patrol/sight/attack rules, R-V13..R-V15). Repro: `git grep -n LINGER main -- pop`. Expected: `pop/versus.py`. Not worth another attempt.

## Known limitations (follow-ups, not findings)
- GDD Section 2 rows Players, Genre, Session (lines 76, 79, 80) say `Planned`; Players/Genre are partly on `main` (two rivals, versus duel); Session's 5 minutes is on `orch/reviewed` only. Context row (77) and Platform row (78) are mixed and labelled.
- GDD Section 6 "Controls and feedback [Planned]" (line 151) and its HUD bullet contradict the pygame HUD on `main`.
- Line 15 (decision table, "Planned" for play context) is a decision status, probably fine.
- The word "5.3 time-out" claim is by code reading, as for Tech Lead; I did not run a duel.

## Not checked
No duel or browser run (docs-only change). `orch/preview` claims (loose floor rigging) checked by grep only, not by running its suite.

## Requested next action
Orchestrator: close Gate 1; queue Section 2 and 6 relabel and G1 as optional follow-ups.

## Student decision required
none
