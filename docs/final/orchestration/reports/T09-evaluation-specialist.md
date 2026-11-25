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

## Stale diagnostic (tuning split only, never H6, no ledger)

Method: the same scratch seed key, `--split tuning --configs SvS,MvS,SvM --trials 3`, on two trees. Post-T19 = `0ea8d73`. Pre-T19 = a scratch copy of `0ea8d73` with `pop/engine.py` and `pop/versus.py` replaced by their `fc02687` versions (`fc02687` itself has no `evaluation/` or `tools/eval/`, and `git diff fc02687 0ea8d73 -- pop agents` touches only those two files, so this is the pre-T19 engine under the same harness). The tree is not a git checkout, so its rows record commit "unknown"; used for diagnosis only.

Numbers (141 rows each): stale per seat is **identical on both engines**. SvS: A 9, B 9. SvM: A (scripted) 3, B (PPO) 0. MvS: A (PPO) 0, B (scripted) 0. Invalid 0. Replaced inputs also identical (MvS A 78; SvM A 48, B 111; SvS 720 and 720). 0 of 141 rows differ in stale count, replaced count or `final_snapshot_sha256`. The rows are the same five (start, config) groups every trial: D1-a SvS (1), D1-c SvS (2), and the -B mirrors, and F5-c SvM seat A (1). **So stale inputs are not a T19 effect**; they were there before T19 and T19 changes none of these tuning trajectories.

What is dropped (probe on the post-T19 engine, logging at `pop/versus.py` line 755): a scripted seat's queued directional input (UP at frames 1422 and 1710, both with move `_HOP_FLIP_RIGHT`; LEFT at 1578 with `RUN_JUMP_RIGHT`; F5-c: LEFT at frame 156, `RUN_JUMP_RIGHT`) arrives as the previous move finishes in a **fall** (posture `falling`, legal actions only WAIT). The input would have been refused anyway, so the drop costs the baseline no action it could have taken; the real event is that the baseline's hop-flip or run-jump ended in a fall (pit ahead). SvS D1 is symmetric, so A and B drop at the same frames.

Does the PPO seat face the same? Mechanically yes: any controller decides every 6 frames from the legal list at decision time, so a move that ends in a fall can strand a queued input. The PPO seat had 0 stale in every MvS and SvM row here, but those are 3 deterministic repeats of the same few starts, so that is not proof it cannot happen on H6.

Bias on H6: stale is a symptom, not an extra handicap. The drop removes only an input that was illegal in a fall. The baseline's fall (hurt, positioned away, lost frames) is a real baseline weakness on hazard-ahead starts (H6-5, H6-6, H6-8). That would favour the PPO seat if the PPO seat avoids the pit, and it is a confound to report beside the existing "hazard-ahead" flag, not a harness fault. It does not affect the bar mechanics (14 of 16 duels, no abort).

**Recommendation:** read the health criterion as "0 aborted, 0 fallbacks, 0 invalid on both seats; 0 stale on the PPO seat; baseline stale reported per row". The criterion text (PROTOCOL H-c "0 for both") does not distinguish seats, so Saad should confirm this wording, but waiting for a baseline fix is not justified: the stale counts are unchanged by T19, are the baseline's own pit falls, and a baseline change after seeing this would alter the baseline between tuning and H6 (and is outside this task's permitted writes). I did not change H6, PROTOCOL or the bar. H6 has still not been run.
