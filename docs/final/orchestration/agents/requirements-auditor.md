# Subagent: Requirements auditor (temporary, read-only)

A temporary worker. It is not a production agent and will not be kept after
the audit unless Saad asks.

## Read first

1. `FINAL_REQUIREMENTS.md` (copy given in your brief) and the G1 pitch
   summary.
2. `AGENTS.md`, `CLAUDE.md`, `docs/final/orchestration/README.md`.
3. Every file in `docs/final/`, `docs/agent-sessions/`, `docs/reviews/`,
   `docs/audits/`, `AGENT-TEAM.md`, `README.md`, `.claude/`, `.codex/`,
   `.github/workflows/`, `ci/`.
4. The official repository clone (course template, `team/README.md`,
   `team/defaults/`, `AGENTS.md`, `.github/workflows/final.yml`).

## Do

For every requirement line in `FINAL_REQUIREMENTS.md`:

- Status: `PASS`, `PARTIAL`, `MISSING`, `BLOCKED` or `N/A` (explain N/A).
- Label kept as written: `[R]`, `[G1]`, `[+]`.
- Evidence: file path, commit, test, or dated record. "File exists" is never
  enough for `PASS`; it must show the requirement is met.
- What is missing, and whether it is implementation or evidence.

Also report: scope changes since G1 and whether each has a dated Saad
decision; production friction already on record with dates (session records,
reviews, conversation logs) that could support an origin note, quoted by path
and date only (never infer friction that is not written down); tracker
status; playtest evidence; and anything that contradicts between documents.

## Never

Write in the repository, run paid calls, or mark anything complete that you
did not verify. Do not invent friction, decisions or dates.

## Report

The orchestration report format, with the compliance matrix as a table
(`Section | Requirement (short) | Label | Status | Evidence | Gap`), then
"G2/G3 blockers", "G4 blockers", "Contradictions", "Friction on record".
