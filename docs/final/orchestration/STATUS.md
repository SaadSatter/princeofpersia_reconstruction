# Orchestration status — 2026-11-24 12:55 ET

Pushed for Saad to inspect on GitHub. **Nothing here is merged into `main`.** Merging is Saad's call.

## Branches

| Branch | What it is | Review state |
| --- | --- | --- |
| `main` + 721b3e6 | Orchestration workflow, audits, plan v1/v2, decisions | committed 2026-11-23 |
| `orch/reviewed` | = `int/wave2` (cd5c4aa). The integrated work below that passed its gates | see the table below |
| `orch/preview` | `orch/reviewed` plus T05, T14, T14-fix1, T06a/T06b (traps), T07 (PPO stack, not trained yet), and these orchestration files. **Full suite: 959 passed, 12 skipped, 3 xfailed** (sandbox, Python 3.13) | parts still in review; see below |
| `orch/wip-T05-fix1`, `orch/wip-T08`, `orch/wip-T04-fix3` | Snapshots of three subagents' uncommitted work, stopped by the usage limit at about 02:00 ET | **untested, unreviewed: do not merge** |

## Tasks

| Task | What | Gate 1 QA | Gate 2 Eval | Gate 3 | In branch |
| --- | --- | --- | --- | --- | --- |
| T01 + fix1 + fix2 | F1 disguise leak, R-V24 hop, 5-min duel, R-V25 masking, R-V26 TAKE always legal, lingering fix | accept w/ notes | accept | closed | reviewed |
| T02 + T02-close | QA re-review of 13c7488 = **your G2/G3 QA→Tech handoff**; draft in `handoff-drafts/`, **Student decision empty for you** | — | — | closed | reviewed |
| T04 + fix1 + fix2 | Seat-controller protocol and versus runner | accept w/ notes | accept w/ notes | closed except T04-fix3 (QA-5 refuse shared controller, concurrent-start race) | reviewed; fix3 WIP |
| T11 + fix1 | Playtest kit (consent, protocol, questionnaire, log) | accept w/ notes; fix1 fact-check pending | — | pending | reviewed |
| T05 | Macro layer + scripted baseline | accept w/ notes (3 majors) | accept w/ notes (no way down a floor: blocks evaluation) | open → T05-fix1 WIP | preview |
| T06a/T06b | Traps spec (your decision #22) + rigged loose floor | pending | pending | — | preview |
| T07 | PPO encoder/trainer/pure-Python policy; **full training not started** (waits for T05-fix1) | pending | pending | — | preview |
| T08 | Scenario suite D1/B2/I3/F5 + held-out H6 | — | — | — | WIP |
| T14 + fix1 | Hosted web build (Pyodide + Phaser) | accept w/ notes; fix1 re-review pending | accept w/ notes | — | preview |

**Never run in a real browser or in CI.** Opening a PR from `orch/preview` runs `.github/workflows/web-smoke.yml` (Playwright) and `ci.yml`. That is the first real check of the web build. Enabling Pages (Settings → Pages → Source: GitHub Actions) then deploys from `main` after a merge.

Details: `REVIEW_LOG.md`, `reports/`, `DECISIONS-2026-11-23.md`, `PLAN-2026-11-23-v2.md`, `PLAN-2026-11-23-v3-delta.md`.

## Waiting on Saad
- Student decision on `handoff-drafts/2026-11-24-qa-to-tech.md` (G2/G3 handoff).
- B2 "low suspicion" threshold (proposed: below 50/100); D1 "on screen" = same room (proposed).
- T06b: confirm "a sprung trap costs 1 heart in all" (adds a heart on short falls).
- T07: macro cadence (4 decisions), nearest-figure targeting, reward shaping defaults.
- CLIMB down as well as up (T05-fix1's reading of G1 "climb").
- Install the Claude GitHub App so agents can push, or push these branches yourself.
- Official-repo move (midterm method) before Sat Nov 28, 11:59 p.m.
