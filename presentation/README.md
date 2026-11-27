# G2/G3 presentation (task T33)

Tooling only (decision #134): python-pptx and imageio-ffmpeg come in through `uv run --with`, never
through `pyproject.toml`. Nothing here changes `pop/`, `server/`, `agents/`, `render/` or any test.
Tracked images are `.jpg` on purpose: `tests/test_frontend.py` fails on any tracked `.png`.

| File | What it is |
| --- | --- |
| `out/ShadowMasque-G2G3.pptx` | the editable deck, 7 slides, speaker notes, MP4 embedded on slide 4 |
| `out/ShadowMasque-G2G3.pdf` | PDF export through Keynote (made from the notes-free render copy) |
| `out/xgjt-001-segment.mp4` | replay of room XGJT duel 1, ticks 216 to 465 |
| `out/slides/` | one JPG per slide, from the Keynote export, for inspection |
| `NARRATION.md` | standalone narration script with timestamps (4:30) |
| `DEMO_RUNBOOK.md` | live demo commands, route and fallbacks |
| `REPLAY_AUDIT.md` | stage 2a: is the playtest reconstructable, event by event |

Rebuild, from the repository root:

```sh
uv run --extra play --with imageio-ffmpeg --with numpy python presentation/render_replay.py   # verifies the state hash, then renders the MP4
uv run --extra play python presentation/shots.py                                               # menu and rehearsal stills
uv run --with python-pptx python presentation/build_deck.py                                    # deck and NARRATION.md
NO_NOTES=1 DECK_NAME=render.pptx uv run --with python-pptx python presentation/build_deck.py   # copy Keynote can open
osascript presentation/export_keynote.applescript "$PWD/presentation/out/render.pptx" "$PWD/presentation/out/ShadowMasque-G2G3.pdf" "$PWD/presentation/out/slides"
```

Keynote cannot import the notes master python-pptx writes (the import returns no document), so the
PDF and slide images come from the copy built without notes. The slides are identical.
