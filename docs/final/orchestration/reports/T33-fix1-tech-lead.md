---
handoff_id: HO-T33-fix1-tech-lead
task_id: T33-fix1
date: 2026-11-27 17:30 ET
from: tech-lead
to: qa
configured_model: claude-sonnet-5-5
runtime_model: not visible to the agent (orchestrator records the verified id in REVIEW_LOG.md)
consumed: docs/final/orchestration/tasks/T33-fix1.md@e480ff1; reports/T33-qa.md@e90a0e2; reports/T33-requirements-auditor.md@c3ba2b0
source_branch: task/T33-fix1
source_commit: f22c77b
reviewed_commit: n/a
verdict: n/a
---

# T33-fix1: tech-lead report

Status: done

## Work completed
Branch `task/T33-fix1` from b64f58c. Fixed F1 to F4, F6, F7 and the fixable auditor rows; F5 is handled by decision #136 (wording kept).

## Findings fixed
| Finding | Fix | Evidence |
| --- | --- | --- |
| F1 blocker: pptx does not open in Keynote | Root cause: python-pptx writes the notes master part and relationship but not `<p:notesMasterIdLst>` in `ppt/presentation.xml`. New `presentation/fix_notes_master.py` adds that one element; `build_deck.py` runs it after saving. No other change to the package. | Keynote via osascript opens the shipped `ShadowMasque-G2G3.pptx`: `slides=7`, notes lengths 451/790/1506/1525/1382/1245/1168 (all 7 present), `movies=1` on slide 4 only. (Playback itself not clicked: no UI-scripting rights; PowerPoint not available.) The PDF and slide JPGs are now exported from the shipped deck, not a notes-free copy. |
| F2 render_replay option bug, default start | `args.jpg_dir` (my sed damage) back to `args.png_dir`; default `--start` 216; default hold 2.0 s | `render_replay.py` with no options re-rendered the clip: sha256 identical to the shipped MP4 (6568ea4a...). README command works end to end |
| F3 MP4 untracked | `presentation/.gitignore` un-ignores only `out/xgjt-001-segment.mp4`; root `.gitignore` untouched | `git ls-files presentation/out` lists the MP4 |
| F4 slide 3 wording | "No recorded comparison with a human yet, so what a player would lose ... is an open question." Footer: "0 aborted duels, 0 runner fallbacks (16 duels, 3 identical trials each)", no "48 trial rows" | slide-003.jpg |
| F6 slide 6 | Out list now the full SCOPE_LOCK out-of-scope row (adds matchmaking, adaptive guards, more than two players; public server "not excluded forever, #123"); Deferred split out; fallbacks grouped by source: scope lock cut order (trigger: time runs out) and GDD section 5 runtime fallbacks (trigger: the event), with the online "never aborts (#49)" distinction | slide-006.jpg |
| F7 wording | REPLAY_AUDIT "no input strictly between 240 and 372 (inputs exist at both ends)"; runbook says the Pit Hall tick-68 fact is read from the replay engine state | files |
| Slide 1 caption | "Rehearsal frame (scripted input, the game's own renderer and art): ..." | slide-001.jpg |
| Decision #138 | Slide 4 narration marks "SAY BEFORE PLAYING (9 s)", "CLICK PLAY NOW" (22 s clip, say over it about 20 s), "CLIP ENDS" (15 s). Same text in the speaker notes and NARRATION.md. About 100 spoken words, about 45 s with the clip. Total slots still 4:30 | notes of slide 4 contain "CLICK PLAY NOW" |
| Decision #136 | "localhost only, not on two machines" kept on slide 6; slide 7 hold box unchanged | slides |
| Coverage file | `presentation/COVERAGE.md`: the auditor's matrix copied, cites `c3ba2b0`, not re-audited | file header |

## Paths
Only `presentation/**` and this report. Changed: `.gitignore` (new), `COVERAGE.md` (new), `fix_notes_master.py` (new), `DEMO_RUNBOOK.md`, `NARRATION.md`, `README.md`, `REPLAY_AUDIT.md`, `build_deck.py`, `render_replay.py`, `out/*` (pptx, pdf, 7 slide JPGs, MP4 now tracked).

## Tests run
```
uv run --extra play --extra online --extra train pytest -q   (commit f22c77b, clean tree)
2376 passed, 11 skipped, 5 xfailed, 2 warnings in 341.37s (0:05:41)
```
Scope check: `git diff --name-only b64f58c..HEAD` lists only `presentation/**` (plus this report in its own commit). No `.png` tracked in `presentation/`.

## Findings
- No new findings. Slide re-inspection: viewed slides 1, 3, 4 and 6 after the final export (all fit, nothing clipped); 2, 5 and 7 are unchanged apart from re-export.
- F5 stays as decided (#136): XUKM was one machine, so "localhost only, not on two machines" is accurate for the sessions run.

## Known limitations
- Clip playback inside Keynote slideshow and in PowerPoint is still not clicked-through (no UI scripting here; no PowerPoint). Keynote reports the movie object and the poster renders in the PDF.
- Slide 6's suite line is the run on 74a918e; code is unchanged since (this fix touches only `presentation/`, suite re-run above gives the same line).
- CI status on slide 6 must be re-read on recording day.
- Slide 4's verbatim boxes remain about 12.5 pt (decision #135 layout).

## Unresolved findings
None of mine.

## Requested next action
QA: re-check F1 (open the shipped pptx in Keynote, count slides, notes, movie; try PowerPoint if available), F2 (README render command, hash), F3, and re-view the slide JPGs. Orchestrator: Gate 3.

Commit to review: f22c77b on task/T33-fix1
What changed: Keynote can open the deck (missing notesMasterIdLst added), MP4 tracked, render script fixed, slides 1/3/6 wording, clip-timed slide 4 narration, coverage checklist.
How to check it: see "Requested next action"; Keynote check is an osascript `open` then `count of slides`, `presenter notes`, `count of movies`.
What I am unsure about: actual clip playback in a slideshow.
Touches the knowledge boundary or AI seat: no.

## Student decision required
none.
