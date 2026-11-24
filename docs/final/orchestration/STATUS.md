# Orchestration status: 2026-11-24 (native agent hierarchy)

The first file a new orchestrator session reads. Branches are the facts; if
this file and `git branch -a -vv` disagree, fix this file.

**Gameplay on `main`: unchanged** since 721b3e6 (Saad's merges of PRs #1 to
#4, then the orchestration workflow). All newer gameplay work is on the
`orch/*` branches. Merging is Saad's call.

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
| `orch/reviewed` | cd5c4aa | reviewed integration candidate | T01 chain, T02, T04 chain (except T04-fix3), T11 + fix1 |
| `orch/preview` | 87606b9 | preview / demo build; some gates pending | `orch/reviewed` + T05, T14, T14-fix1, T06a/T06b, T07, 2026-11-24 records. Suite there: 959 passed, 12 skipped, 3 xfailed (sandbox, Python 3.13, as recorded by the previous orchestrator; not re-run 2026-11-24) |
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
| under review | T05 | macro layer + scripted baseline | G1 accept w/ notes (3 majors), G2 accept w/ notes (blocking for evaluation: no way down a floor) | `orch/preview` 19b5da2 | none |
| under review | T06a / T06b | traps spec (decision #22) + rival-rigged loose floor | G1, G2 pending (brief `tasks/GATE-wave3.md`; no report on record) | `orch/preview` 9af96a9 / 4e9121b | none |
| under review | T07 | PPO encoder, trainer, stdlib policy. **Full training not started** | G1, G2 pending (GATE-wave3) | `orch/preview` 1e34cf2 | none |
| under review | T14 + fix1 | hosted web build (Pyodide + Phaser) | T14 G1/G2 accept w/ notes; fix1 G1/G2 pending (GATE-wave3) | `orch/preview` ca3667b | none |
| unreviewed WIP | T05-fix1 | macro reachability, CLIMB down, baseline fixes | — | `orch/wip-T05-fix1` (failing tests 0846a16 + WIP ab78522) | none |
| unreviewed WIP | T04-fix3 | refuse shared controller (QA-5), in-flight race | — | `orch/wip-T04-fix3` (tests 7fe2e9c + WIP 76de25c) | none |
| unreviewed WIP | T08 | scenario suite D1/B2/I3/F5 + held-out H6, CLI, analysis | — | `orch/wip-T08` 25e4587 | none |
| blocked | T07 full training run | ~85 min PPO run | needs T05-fix1 closed **and** Saad's go-ahead | — | none |
| closed | SMOKE-01 | orchestration smoke test: every path in README Files + CLAUDE.md Roles tables, and agent procedure pointers, exist on `main` | G1 ACCEPT WITH NOTES (1 minor), G2 n/a, G3 closed | `task/SMOKE-01` fc16525, `gate/SMOKE-01-qa` 3bb36f5 (not merged) | none |
| not started | T03 | official-repository move (decision #6), `python -m team init` | — | — | — |
| not started | T10 | "Changes since the last gate": GDD/Configuration still describe the LLM rival (Haiku 4.5, ~4 s decisions), which decision #3 replaced | — | — | — |

## Next eligible task

**T05-fix1 (resume)**, assigned to `tech-lead`. Brief: `tasks/T05-fix1.md`
(written for the sandbox; add a dated "Resumed" note with the local setup
from `tasks/_EXEC_COMMON.md`). Base `6692771`. The WIP snapshot `ab78522` is
unreviewed input the Tech Lead may read, not a base to trust. It unblocks
T07 training and T08. Gates: QA and Evaluation.

Can run at the same time (disjoint write paths): **GATE-wave3** (QA and
Evaluation reviews of T06b, T07, T14-fix1 on `orch/preview`), and
**T04-fix3 (resume)** (`pop/versus_runner.py`, `pop/seats.py` only).

Deadline pressure: G2/G3 recording and the official-repository move are due
**Sat 2026-11-28, 11:59 p.m.** (T03, `COURSE_ROLE_MAP.md`).

## Waiting on Saad

- **SMOKE-01 minor finding:** `CLAUDE.md:76` names `agents/rl/` and `docs/final/RL_POLICY.md`, which are not on `main` (only on `orch/preview`, T07). Either leave it until T07 merges, or approve a `CLAUDE.md` wording change such as "on `orch/preview`". Editing `CLAUDE.md` needs your approval.
- **SMOKE-01 branches:** `task/SMOKE-01` and `gate/SMOKE-01-qa` hold only the two reports. Merge them, keep them, or delete them (deleting needs you). The two worker worktrees are still registered.
- **Student decision** on `handoff-drafts/2026-11-24-qa-to-tech.md` (G2/G3 handoff).
- B2 "low suspicion" threshold (proposed below 50/100); D1 "on screen" = same room (proposed).
- T06b: confirm "a sprung trap costs 1 heart in all".
- T07: macro cadence (4 decisions), nearest-figure targeting, reward-shaping defaults.
- CLIMB down as well as up (T05-fix1's reading of G1 "climb").
- **Pushing:** AGENTS.md needs your approval to push; decision #14 chose Issues + PRs. Approve pushes per session, or say "push orch branches freely".
- **Course registration:** spawn the native `tech-lead`/`qa`, or the course-rendered `team-tech`/`team-qa`, once `agent-team/` exists (`COURSE_ROLE_MAP.md`).
- `inputs/FINAL_REQUIREMENTS.md` is now in this repository, which is public on GitHub. Confirm before it is pushed.
- Cloud sessions: the `agent` setting is not yet verified in Claude Code on the web.
- Official-repository move (decision #6) before Sat Nov 28, 11:59 p.m.

## Uncommitted work on Saad's checkout (not touched by agents)

`docs/agent-sessions/README.md`, `docs/final/EVIDENCE_INDEX.md` (modified),
`docs/agent-sessions/13-flip-audit-review-fixes.md` (untracked), as of 2026-11-24.
