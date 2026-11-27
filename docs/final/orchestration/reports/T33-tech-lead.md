---
handoff_id: HO-T33-tech-lead
task_id: T33
date: 2026-11-27 16:20 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T33.md@ab395fc; docs/final/orchestration/reports/T33-evaluation-specialist.md@0d73e48; decision #135 (main 43e9ce1)
source_branch: task/T33
source_commit: see "Commit to review" (the work commit; this report's own commit follows it)
reviewed_commit: n/a
verdict: n/a
---

# T33: tech-lead report

Status: done

## Work completed
Stage 2a: audited the XGJT-001 telemetry. The replay is FULL: the repository's own `server.trace.replay` reproduces the recorded outcome and state hash. Stage 2b: rendered ticks 216 to 465 with the real renderer. Stage 2c: screenshots, demo configuration and runbook. Stage 2d: the 7-slide deck (editable pptx with notes and the MP4 embedded), PDF through Keynote, slide JPGs, narration script. Slide 3 and 6 numbers follow the T33-eval fact sheet and its wording limits; slide 4 follows decision #135.

## Stage 2a verdict: replay is FULL (state, inputs, AI actions, events)
- The playtest is room XGJT, duel 1 (LOG.md section 3). XUKM is Human vs Human.
- `server.trace.replay` on `docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json`: outcome `won:B`, 465 frames, state hash `5dadb78e1da67d1fb312711bd48dbc60a2a4f71f5000fb00b14ec1463572a910`, equal to the recorded hash; the whole outcome dict is equal.
- Game version: telemetry header `6eaced529faf`, LOG.md `cca7002`; `git diff --stat` of `pop server agents render web play.py` from each to `ab395fc` is empty.
- Replay events against the telemetry log (rooms 67/153/246, hits 417/441/465, sword drop 465, idle 240 to 372): all agree. Full table: `presentation/REPLAY_AUDIT.md`.
- **Not supported by the replay (agrees with T33-eval N6):** "disarming" (the only sword drop is the human's own THROW input at tick 463, drop at 465); "defeating scripted guards" (a guard goes down at 327, no attacker recorded; B alone acted nearby and lunged at 325; the human sent nothing from 240 to 372); "identify" and "locate" (not measurable). Slide 4 shows Saad's notes verbatim as his and a separate "Replay shows" box (decision #135). The video captions state only replay facts.
- Limits: the video is seat A's view drawn by the pygame renderer with the generated art; the player used the Phaser client (same engine state, different drawing program). Frames before tick 216 are not shown.

## Paths
All under `presentation/`: `render_replay.py`, `shots.py`, `build_deck.py`, `export_keynote.applescript`, `README.md`, `REPLAY_AUDIT.md`, `DEMO_RUNBOOK.md`, `NARRATION.md`, `SUITE_RESULT.txt`, `shots/*.jpg`, `out/ShadowMasque-G2G3.pptx`, `.pdf`, `xgjt-001-segment.mp4`, `out/slides/slide-00N.jpg`. Plus this report. Images are `.jpg` because `tests/test_frontend.py::test_tracked_images_are_the_bundle_or_nothing` fails on any tracked `.png` (my first run hit exactly that).

## Acceptance criteria → evidence
| # | Criterion (brief / spec) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Stage 2a: identify XGJT duel 1, check replay, verify events, say full/partial/impossible | Met: full | REPLAY_AUDIT.md |
| 2 | Real renderer, 20 to 25 s, label "External playtest — reconstructed from telemetry", MP4 | Met | out/xgjt-001-segment.mp4: 22.83 s, h264, 960x672, 24 fps (ffmpeg -i); 20.8 s of play plus 2 s hold; label on every frame |
| 3 | Screenshots slides 1, 2, 4, demo configuration and runbook with exact commands and fallback | Met | shots/, DEMO_RUNBOOK.md; command checked: `play.py ARENA --mode ai --seed 0 --scale 3 --screenshot` exits 0 |
| 4 | Max 7 slides, python-pptx, script, MP4 embedded, notes per slide | Met | build_deck.py; pptx has 7 slides, 7 notes, `ppt/media/media1.mp4` |
| 5 | Narration script with timestamps, target 4:30 | Met (estimate) | NARRATION.md: slots sum to 4:30; spoken text is 568 words, about 3:47 at 150 wpm, the rest is the live demo and the clip |
| 6 | PDF via Keynote AppleScript, PNGs of every slide inspected | Met, with a workaround | PDF and slide images exported from a notes-free copy (Keynote cannot open python-pptx's notes master: open returns no document); slides identical; images stored as JPG |
| 7 | Slides 3 and 6 from the fact sheet, with its wording limits | Met | 16 duels (not 48), 120/8/0 absent, "$0 API" and "no final-project paid LLM calls", no "0 policy errors", H1/H2 labelled untested |
| 8 | Milestone checks from PROJECT_PLAN and SCOPE_LOCK; unapproved ones marked Proposed | Met | The records name no Alpha or Beta check (only "Sat 5 Dec Gold build recording"); checks drawn from the G4 checklist in FINAL_REQUIREMENTS section 6 and SCOPE_LOCK limitations; every check marked "Proposed, not yet approved" |
| 9 | Do not touch rules, tests, pyproject; no recording | Met | scope check below |

## Tests run
```
uv run --extra play --extra online --extra train pytest -q     (commit 74a918e, clean tree)
2376 passed, 11 skipped, 5 xfailed, 2 warnings in 341.73s (0:05:41)
```
Earlier runs, for the record: dirty tree gave `3 failed` (held-out ledger tests refuse a dirty tree) and a tree with tracked PNGs gave `1 failed, 2375 passed` (the tracked-images test). Both causes fixed. Later commits change only `presentation/` and this report (no PNG tracked: `git ls-files presentation | grep -ci '\.png'` is 0).

Scope check: `git diff --name-only ab395fc..HEAD` lists only `presentation/**` and `docs/final/orchestration/reports/T33-tech-lead.md`.

## Findings
- [major, for Saad, already routed by decision #135] The observer notes list "disarming" and "defeating scripted guards"; the replay does not support them. Slide 4 handles it as decided.
- [minor] Slide 6 shows the official CI as "queued" (`Final`, run 46058158697, queued 1 h 17 min at 15:56 ET). Re-read it before recording; the slide text says "at last check".
- [minor] The dev CI run cited (46065581056, main 43e9ce1) is green as of 15:56 ET.
- [minor] The slide 6 suite line is the local run (2376 passed, 11 skipped, 5 xfailed). CI counts 14 skipped in the T03 record; the skip count depends on installed extras.
- [minor] Slide 4's embedded video shows the first frame as its poster in Keynote; PowerPoint uses the poster image given (tick 420).

## Known limitations
- Video playback inside the pptx was not tested in PowerPoint or Keynote slideshow (Keynote cannot import the shipped pptx here); the MP4 itself was checked with ffmpeg and the poster renders in the PDF. QA should open the pptx in PowerPoint.
- The speaker notes are in the shipped pptx only (the PDF has none).
- The slide 2 stills are a scripted rehearsal (a bot drove seat A; the real PPO policy was seat B, out of sight), labelled as such on the slide.
- Slide 4 is dense (12.5 pt for the two verbatim quotes), by decision #135's layout.
- Alpha and Beta checks are proposals for Saad; the PPO run, deferred items and fallbacks come from SCOPE_LOCK and GDD section 5.
- Slide 5 quotes the T02 closing evidence (650 passed, 12 skipped, 2 xfailed) at commit 72f6552; today's suite is on slide 6.

## Unresolved findings
None of mine. N4 and N5 of the fact sheet (GDD "No paid run has been made" and the stale RL_POLICY header) are not edited here.

## Requested next action
QA (`gate/T33-qa`): reproduce the replay hash (`uv run --extra play --with imageio-ffmpeg --with numpy python presentation/render_replay.py --verify-only`), check every claim in `presentation/NARRATION.md` and the slide notes against its source, open the pptx in PowerPoint and play the clip, re-read both CI runs, and time the narration. Auditor (`audit/T33`): map the spec to slides and notes.

Commit to review: WORK_COMMIT on task/T33
What changed: new `presentation/` tree only: a replay renderer that verifies the state hash first, the deck builder, screenshots, runbook, narration, audit; no game, server, agent, render or test change.
How to check it: see "Requested next action"; deck rebuild commands are in `presentation/README.md`.
What I am unsure about: video playback in PowerPoint; whether the Hold list and the Alpha/Beta checks are what Saad wants (proposed only); the 4:30 total is an estimate from word counts and the slot lengths.
Touches the knowledge boundary or AI seat: no (presentation material only; the replay uses seat A's own view; no engine, observation or controller code changed). Gate 2 applies only to the replay claim if Gate 1 raises one.

## Student decision required
none. (Slide 7 asks Saad for G2, G3 and Hold decisions, and marks the Alpha and Beta checks "Proposed" for his approval.)
