# T13-fix1 session (tech-lead worker)

Base `9a3feac`, branch `task/T13-fix1`. Fixed the Gate 1 and Gate 2 findings on the online server: per-seat
send queues with a send timeout, instant reconnect hello with a background close of the old socket, seat release
when hello fails, keepalive 3 s / 3 s, Origin check, per-duel fallback trace, `TimeLimitedRival` reset and close,
no auto-reconnect after "replaced", docs and `.gitignore`. No paid calls, no training, no server left running.
Suite result and open points are in `docs/final/orchestration/reports/T13-fix1-tech-lead.md`.
