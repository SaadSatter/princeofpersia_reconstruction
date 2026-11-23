# Independent review: Level 1 reconstruction P0–P4 (pre-stabilization)

> **This review was made BEFORE the stabilization fixes.** It reviewed commit
> `8e68e568e14404998a68183a372d5f161f888563` (`8e68e56`). The fixes that followed
> (`b061194`, `e999181`, `a2b49ae`, `04cf17f`, session 10) are **not** reflected
> here. The findings below are preserved as they were reported and have not been
> revised in light of those fixes.

## Record

| Item | Value |
|---|---|
| Date | 2026-10-26 |
| Claude Code session identifier | `e30df6dd-58aa-41ba-813c-5570ce859320` (a shareable session link was not available to the agent; the identifier is from the session's local scratchpad path) |
| Orchestrating model | Claude Opus 5.5 (`claude-opus-5-5`), Claude Code CLI |
| Reviewer | `rules-reviewer` subagent (`.claude/agents/rules-reviewer.md`), tools Read, Grep, Glob only (cannot execute code or git) |
| Reviewer usage | 62 tool uses, 168,523 tokens, about 530 s |
| Reviewed branch | `level1-reconstruction` (local) |
| Reviewed commit | `8e68e568e14404998a68183a372d5f161f888563` |
| Commits in scope (vs `main`) | `f9c2c14` (S3 climb fix), `d5f6bda`, `f23efa9`, `78422ee`, `83892fc`, `8e68e56` |
| Mode | Read-only. No files modified, nothing committed, pushed, or synced to PR #57 during the review. |

### Scope (as requested by the student)

1. Fidelity of original Level 1 room layout, links, gates, plates, traps, sword pickup, and exit.
2. Whether L1-specific mechanics can affect the six frozen evaluation scenarios.
3. Whether all 16 committed traces still replay identically.
4. Hidden-state leakage in observations and action results, especially loose floors in adjacent unseen rooms.
5. Correctness of the S3 loose-floor climb crash fix.
6. Whether the 87-action successful route genuinely tests the intended Level 1 mechanics.
7. Missing mechanics that could make the current Level 1 misleadingly easy.
8. Documentation, provenance, and tests.

## 1. Run-time evidence collected by the orchestrator before the review

The reviewer cannot execute code, so the orchestrating agent ran these at
`8e68e56` and passed the results to the reviewer as given:

- `uv run pytest -q`: **251 passed, 1 skipped** (`tests/test_provider_sdk.py:13`, `anthropic` not installed). Working tree clean.
- `uv run pytest -v tests/test_trace_replay.py`: **17 passed**, i.e. `test_there_are_committed_traces` plus all 16 traces:
  `traces/dev/S3-scripted-route-100.jsonl`; `traces/eval/20261026T060347Z-baseline-{H1,H2,H3,S1,S2,S3}-{100,101}.jsonl` (12);
  `traces/live/{20261026T061626Z,20261026T162629Z,20261026T180142Z}-model-history-S1-0.jsonl` (3).
- `uv run python tools/fetch_level1.py --check`: "ok both files verified; Apple II and DOS layouts are identical; L1 loads".
- `tests/test_level1_original.py` (runs only with the local, git-ignored level file; **not in CI**): 6 passed, including `test_sword_route_completes_level1`. `tests/test_level1.py`: 14 passed.

## 2. `rules-reviewer` invocation (prompt as sent)

````text
Independent, READ-ONLY review of the Prince of Persia (1989) Level 1 reconstruction, phases P0–P4, on the local branch `level1-reconstruction` (project root: <project folder>). Do not modify any file. Do not approve the work; report findings for the student to decide.

Branch commits vs main (newest first): 8e68e56 docs P4; 83892fc fix bumped_ceiling revealed a loose floor in the unseen room above (audit F1); 78422ee frontend play L1; f23efa9 level1 as separate scenario L1 read from local file; d5f6bda Week 7 pair audit CLI; f9c2c14 fix loose ledge falling during a climb crashed or left the kid hanging on air (S3).

Read first: CLAUDE.md, docs/MIDTERM_GUIDELINES.md (authoritative rubric), docs/GAME_SPEC.md, docs/LEVEL1.md, docs/EVALUATION_SUITE.md, docs/RULE_SOURCE_MAP.md, docs/IMPLEMENTATION_PLAN.md, docs/agent-sessions/08-level1-reconstruction.md, docs/reviews/CHANGE-SUMMARY-session08.md, docs/ASSET_PROVENANCE.md. Then the implementation: pop/levelfile.py, pop/levels.py, pop/engine.py, pop/mechanics.py, pop/physics.py, pop/observation.py, pop/interface.py, pop/runner.py, pop/situations.py, evaluate.py, play.py, render/*, tools/fetch_level1.py, tools/solve_level1.py; and tests: tests/test_level1.py, tests/test_level1_original.py, tests/test_levelfile.py, tests/level_fixture.py, tests/test_trace_replay.py, plus any regression tests for the S3 climb crash and the bumped_ceiling leak (grep for test_regression_).

Run-time evidence I (the orchestrator) collected today, since you cannot execute code — treat as given, but check whether the tests actually assert what their names claim:
- `uv run pytest -q`: 251 passed, 1 skipped (tests/test_provider_sdk.py: `anthropic` not installed). Working tree clean.
- tests/test_trace_replay.py: 17 passed — test_there_are_committed_traces + 16 traces: [list as in section 1]. Please check WHAT "replays identically" compares (full per-step observation/state? outcome only?), and whether any trace was regenerated on this branch (git history of traces/ would show it; check the eval results JSON/table headers for engine version/hash fields).
- `tools/fetch_level1.py --check`: "ok both files verified; Apple II and DOS layouts are identical; L1 loads" (local git-ignored vendor/levels/LEVEL1 and res2001.bin present).
- tests/test_level1_original.py (runs only when the local file exists, so NOT in CI): all 6 passed, incl. test_sword_route_completes_level1 (87 actions, 798 frames per docs/LEVEL1.md, ends at 1 HP). tests/test_level1.py: 14 passed.

Review questions — answer each with severity (BLOCKER / HIGH / MEDIUM / LOW / INFO), file:line references, and concrete evidence (quote code/doc lines):
1. Fidelity of original Level 1 [...]
2. Can any L1-specific mechanic [...] change behavior of the six frozen evaluation situations (S1–S3, H1–H3)? [...]
3. Do all 16 committed traces genuinely replay identically, and is the replay test strong enough to detect divergence?
4. Hidden-state leakage in observations, legal_actions, and step/action results [...] Verify the 83892fc fix is complete and look for sibling leaks of the same shape.
5. Correctness of the S3 loose-floor-during-climb crash fix (f9c2c14) [...]
6. Does the 87-action successful route genuinely exercise the intended Level 1 mechanics [...]? Note it is not in CI.
7. Missing mechanics that could make the current Level 1 misleadingly easy [...]
8. Documentation, provenance, and tests [...]

Finish with: (a) a ranked findings list, (b) a list of BLOCKING findings, and (c) a verdict on whether P5 (combat: sword, guards, STRIKE/BLOCK/ADVANCE/RETREAT) can safely proceed, with any preconditions.
````

(`[...]` marks question detail shortened here for length; the absolute project
path is replaced with `<project folder>`. Nothing else was changed.)

## 3. Reviewer's report (original findings, unrevised)

**Redaction note.** Finding 7 originally quoted specific decoded Level 1
coordinates (gate, plate, guard and loose-floor positions). CLAUDE.md forbids
committing decoded original layouts "in any form", so only those coordinate
values are replaced with `[redacted: decoded L1 position]`. The finding, its
severity, and its file:line references are unchanged.

Read-only review. Nothing was executed. Original source was checked in the local, git-ignored copies
`vendor/ref-levels/src` (Apple II `.S`) and `vendor/ref-levels/sdlpop-src`.

### (a) Ranked findings

1. **[HIGH, blocking for P5 and for any further live trials on S3/H3/L1]** `pop/engine.py:241` (`_run`), `:256` (`_step`), `:269` and `:286` (`_jump`), `:315` (`_up` climbing from standing).
   - **The bug:** each of these picks a target cell before its frames run, then calls `_enter(target)` afterwards without checking `k.posture`. If the loose floor under the kid falls during those frames, `_tick` (lines 140-141) has already started his fall. `_enter` then moves him to the target with posture `"falling"`. Because the target has a floor, nothing resets the posture. On the next tick `_descend` (167-176) moves him into the cell below the target, even if that cell is a WALL; `supported(WALL)` is False, so he keeps falling.
   - **A standing JUMP (12 frames) or a standing-climb UP (12 frames) from a loose floor always hits this.** `_enter` starts the 10-frame timer when he arrives, so the floor always falls during the move.
   - **Concrete S3 path (traced by hand, not run):** in room 2, step RIGHT onto `L` at (1,5), then JUMP_RIGHT. The target is (1,8), which is floor. The floor falls at frame 10 and the step returns effect `fell`, posture `falling`, at (1,8). The next WAIT takes him down into (2,8) `#` and then to BOTTOM, ending in `died:fall`. In the original, that jump lands safely.
   - **Same root cause as f9c2c14.** That commit patched only the hanging branch of `_up` and `_down` (lines 295 and 359), so the fix is incomplete.
   - **Why the committed traces miss it:** I checked `traces/eval/*S3*`. The baseline's RUN_JUMP leaves the loose tile after 8 frames, so no trace exercises this.
   - **Fix needed:** add a posture check after the frames in every macro, with one `test_regression_*` per macro.
   - **Frozen suite:** fixing this changes S3/H-suite behaviour on paths no trace has recorded. That needs student approval and a change-log row.

2. **[HIGH]** `docs/ASSET_PROVENANCE.md:11,92` vs `docs/MIDTERM_GUIDELINES.md:125`.
   - The provenance doc says the course repo and PR #57 are **private**. The authoritative guidelines say "The course repository is public."
   - That premise is why the 207 PNGs were bundled, and D4 plans to add sword, guard and animation images in P5.
   - The reviewer did not check the repo's actual visibility. Settle this before the D4 art step.

3. **[MEDIUM]** `pop/mechanics.py:133` and `docs/RULE_SOURCE_MAP.md:59` (R-C09).
   - The code opens an exit only from a raise plate (`kind == T.RAISE_PLATE`).
   - In the original, `trigobj` (`MOVER.S:546-555`) sends any plate type to `openexit` for an exit target. Only gates check `pptype` (`MOVER.S:584-588`).
   - So the map row and the engine both differ from the cited code. The reviewer could not check whether L1's second drop plate links to the exit.

4. **[MEDIUM]** `pop/levels.py:96-109`: the "required" bit is ignored.
   - `level.required()` (`levelfile.py:72`) is never consulted. A loose tile with bit 5 set is therefore made breakable.
   - R-C14 and R-C31 say required pieces never break (`MOVER.S:395-397`).
   - The reviewer could not check whether any of L1's 12 loose tiles carry the bit. Either refuse such tiles, as R-D32 does for unsupported ids, or implement the rule.

5. **[MEDIUM]** The 87-action route (`tests/test_level1_original.py:74-85`) may rely on engine bugs; the reviewer could not check this.
   - `tools/solve_level1.py` is a breadth-first search over the real engine. It will use any bug-created moves, including finding 1's fall through floors and walls.
   - The test checks only `won`, 87 actions and the sword. It does not check that the kid is never inside a WALL cell, or never ends a step "falling" on a cell with a floor.
   - It also does not check which gates and plates were used, so LEVEL1.md:139-143's "necessarily uses their original plates" is unproven.
   - The route also depends on R-D01's exact 3/5-block jumps; the original jumps about 2.9/4.8 blocks (LEVEL1.md:152 lists this as unchecked).
   - It is not in CI. Re-solve after fixing finding 1 and add invariant checks to the test.

6. **[MEDIUM]** The frozen-suite guard is narrower than the claim in LEVEL1.md:50-55.
   - `test_frozen_suite.py` pins the definitions, the reset observation and the prompt.
   - `test_trace_replay.py:49-64` compares only `accepted`, `effect`, `frames`, the `kid` dict and the `room` per step, plus the outcome's reason, actions and frames. It does not compare tiles, `state` (gates, loose floors, spikes, plates) or `last_result.fell_rows`/`hp_change`, and it skips `call_limit` reasons.
   - The 16 traces cover few paths: 12 are baseline wins, the 3 live traces are S1 only, and one of them is 40 WAITs.
   - f9c2c14 already changed S3 behaviour on paths no trace covers (crash → fall), so "behave exactly as when recorded" is true only for the recorded paths.
   - Trace headers show `game_version` `0.1.0+3c4c210` (eval), `06ff044`/`b2a6e2a`/`c23ebf7` (live) and `0.1.0` (dev), so nothing looks regenerated. Git history was not checked.

7. **[MEDIUM]** Decoded original layout facts are committed in docs and tests, against CLAUDE.md "never commit … decoded original layouts … in any form".
   - `RULE_SOURCE_MAP.md:66-69`: gate, plate and guard positions `[redacted: decoded L1 position]`.
   - `AUDIT-2026-10-26-session08-level1.md:42`: a loose-floor position above another room `[redacted: decoded L1 position]`, and two further rooms `[redacted]`.
   - `LEVEL1.md:44-47,139-141`: the room graph and route.
   - `test_level1_original.py:53-58,74`: object counts, the start position and a full solution route.
   - `test_no_original_level_file_is_tracked_by_git` (`test_level1.py:68-77`) catches only the exact pinned binaries. The student needs to decide whether partial facts fall under D1.

8. **[LOW]** `RULE_SOURCE_MAP.md:66` (R-C29) is labelled `code`, but its only locator is SDLPoP, a C reimplementation. The map's own definition (`:9`) limits `code` to the 6502 source or decoded files. The Apple II conversion "was not located". Either label it `assumed` with SDLPoP as support, or widen the definition.

9. **[LOW]** `docs/LEVEL1.md:79` lists "Four potions, all heal +1" under "Implemented as in the original (evidence `code`)", but it rests on R-A03, which is `assumed`. The Apple II reads the type as `spec>>5` (`CTRL.S:2146-2151`), which gives 0 for a stored 1.

10. **[LOW]** `RULE_SOURCE_MAP.md:32` (R-C02): the locator `EQ.S:264` does not establish the L/R/U/D order. `CTRLSUBS.S:244-274` (`GETLEFT` `MAP-4` … `GETDOWN` `MAP-1`) does. The order is correct.

11. **[LOW]** `tests/test_level1.py:174`: `assert ep.legal_actions("kid") == list(ep.legal_actions("kid"))` is always true. No L1 test checks that legal actions depend only on posture. The leakage check (`:161-173`) runs only on the reset observation, not after changing rooms.

12. **[LOW]** `tests/level_fixture.py:15-19` encodes links as the exact inverse of `levelfile.link_chain`, so the CI tests are round-trips that cannot catch a shared misreading. The reviewer checked the decoder by hand against `MOVER.S:1561-1580` (`getscrn`) and `EQ.S:258-287`; offsets 2112/2119/2143/2215 are right. LINKLOC `$ff` ("linked to nothing", `MOVER.S:509-511`) is not special-cased; it decodes to a block-31 target, which does no harm.

13. **[LOW]** `docs/REQUIREMENTS_CHECKLIST.md` has no L1/session-08 entries (1a/1b/2c/3c evidence not updated).

14. **[INFO]** Hidden state (question 4): the 83892fc fix is complete for its branch.
    - `engine.py:324` names the effect only when `above[0] == k.room`. Frames (`JUMP_IN_PLACE`) are the same either way, and `loose_shaking` (`observation.py:53`) is filtered to the current room.
    - No other effect, error or `last_result` field was found that names an unseen tile.
    - Some adjacent-room facts still come out through physical results: `bumped`/`edge` at room edges (`engine.py:234,249`), climbing into the room above (`:309-316`), a hang into the next room (`:354`), and a crush from above (`:145`). Each matches what a human would see; this is existing design.
    - `room_label` (`observation.py:23-26`) is an unsalted, truncated SHA-1 of `"<sid>:<room>"`. Players have no tools, so inverting it is not a practical concern.

15. **[INFO]** Gating (question 2): L1-only behaviour is gated by `Situation.rules`, `start_falling`, `start_presses` and `gates_open`, and `test_level1.py:49-51` checks the suite's defaults. Apart from finding 1 and the f9c2c14 fixes, no ungated branch was found. `SWORD`/`BONES` join `HAS_FLOOR`, but the suite rooms never use them.

16. **[INFO]** The source citations check out: `SUBS.S:1516-1518` (`eor #$ff`, kid faces right); `SUBS.S:1540-1549` (`pushpp` at screen 5, then `stepfall`); `CTRL.S:1999-2005` (`touchceil`); `CTRL.S:2157-2162` (sword pickup); `seg008.c:1183-1194` (gate 1→188, potion `<<3`). Pressing a plate while hanging from it (`CTRL.S:1992-1994`) matches `_pressing` (`engine.py:126`).

### (b) Blocking findings

- Finding 1 (the macro posture bug: rule correctness in S3 and L1, an incomplete S3 fix, a possible route exploit).
- Finding 2 (the public/private contradiction, blocking for the D4/P5 art step).

### (c) P5 verdict

**Do not start P5 yet.** Preconditions:

1. Fix finding 1 in every macro, with `test_regression_*` tests (standing jump from loose, standing climb from loose, run/step with the timer running out mid-move, run-up), with student approval and a change-log row for the S3 behaviour change.
2. Re-solve L1 and add invariant checks to the route test (finding 5).
3. Resolve findings 3 and 4, or show they don't arise in L1.
4. Settle finding 2 before adding any images.
5. Decide on finding 7.
6. For combat itself:
   - Gate the new actions per scenario. `LEGAL_BY_POSTURE` (`engine.py:25-31`) is global, and the suite's legal lists and the model prompt hash must not change.
   - Keep guard state (position, alert from `alertguard` when plates are pressed or loose floors break, `MOVER.S:459-460`, `CTRL.S:1986-1987`) out of observations for other rooms.
   - Run `/game-rules-audit` plus an independent review on that change.

**Not checked by the reviewer:** anything needing execution; git history of `traces/`; `pop/runner.py`, `agents/`, `render/*` beyond a grep for hidden-state access (none found), `test_level1_frontend.py`, and the session 08 log; whether the course repo is actually public; the 6502 port-vs-paraphrase question beyond spot checks (no copied tables seen in the files read).

## 4. Orchestrator verification of the reviewer's unverified points

After the report, the orchestrating agent ran throwaway scripts from the session
scratchpad (not committed; no repository file changed) at `8e68e56`:

- **Finding 1 reproduced in S3.** `Episode("S3")`, seed 100, with the kid placed at room 2 (1,4) facing right:
  `RIGHT` → `moved`, standing on `L` at (1,5); `JUMP_RIGHT` → effect `fell`, posture `falling`, at (1,8) on floor `_`;
  `WAIT` → posture `dead` at (2,8), a `#` wall cell; outcome `died:fall` after 3 actions, 21 frames.
  Control: `JUMP_RIGHT` from (1,4) (solid floor) → `jumped`, standing at (1,7).
- **Findings 3 and 4 do not arise in Level 1** (checked against the local file). None of the 12 loose tiles has the required bit, and the only plate linked to the exit is a raise plate. Both remain latent code-vs-source differences.
- **Finding 5 confirmed: the 87-action route uses finding 1.** Replaying `SWORD_ROUTE` with invariants (no step ends inside a wall; no step ends `falling` on a supported cell) flagged step 5 (`JUMP_RIGHT`): effect `fell`, posture `falling` on floor. Step 6 (`WAIT`) moved the kid into the next room with effect `hurt` (HP 3 → 2). The route still ends `won`.

## 5. Status at the time of the review

At `8e68e56`, the review recommended that **P5 combat should not proceed**
until findings 1 and 2 were resolved and preconditions 2–6 were addressed.
Fixes made afterwards (session 10) are recorded separately in
`docs/reviews/CHANGE-SUMMARY-session10.md` and the session log, and are not
assessed here.
