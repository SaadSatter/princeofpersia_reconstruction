---
handoff_id: HO-T33-fix1-qa
task_id: T33-fix1
date: 2026-11-27
from: qa
to: orchestrator
configured_model: claude-sonnet-5-5
consumed: docs/final/orchestration/reports/T33-fix1-tech-lead.md@fcbbc72 (on task/T33-fix1); docs/final/orchestration/reports/T33-qa.md@e90a0e2
source_branch: gate/T33-fix1-qa
reviewed_commit: fcbbc72b7faf79daa983f69ecf592486ca3db0ee
source_commit: this branch head (report only; no new tests, the deliverable is not code)
verdict: ACCEPT WITH NOTES
---

# T33-fix1: QA re-check

Verdict: ACCEPT WITH NOTES. F1, F2, F3, F4, F6, F7 and brief items 4 to 7 are fixed. No blocker or major finding. Note: the handoff names f22c77b as its source; fcbbc72 (the branch head I reviewed) adds the handoff report on top of it. The tech lead's mention of f22c77b is consistent with `git diff b64f58c..fcbbc72`, which touches only `presentation/**` and the handoff report.

## Acceptance criteria to evidence
| # | Criterion | Met | Evidence (I ran it this session) |
| --- | --- | --- | --- |
| F1 | Shipped pptx opens in Keynote with notes and video | met | Copied `out/ShadowMasque-G2G3.pptx`, `open` in Keynote via osascript: `slides=7`; presenter-notes lengths 451/790/1506/1525/1382/1245/1168 (7 of 7 non-empty); `movies` = 0,0,0,1,0,0,0 (movie only on slide 4). `ppt/presentation.xml` now contains `notesMasterIdLst`. (Earlier I could not open it at all.) |
| F1b | Playback | partly | `start d from slide 4`: `playing=true`, current slide 4, movie object present (volume 80, repetition none); `stop` returned `playing=false`. I did NOT see or hear the clip play: no UI scripting, no screen capture of the slideshow, no PowerPoint. Slideshow starts and the slide holds a movie object; actual playback on click remains unverified. |
| F2 | render_replay works, README command end to end | met | Ran the README command verbatim (`uv run --extra play --with imageio-ffmpeg --with numpy python presentation/render_replay.py`): "match: True" on recorded hash, wrote ticks 216-465 (20.8 s), final `won:B at frame 465`. |
| F2b | Reproduces tracked MP4 | met | sha256 of the re-rendered file = `6568ea4acc87ee96458a7ac6593f74c6c16e56be671bf2567c8f7860e0a8024a`, identical to the tracked file before re-render; `git status` clean afterwards. |
| F3 | MP4 tracked | met | `git ls-files presentation/out` lists `xgjt-001-segment.mp4`, pdf, pptx and seven slide JPGs. Root `.gitignore` is not in the diff. |
| F4 | Slide 3 wording | met | slide-003.jpg: "No recorded comparison with a human yet, so what a player would lose without the learned rival is an open question"; footer "0 aborted duels, 0 runner fallbacks (16 duels, 3 identical trials each)". `grep "48 trial"` hits only a "Do NOT say" line in the speaker notes. |
| F6 | Slide 6 Out list and fallbacks | met | slide-006.jpg lists gate-plate, accounts, matchmaking, public server (not excluded forever, #123), levels 2-14, original level data, sound, adaptive guards, more than two players, LLM rival; matches `SCOPE_LOCK.md` lines 32-37. Fallbacks grouped: scope-lock cut order (trigger: time runs out) and GDD section 5 runtime (trigger: the event). |
| F7 | Audit wording | met | `REPLAY_AUDIT.md:42` "no input strictly between 240 and 372 (inputs exist at both ends)". |
| Slide 1 | Rehearsal caption | met | slide-001.jpg (and PDF page 1): "Rehearsal frame (scripted input, the game's own renderer and art)". "real game frame" not found in the deck sources. |
| #138 | Notes and NARRATION mark clip start | met | NARRATION.md line 19-21 and slide-4 notes XML contain "SAY BEFORE PLAYING (about 9 s)", "CLICK PLAY NOW. The clip runs 22 s. Say over it, about 20 s", "CLIP ENDS. Say after it, about 15 s". Slide 4 slot 1:55 to 2:40 = 45 s. Slots 15+60+40+45+40+40+30 = 270 s = 4:30. |
| #136 | Localhost only, not on two machines | met | Slide 6 limitations and slide 7 HOLD box; NARRATION slide 6 says "localhost-tested only". |
| Cov | COVERAGE.md | met | Header cites `c3ba2b0` (audit/T33), says copied and not re-audited, lists the fixes made since. |
| Render | Slides and PDF re-inspected | met | Viewed all 7 slide JPGs; nothing clipped or overlapping. PDF has 7 pages (page count of `/Type /Page` objects); I viewed page 1 rendered (sips) and it matches slide-001.jpg; pages 2-7 not individually viewed (no poppler). |
| Scope | Diff inside presentation/** and report | met | `git diff --name-only b64f58c..fcbbc72`: `docs/final/orchestration/reports/T33-fix1-tech-lead.md` plus `presentation/{.gitignore,COVERAGE.md,DEMO_RUNBOOK.md,NARRATION.md,README.md,REPLAY_AUDIT.md,build_deck.py,fix_notes_master.py,render_replay.py}` and `presentation/out/*` only. |

## Findings
No blocker, major or minor reproduced. Notes (unverified or cosmetic):
1. Playback of the clip in a Keynote slideshow, and opening in PowerPoint, remain unverified (see F1b). Do one manual click-through before recording.
2. Cosmetic: NARRATION slide 6 says "Out: gate plates, public servers, sound" while the slide shows the full out list; acceptable as a spoken summary.
3. Cosmetic: slide 4 verbatim boxes are about 12.5 pt (decision #135 layout), readable in the JPG but small on a recording.
4. Slide 6 "Official repo CI: not passed, queued ... at last check" is time-dependent; recheck on recording day (the tech lead says the same).

## Not checked
- Full pytest suite: the change touches only `presentation/`; I did not re-run it and rely on the tech lead's reported line (2376 passed, 11 skipped, 5 xfailed), which I did not verify.
- Gate 2 and CI workflows: not applicable (no engine or AI change).
- PDF pages 2 to 7 visually; PowerPoint; audible playback.

## Student decision required
none.
