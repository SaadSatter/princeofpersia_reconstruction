---
task: T09
from: evaluation-specialist
to: orchestrator
base: 0ea8d73
status: STOPPED at step 1 (health re-check); H6 NOT run
consumed: docs/final/orchestration/tasks/T09.md@8efab43
---

# T09 evaluation report: stopped at step 1

**Verdict: no H6 verdict. The held-out comparison was not run.** The ledger has no claim.

## Step 1 result (tuning split, scratch key and scratch out outside the repository)

- Shipped weights SHA-256 80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c equals `SHIPPED_SHA256`; loads; sizes (251, 64, 64, 9), `N_FEATURES` 251, 8 macros (9 slots): match.
- `--split tuning --configs SvS,MvS,SvM --trials 3`: 141 rows, 0 aborted, 0 fallbacks, 0 refused, 0 errors, 0 timeouts, 0 busy, 0 invalid, both seats. Commit 0ea8d73, clean tree. Measured latency of the PPO seat in the first MvS row: mean 0.26 ms, max 1.7 ms.
- **0 stale: FAILED.** Summed over rows, stale_inputs A=12, B=9 (replaced_inputs A=846, B=831, which the brief does not count).
  Every stale row is a scripted seat: D1-a, D1-c and their -B mirrors in SvS (1 or 2 per row), and F5-c/SvM (seat A, scripted, 1 per trial). No row where the PPO seat is the stale seat; the PPO seat has 0 stale.
  Mechanism (`pop/versus.py` line 755): a pending macro input is no longer legal when it is applied, so it is dropped and the frame is free. The scripted baseline does this on its own in SvS, so it is not caused by the PPO rival.

## Why I stopped

The brief says "0 stale for both seats" and "if anything fails: stop, do not run H6". The held-out run is one-shot and cannot be repeated, so I did not read the criterion loosely. Whether baseline-only stale inputs should block H6 is the orchestrator's (or Saad's) call. If the criterion should have read "the PPO seat has 0 fallbacks, invalid and stale, and no seat has aborts", it is met. I did not run steps 2 and 3, made no ledger row, and changed no code, weights, H6 or PROTOCOL.

Scratch outputs are in `$TMPDIR/t09` (outside the repository, not committed). Not run: the test suite (step 2).
