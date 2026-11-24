# GATE-T14 Evaluation Specialist (Gate 2, Sonnet) on e6c274d — condensed by the orchestrator
ACCEPT WITH NOTES. gate/T14-eval 8de230a (tests/test_gate_t14_eval_boundary.py); 562 passed, 12 skipped, 1 xfailed.
No leak in the human payload. Probed: every key; 240 random ticks; a hostile rival that scrambles its view changes nothing.
Notes:
1. [low] outcome.reason printed raw ("You lose (won:B)"). It reveals draw:both_died, which the player did not see. Recommendation: in human_vs_ai show only win/lose/draw/time up (xfail strict test). This conflicts with Saad's decision #25 ("the end screen states how the duel ended"). Decision #25 stands unless Saad changes it.
2. [info] Shared guards make seat A's view diverge with the AI seat's actions even in another room. That is world behaviour, not a bridge leak.
3. [cosmetic] same-cell figure order (fixed by T01-fix1 L2).
Plug-in path for T05:
- an adapter is needed (MacroController.decide vs the hook's `rival(obs, legal)`);
- pass a tuple;
- map WAIT to None;
- the bridge calls the rival every tick, bypassing the T04 runner (limits, fallback, traces, cadence not in force in the web build).
Runtime: bridge tick about 0.7 ms in CPython; a pure-Python MLP about 1.8 ms. A wide margin even at 10x Pyodide, but unmeasured in Pyodide. T07 inference must be stdlib-only, with weights inside game.zip.
Playtest:
- game.zip is public (engine, baseline, weights);
- the query string is editable;
- the rival label must be neutral for blind Session B;
- the protocol should say devtools stay closed;
- show the build hash on the page for the log;
- IdleRival makes Session A meaningless until the baseline is plugged in;
- rematch with the same seed is a learning confound across rounds.
Unverified (no browser): Pyodide/Phaser API use, 12 Hz clock, pinned versions, workflows, drawing fidelity; no SRI hashes.
