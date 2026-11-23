# Common setup for the initial audit (AUDIT-A to AUDIT-D), 2026-11-23

All four audits are **read-only**. Nothing is written in either repository.

## Where things are (orchestrator sandbox)

| What | Path |
| --- | --- |
| Development repo, every branch, snapshot of Saad's local clone taken 2026-11-23 ~17:30 ET (`git bundle --all`) | `/home/claude/sm/mirror.git` (bare mirror) |
| Uncommitted changes on Saad's working tree (`final/versus-engine`): diff of `docs/agent-sessions/README.md` and `docs/final/EVIDENCE_INDEX.md`, and one untracked session record | `/home/claude/sm/inputs/sm-uncommitted.patch`, `/home/claude/sm/inputs/sm-untracked-13.md` |
| Official submission repo (course template, shallow clone of `main`) | `/home/claude/final-saadsatter` (read only; do not modify) |
| `FINAL_REQUIREMENTS.md` (claude.ai Project doc) | `/home/claude/sm/inputs/FINAL_REQUIREMENTS.md` |
| G1 pitch, slide summary | `/home/claude/sm/inputs/G1_PITCH_TEXT.md` |
| Orchestration files (`docs/final/orchestration/` in the repo once committed) | `/home/claude/sm/orch/` |

Make your own checkout; never share one with another auditor:

```
git clone -q /home/claude/sm/mirror.git /home/claude/sm/wt/<TASK-ID>
cd /home/claude/sm/wt/<TASK-ID> && git checkout -q <branch>
```

Use `git -C /home/claude/sm/mirror.git ...` for log, diff, merge-base,
show across branches. Known refs: `main` 0e5df5f, `level1-reconstruction`
2b5c909 (local; `origin/level1-reconstruction` is d5f6bda, they differ),
`final/g1-shadow-masque` 1b8d684, `final/art-pixellab` 3c0b0b4,
`final/agent-setup-online` dbb66ff, `final/versus-engine` 13c7488 (Saad's
current checkout). Remote-tracking refs are as of Saad's last fetch; GitHub
PR state is not available in this sandbox, so say "not verified" for PRs.

## Tests

`python3 -m pytest -q -p no:cacheprovider` (Python 3.13, pytest 9.1; the
project pins pytest<9 and Python>=3.11; pygame is not installed so frontend
tests skip). No network, no API keys, no `--live`. The orchestrator measured
`final/versus-engine` @13c7488: `419 passed, 12 skipped`.

## Report

Return the report format in `/home/claude/sm/orch/README.md`, with concrete
paths, commit shas and actual test output lines. Keep it under ~1,500 words
plus tables. Say plainly what you could not verify.
