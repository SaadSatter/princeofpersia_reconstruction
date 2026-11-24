# T11-fix1: playtest kit corrections after the QA fact-check
Assigned agent: `agents/evaluation-specialist.md`
Setup: `_EXEC_COMMON.md`. Base: `e47c996` (task/T11): `git clone -q /home/claude/sm/wt/T11 /home/claude/sm/wt/T11-fix1 && cd /home/claude/sm/wt/T11-fix1 && git checkout -q -b task/T11-fix1 e47c996`.
Inputs: `/home/claude/sm/orch/reports/GATE-T01-qa.md` (T11 section), `/home/claude/sm/orch/DECISIONS-2026-11-23.md` (#12–13: the playtest build is now the hosted web build, Pyodide + Phaser, by G2/G3; a per-round trace download is planned in T14 but **not yet verified**), `/home/claude/sm/orch/PLAN-2026-11-23-v3-delta.md`.
Permitted write paths: `docs/final/playtest/` only.
Fix:
1. Consent and logging must match exactly what the build records. Write the consent so it covers both cases explicitly, and selects between them by a field on the observation sheet:
   - (a) no game log: only the observer's notes and the answers are kept;
   - (b) a per-round trace file is saved, but only if the build used has it.
   Do not claim that a log exists.
2. PROTOCOL §4 item 6: the 5-minute limit is now the default (T01); remove the "set explicitly" requirement, and keep a check that the build shows 5:00.
3. Add a session type for the [R] "external test of revised encounter, between G2/G3 and G4", linked to a specific change (finding → change → retest).
4. Replace "observed exactly as a guard" with an accurate statement that points to the known remaining tells (GATE-T01-qa QA1–QA3, GATE-T01-eval tells list) and says the playtest records which cue a player used.
5. Point the playtest build at the hosted web build (URL to be filled in by Saad), keeping the local bench as the fallback.
Never fill in any session or result. Report the files changed and the open choices for Saad.
