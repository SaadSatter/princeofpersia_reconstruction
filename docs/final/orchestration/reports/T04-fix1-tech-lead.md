# T04-fix1 report (Tech Lead, earlier model), 2026-11-23 — condensed by the orchestrator
Status: partial (all routed findings fixed except eval-1, mitigated by an opt-in key). task/T04-fix1 (/home/claude/sm/wt/T04-fix1), base af76c30: f1bd7c7, 2fb60ff failing tests -> 93c8cc6 fix -> 616ba8d docs.
Tests: before fix 45 failed; at 616ba8d 524 passed, 12 skipped, 2 xfailed; scratch merge with task/T01 617 passed, 12 skipped, 2 xfailed; runner files ×5 runs stable.
Gate xfails removed: QA-1..4, eval-2..4. Kept: QA-5 (Saad), eval-1 (default unkeyed). Orchestrator verified the two gate files differ from the gate branches only by the removed marks.
New: plain-str normalisation; unprintable repr/str handled; decide and reset under timeout; busy controller (no concurrent calls; fallback reason busy; counts toward max_fallbacks); BaseException -> error; VersusLimits validation; controller_seed HMAC with seed_key (opt-in); on_frame(frame, EpisodeView) runner-side hook; copy_mode json / threaded False fast path (defaults unchanged, recorded in result and trace header); VERSUS_RUNNER.md documents in-process isolation by convention.
Throughput: default ~3,800 decisions/s; threaded=False ~6,300; both ~6,400.
Unsure: busy keyed per runner instance; timing tests use short sleeps; EpisodeView hiding by convention; JSON copy turns tuples into lists.
Decisions: QA-5; eval-1 default; cadence 6 / 5 s; aborted vs forfeit; exact-name validation.
