# Native agents and the course's formal production roles

The native Claude Code agents in `.claude/agents/` are how work gets done in
this repository. The course's production roles (`python -m team` in the
official repository `columbia-university-ai-games/final-saadsatter`) are what
is graded at G2/G3 and G4. The two overlap, but they are not the same thing.
This file maps one to the other so nothing is double-counted.

Written 2026-11-24. Course facts come from the official repository's
`team/README.md`, `team/defaults/roles/{tech,qa}.md`, `AGENTS.md` and
`.github/workflows/final.yml` as read on 2026-11-24 with `gh api` (private
repository), and from `inputs/FINAL_REQUIREMENTS.md` section 4.

## Mapping

| Native agent | Course role id | Counts as a formal production agent? | Notes |
| --- | --- | --- | --- |
| Production Orchestrator (main session) | none | **No** | Execution architecture only. Saad remains Executive Producer and Creative Director and holds the producer duties the course assigns to him |
| `tech-lead` | `tech` (Tech Lead) | **Yes**, a G2/G3 starter, once `agent-team/roles/tech.md` exists and is tailored | The course file is `agent-team/roles/tech.md`, rendered to `.claude/agents/team-tech.md`. The native file `.claude/agents/tech-lead.md` carries the procedure |
| `qa` | `qa` (QA) | **Yes**, a G2/G3 starter, once `agent-team/roles/qa.md` exists and is tailored | Rendered to `.claude/agents/team-qa.md`. Course rule kept: QA writes tests, never game code |
| `evaluation-specialist` | none yet | **No**, unless Saad adds it with an origin note backed by real, dated friction that predates its first commit (721b3e6, 2026-11-23) | Never counted automatically |
| `requirements-auditor` | none | **No** | Temporary worker |
| `rules-reviewer` | part of `qa`'s rule-change check | No (it is a review task, as in the course starter) | The course QA role's `rules` slot already says "Run rules-reviewer on any change to a rule or the player interface" |
| In-game PPO rival | none | No | "Your in-game agent is separate" (`team/README.md`) |

## Avoiding conflicting registrations

`python -m team render` writes `.claude/agents/team-<id>.md` and
`.agents/skills/team-<id>/SKILL.md`, and leaves other agents alone. The
native names here (`orchestrator`, `tech-lead`, `qa`, `evaluation-specialist`,
`requirements-auditor`, `rules-reviewer`) never begin with `team-`, so the
files cannot collide. Once `agent-team/` exists in the official repository,
two registrations describe the same course role (`team-tech` and
`tech-lead`; `team-qa` and `qa`). The rule then is:

1. The course role file (`agent-team/roles/<id>.md`) is the formal source.
   Saad tailors it, `render` generates `team-<id>.md`, and nobody edits the
   generated file by hand.
2. The native worker keeps its procedure and names the course role file as
   one of its inputs. The orchestrator spawns the native worker (`tech-lead`,
   `qa`), and the worker reads `agent-team/roles/<id>.md` too.
3. If Saad prefers a single registration, the orchestrator spawns `team-tech`
   and `team-qa` directly. That choice is his. It is listed under "Waiting on
   Saad" in `STATUS.md`.

`agent-team/` does not exist yet: `python -m team init` has not been run.
The official-repository move is decision #6, due Sat 2026-11-28 11:59 p.m.

## G2/G3 (recording Sat 2026-11-28)

| Requirement (`FINAL_REQUIREMENTS.md` section 4, `team/README.md`) | Plan | State on 2026-11-24 |
| --- | --- | --- |
| Tailor the two starters (tech, qa) to Shadow Masque | `python -m team init` in the official repository. Saad (or the Tech Lead under a brief) tailors `roles/tech.md` and `roles/qa.md` from `agents/tech-lead.md` and `agents/qa.md`, then runs `render` | Not started: no `agent-team/` |
| One routed handoff with a student decision | **Saad's choice, decision #7:** "Yes let this be my tech handoff". The QA re-review of 13c7488 (T02) returned to the Tech Lead (T01). Draft: `handoff-drafts/2026-11-24-qa-to-tech.md` | Draft ready. **Student decision empty, for Saad.** It moves to `agent-team/handoffs/2026-11-24-qa-to-tech.md` |
| Coverage map: every role one line | `other-roles.md` lists producer, design, art, narrative, bi, release, each as named agent, student, or "not needed" with a reason | Not started. Every line is Saad's call |
| At least one genuine file-based handoff | The T02 → T01 chain is file-based: a review document and xfail tests on a branch, read by the implementer. From 2026-11-24 every chain follows `HANDOFF_PROTOCOL.md` | Met by T02/T01 (evidence: `REVIEW_LOG.md` 2026-11-23/24) |

## G4 (recording Sat 2026-12-05)

| Requirement | What it needs | Rule this repository follows |
| --- | --- | --- |
| At least three production agents | tech, qa, plus one more, **added with `python -m team add <role>`** | The third role comes only from real friction. Candidates are listed below with their evidence, but the orchestrator does not choose one |
| Origin note with two dated friction instances, before the agent's first commit | `handoffs/YYYY-MM-DD-student-to-<role>.md`, "Why this agent", two or more links | Link only friction already on record. Never write the friction for Saad |
| Chain of three roles, two handoffs, each with a student decision | For example `<third role>` → `tech` → `qa` | Each handoff is a committed file written by the producer (`HANDOFF_PROTOCOL.md`), copied into the course format. Saad writes each Student decision |
| Revise one agent because a handoff exposed a weakness | Edit `agent-team/roles/<id>.md` after a committed handoff from it, then run `render` (coverage map shows `revised`) | Record before and after, and link the triggering handoff |

**Friction already on record** (from `reports/AUDIT-D-requirements.md`,
paths and dates only; whether any of it justifies a role is Saad's decision):

- Design: dfc8ade (2026-11-17), 05fe136 (2026-11-17), session record S13
  (2026-11-23), S06 (2026-10-26).
- Art: S12 (2026-11-17), fbcff5b, 3784127, fa086fe.
- Evaluation/live: S04 (2026-10-26), S09, S03.
- Release/provenance: c3aa550, bb89412, 0e5df5f (2026-10-26), S05–S07.

## What never counts

The orchestrator, temporary workers (`requirements-auditor`, any one-off
worker), the Evaluation Specialist (unless Saad adds it), the in-game rival,
and any handoff without Saad's own Student decision.
