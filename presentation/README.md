# G2/G3 presentation (task T33)

Tooling only (decision #134): python-pptx and imageio-ffmpeg come in through `uv run --with`, never
through `pyproject.toml`. Nothing here changes `pop/`, `server/`, `agents/`, `render/` or any test.
Tracked images are `.jpg` on purpose: `tests/test_frontend.py` fails on any tracked `.png`.

| File | What it is |
| --- | --- |
| `out/ShadowMasque-G2G3.pptx` | the editable deck, 7 slides, speaker notes, MP4 embedded on slide 4 |
| `out/ShadowMasque-G2G3.pdf` | PDF export through Keynote (no speaker notes in a PDF) |
| `out/xgjt-001-segment.mp4` | replay of room XGJT duel 1, ticks 216 to 465 |
| `out/slides/` | one JPG per slide, from the Keynote export, for inspection |
| `NARRATION.md` | standalone narration script with timestamps (4:30) |
| `DEMO_RUNBOOK.md` | live demo commands, route and fallbacks |
| `COVERAGE.md` | requirements coverage checklist (the auditor's matrix, copied) |
| `fix_notes_master.py` | post-process that makes the .pptx importable by Keynote |
| `REPLAY_AUDIT.md` | stage 2a: is the playtest reconstructable, event by event |

Rebuild, from the repository root (each command was run end to end in T33-fix1):

```sh
uv run --extra play --with imageio-ffmpeg --with numpy python presentation/render_replay.py   # verifies the state hash, then renders ticks 216 to 465 to out/xgjt-001-segment.mp4
uv run --extra play python presentation/shots.py                                               # menu and rehearsal stills
uv run --with python-pptx python presentation/build_deck.py                                    # deck, narration, and the Keynote notes-master fix
osascript presentation/export_keynote.applescript "$PWD/presentation/out/ShadowMasque-G2G3.pptx" "$PWD/presentation/out/ShadowMasque-G2G3.pdf" "$SCRATCH_DIR"   # PDF and one PNG per slide (convert to JPG, name slide-00N.jpg)
```

Keynote: python-pptx writes a notes master but not the `notesMasterIdLst` entry in `ppt/presentation.xml`; Keynote
then refuses the file. `fix_notes_master.py` adds that entry (build_deck.py runs it), and the shipped .pptx now opens
in Keynote with 7 slides, all 7 speaker notes and the clip as a movie object on slide 4.
`NO_NOTES=1` builds a notes-free copy; it is no longer needed.
