# Change summary for the independent reviewer — session 03

For `.claude/agents/rules-reviewer.md`, run in a **separate** session that did
not write this code. Base commit `06ff044`; the commit range is in
`docs/agent-sessions/03-audit-fixes-live-prep.md`.

## What changed

1. **Late replies (R-D23, audit F-1)** — `pop/runner.py`: on timeout the
   runner keeps the abandoned `(thread, box)` and reads it only after the
   episode, into `late_replies` (`arrived` / `failed` / `pending`). New
   optional player hook `commit(observation, action, source, error)`, called
   by the runner after `ep.step`. `agents/model_player.py`: `decide` no
   longer writes memory; `commit` does, under a lock.
2. **Unknown cost (R-D24, audit F-2)** — `cost_usd` is `None` when the model
   has no price; episode usage, summary rows and `table.md` ("unknown")
   propagate it. A `pending` late reply also makes cost unknown.
3. **Price record** — `agents/providers.py`: `PRICE_DATE = "2026-10-26"`,
   `PRICE_SOURCE`; `evaluate.py` writes `price_source` into model headers.
4. **Tests** — `tests/test_regressions.py` (two `test_regression_*` tests
   written before the fix and seen failing; one pending-reply test),
   `tests/test_provider_sdk.py` (offline SDK check; skipped without the
   `model` extra, i.e. in CI).

## Questions worth checking

- Can a late reply still reach the episode, the step trace, or the prompt
  by any path (e.g. shared objects inside `obs` or `meta`)?
- Is the baseline's in-`decide` memory (not moved to `commit`) acceptable,
  given the student's decision not to change the baseline?
- Is "one pending late call makes the whole episode cost unknown" the right
  reporting choice, or should known and unknown parts be shown separately?
- Does `test_regression_late_reply_after_timeout_rewrote_player_memory`
  depend on timing in a way that could flake on a slow CI runner
  (timeout 0.3 s, events used for ordering)?
