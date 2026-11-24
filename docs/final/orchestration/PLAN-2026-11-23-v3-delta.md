# Plan v3 delta — hosting by G2/G3 (2026-11-23, 22:15 ET)

This adds to [`PLAN-2026-11-23-v2.md`](PLAN-2026-11-23-v2.md) after decisions 12–15 in
[`DECISIONS-2026-11-23.md`](DECISIONS-2026-11-23.md). Everything else in v2 stands.

## New and changed tasks

| ID | Task | Agent | Depends on | Acceptance (summary) | Target |
|---|---|---|---|---|---|
| T14 | **Hosted web build (Pyodide + Phaser).** The pieces: <br>• `web/bridge.py` (pure Python): human seat input in, the human seat's observation and a **draw list** out (sprites, frames, positions, HUD), computed by pygame-free layout code. <br>• `web/index.html` and `web/main.js` (Phaser): load Pyodide and Phaser from pinned CDN versions; send keys to the bridge; draw the draw list. <br>• `tools/web/build.py`: packs `pop/`, `agents/`, `render/` helpers and assets for the page. <br>• A Pages deploy workflow. <br>• A CI Playwright smoke test that loads the page, plays a few seconds and saves a screenshot. | Tech Lead | T01 (engine); later T05 and T07 for the AI rival | CPython tests: the bridge payload never contains more than `observe(human_seat)` plus its draw list (leak test); deterministic; key map matches `play.py`. CI smoke runs green on GitHub (Saad pushes) | Tue 24–Thu 26 |
| T12 | (changed) The local `play.py --rival` stays useful for development; the web build becomes the demo and playtest build | Tech Lead | T05, T07 | — | Thu 26 |
| T01-fix1 | `TAKE` always legal over a downed guard (decision 15, new R-V row); same-cell figure order with no rival-first tie (L2); remove the matching gate xfails | Tech Lead | GATE-T01-qa report | Gate tests pass; rule row added | Tue 24 |
| T03 | (changed) The official-repo snapshot must also carry `web/`. The hosting URL goes in the README | Tech Lead prep; Saad pushes | T14 | — | Fri 27 |

## Limits of this sandbox (stated, not hidden)
- **No CDN.** The sandbox cannot download Phaser or Pyodide, so the full browser page cannot be run here. Verification is split: Python logic and the leak boundary are tested here; the real page is checked by a CI Playwright job on GitHub; Saad opens it on his Mac.
- **No push.** Hosting needs Saad to push, enable GitHub Pages, and optionally install the Claude GitHub App.
- **Known limitation:** in a static page the whole game state lives in the browser. A human could read hidden state through the browser devtools. That is acceptable for human vs AI (it is cheating against yourself) and for local play, but not for online human vs human, which needs the server. This goes into the Configuration doc's knowledge-boundary section.
