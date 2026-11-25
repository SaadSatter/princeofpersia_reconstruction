# T18 session (tech-lead worker)

Base `f08c1a8`, branch `task/T18`. Online room codes (decision #52): Create room / Join room with a 4-letter code
(`server/rooms.py`, `server/app.py`, `server/__main__.py`, `web/online.html`, `web/online.js`), many rooms each with
its own `Match`, expiry (10 min without a second player, 15 s with nobody connected), per-room tokens, 10 failed
joins a minute per connection, and `docs/final/ONLINE_PLAY.md`. No paid calls, no training, no server left
running, no browser run. Result line and the three old tests that pin the single-duel lobby are in
`docs/final/orchestration/reports/T18-tech-lead.md`.
