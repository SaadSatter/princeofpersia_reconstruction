# T08-fix1 session (tech-lead worker)

Base `059aea5` (`gate/T08-eval`), branch `task/T08-fix1`, corrective attempt 1 of 2 for T08. Decisions #58 to #61, #64 to #66,
#74 to #77.

Order of work: the H6-5 to H6-8 selection rule was committed first (PROTOCOL.md 3.1, `1f6fe1e`), then the failing tests
(`4b08daa`), then the fixes (`25475a3`: run-once key (weights, commit) with a clean-tree check and a refusals file, D1
attribution (F-1), mirrored seat-B starts with per-seat analysis (#65), `duel_results` with no controllers (F-2), `--replay`
reading the split from `meta.json` (F-4), B2 needs the disguise at the end (#76)), then H6 re-frozen to 8 starts by a
script that uses only cell lists (`632fc95`), then the documents (`681ac3a`: #75 wording, E-6 sentence, the pre-registered
T09 bar of 14 of 16 with no aborted duel, Wilson table, exposure script).

Never done: no policy (PPO or baseline) ran on H6 (WAIT or scripted seats with a 30-frame cap and a temporary ledger, for
schema tests only); the real ledger was not written; no result was consulted for any new start; no training, no `--live`;
nothing under `pop/`, `agents/`, `tools/rl/`, `play.py`, `render/`, `web/` or `server/` was touched. The report is
`docs/final/orchestration/reports/T08-fix1-tech-lead.md`.
