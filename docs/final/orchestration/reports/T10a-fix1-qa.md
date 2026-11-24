---
handoff_id: HO-T10a-fix1-qa
task_id: T10a-fix1
date: 2026-11-24 ET
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent
consumed: docs/final/orchestration/reports/T10a-fix1-tech-lead.md@5379d62
source_branch: gate/T10a-fix1-qa
source_commit: see branch head
reviewed_commit: 5379d62 (work commit 562c634)
verdict: ACCEPT WITH NOTES
---

# T10a-fix1: QA report

Verdict: ACCEPT WITH NOTES. F1-F3 are fixed. One new minor finding (N1): the new Section 4 labels say "not on main" for work that is on main. No tests added (docs-only change).

## Acceptance criteria -> evidence
| # | Criterion | Met? | Evidence |
|---|---|---|---|
| 1 | F1 markers on s6/s7, devtools fact, Platform row, s4 labels | Met for markers; s4 labels see N1 | `git diff 7faccc0..562c634`: italic `[Superseded ... #1, #12 ...]` under s6 and s7, G1 text kept, both state Pyodide/devtools/ok for human-vs-AI/not human-vs-human, cite v3-delta "Known limitation". Platform row says the same. |
| 2 | F2 A0 = 18, sums to 251 | Met | `orch/preview:agents/rl/encoder.py` `_names()`: me = 3 + 4 + 2 + 4 + 5 = 18. 150+2+18+2+4+60+15 = 251 (macro history 9+1+5 = 15, figures 3x20). |
| 3 | F3 Session row keeps G1 phrase with marker | Met | Row has `*[G1 text: "about 5 minutes (OQ-3)"; superseded by decision #5]*`. |
| 4 | Nothing else changes | Met | `git diff --name-only 7faccc0..562c634` = GDD.md, CONFIGURATION.md only; 562c634..5379d62 adds only the Tech Lead report. |

Tests: `uv run pytest -q` -> `435 passed, 12 skipped in 3.07s`. Link check on both files (relative `](target)` resolved from docs/final/): no broken links.

## Regression scan (7faccc0..562c634)
Only the A0 "19"->"18" edit, the Platform row addition, two s4 rows, two s6/s7 marker lines and the Session marker. No other text touched. No regression found.

## Findings
**N1 (minor, reproduced) docs/final/GDD.md s4 "Act"/"Respond" rows (lines ~104-105)**: the labels are wrong in the opposite direction from the old ones.
- Written: "disguise [Planned; built on `orch/reviewed`, not on `main`]", "guard rule [Planned; lingering rule built on `orch/reviewed`, not on `main`]".
- Actual on `main` (721b3e6 base, tree now 9d942d3): `pop/versus.py` has swordplay (R-V01..R-V12: draw, lunge, throw, kick, sweep, sword pickup), hearts, disguise (R-V17..R-V21, `_take`, `disguised`, `BREAKS_DISGUISE`) and suspicion; `pop/guards.py` and the lingering rule (`LINGER_AFTER`, R-V19, versus.py:77, :420) are on `main` too, present since 721b3e6. Tests on main: `tests/test_swordplay.py` (23 tests), `test_versus.py` (21), `test_guards.py` (15), `test_disguise.py` (18). `orch/reviewed` adds fixes and seat/runner code (T01 fixes, `pop/seats.py`, `pop/versus_runner.py`), not the base rules.
- Reproduce: `git show main:pop/versus.py | grep -nE "disguised|LINGER"`; `git ls-tree --name-only main tests/ | grep -E "sword|disguise|guards|versus"`.
- Expected: disguise, guard rule (incl. lingering), sword **Implemented on `main`** (desktop versus engine; the disguise leak/hop fixes are on `orch/reviewed`).

**N2 (minor, reproduced) Section 4 "Interpret" row and Section 5.2 [Planned]**: HUD [Planned] is stale. On `main`, `render/draw.py:291` draws hearts and `play.py:195-262` draws the suspicion eye/bar and a "DISGUISED" marker from the seat's observation (same code on `orch/preview`, plus `render/draw_list.py`). Hearts and suspicion HUD are Implemented in the desktop Pygame frontend; the browser HUD is on `orch/preview` only. Loose-floor trap is correctly not on main (`my_traps`, `traps_left` appear only on `orch/preview`; `tests/test_traps*.py` only there). Also the s6 "Controls and feedback [Planned]" header and s5.2/s5.3 headers were not rechecked item by item.

**Answer to the Tech Lead's open question**: sword, hearts, disguise, guards, suspicion HUD (desktop) are built on `main`; the Tech Lead's "no evidence in STATUS.md" held because STATUS.md says only "gameplay on main unchanged since 721b3e6" and does not list what 721b3e6 contains. Fix is a follow-up docs edit (not done by QA): relabel to Implemented (desktop) on `main`; keep trap [Planned; loose floor on `orch/preview`].

## Not checked
Section 5.2/5.3 row-by-row labels beyond the lines above; the browser build; RL_POLICY.md (out of scope, T07).

## Student decision required
none
