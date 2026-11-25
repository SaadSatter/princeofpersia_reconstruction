# Wave-2 reports, 2026-11-24 early hours — condensed by the orchestrator

## GATE-w2 (QA b56e573; Eval d2e7a00) on int/wave2 cd5c4aa
- T01-fix1 + T01-fix2: QA ACCEPT WITH NOTES, Eval ACCEPT.
  - Revert experiments confirm each fix is tested (R-V26 23 fails, QA3 4, QA1 3, L2 3).
  - Eval differential 83127cf→cd5c4aa: changes explained by R-V26 and QA3.
  - QA's harder harness shows L2 also changes the hash: reword the session note to "R-V26, QA3 and L2".
  - Cosmetic: a76b3a7 trailer says Opus but was written by a Sonnet subagent (trailer rule fixed in _EXEC_COMMON).
  - New confounds: TAKE spam wastes frames; the linger change makes pre-fix tuning runs incomparable.
- T04-fix2: QA and Eval ACCEPT WITH NOTES.
  - Spoof, decision_every and sequential cross-runner busy are all closed.
  - Eval confirms the implementer's flip of its probe.
  - Both found a minor race: runners started concurrently in threads can call a shared controller at once (busy is recorded only after a timeout). Fix: mark in-flight at call start under the lock, or document "trials sharing a controller run sequentially". xfails GATE-w2-QA-1 / GATE-w2-eval-1.

## GATE-T05-qa (Sonnet) dec85c8 on 19b5da2: ACCEPT WITH NOTES
- Determinism (including fast path), boundary (replay of 4 recorded duels gives identical inputs; no engine imports), executor (13,175 decisions in 40 random-room duels, 0 illegal) all met.
- Majors: QA-2 lone-guard rule loses to WAIT (40 random starts: 22 W, 8 L, 10 timeouts); QA-3 SEARCH stays on one row of rooms; QA-1 mirror match deadlocks (10/10 draws, no hearts lost; sweeps in step).
- Minor: decide crashes on a None or malformed policy tuple. All forwarded to T05-fix1.

## T07 (Tech Lead, Sonnet): PPO stack built, full training not started (as instructed) — 6cea0a9 tests, 1e34cf2 implementation, base 6692771
- agents/rl/ (encoder, mask, weights loader with hash, PolicyMacro, make_rl_rival; stdlib only).
- tools/rl/ (env, numpy PPO, train CLI); docs/final/RL_POLICY.md; session record 11-* (number collides).
- 829 passed, 12 skipped, 3 xfailed.
- Encoder leak test runs the real engine (disguised vs guard identical over time); key-access spy; minutes_left and outcome never read; order invariance; mask; deterministic rollouts; parity 1e-9 over 200 observations; hash checked (wrong, tampered, missing); smoke run under 60 s.
- Open: the target rule is "nearest non-downed figure" (I3 partly depends on it); macro_every 4 decisions (2 s); shaping +0.1 per heart dealt, -0.1 per heart taken, +0.05 per disguise (default on); only 2 tuning starts; 2-worker determinism untested; 85-min cap.

## T06b (Tech Lead, Sonnet): rival-rigged loose floor — 61e4ffb spec, d390998 32 failing tests, 9af96a9 implementation, 4e9121b record (base cd5c4aa)
- 810 passed, 12 skipped, 3 xfailed.
- Covered: RIG action; 12-frame kneel (the trap is spent at start); springs on any body; one-shot; double rig; traps_left; my_traps; +3 suspicion per kneel frame when disguised in sight (36 total).
- Gate plate not built (macro shape not decided; slam harm needs pop/mechanics.py).
- Open:
  - legality reads visible tiles only (stricter than the spec, to avoid leaking room links);
  - "1 heart in all" adds a heart on short falls (Saad to confirm);
  - a disguised kneel is masked as standing still by R-V25;
  - ModelPlayer prompt ignores my_traps (irrelevant now that the rival is PPO);
  - RIG_TRAP must map to RIG in the agents.

## T14-fix1 (Tech Lead, Sonnet): ca3667b (tests first dcae399), base 4bbabec (int/wave2-web)
- 896 passed, 12 skipped, 3 xfailed.
- SeatControllerRival(every=6); the baseline is the page default; fresh controller per game; agents/ in game.zip (stdlib); smoke checks position and pixels (text-tested only); key hints per seat; ?label=neutral; build hash on the page; WEB_BUILD.md playtest notes.
- Edited three existing tests inside its permitted web test paths (test_web_build, test_web_bridge, keys.test.js), to allow agents/ in the zip and the new defaults.
- Still unrun in a browser or CI.
