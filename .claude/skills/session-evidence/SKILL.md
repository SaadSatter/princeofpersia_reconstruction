---
name: session-evidence
description: Write or refresh the redacted evidence record for one or more Claude Code or Codex sessions in docs/agent-sessions/, using tools/evidence/extract_sessions.py, and update docs/agent-sessions/README.md and docs/final/EVIDENCE_INDEX.md. Records session ids, roles, Saad's instructions, what was done, test results, commits, PRs and artifacts. Never invents session links, invocations or results. Use after an implementation, skill or review session, or to document historical sessions.
argument-hint: "<session id prefix(es) | latest> [role] [title]"
allowed-tools: Read, Grep, Glob, Edit(docs/agent-sessions/**), Write(docs/agent-sessions/**), Edit(docs/final/EVIDENCE_INDEX.md), Edit(docs/final/REQUIREMENTS_CHECKLIST.md), Bash(python3 -I tools/evidence/extract_sessions.py:*), Bash(python3 -I tools/evidence/scan_secrets.py:*), Bash(git log:*), Bash(git show:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(gh pr view:*), Bash(gh pr list:*), Bash(ls:*)
---

# Session evidence

Sessions to record: **$ARGUMENTS**

Turn local session transcripts into evidence files a grader can check, in the
style of the existing `docs/agent-sessions/NN-*.md` records. You record what
happened. You do not judge the work, and you never fill gaps with
likely-sounding facts.

## Hard rules

1. **No fabrication.** The session URL is "None. Local session; no shareable
   URL was created." unless Saad gives you a link in this session. Never
   build a URL from an id. Never record a test, commit, PR, skill invocation
   or review that the transcript or git does not show.
2. **Separate the sources.** Mark a claim **verified** only when git, GitHub
   or a command you ran in this session confirms it. A claim that comes only
   from the recorded agent's own message is the **agent's report**.
3. **Classify honestly.**
   - Codex `codex-auto-review` (guardian) transcripts are permission checks,
     not reviews.
   - Configuration smoke tests are not skill invocations.
   - A subagent spawned by the implementing session is not an independent
     review.
   - A skill counts as invoked only if the transcript shows it was loaded or
     read by name.
4. **Redact.** The extractor passes every string through
   `tools/evidence/redact.py`. Before finishing, run
   `python3 -I tools/evidence/scan_secrets.py docs/agent-sessions docs/final`.
   It must report 0 findings. Never print a secret, even to explain a finding.
5. **Never commit raw transcripts or the facts file**, and never copy whole
   long briefs; quote them truncated.
6. **Do not write Saad's voice.** Leave `AGENT-TEAM.md`, decisions,
   playtest interpretations and reflections to Saad.

## Procedure

1. **Extract** to the scratchpad, outside the repository:
   `python3 -I tools/evidence/extract_sessions.py --out <scratch>/facts.json --exclude <this session's id prefix>`.
   For `latest`, choose the most recent transcript for this repository,
   excluding the session you are running in.
2. **Write** `docs/agent-sessions/NN-<slug>.md` with the next unused number:
   - header table: tool, session id, date range (UTC), model id, branch,
     role and its instruction file (`CLAUDE.md`, a skill, or a reviewer
     config), whether it is independent of the builder, session URL;
   - Saad's instructions, quoted and truncated;
   - 3–8 bullets: what was asked, what was done, what was verified, what was
     not done or failed;
   - commits (check with `git log`/`git show`) and PRs (`gh pr view`); when a
     time-window commit could belong to an overlapping session, say so;
   - tests run and their reported result, labelled verified or agent's report.
3. **Index.** Add the session to `docs/agent-sessions/README.md`, and to the
   rows it supports in `docs/final/EVIDENCE_INDEX.md` (including the
   "Skill and reviewer invocations" table). Change a status in
   `docs/final/REQUIREMENTS_CHECKLIST.md` only when the evidence now exists,
   and link to it.
4. **Scan and report.** Run the secret scanner. Then tell Saad which files
   you wrote, the session ids recorded, anything you could not verify, and
   the scanner result.

Do not commit unless Saad asks.

## Invocation

```text
/session-evidence latest
/session-evidence 2d9cf368 implementation "Final-project agent setup"
/session-evidence 01a1bc9f review
```

The course counts a reusable skill when it is invoked by name in at least two
separate sessions. Record each invocation of this skill in the evidence file
of the session it ran in.
