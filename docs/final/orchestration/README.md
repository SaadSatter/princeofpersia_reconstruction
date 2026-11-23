# Shadow Masque — production orchestration

How the central orchestrator delegates work to subagents, and how every
finished feature gets an independent review before it is closed. Everything
here is plain Markdown so any session (Claude Code, Codex, or a person) can
reproduce a run from the files alone.

Created 2026-11-23 at Saad's request ("for each sub agent make a separate md
file for it to know its instructions and make it reproducible and perform
independent reviews in between finished features"). These files are
**orchestration instructions**, not course `team` role files. They do not
count as formal production agents and are not rendered by `python -m team`.
The formal Tech Lead and QA roles belong in the official repository's
`agent-team/roles/`, created with `python -m team init` and rendered by
`python -m team render` (see the plan's decision list).

## Files

| Path | What it is |
| --- | --- |
| `agents/tech-lead.md` | Implementation subagent. Builds approved tasks, writes failing tests first, hands off to QA |
| `agents/qa.md` | Independent QA subagent. Runs tests, writes tests, reproduces failures; never edits game code |
| `agents/evaluation-specialist.md` | Reviews AI-rival changes and the evaluation harness; owns evaluation scenarios and analysis |
| `agents/requirements-auditor.md` | Temporary read-only worker that checks the project against `FINAL_REQUIREMENTS.md` |
| `tasks/<TASK-ID>.md` | One brief per delegated task: objective, write paths, acceptance criteria, required tests |
| `reports/<TASK-ID>-<agent>.md` | The subagent's report as saved by the orchestrator (any condensing is stated at the top) |
| `PLAN-YYYY-MM-DD.md` | Reconciled plan presented to Saad for approval (status stated at the top) |
| `DECISIONS-YYYY-MM-DD.md` | Saad's answers, verbatim, with the orchestrator's reading of each |
| `tasks/_EXEC_COMMON.md` | Shared setup for execution tasks (sandbox clone, branch, commit trailer, test command) |
| `handoff-drafts/` | Drafts of formal course handoffs, until `agent-team/` exists; Saad writes every Student decision |
| `REVIEW_LOG.md` | One line per review gate: task, reviewer, verdict, evidence, follow-up |

A subagent is always started with the same two-line prompt, so a run can be
repeated:

```
Read docs/final/orchestration/agents/<role>.md and follow it.
Your task brief is docs/final/orchestration/tasks/<TASK-ID>.md.
```

The orchestrator adds only facts that are not in the files (for example the
path of a fresh worktree). Anything else it wants a subagent to know goes
into the task brief first.

## Sources every subagent reads

1. `AGENTS.md`, `CLAUDE.md` (project invariants; they always win).
2. `FINAL_REQUIREMENTS.md` (claude.ai Project doc; a copy is given with each
   task).
3. `docs/final/README.md`, `docs/final/REQUIREMENTS_CHECKLIST.md`,
   `docs/final/EVIDENCE_INDEX.md`, `docs/final/VERSUS_SPEC.md`.
4. Its own role file and task brief.

## The feature cycle and its review gates

No feature is closed on the implementer's word. Each one passes these gates
in order; a gate is a separate subagent that did not write the change.

```
Task brief ──> Tech Lead ──> [Gate 1: QA] ──> [Gate 2: Evaluation Specialist,  ──> [Gate 3: orchestrator ──> close, update
 (approved)    implements                       only if AI, observation,             re-runs the tests,       checklist and
               + handoff                        action set, runner or harness        checks the evidence]     tracker
                                                changed]
                    ^                │                    │
                    └── corrective task (max 2) ──────────┘
```

1. **Implement.** The Tech Lead works in its own worktree and branch,
   writes failing tests first, commits locally, and returns the report in the
   format below plus a handoff summary for QA (`what changed`, `how to
   check it`, `what I am unsure about`).
2. **Gate 1, QA.** QA checks out the exact commit, runs the full suite and
   the task's required tests, tries to break the acceptance criteria, writes
   any missing tests under `tests/` (in its own commit), and returns a verdict:
   `ACCEPT`, `ACCEPT WITH NOTES` or `REJECT`, each finding with severity and
   reproduction. A test QA adds that fails against the change is a finding,
   not something QA fixes.
3. **Gate 2, Evaluation Specialist** (when the change touches
   `pop/observation.py`, `pop/interface.py`, `pop/runner.py`, `agents/`,
   `evaluate.py`, the macro-action vocabulary, prompts, or anything a seat can
   see). Same verdicts, focused on knowledge boundary, baseline fairness,
   fallback and evaluation validity.
4. **Gate 3, orchestrator.** Re-runs the test command on the merged-candidate
   commit, reads both verdicts, and checks that every acceptance criterion
   has evidence. Only then marks the task done in `REVIEW_LOG.md`, the
   checklist and the tracker.
5. **Corrective work.** A `REJECT` becomes a new brief `<TASK-ID>-fix<n>` for
   the Tech Lead, then the gates run again on the fix. After two failed
   corrective attempts the orchestrator stops and escalates to Saad with the
   evidence.

A gate is not skipped because the change looks small. Documentation-only
tasks go through Gate 1 with QA checking facts and links instead of code.

## Formal course handoffs

Internal gate reports are not automatically course handoffs. When Saad
chooses a gate review to become a formal handoff, the receiving agent's
findings are written to `agent-team/handoffs/YYYY-MM-DD-<from>-to-<to>.md`
(in the official repository, from `team/defaults/handoff-template.md`), and
Saad fills **Student decision** himself. Agents never write a student
decision, an origin note's friction, or anything in Saad's voice.

## Task brief template (`tasks/<TASK-ID>.md`)

```
# <TASK-ID>: <objective>
Assigned agent: <role file>
Requirements: <FINAL_REQUIREMENTS section / label, checklist rows, R-V ids>
Context and dependencies: <what exists, what must land first>
Base: <branch and commit to start from>
Permitted write paths: <explicit list; everything else is read-only>
Acceptance criteria: <numbered, each checkable>
Required tests: <names or behaviours; failing first>
Required evidence: <test output, trace, screenshot, report path>
Approval needed before: <anything in the "ask Saad" list this task touches>
```

## Report format (every subagent, every task)

```
Task ID / status: <done | partial | blocked> 
Summary: <3–6 lines>
Files changed: <paths>
Commit or diff: <sha on branch, or "none (read-only)">
Tests executed: <exact command> -> <actual result line>
Evidence: <paths>
Limitations and blockers:
Recommended next action:
Decisions requiring Saad:
```

Plain rules: never report a test as passing that was not run in this
session; separate what was observed from what is suspected; never treat a
plan, a replay or a fixture as a live result.

## Test environment

The project needs Python 3.11+ and `pytest`. Run the suite from the
repository root:

```
uv run pytest -q            # Saad's machine / CI
python3 -m pytest -q -p no:cacheprovider   # orchestrator sandbox (Python 3.13, pytest 9; pygame absent, so frontend tests skip)
```

Record which one was used. A skipped test is reported as skipped, not passed.

## What needs Saad's approval

Changing design or scope; changing evaluation success criteria; any paid
(`--live`) model call; destructive git operations; pushing or merging into the
official repository; submitting graded work; release decisions; editing
`.claude/agents/**`, `.claude/skills/**`, `.codex/agents/**`, `AGENTS.md`,
existing tests, `pyproject.toml`/`uv.lock` or the frozen midterm suite.
