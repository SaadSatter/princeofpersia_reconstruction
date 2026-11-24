# Reports, 2026-11-23 late evening — condensed by the orchestrator

## T02-close (QA, Sonnet): ACCEPT — 72f6552 on task/T02-close (base 03856b9)
Removed only the 5 T02 xfail marks; read each assertion (WAIT and DOWN masked, UP costs 48 suspicion: passes via its "costs suspicion" branch by design). 650 passed, 12 skipped, 2 xfailed (the remaining 2 are T04 QA-5 and eval-1). Handoff draft: "Closing evidence" added; Student decision left empty. Notes: an unused EXPECTED_TELLS and an outdated docstring; the handoff's Produce/Accepted sections still describe the xfails as open (superseded by the closing evidence).

## T06a (Tech Lead, Sonnet): traps spec proposal — bac29a1, docs/final/TRAPS_SPEC.md only
R-V27..R-V34.
- RIG: on the plain floor cell ahead, standing; 12-frame kneel; a hit cancels it and the trap is spent; disguise kept, +3 suspicion per frame in a guard's sight.
- Loose floor springs on any body (1 heart, downs guards). Gate plate slams the room gate (only the Gatehouse and Undercroft have gates).
- 4 per rival, shared; one-shot. Double rig allowed (refusing it would leak).
- Tiles look normal to every seat. The owner gets `my_traps` and `traps_left`, with the same shape for both seats.
- Macro RIG_TRAP. 8 leak tests. G2 minimum: loose floor only.
- Decisions: one-shot vs re-arm 120 frames; ahead vs under feet; 4 shared vs 2+2; disguised rigging +3/frame vs illegal in sight; gate slam 1 heart vs block only; double rig; 12-frame kneel and spent-on-cancel; macro shape; G2 = loose floor only.
(Its "5 failed" was the pre-T02-close XPASS state, not caused by the doc.)

## T05 (Tech Lead, Sonnet): macros + competent scripted baseline — 2f927c4 failing tests, 19b5da2 implementation (base 03856b9)
agents/macros.py (MacroExecutor, MacroController, FieldView), agents/versus_baseline.py (FigureTracker, VersusBaseline), docs/final/MACROS.md, session record 14 (number provisional).
- Vocabulary: BLEND, DISGUISE, WAIT, FOLLOW, STRIKE, FLEE, CLIMB, plus **SEARCH** (new: room-to-room movement; needs approval under CQ-1). RIG_TRAP is reserved.
- Executor plans from `me.motion.to` (no idle gap), re-validates every input, and has a cooldown of 5 decisions after a failure.
- Baseline tells, all visible to a human: a "guard" that jumps, climbs or flips; runs unarmed; is still for more than 24 frames while unarmed; or does not draw within 12 frames on an undisguised rival in sight. Sweep then lunge.
- Results, 2 seeds, seats swapped: vs WAIT 8/8 tuning and 16/16 held-out; vs Random 8/8 and 16/16. Competence against passive seats only.
- Throughput about 2,100 decisions/s (default) and about 3,000 (fast path). Suite 671 passed plus the 5 pre-T02-close XPASS.
- Unsure: the swap-a-guard test only covers short sequences; tells were never tested against a disguised AI; SEARCH stays on the current row of rooms; TAKE no_uniform compatibility not tested against T01-fix1.

## T14 (Tech Lead, earlier model): hosted web build — partial — aa66b60 failing tests, 444cb92 implementation, e6c274d docs (base 83127cf)
Files: web/bridge.py (WebGame; rival hook with placeholder IdleRival/RandomRival, both labelled), render/draw_list.py, render/webart.py (stdlib PNG), web/index.html, web/main.js (draws only), web/keys.js plus a Node test, web/versions.json (Pyodide 0.27.7, Phaser 3.88.2, Playwright 1.49.1: chosen from memory, never fetched), tools/web/build.py (two builds byte-identical), tools/web/smoke.cjs, .github/workflows/pages.yml (deploy needs pages:write and id-token:write), .github/workflows/web-smoke.yml, docs/final/WEB_BUILD.md. 560 passed, 12 skipped.
Not run in a browser at all (the CDN is blocked; headless Chrome shows `loadPyodide is not defined`, as expected). Workflows not run (nothing pushed). Decisions: pinned versions; deploy permissions; human keys (WASD for seat A); rematch with the same seed; terminal reason shown even if the death happened out of view.
