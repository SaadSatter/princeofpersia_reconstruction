# T03-fix1: refresh the official snapshot from main 803092f (decision #131)

- Assigned: tech-lead; then qa (Gate 1); Gate 3; then the orchestrator merges official PR #2 (#131).
- Target: official `g23-migration` (head d907859). Push only that branch.
- Do: replace `game/` with a fresh `git archive` of this repository's `main` at 803092f, by the same method and rules as T03 (only `assets/original/MANIFEST.tsv` from `assets/original/`; no level data, secrets or raw transcripts; `traces/` absent except what is tracked). Keep everything outside `game/` (template, `agent-team/`, README, `final.yml` with the T31 subset) unchanged, except README links if a path moved. Confirm `game/docs/final/SCOPE_LOCK.md` still equals the approved file, and `agent-team/handoffs/2026-11-24-qa-to-tech.md` is unchanged. Run the T31 subset from `game/`, `python -m team validate`, render and the drift check.
- Report on `task/T03-fix1` in this repository: the diff summary `d907859..<new head> -- game/` (file count, notable additions), checks and results.
