# Held-out set H6: OFF LIMITS

`H6.json` is the frozen held-out set of the versus evaluation (decision #9,
task T08). Eight full-duel starts (H6-1 to H6-8) with sixteen guard posts. It
is **unseen start pairs and guard layouts**: start cells and guard post tuples
are disjoint from every tuning scenario, every training start and the default
arena starts and posts; patrol ranges are not (a patrol is a stretch of a
ten-column corridor, and the training patrols span columns 1 to 8 of rooms 4
and 5). So the claim is "unseen start pairs and guard layouts", not "unseen
cells". T09 reports each start and labels the most training-like ones
(`tools/eval/exposure_table.py` generates the table).

**OFF LIMITS** to training, tuning, reward design, prompt design and anyone
choosing a policy checkpoint. `agents/rl/**` and `tools/rl/**` must never read
this directory or import `evaluation`; `tests/test_eval_registry.py` fails if
they do. Only `tools/eval/run_versus_suite.py --split heldout` reads the file,
through `evaluation.manifest.load_heldout`.

- SHA-256 of `H6.json`: `d013152a84aed5d6ddf189a306e1dfa66f8b178a68dde2f6d5039684e82a5266`
  (also in `evaluation/manifest.py` and `docs/final/evaluation/PROTOCOL.md`).
  The CLI recomputes it before parsing and refuses to run on a mismatch.
  The first freeze (four starts, `44da40ec...0847`) is superseded; it was never
  run, so nothing is voided.
- H6-1 to H6-4 are the first freeze unchanged. H6-5 to H6-8 follow from the
  selection rule in `docs/final/evaluation/PROTOCOL.md` section 3.1
  (decision #74), which was committed before any new start was added and uses
  only the cell lists, never a policy or a result. `tools/eval/select_heldout_starts.py`
  reproduces them.
- Freeze rule: once committed the file is not edited. A change means a new
  hash, a new commit, a note in the protocol, and any earlier held-out result
  is void.
- Run-once rule (decision #64): one held-out run per (weights SHA-256, engine
  commit) pair. `ledger.jsonl` (append only, created by the first real
  held-out run) records the claim before the first trial, so an aborted run
  still counts. The same weights on a new commit may run again and both lines
  stay. Refused attempts go to `refusals.jsonl` beside it. A real run is also
  refused on an unknown commit or a dirty tree.
- A held-out dry run (`--dry-run --split heldout`) uses WAIT seats only,
  writes no ledger line and never shows the set to a policy.
