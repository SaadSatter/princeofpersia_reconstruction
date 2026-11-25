# Shadow Masque: production orchestration

How the Production Orchestrator (the main Claude Code session, Opus 5.5)
delegates work to named Sonnet worker subagents, how work passes between them
as files in git, and how every finished feature gets independent review
before it is closed.

History. Created 2026-11-23 at Saad's request ("for each sub agent make a
separate md file for it to know its instructions and make it reproducible
and perform independent reviews in between finished features"). On
2026-11-24 it became a native Claude Code agent hierarchy, with a file-based
handoff chain, at Saad's request. Until then the orchestrator had run in a
claude.ai sandbox and started generic subagents with these files as
instructions. The task briefs from that period name sandbox paths
(`/home/claude/sm/...`); they are historical records.

These are **orchestration** files, not course `team` role files. See
`COURSE_ROLE_MAP.md` for how they relate to the formal course roles.

## The agents

| Agent (`subagent_type`) | Runs as | Model (pinned) | Native definition | Procedure |
| --- | --- | --- | --- | --- |
| Production Orchestrator | main session | `claude-opus-5-5` | `.claude/agents/orchestrator.md` | `agents/orchestrator.md` |
| `tech-lead` | worker, own worktree | `claude-sonnet-5-5` | `.claude/agents/tech-lead.md` | `agents/tech-lead.md` |
| `qa` | worker, own worktree | `claude-sonnet-5-5` | `.claude/agents/qa.md` | `agents/qa.md` |
| `evaluation-specialist` | worker, own worktree | `claude-sonnet-5-5` | `.claude/agents/evaluation-specialist.md` | `agents/evaluation-specialist.md` |
| `requirements-auditor` | worker, own worktree, read-only | `claude-sonnet-5-5` | `.claude/agents/requirements-auditor.md` | `agents/requirements-auditor.md` |
| `rules-reviewer` | worker, read-only, no shell | `claude-sonnet-5-5` | `.claude/agents/rules-reviewer.md` | itself |

- Each native definition holds only identity, model, tools, inputs, outputs
  and stop conditions. The detailed procedure lives once, in `agents/*.md`,
  and the worker reads it at the coordination commit. This keeps the two
  from drifting apart.
- The orchestrator's tool list allows only the agents above, plus `Explore`,
  `claude-code-guide` and `web-fetch` for lookups. A `general-purpose`,
  `claude` or `fork` spawn is refused.
- Workers have no Agent tool, so they cannot spawn agents or become
  orchestrators. `CLAUDE.md` tells a worker to follow only its own role file.
- There is no orchestration server, scheduler or database. The state is the
  files in this folder and the branches in git.

## Start and resume

Local terminal, from the repository root:

```sh
claude                          # uses "agent": "orchestrator" from .claude/settings.json
claude --agent orchestrator     # the same, explicit (overrides any other agent setting)
claude --agent orchestrator --continue        # resume the most recent session in this folder
claude --agent orchestrator --resume <id>     # resume a specific session
```

The project setting is checked in (`.claude/settings.json`):

```json
{ "agent": "orchestrator", "model": "claude-opus-5-5" }
```

A resumed or new session recovers task state from `STATUS.md`,
`REVIEW_LOG.md`, the decision records and the branches, not from the old
conversation (`agents/orchestrator.md`, section 1). A context compaction, a
usage limit or a killed session therefore loses only uncommitted work in a
worker's worktree. `git worktree list` shows any such worktree, and the
orchestrator preserves it.

**Claude Code on the web (cloud sessions).** A cloud session clones the
repository, so `.claude/settings.json` and `.claude/agents/` come with it if
they are on the branch the session starts from (push them first). Check the
model the session reports in its first reply. If the cloud environment does
not apply the `agent` setting, start the session's first message with:
"Act as the Production Orchestrator: follow
docs/final/orchestration/agents/orchestrator.md", and select Opus 5.5 in the
model picker. The named workers still come from `.claude/agents/`, with their
pinned Sonnet model. (Not yet verified in a cloud session; see `STATUS.md`.)

## Checking which models actually ran

Configured models are in the files above. Runtime models are in the session
transcripts Claude Code writes under `~/.claude/projects/<project>/`:

```sh
python3 tools/orchestration/verify_models.py --latest
python3 tools/orchestration/verify_models.py --session <session-id>
claude -p --output-format stream-json --verbose "..."   # init line: "model"; result line: "modelUsage"
```

`verify_models.py` prints the main session's model ids and, for each
subagent, its `agentType` (from `subagents/agent-<id>.meta.json`) and the
model ids on its API responses. Inside an interactive session, `/status`
shows the main model and `/agents` lists the registered agents.

These override the configuration, so check them when a model looks wrong:
`/model`, `--model`, `ANTHROPIC_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL` (with
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` it overrides pinned worker models),
`ANTHROPIC_DEFAULT_OPUS_MODEL` / `ANTHROPIC_DEFAULT_SONNET_MODEL`, managed
settings (`availableModels`), and `.claude/settings.local.json`. On
2026-11-24 none of them was set on Saad's Mac. The user setting
`"model": "opus"` is overridden by the project's `claude-opus-5-5`.

## Files

| Path | What it is |
| --- | --- |
| `agents/<role>.md` | The procedure for each role (orchestrator and the four workers) |
| `HANDOFF_PROTOCOL.md` | How work passes between agents as committed files; report fields; the chain |
| `COURSE_ROLE_MAP.md` | Native agents mapped to the course's formal production roles (G2/G3, G4) |
| `tasks/<TASK-ID>.md` | One brief per delegated task, committed to `main` before dispatch |
| `tasks/_EXEC_COMMON.md` | Shared setup for execution tasks (local worktrees, branches, trailer, test command) |
| `reports/<TASK-ID>-<role>.md` | A worker's report = its handoff, written and committed by the worker on its branch |
| `reports/_TEMPLATE.md` | The report template |
| `STATUS.md` | Current state: branches, tasks by state, next eligible task, waiting on Saad |
| `REVIEW_LOG.md` | One row per gate or chain event: task, gate, reviewer, model, commit, verdict, evidence |
| `PLAN-YYYY-MM-DD*.md` | Plans presented to Saad (status stated at the top) |
| `DECISIONS-YYYY-MM-DD.md` | Saad's answers, verbatim, with the orchestrator's reading of each |
| `handoff-drafts/` | Drafts of formal course handoffs until `agent-team/` exists. Saad writes every Student decision |
| `inputs/FINAL_REQUIREMENTS.md` | Saad's working compliance checklist (2026-11-23), copied unchanged from his claude.ai Project doc |

## The feature cycle and its review gates

No feature is closed on the implementer's word. A gate is a separate worker
that did not write the change.

```
brief @ main ─► tech-lead ─► [Gate 1: qa] ─► [Gate 2: evaluation-specialist] ─► [Gate 3: orchestrator] ─► close
                   ▲          reads the         reads QA's report;             reads every report,
                   │          tech-lead report  only for AI / boundary /       re-runs the tests,
                   │                            baseline / training / eval     checks the chain
                   └──── <ID>-fix<n> brief (at most 2, then escalate to Saad) ◄── any REJECT
```

1. **Implement.** The Tech Lead works on `task/<ID>` in its own worktree,
   commits failing tests first, then the change, then its report.
2. **Gate 1, QA.** QA reads the Tech Lead's report at its sha, checks out
   that exact commit on `gate/<ID>-qa`, runs and writes tests, and commits
   its report with a verdict.
3. **Gate 2, Evaluation Specialist**, when the change touches AI controllers,
   PPO observations, rewards or actions, hidden information,
   `pop/observation.py`, `pop/interface.py`, a runner, the scripted baseline,
   the macro layer, training or evaluation code, scenario definitions,
   replay or fallback. It reads QA's report first.
4. **Gate 3, orchestrator.** It reads every report from git, integrates the
   branches, re-runs the tests on the integrated commit, checks every
   acceptance criterion and the chain, and only then marks the task closed
   in `REVIEW_LOG.md`, `STATUS.md` and the checklist.
5. **Corrective work.** A `REJECT` becomes `<ID>-fix<n>`, and all the gates
   run again. After two rejected fixes the orchestrator escalates to Saad.

A gate is not skipped because the change looks small. Documentation-only
tasks go through Gate 1, with QA checking facts and links.

## Task brief template (`tasks/<TASK-ID>.md`)

```
# <TASK-ID>: <objective>
Handoff id: HO-<TASK-ID>-orchestrator
Assigned agent: <subagent_type> (procedure: agents/<role>.md)
Requirements: <FINAL_REQUIREMENTS section / label, checklist rows, R-V ids>
Decisions in force: <DECISIONS #n, quoted where they bind the task>
Context and dependencies: <what exists, what must land first, overlapping WIP>
Base: <branch and commit to start from>
Branch: task/<TASK-ID>
Permitted write paths: <explicit list; everything else is read-only>
Acceptance criteria: <numbered, each checkable>
Required tests: <names or behaviours; failing first>
Required gates: Gate 1 QA; Gate 2 Evaluation <yes/no, why>; Gate 3
Required evidence: <test output, trace, screenshot, report path>
Approval needed before: <anything in the approval list this task touches>
```

The orchestrator starts a worker with:

```
Read docs/final/orchestration/agents/<role>.md and follow it.
Coordination commit: <sha on main>. Your task brief: docs/final/orchestration/tasks/<TASK-ID>.md at that commit.
Consume: <report path> at <sha>          # reviewers only
```

## Test environment

```
uv run pytest -q                              # Saad's Mac and CI
python3 -m pytest -q -p no:cacheprovider      # where uv is missing (say which was used)
```

A skipped test is reported as skipped, not passed.

## What needs Saad's approval

Changing design or scope; changing evaluation success criteria; any paid
(`--live`) call; the full PPO training run; destructive git operations;
merging a PR; merging into `main` (except orchestration records, decisions
#11 and #29) or into the official repository; submitting graded work; release decisions;
editing `.claude/**`, `.codex/**`, `AGENTS.md`, existing tests,
`pyproject.toml`/`uv.lock` or the frozen midterm suite.

Pre-approved (decisions #27 to #29): pushing branches (never force), issues
and PRs for handoffs, and orchestration records committed to `main`.
