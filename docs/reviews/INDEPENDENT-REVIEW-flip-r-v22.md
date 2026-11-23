# Independent review: flip (R-V22)

- **Date:** 2026-11-18
- **Reviewer:** `rules-reviewer` agent (`.claude/agents/rules-reviewer.md`),
  read-only tools (Read, Grep, Glob), started from the audit session, not
  from the session that built the flip.
- **Scope:** commits `8c2d9bd` and `05fe136` on `final/versus-engine`
  (base `339cbdb`), at `05fe136`.
- **Independence:** the reviewer read
  `docs/audits/AUDIT-2026-11-18-flip-r-v22.md` (findings section). It says it
  did so after forming its own findings, and it notes the overlap.
- Everything below the line is the reviewer's output, unedited.

---

[blocking] pop/versus.py:128-143 (Rival.blocks / Rival._can_vault), docs/final/VERSUS_SPEC.md:103, tests/test_flip.py:140-148 — R-V22 says a body in another room "still blocks, as before, so a jump never reveals someone out of sight". That is false. The block is itself what gives the body away. The test named `..._is_not_revealed` actually shows the leak. — From (2,0,8) facing right with nobody in (3,0,0), JUMP_SPAN=3 targets (3,0,1): `motion.to` is None and A ends in room 3. With B at (3,0,0), A's `motion.to` is [0,9] from the first frame and A stays in room 2 (the test asserts exactly this). The arena layout never changes, so a seat that has seen room 3 knows (3,0,0) is floor and can tell a rival or guard is standing there out of sight. Running into that cell ("bumped") leaks the same way. This was already true before the flip, but the flip's spec, rule-map row and test now claim it is closed. A real fix would treat out-of-room bodies as not blocking at take-off and settle any overlap on arrival. A leak test should compare A's observations with and without the hidden body; it would fail today.

[should fix] pop/versus.py:341-346 (Duel.landings), 333-339 (cell_free_for_guard); pop/guards.py:182-186 — The landing claim covers landing cells in any room. A running jump (or a standing jump from the room edge) that lands in the next room makes a guard there pause and turn around (PATROL_PAUSE, then turn) up to one flight before the jumper appears. A seat in that room sees a guard react to something it cannot see. It also stops a guard's `moved` action short in `_complete` (guards.py:144). — Only claim cells in the jumper's own room. No test covers this channel.

[should fix] pop/versus.py:341-346, 573-582 (Duel._separate) — Only guards are kept out of a landing cell. The other rival, disguised or not, can walk, run or be pushed (`_push` → `_free` → `blocks`) into it during the flight. On arrival `_separate` sends the jumper back to its take-off cell: after a full flight shown heading for `motion.to`, it ends up on the near side of the body it flipped over. R-V22 says it "lands beyond (never on anyone)" and does not specify this case. If the jumper's next pending move started in the same `_advance`, `_separate` also moves it after that move's first frame. No test covers either case.

[should fix] pop/versus.py:479-480, 346-353 via pop/engine.py:346-354 — Where a jump lands depends on seat order. Jump targets are computed in `_advance(A)` before B's arrival for that frame is applied, while contacts are resolved on the frame's end state. — Example: A at col 2 facing right does JUMP_RIGHT on the frame B's run arrives at col 4 from col 5. As seat A it sees B at col 5 and plans a plain jump to col 4, onto B's new cell, which then ends in the snap-back above. With the seats swapped it sees B at col 4 and flips to col 5. The audit's G5 probe only covered a mutual flip from standing. A swap-seat test is missing.

[should fix] tests/test_flip.py (whole file); tests/test_disguise.py — Missing leak tests for the new hidden facts:
- Flipping over a disguised rival vs over a real guard in the same cell and pose, checking both seats' observations frame by frame. No R-V22 test exists in test_disguise.py at all.
- An observer in another room never receives `flipped` or `motion` for that jump.
- The cross-room guard reaction above.
- A seat sending `_HOP_FLIP_LEFT` is refused. The audit says this was probed, but no committed test checks it.
- A determinism trace that includes a hop-flip and a running flip.

[should fix] docs/RULE_SOURCE_MAP.md:156 — The R-V22 `design` row gives Saad's decision and a spec section, but no rationale and no rejected alternative (rubric 4a). VERSUS_SPEC mentions "no separate key" and the out-of-sight reason, but the row should name the alternatives it beat: a separate FLIP input, and flips over bodies only. Its "bodies in another room still stop it" wording repeats the false guarantee from the first finding.

[note] pop/versus.py:511-518, 533-540 — The hop-turn window lasts one frame past the hop. `_hop_turn` is checked before `next(gen)`, so a direction pending on the tick when the 8-frame hop would raise StopIteration still becomes a flip, although the hop's animation (JUMP_IN_PLACE=8) has finished. VERSUS_SPEC says "A direction after the hop has landed is an ordinary move". `test_a_direction_after_the_hop_lands_is_an_ordinary_move` checks after JUMP_IN_PLACE+1 ticks, so the boundary is untested.

[note] pop/versus.py:533-540 (DIRECTIONAL) — Any pending STEP_d, JUMP_d or RUN_JUMP_d (as well as LEFT/RIGHT) turns a hop into a standing flip of span 3. A RUN_JUMP sent mid-hop silently becomes a 3-cell standing flip. When the versus AI seat is built (agents/ has no versus player yet), its action description must explain that a direction sent mid-hop is reinterpreted. Otherwise the model's input means something different from what it was told.

[note] pop/versus.py:151-162 with pop/engine.py:360 — For a hop-flip or a running jump, `last_result.effect` is "jumped" while `motion.effect` is "flipped". The two parts of one seat's observation disagree.

[note] pop/versus.py:333-339 — A disguised rival is the only "guard" that can step into a jumper's landing cell. Real guards are kept out by the engine, so a "guard" that walks in is known to be the other rival. This is not a field leak, but it is a deterministic behavioural tell that the flip makes more likely. Applying the same-room landing claim to rivals as well would remove it and the snap-back.

[note] tests/test_flip.py:114-119 — The guard-flip test uses a guard facing away. A guard facing the jumper sees and stabs it at its take-off cell mid-flight (it keeps its cell until it lands). That matches "a lunge into that cell still hits it", but whether "guards can be flipped over" includes an alert guard is Saad's call and is not written down.

[note] render/versus_view.py:49-50, 125-136 — Every `flipped` motion is drawn as a standing-jump clip with the spin timed to the standing jump's take-off at 20%. A running jump leaves the floor at frame 0 (pop/engine.py:345, depart=0), so its picture stays grounded for the first ~20% of a flight the engine treats as airborne (sweeps miss, KICK legal). This affects the picture only.

[note] docs/final/VERSUS_SPEC.md:103 — The R-V22 table row has a fourth cell holding a stray sentence ("Swords dropped in a room stay there; they are visible to whoever is in that room."), which breaks the 3-column table. The sentence seems to belong after the table.

Single-player and midterm invariance: no finding. `Game._can_vault` returns False and `Game._jump_look` returns "jumped" (pop/engine.py:103-112). With these, the new loop at engine.py:346-361 is equivalent to break-on-block, and `_jump_look` only feeds the display-only `plan`. tests/test_trace_replay.py replays all 16 committed traces against golden full-state fingerprints. pop/situations.py was not touched by these files.

Headless and input mapping: no finding. pop/versus.py imports no pygame. play.py `versus_input` emits only seat-vocabulary actions (RUN_JUMP_*, JUMP_*, LEFT/RIGHT, STEP_*). `running_dir` reads only the seat's own `me.motion` and submits through `ep.legal_actions`/`ep.step`. The hop-to-flip runs inside the engine, so agent seats get the same behaviour.

Files read:
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/CLAUDE.md
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/AGENTS.md
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/pop/engine.py (lines 60-460)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/pop/versus.py (full)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/pop/guards.py (lines 80-202)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/pop/physics.py (constants, by search)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/play.py (lines 40-270)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/render/versus_view.py (full)
- render/draw.py, render/dungeon.py, render/anim.py (flip/spin lines, by search)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/tests/test_flip.py (full)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/tests/test_disguise.py (full)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/tests/test_trace_replay.py (full)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/docs/final/VERSUS_SPEC.md (lines 60-213)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/docs/RULE_SOURCE_MAP.md (lines 1-30, 140-157)
- /Users/saadsatter/Classes/AI_Pract_Building_Games/princeofpersia_reconstruction/docs/audits/AUDIT-2026-11-18-flip-r-v22.md (lines 70-101; read after forming my own findings, which overlap on the landing-claim and cross-room issues)
- agents/ (search only: no versus player exists)

Not checked:
- docs/MIDTERM_GUIDELINES.md, docs/final/REQUIREMENTS_CHECKLIST.md, GDD.md, CONFIGURATION.md, GAME_SPEC.md, docs/REQUIREMENTS_CHECKLIST.md, EVALUATION.md, traces/: not touched by the two commits under review, so I did not do a full rubric walk this session.
- pop/interface.py, pop/observation.py, pop/runner.py, evaluate.py, .github/workflows/, ci/: not changed by these commits. Episode limits (3b) and CI (3c) were not re-checked.
- server/ and web/: they do not exist, so the online boundary (item 8) is not applicable yet.
- Git diffs of 8c2d9bd and 05fe136: I cannot run git. I reviewed the current file contents, so I cannot confirm exactly which test_disguise.py lines the commits added (no R-V22-specific test is present in it).
- The reference source: R-V22 is `design` with no `code` locator. Inherited `code` locators were not verified by the reviewer.
- I could not run anything, so the pytest results and the probe scenarios above come from reading the code, not from running it. The flip picture was not checked by eye.
