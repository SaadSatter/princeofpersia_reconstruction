# GATE-T14 QA (Gate 1, Sonnet) on e6c274d — condensed by the orchestrator
ACCEPT WITH NOTES. gate/T14-qa 9499a4e (incl. a Node vm contract test running the real main.js against recorded payloads with fake Pyodide/Phaser/DOM; mutation-checked). 578 passed, 12 skipped, 1 xfailed.
Met: key parity; local-mode keys independent; determinism; archive completeness and reproducibility; JS–Python contract; workflows least privilege; docs commands work.
Findings:
1. [major] The rival hook does not fit T05: `WebGame(rival=make_baseline())` gives TypeError (MacroController is not callable; the bridge calls every tick; the controller expects a 6-tick cadence, a tuple, and WAIT as a no-op). A 12-line adapter gave 24 inputs and 0 invalid over 600 ticks. WEB_BUILD.md's "any callable plugs in" overstates it.
2. [minor] smoke.cjs passes even with a dead key handler (it only checks the frame counter); xfail QA-T14-1.
3. [minor] Key hints are for seat A only; press(None) raises (unreachable from the page).
4. [minor, unverified] Pinned CDN versions were chosen from memory; no SRI hashes.
Not checked: real browser, workflows not run, Pyodide timing; outcome.reason left to the Evaluation gate.
