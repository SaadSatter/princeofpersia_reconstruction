# T23 session: a released direction never runs after landing (decision #93)

Tech Lead worker (Claude Sonnet 5.5), 2026-11-25, branch `task/T23` from `a93d36a`.

- Reproduced Saad's sequence through `WebGame` and `VersusEpisode`: after a flip left with left
  released before landing, the queued LEFT started on the landing tick and was logged.
- Failing test first (`tests/test_t23_release.py`), then `VersusEpisode.release(seat)` and one
  `else` branch in `WebGame.tick`. Rule row R-V36 in `docs/RULE_SOURCE_MAP.md`.
- `play.py --versus` has its own input loop; it needs the same one-line call and was left
  alone because T22-fix2 owns it. Reported to the orchestrator.
- No paid calls, no training. The engine's AI path (`step` from controllers) is untouched.
