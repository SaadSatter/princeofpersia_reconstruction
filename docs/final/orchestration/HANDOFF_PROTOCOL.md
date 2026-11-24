# Handoff protocol

How work passes between agents as files in git. Adopted 2026-11-24 at Saad's
request, after the professor's clarification that a genuine handoff is one
agent writing its results into a GitHub-tracked file or artifact, and the next
agent reading that file before it continues.

## The rule

1. **The producer writes the handoff.** Every worker ends its task by writing
   its report to `docs/final/orchestration/reports/<TASK-ID>-<role>.md` and
   committing it on its own branch, together with its work. The report is
   its handoff to the next agent.
2. **The receiver reads it at a commit.** The next worker reads that file
   with `git show <sha>:<path>` before doing anything else, and records the
   path and sha under `consumed:` in its own report.
3. **The orchestrator reads them all.** Before Gate 3 the orchestrator reads
   every report in the chain from git, checks that the `consumed` links run
   unbroken from the brief to the last report, and logs the chain in
   `REVIEW_LOG.md`.
4. **Nothing is reconstructed silently.** If the orchestrator has to save a
   worker's returned message itself (a worker without write tools, such as
   `rules-reviewer`, or a session that ended before committing), the file's
   first line says so:
   `> Saved by the orchestrator from the worker's returned message; not written by the worker.`

## The chain

```
                    tasks/<ID>.md @ main (coordination commit)
orchestrator ──────────────────────────────────────────────► tech-lead
                    reports/<ID>-tech-lead.md @ task/<ID>
tech-lead ─────────────────────────────────────────────────► qa
                    reports/<ID>-qa.md @ gate/<ID>-qa
qa ────────────────────────────────────────────────────────► evaluation-specialist   (Gate 2 tasks)
   └──────────────────────────────────────────────────────► orchestrator             (other tasks)
                    reports/<ID>-evaluation-specialist.md @ gate/<ID>-eval
evaluation-specialist ─────────────────────────────────────► orchestrator
                    REVIEW_LOG.md row + Gate 3 note @ main
orchestrator ──────────────────────────────────────────────► Saad
```

A `REJECT` at any gate goes back to the orchestrator, which writes
`tasks/<ID>-fix<n>.md` for the Tech Lead. The fix then runs the whole chain
again. After two rejected fixes the orchestrator escalates to Saad.

## Handoff ids

`HO-<TASK-ID>-<role>`, for example `HO-T05-fix1-qa`. A task id is used once,
and fixes get their own ids (`T05-fix1`, `T05-fix2`), so the id is unique.
The orchestrator's brief counts as handoff `HO-<TASK-ID>-orchestrator`.

## Report fields

Every report starts with this front matter and keeps these headings. The
full template is `reports/_TEMPLATE.md`.

| Field | Meaning |
| --- | --- |
| `handoff_id` | `HO-<TASK-ID>-<role>` |
| `task_id` | the brief's id |
| `date` | ISO date and local time (ET) |
| `from` / `to` | producing role / receiving role (`orchestrator` when the chain ends) |
| `configured_model` | the model pinned in your `.claude/agents/<name>.md` |
| `runtime_model` | always `not visible to the agent`. The orchestrator fills the verified value in `REVIEW_LOG.md` from transcript metadata |
| `consumed` | `<path>@<sha>` of the brief or report you read first |
| `source_branch` / `source_commit` | the branch and commit you produced or reviewed |
| `reviewed_commit` | reviewers: the exact commit under review |
| `verdict` | reviewers: `ACCEPT`, `ACCEPT WITH NOTES` or `REJECT`; producers: `n/a` |

Body headings: Work completed · Paths · Acceptance criteria → evidence ·
Tests run (exact command → actual result line) · Findings (severity) · Known
limitations · Unresolved findings · Requested next action · Student decision
required.

## Commits

- A worker commits its work and its report on its own branch, in its
  isolation worktree. The report may be in the same commit as the work or the
  commit after it. `source_commit` names the commit that holds the work.
- The orchestrator merges `task/<ID>` and `gate/<ID>-*` into the integration
  branch, so the reports travel with the code they describe.
- `REVIEW_LOG.md` and `STATUS.md` on `main` point to every report by branch,
  path and sha, so `main` alone is enough to resume.
- Commit trailer for workers: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`
  (the configured model; the verified one is in the review log).

## GitHub

When Saad has approved pushing for the session (AGENTS.md), the orchestrator
pushes the branches and opens a PR for each integrated task. The PR body
lists each report as `path @ sha` and quotes each verdict line. QA and
Evaluation findings may also be posted as PR comments (decision #14). A
report counts as published only after `git ls-remote` or `gh` shows it.

## Formal course handoffs are different

A course handoff (`agent-team/handoffs/YYYY-MM-DD-<from>-to-<to>.md`, from
`team/defaults/handoff-template.md`) is created only when Saad picks an
internal handoff to become one. Until `agent-team/` exists, drafts live in
`handoff-drafts/`. Saad writes every **Student decision** himself. See
`COURSE_ROLE_MAP.md`.
