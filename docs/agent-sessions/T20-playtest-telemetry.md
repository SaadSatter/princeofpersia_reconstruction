# T20 session (tech-lead worker)

Base `bdc3c76` (`orch/reviewed`), branch `task/T20`. Playtest telemetry from decisions #67 and #68.
Tests first (commit `bd8109a`, importing `server.telemetry`, which did not exist there), then
`server/telemetry.py` (a pure reader: `observe`, `legal_actions`, `outcome`), the hooks in
`server/match.py`, `server/app.py` (`_room_failed` closes the logs), `server/__main__.py`
(`--playtest`, `--telemetry-dir`) and `play.py --versus --playtest`, then
`tools/telemetry/summarize.py`, `docs/final/playtest/TELEMETRY.md`, the one draft CONSENT sentence and the
`ONLINE_PLAY.md` flag line. No change to `pop/`, no paid calls, no training, no server left running.
Details, the result line and open questions: `docs/final/orchestration/reports/T20-tech-lead.md`.
