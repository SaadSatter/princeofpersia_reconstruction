# T13 session: online play (tech-lead worker, claude-sonnet-5-5)

Task brief: `docs/final/orchestration/tasks/T13.md@f2c25e8`. Base `ae90c8c`, branch `task/T13`.

* Read: the brief, `web/bridge.py`, `web/main.js`, `render/draw_list.py`, `pop/observation.py`,
  `pop/versus.py`, `docs/final/WEB_BUILD.md`, AGENTS.md "Online play".
* Order of work: `online` extra and lock, then failing tests (commit 7119f91), then
  `server/` (match, app, trace, rival, CLI), the page (`draw.js` moved out of `main.js`,
  `ui.js`, `online.js`, `online.html`), docs.
* Mid-task note from the orchestrator (GATE-wave3 QA inherited findings): handled and
  listed in the report.
* No paid calls, no push, no training. A scripted localhost run of the server was made
  (three WebSocket clients). No browser was available.
* Report: `docs/final/orchestration/reports/T13-tech-lead.md`.
