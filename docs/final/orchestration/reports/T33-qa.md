---
handoff_id: HO-T33-qa
task_id: T33
date: 2026-11-27 16:50 ET
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/reports/T33-tech-lead.md@b64f58c; docs/final/orchestration/reports/T33-evaluation-specialist.md@0d73e48; docs/final/orchestration/tasks/T33.md and inputs/G23_PRESENTATION_REQUEST.md@43e9ce1; decision #135
source_branch: gate/T33-qa
source_commit: ddbe157 (tests; this report's own commit follows)
reviewed_commit: b64f58c
verdict: ACCEPT WITH NOTES (one playback blocker for the shipped .pptx in Keynote, see F1)
---

# T33: QA report (video provenance, facts, readability, playback, timing)

Status: done

Verdict: **ACCEPT WITH NOTES, with a blocker for Saad's recording workflow.** Every fact I checked matches its source and the video is provenance-clean. But the shipped `.pptx` does not open in Keynote (reproduced), the only Mac presentation tool Saad has, and the standalone MP4 is not on the branch. Both must be fixed (or Saad told how to work around them) before he records. This is a blocker for use, not for the evidence; the orchestrator decides how to class it.

## 1. Video provenance (reproduced)
- `server.trace.replay` on `docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json`: `won:B`, 465 frames, hash `5dadb78e1da67d1fb312711bd48dbc60a2a4f71f5000fb00b14ec1463572a910` = recorded (via `render_replay.py --verify-only`, "match: True", and independently in my own test).
- New test `tests/test_gate_t33_qa_replay.py` (3 tests, pass): hash and whole outcome dict equal; per-tick engine state gives A's room changes at 67/153/246 and heart losses 417 (3 to 2), 441, 465 (0), equal to the `hit` events in `2026-11-27-XGJT-001-A.jsonl`; the only `sword_drop` is t 465 cause `thrown`; A's input at tick 463 is `THROW`; A sends no input strictly between 240 and 372 (inputs exist at both 240 and 372; the audit's "240 to 372" is loosely stated, cosmetic).
- Frames: the MP4 embedded in the pptx is byte-identical to the Tech Lead's file (sha256 `6568ea4a...8024a`). I re-rendered ticks 216 to 465 myself (with a scratch copy of the script, see F2) and compared ffmpeg `framemd5` of all 548 frames: identical. So the video is ticks 216 to 465, 20.8 s of play at 24 fps plus 2 s hold, 960x672, h264, 22.83 s. Label "External playtest — reconstructed from telemetry" is drawn on every frame in the renderer code.
- Replay audit table spot-checked: all agreed except the cosmetic boundary above. Guard-down at 327 and B's lunge at 325 I did not re-derive (relied on the Tech Lead and the T33-eval spot check).

## 2. Facts against sources
Verified (met):
- Slide 3: 16 duels, 13/2/1, bar 14, NOT SUPPORTED, identical trials, effective n about 8, 0 aborted, 80 min local CPU, 1.49 M steps, $0, no final-project paid calls: all as in the eval fact sheet and its wording limits (no "48 trials", no 120/8/0, no "0 policy errors"). Eval sheet not re-derived by me from the 48 rows; I trust Gate 2's own check.
- Slide 4 quotes: both are exact substrings of LOG.md section 4 and section 6 (programmatic check, including the apostrophe in "AI's"). Decision #135 layout is followed: observer box, interpretation, separate "Replay shows" box, open question, consent line.
- Slide 5: 650 passed, 12 skipped, 2 xfailed is in the T02-close commit 72f6552 message and in `handoff-drafts/2026-11-24-qa-to-tech.md` ("650 passed, 12 skipped, 2 xfailed in 4.75s"); the 2 xfails are the T04 gate findings. T02-F1 "waited" vs none, F2/F2b, 558ef6d, a1100f6, 13c7488, 7c4fc1d, decisions #4, #7, #18 (48 per hop = +6 x 8 frames), #120 all exist as stated. "I consider this handoff complete." is an exact fragment of Saad's student decision. Chain order on the slide is a presentation order; Saad's decision text is the final one.
- Slide 6 CI, read with `gh run view` at 16:20 ET: dev run 46065581056 "Deterministic checks (dev)" on main 43e9ce1 is success (pytest 3.11 and 3.12). Official run 46058158697 "Final", head a251335, status `queued`, no conclusion, created 19:38Z. The slide says "queued ... at last check" and "not passed": correct as of now. Re-read before recording.
- Slide 6 suite line "2376 passed, 11 skipped, 5 xfailed": I ran `uv run --extra play --extra online --extra train pytest -q` on my branch (2376 + my 3 new tests): `2379 passed, 11 skipped, 5 xfailed, 2 warnings in 345.75s`. Matches.
- Scope, exclusions, deferred, cut order, limitations match `docs/final/SCOPE_LOCK.md` (decision #127).

## 3. Readability and clipping (viewed all 7 slide JPGs)
No clipping or overflow found. Dark palette, high contrast. Smaller text: slide 4's two verbatim quote boxes (about 12.5 pt, by #135), slide 6 (dense, 6 boxes, fallbacks and limitations text is small for a recording), slide 7 bullet text and the tiny "Proposed" captions. Readable in the 960x540 JPG, tight on a shared screen. Slide 1 caption calls the still "a real game frame" though it comes from a scripted rehearsal (the notes say so, the slide does not).

## 4. Playback (Keynote 14 on this Mac, no PowerPoint)
- **Shipped `presentation/out/ShadowMasque-G2G3.pptx`: does NOT open in Keynote.** `osascript` `open` returns "AppleEvent timed out" after 90 s and `count of documents` stays 0. Reproduced twice (Keynote restarted between).
- A copy of the same file with only the notes slides and notes master removed (zip surgery, scratch only: `/private/tmp/claude-501/qa/nonotes.pptx`) opens at once: 7 slides, and slide 4 reports `movies=1` (the MP4 is imported as a movie object). So the python-pptx notes master is the cause, as the Tech Lead said; the embedded video is not the cause.
- Not verified: actual playback of the clip (no accessibility rights for UI scripting; I could not click Play). I confirmed import only. PowerPoint cannot be tested here.
- Consequence: Saad cannot open the notes-bearing deck in Keynote. Options for the Tech Lead: ship a Keynote-importable pptx (notes carried in a fixed notes master or a separate notes-free deck plus notes in `NARRATION.md`), and say in the README which file Saad should open. The PDF (7 pages in the Tech Lead's export; I viewed the JPGs, not the PDF pages) is made from the notes-free copy, so it is not affected.

## 5. Timing
- NARRATION.md: 568 spoken words. At 150 wpm 3:47; at 130 wpm 4:22; at 160 wpm 3:33. Per slide at 150 wpm: 16 s (slot 15), 30 (60, rest is live demo), 42 (40), 36 (45), 39 (40), 37 (40), 28 (30).
- Slot sum is 4:30. Risks: slides 1 and 3 run 1 to 2 s over their slots at 150 wpm. Slide 4: the clip is 22.8 s and the speech 36 s; if they are not spoken over each other the slide takes about 58 s, not 45. Slide 2 is 30 s of speech plus a live demo that the runbook says takes about 60 s: with that 30 s unspoken, the whole run is about 4:15 to 4:55 depending on whether the clip and demo overlap speech. Inside 3 to 5 minutes in every case I computed, but near 5:00 in the pessimistic case (sequential clip plus a 60 s demo on top of 3:47 of speech = about 5:10). Saad should rehearse once with a stopwatch.

## Acceptance criteria → evidence
| # | Criterion (brief, stage 4 and spec) | Met? | Evidence |
| --- | --- | --- | --- |
| 1 | Video provenance, replay hash reproduced | Met | section 1, test file |
| 2 | MP4 frames correspond to ticks 216 to 465 | Met | framemd5 of 548 frames identical to my re-render |
| 3 | Every factual claim against its source | Met, with notes | section 2, F4 to F6 |
| 4 | Slide readability and clipping | Met, with notes | section 3 |
| 5 | Playback | **Not met for Keynote** | section 4, F1 |
| 6 | Timing vs 4:30 | Met (estimate) | section 5 |
| 7 | Max 7 slides, deliverables present | Partly | MP4 not tracked (F3); PDF, pptx, notes, narration, runbook present |
| 8 | Slides 3 and 6 follow the eval fact sheet limits | Met | section 2 |
| 9 | #135 layout; quotes verbatim | Met | section 2 |

## Tests run
```
uv run --extra play --extra online pytest tests/test_gate_t33_qa_replay.py -q   -> 3 passed in 0.04s
uv run --extra play --extra online --extra train pytest -q                      -> 2379 passed, 11 skipped, 5 xfailed, 2 warnings in 345.75s (0:05:45)
render_replay.py --verify-only -> match: True
gh run view 46065581056 --repo SaadSatter/shadow_masque -> success
gh run view 46058158697 --repo columbia-university-ai-games/final-saadsatter -> queued
```

## Findings
Reproduced:
- **F1 [blocker for use] presentation/out/ShadowMasque-G2G3.pptx**: does not open in Keynote. Repro: `osascript` with `tell application "Keynote" to open (POSIX file ".../ShadowMasque-G2G3.pptx")` times out, 0 documents. Same file minus notes parts opens (7 slides, 1 movie on slide 4). Expected: opens. Fix goes to the Tech Lead (not by me).
- **F2 [major] presentation/render_replay.py:128 (and the README rebuild line)**: `args.jpg_dir` does not exist; the option is `--png-dir`, so the argparse attribute is `png_dir`. Any render (not just with `--png-dir`) dies with `AttributeError: 'Namespace' object has no attribute 'jpg_dir'` and leaves an empty MP4. Repro: `uv run --extra play --with imageio-ffmpeg --with numpy python presentation/render_replay.py --start 216 --end 465 --out /tmp/x.mp4`. Expected: renders. Also the default `--start 205` differs from the shipped clip (216). My re-render used a scratch copy with the attribute fixed; frames matched the shipped MP4, so the committed script was evidently edited after the MP4 was made. The video is sound; the reproduction command is broken.
- **F3 [major] presentation/out/xgjt-001-segment.mp4**: not tracked (`.gitignore:33 *.mp4`). The README, slide 4 notes and runbook fallback 4 point to it, and the spec lists the MP4 as a deliverable. It exists only in the Tech Lead's worktree and inside the pptx (media1.mp4). Saad's only fallback if the embed fails is a file the repository does not have. Combined with F1 it is the second way the clip can be unavailable. Expected: the MP4 delivered (force-add or a release attachment, orchestrator's call) or the docs say to extract it from the pptx.
- **F4 [minor] slide 3**: "No one has yet played the scripted baseline in a comparison" is stronger than the record, which says Session B has not been run. Suggest "No recorded comparison with a human yet".
- **F5 [minor] slides 6 and 7 (online testing "on localhost only", "not on 2 machines")**: copied from SCOPE_LOCK, approved before the XGJT session. The XGJT/XUKM sessions ran from Saad's laptop with an external player (telemetry README) and the records do not say how that player connected. Unverified, could be stale. Saad should confirm the wording before recording.
- **F6 [minor] slide 6 "Out" list**: omits matchmaking, adaptive guards and more than two players from the SCOPE_LOCK out-of-scope row; the fallbacks box mixes the evaluation runner's abort rule with the online rule (CONFIGURATION: online fallback never aborts a duel). Spec says do not omit; the slide is compact by design.
- **F7 [cosmetic]**: REPLAY_AUDIT "no input 240 to 372" (inputs at both ends); runbook says the rival was in the Pit Hall "from tick 68" (not checked by me, the audit says A enters that room at 246 and does not give B's room history).

Unverified concerns: actual video playback in Keynote slideshow and in PowerPoint; PDF page-by-page view; the eval-sheet numbers were not re-derived from the 48 rows.

## Known limitations / Not checked
Playback of the clip (see section 4); PowerPoint; PDF pages (viewed the JPG exports instead); guard-down tick 327 and the rival's room history; Dec 2/4/5 checks are proposals and not verified against anything but the Tech Lead's stated source; no browser build or Playwright (not in scope of this task).

## Unresolved findings
F1, F2, F3 (fix by Tech Lead, then a short re-check by QA); F4 to F6 for Saad or Tech Lead.

## Requested next action
Orchestrator: route F1 to F3 to the Tech Lead (T33-fix1), and ask Saad to confirm F5. Re-read the official CI run on recording day.

## Student decision required
none. (F5 needs Saad's confirmation of a fact, not a decision.)
