# Orchestration status: 2026-11-24 (native agent hierarchy)

The first file a new orchestrator session reads. Branches are the facts; if
this file and `git branch -a -vv` disagree, fix this file.

**Gameplay on `main`: unchanged** since 721b3e6 (Saad's merges of PRs #1 to
#4, then the orchestration workflow). All newer gameplay work is on the
`orch/*` branches. Merging is Saad's call.

**What `main` already contains** (G1 engine, PRs #1 to #4; checked 2026-11-24
after T10a-fix1 QA finding N1): two rivals in one `GameState`
(`pop/versus.py`); sword strike and block (R-V01 to R-V12,
`tests/test_swordplay.py`, 23 tests); hearts; disguise with `TAKE` and
disguise-breaking actions (R-V17 to R-V21, `tests/test_disguise.py`, 18);
suspicion, with the lingering rule `LINGER_AFTER` (R-V19); scripted guards
(`pop/guards.py`, `tests/test_guards.py`, 15); the six-room arena
(`pop/arena.py`); the flip (R-V22, R-V23); and a pygame HUD with hearts, the
suspicion eye and bar, and a DISGUISED marker (`render/draw.py`, `play.py`).
**Not on `main`:** the T01 fixes (R-V24 hop, R-V25 masking, R-V26, 5-minute
duel, WAIT lingering), the seat controllers and versus runner, macros and
baseline, traps, PPO, and the web build.

## Orchestration architecture (from 2026-11-24)

The main session is the Production Orchestrator (`claude-opus-5-5`, set by
`.claude/settings.json`). It spawns named workers (`claude-sonnet-5-5`):
`tech-lead`, `qa`, `evaluation-specialist`, `requirements-auditor`,
`rules-reviewer`. Work passes as committed report files
(`HANDOFF_PROTOCOL.md`). Smoke test SMOKE-01 ran the full chain on 2026-11-24
(brief 58ea6e7 → tech-lead fc16525 → qa 3bb36f5 → Gate 3 closed). The worker
models were verified from transcripts as `claude-sonnet-5-5`. See `REVIEW_LOG.md`.

Earlier work (2026-11-23/24 02:00 ET) was orchestrated from a claude.ai
sandbox with generic subagents. Those briefs name `/home/claude/sm/...`
paths and are historical.

## Branches

| Branch | Head | Class | Content |
| --- | --- | --- | --- |
| `main` | see `git log` | Saad's merged work + orchestration records | gameplay as of 721b3e6; orchestration docs |
| `orch/reviewed` | f08c1a8 | reviewed integration candidate | everything on the preview line, all gates passed: T01, T02, T04 (incl. fix3), T05 + fix1, T06b, T07 + fix1 + T16 + T17, T11 + fix1, T13 + fix1, T14 + fix1, T15 |
| `orch/preview` | f08c1a8 | = `orch/reviewed` (fast-forwarded 2026-11-24) | |
| `int/preview-T05-fix1` | b52d145 | parked integration | `orch/preview` + `orch/reviewed` 2180fea. One T07 test fails (fixture relied on the mirror deadlock). Becomes `orch/preview` after T07-fix1 |
| `int/T13-base` | ae90c8c | preview line (supersedes `int/preview-T05-fix1`) | `orch/preview` + `orch/reviewed` 704521d. 1 known failure (T07 fixture). Base for T13 and GATE-wave3; becomes `orch/preview` after T07-fix1 |
| `task/T05-fix1`, `gate/T05-fix1-qa`, `gate/T05-fix1-eval` | 161a841, 12c11bd, 1b303ff | worker branches (closed task) | merged into `orch/reviewed` |
| `orch/wip-T05-fix1` | ab78522 | unreviewed WIP snapshot | interrupted ~02:00 ET 2026-11-24. **Untested; never merge** |
| `orch/wip-T08` | 25e4587 | unreviewed WIP snapshot | same |
| `orch/wip-T04-fix3` | 76de25c | unreviewed WIP snapshot | same |
| `task/SMOKE-01` | fc16525 | worker branch (closed task) | tech-lead report only; worktree `.claude/worktrees/agent-a9e1b3e19488bb69c` kept |
| `gate/SMOKE-01-qa` | 3bb36f5 | gate branch (closed task) | QA report only; worktree `.claude/worktrees/agent-a3224446806667f0e` kept |

No `rc/*` (approved release candidate) branch exists.

## Tasks by state

| State | Task | What | Gates | Branch / commits | GitHub |
| --- | --- | --- | --- | --- | --- |
| closed | T01 + fix1 + fix2 | F1 disguise leak, R-V24 hop, 5-min duel, R-V25 masking, R-V26 TAKE always legal, lingering | G1 accept w/ notes, G2 accept, G3 closed | `orch/reviewed` cd5c4aa | none |
| closed | T02 + T02-close | QA re-review of 13c7488 = Saad's G2/G3 QA→Tech handoff (decision #7) | closed | `orch/reviewed`; draft `handoff-drafts/2026-11-24-qa-to-tech.md` (**Student decision empty, for Saad**) | none |
| closed (except fix3) | T04 + fix1 + fix2 | seat-controller protocol, versus runner | G1, G2 accept w/ notes; G3 closed | `orch/reviewed` | none |
| under review | T11 + fix1 | playtest kit | G1 accept w/ notes; fix1 fact-check pending | `orch/reviewed` | none |
| closed (Gate 3, 2026-11-24) | T06a / T06b | traps spec + rival-rigged loose floor | G1 e50a846, G2 f02314b ACCEPT w/ notes; G3 closed | `orch/reviewed` 0b32647 | — |
| closed (Gate 3, 2026-11-24) | T07 + T07-fix1 + T16 | PPO encoder, trainer, stdlib policy; fail-fast (#47); 8 tuning starts (#44); no AI traps (#43). **Full training not started** | final G1 37cf95c, G2 805df2b ACCEPT w/ notes; G3 closed | `orch/reviewed` 2835928 | — |
| closed (Gate 3, 2026-11-24) | T14 + T14-fix1 | hosted web build (Pyodide + Phaser); not yet run in a browser | G1 e50a846, G2 f02314b ACCEPT w/ notes; G3 closed | `orch/reviewed` 83a90ea | — |
| closed (Gate 3, 2026-11-24) | T05 + T05-fix1 | macros + baseline; CLIMB both ways (#31), descent, lone-guard rule 5, mirror no longer deadlocked | G1 ACCEPT w/ notes (12c11bd), G2 ACCEPT w/ notes (1b303ff), G3 closed | `orch/reviewed` 2180fea; preview merge parked on `int/preview-T05-fix1` b52d145 (breaks one T07 test, see REVIEW_LOG) | issue #7 |
| closed (Gate 3, 2026-11-24) | T04-fix3 (+ #33 flip) | refuse shared controller, keyed seed, in-flight race | G1 ab7fcba, G2 0eef8e4 ACCEPT w/ notes; G3 closed | `orch/reviewed` 704521d | issue #8 |
| closed (Gate 3, 2026-11-24) | T15 | numpy as optional `train` extra (#34) | G1 ACCEPT (f2ac18b); G2 n/a; G3 closed | `orch/reviewed` 199f858 | issue #9 |
| closed (Gate 3, 2026-11-24) | T13 + T13-fix1 | online play: LAN server (#36), websockets extra (#37), pause 15 s then forfeit (#38), 6 s drop detection (#48), log-only fallbacks (#49), both-press rematch (#41, #46) | fix1 G1 38b0f45, G2 68864ac ACCEPT w/ notes; G3 closed | `orch/reviewed` 4697989 | issue #10 |
| unreviewed WIP | T08 | scenario suite D1/B2/I3/F5 + held-out H6, CLI, analysis | — | `orch/wip-T08` 25e4587 | none |
| **finished** 22:00:26 ET, exit 0; all 8 after-run checks pass | T07 full training run (#51) | 4,800 s cap, 2 workers, seed 0, from f08c1a8: `time_cap`, 1568 updates, 1,487,955 steps, 0 policy errors; weights SHA-256 80e4a110…ba4c; final check (tuning, 128 duels) 120 W / 8 D / 0 L | results committed by T07-run1 (tech-lead → QA → Eval → G3) | worktree `.claude/worktrees/train`, output `tools/rl/logs/run-1/` (**do not delete**) | — |
| closed (Gate 3, 2026-11-24) | T07-run1 | run-1 weights `agents/rl/weights/ppo-run-1.json` (SHA-256 80e4a110…ba4c) and evidence `tools/rl/runs/run-1/`; rerun of the final check matches (120/8/0, tuning, not held-out) | G1 ACCEPT b3d1361; G2 ACCEPT w/ notes 65a3d2c; G3 closed | `orch/reviewed` = `orch/preview` eba8bb1 | — |
| **running** (T08-fix1 tech-lead dispatched, PPO line) | T08 + T08-fix1 | scenario suite, H6 frozen; fix1: #64 ledger key, #65 seat-B starts, #74 H6 to 8 starts (re-freeze), #75 claim wording, #76 B2 disguise lasts, #77 T09 bar 14/16, QA F-1/F-2/F-4 | T08 G1 cf43ba1, G2 059aea5 ACCEPT w/ notes; fix1 G1, G2, G3 to come | `task/T08-fix1` from `gate/T08-eval` 059aea5; brief `tasks/T08-fix1.md` | — |
> **Decision numbers:** two orchestrator sessions append to `DECISIONS-2026-11-24.md`. Fetch and read the last number right before adding one (PPO line #74–#77 were first committed as #67–#70 by mistake).
| queued (after T19 and T08 close) | T09 | held-out comparison, run once on the post-T19 engine; first the T07-run1 E1 re-check of the shipped weights | — | — | — |
| closed (Gate 3, 2026-11-24) | T17 | withhold failed weights (#50) | G1 3943732, G2 55873a6 ACCEPT w/ notes; G3 closed | `orch/reviewed` f08c1a8 | — |
| closed | SMOKE-01 | orchestration smoke test: every path in README Files + CLAUDE.md Roles tables, and agent procedure pointers, exist on `main` | G1 ACCEPT WITH NOTES (1 minor), G2 n/a, G3 closed | `task/SMOKE-01` fc16525, `gate/SMOKE-01-qa` 3bb36f5 (not merged) | none |
| closed (Gate 3, 2026-11-24) | T18 | online room codes (#52), code-less default room HOME (#56), limits (#57) | G1 7f3525e, G2 f4dc475 ACCEPT w/ notes; G3 closed | `orch/reviewed` 6a4b8b5, then fc02687 (with T07-run1) | — |
| **Gate 1** (qa dispatched) | T18-fix1 | one room's error never stops the server (EVAL-T18-1) | — | brief `tasks/T18-fix1.md`; base fc02687 | — |
| **Gate 1** (qa dispatched) | T19 | either control scheme (#55), 2-tick input grace (#54), kneel pickups, flip by default (#53, amends R-V22) | G1, G2, G3 to come | base = `orch/reviewed` tip after T18; brief `tasks/T19.md`@53e7ece | — |
| queued (after T19, T18-fix1) | T20 | playtest telemetry (#67, #68) | G1, G2, G3 | brief `tasks/T20.md` | — |
| queued (after T20) | T21 | telemetry-analyst agent (#69) | G1, G3 | brief `tasks/T21.md` | — |
| not started | T03 | official-repository move (decision #6), `python -m team init` | — | — | — |
| closed (Gate 3); **PR #6 awaiting Saad's merge** | T10a (+fix1, fix2) | docs in line with decisions #1–#30: Changes since G1 in GDD and Configuration, PPO rival, orchestration, checklist, plan, README | G1 accept w/ notes ×3; G2 n/a; G3 closed | `orch/T10a` a1b9738 | issue #5, PR #6 |
| not started | T10b | T10a follow-ups: GDD §2 and §6 labels, `LINGER_AFTER` location (GDD:105), `EVIDENCE_INDEX.md` pass (after Saad commits his edits), tracker `docs/final/TRACKER.md`, scope lock | — | — | — |

> **Worktree note (2026-11-24, Saad's instruction):** the main project folder is back on `main`; the experiment branch `experiment/gcp-ppo-cpu` was only an experiment and is left as is (not deleted). To free `main`, `.claude/worktrees/orch-main` was detached at the same commit (Saad: "Detach that worktree (Recommended)"); no files changed. Sessions working in a worktree commit detached and push with `git push origin HEAD:main`, after `git fetch` and a fast-forward to `origin/main`.

## Next eligible task

**Now (2026-11-24, night):** T18 closed at Gate 3 (`orch/reviewed` fc02687). T19 (controls, grace window, kneel, flip; brief `tasks/T19.md`) is with the tech-lead from base fc02687; then QA, Eval, Gate 3. Saad's request and decisions #52–#55 are in `DECISIONS-2026-11-24.md`. Another Claude session works on PPO (`agents/rl/`, `tools/rl/`); T18 and T19 do not write there. After T19 the PPO rival is re-checked against the new jump rule.

Earlier note: **Running (decision #39):** T13 tech-lead (brief `tasks/T13.md`) and GATE-wave3 QA (then Eval), in parallel. Both were interrupted by the usage limit (about 17:00 ET 2026-11-24) and resumed in place after the reset. Their worktrees hold their work: `.claude/worktrees/agent-a4b0b80a203cad97e` (T13) and `.claude/worktrees/agent-a73f794fc81291219` (wave3 QA). Do not delete them. T04-fix3 and T15 closed. Next after GATE-wave3: T07-fix1 (fixture plus T07 findings), then T08 (scenario suite; must carry the T04-fix3 Eval note "one controller per worker and seat; busy = harness error; strong `seed_key`" and the T05-fix1 note on per-seat reporting). **Then (decision #39):** T13 online play (tech-lead) at the same time as **GATE-wave3** (T06b, T07, T14-fix1 on `orch/preview`), folding in **T07-fix1**: the T07 test fixture collects 200 observations from one mirror duel, and that breaks after the T05-fix1 merge. Decision #32: one chain at a time.

T05-fix1 follow-ups (minor, docs and tests; not blocking):
- F-E3: MACROS.md must state that the planner assumes a floor below a bottom-row pit.
- F-E4: relabel `LOWER_HELD_OUT_STARTS` as "frozen before implementation, not unseen".
- QA-F1: one loss to WAIT, kept as a strict xfail.
- Condition for T08: every comparison that uses the baseline reports results **per seat**, and a mirror match counts as one trial.
- Session record `docs/agent-sessions/15-T05-fix1-macros-baseline.md` shares the number 15 with Saad's uncommitted `15-native-orchestration.md`. Renumber at the next evidence pass (T10b).

Deadline pressure: G2/G3 recording and the official-repository move are due **Sat 2026-11-28, 11:59 p.m.** (T03, `COURSE_ROLE_MAP.md`).

## Waiting on Saad

- ~~T18 follow-ups~~ decided (#62 keep as built, #63 crash fix = T18-fix1). Previously: EVAL-T18-1, where one room's trace-write error stops every room (fix: guard `pump`/`_record`); QA-T18-1, where the ligature "ﬀ" is read as "FF"; the room cap of 50 against a measured safe level of about 40 on the M4; creates are not rate-limited; "full" versus "No room" tells a guesser that a code exists.
- **Note:** the main checkout is on `experiment/gcp-ppo-cpu` (the other session), which was cut from fc02687 and so includes T18. The orchestrator writes `main` records from `.claude/worktrees/orch-main`.

- **Draft PR #11** (`orch/pr-main` 088c3fc → `main`): all reviewed gameplay (T01–T17), online play and the PPO stack. The suite on the merge commit is re-run after training. Merging is Saad's.
- **Two-machine playtest of T13** (online play), and a first browser run of the hosted page. Neither has been verified yet.

- ~~numpy~~ decided #34, done in T15 (closed). Not in `dev` (#40). Previously: **numpy is not a declared dependency.** T07 (PPO trainer and tests) and one T04-fix1 QA probe import it, so a clean `uv` environment fails to collect `tests/test_rl_policy.py` and `tests/test_rl_train.py` on `orch/preview`. Adding it (an optional `train` extra in `pyproject.toml` + `uv.lock`) needs Saad's approval.

- ~~SMOKE-01 minor finding~~ resolved 2026-11-24 in the orchestration refactor (Saad authorized `CLAUDE.md` edits for it): the AI-rival row in `CLAUDE.md` now says the paths are on `orch/preview`, not yet on `main`.
- **SMOKE-01 branches:** `task/SMOKE-01` and `gate/SMOKE-01-qa` hold only the two reports. Merge them, keep them, or delete them (deleting needs you). The two worker worktrees are still registered.
- **Student decision** on `handoff-drafts/2026-11-24-qa-to-tech.md` (G2/G3 handoff).
- B2 "low suspicion" threshold (proposed below 50/100); D1 "on screen" = same room (proposed).
- T06b: confirm "a sprung trap costs 1 heart in all".
- T07: macro cadence (4 decisions), nearest-figure targeting, reward-shaping defaults.
- ~~CLIMB down as well as up~~ decided 2026-11-24 14:19 ET (#31): "CLIMB both ways".
- ~~Pushing~~ decided 2026-11-24 (#27, #28): pushes, issues and PRs need no per-push approval; merging stays Saad's.
- **Course registration:** spawn the native `tech-lead`/`qa`, or the course-rendered `team-tech`/`team-qa`, once `agent-team/` exists (`COURSE_ROLE_MAP.md`).
- ~~FINAL_REQUIREMENTS copy~~ published with `main` on 2026-11-24 (#26).
- **PR #6 (T10a docs):** review and merge. Confirm CQ-7 closed by `agent-config.json` (commit 2d40972).
- Cloud sessions: the `agent` setting is not yet verified in Claude Code on the web.
- Official-repository move (decision #6) before Sat Nov 28, 11:59 p.m.

## Uncommitted work on Saad's checkout (not touched by agents)

`docs/agent-sessions/README.md`, `docs/final/EVIDENCE_INDEX.md` (modified),
`docs/agent-sessions/13-flip-audit-review-fixes.md` (untracked), as of 2026-11-24.
