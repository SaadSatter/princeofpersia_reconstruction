# GATE-T05 Evaluation Specialist (Gate 2, Sonnet) on 19b5da2 — condensed by the orchestrator
ACCEPT WITH NOTES. gate/T05-eval 015a769 (tests/test_gate_t05_eval_baseline.py: 1 passed, 5 xfailed strict).
- No leak: a key-access logger shows the baseline reads only human-visible fields; minutes_left, swords, seed and episode are never read. Swap-a-guard holds by construction (R-V18). The TAKE-not-in-legal probe disappears with R-V26; re-check after merging T01-fix1.
- **Gap 1 [blocking for evaluation]:** no descent. SEARCH and FLEE use left/right edges only, CLIMB only goes up, and RoomView treats a drop as death. From the default start the baseline visits only the top-row rooms and never gets a uniform (they are only in rooms 4 and 5). A WAIT rival in rooms 4–6 is never found: 6/6 draws (xfail GATE-T05-eval-2). This is a vocabulary limit that the PPO rival shares.
- **Gap 2:** rule 5 strikes any lone armed guard at hp ≥ 2. From rooms 4 or 5 vs WAIT it lost 8/8 to the guard (xfail GATE-T05-eval-1).
- Undisclosed asymmetry: the baseline keeps memory (tracker counters, visited rooms, a tried set). Disclose it, or give PPO the same memory.
- Competence beyond passive opponents is untested: baseline vs baseline over 12 duels gave 10 draws and 2 B wins.
- Held-out starts are weak (column shifts within the top row). Their order in the commits is fine (fixed in 2f927c4), but "no tuning after looking" rests on the author's word.
- Confounds: D1 is not reachable by the baseline; I3, F5, H6 are not evaluable on the current starts; report results per seat (seat A resolves first).
