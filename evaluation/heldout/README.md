# Held-out set H6: OFF LIMITS

`H6.json` is the frozen held-out set of the versus evaluation (decision #9,
task T08). Four full-duel starts and eight guard posts that no tuning
scenario, no training start and no default arena start uses.

**OFF LIMITS** to training, tuning, reward design, prompt design and anyone
choosing a policy checkpoint. `agents/rl/**` and `tools/rl/**` must never read
this directory or import `evaluation`; `tests/test_eval_registry.py` fails if
they do. Only `tools/eval/run_versus_suite.py --split heldout` reads the file,
through `evaluation.manifest.load_heldout`.

- SHA-256 of `H6.json`: `44da40eca7a5606a9778cd3dca9756a34eb3962d3143a1304247ef2c92070847`
  (also in `evaluation/manifest.py` and `docs/final/evaluation/PROTOCOL.md`).
  The CLI recomputes it before parsing and refuses to run on a mismatch.
- Freeze rule: once committed the file is not edited. A change means a new
  hash, a new commit, a note in the protocol, and any earlier held-out result
  is void.
- Run-once rule: one held-out run per frozen policy. `ledger.jsonl` (append
  only, created by the first real held-out run) records the claim before the
  first trial, so an aborted run still counts.
- A held-out dry run (`--dry-run --split heldout`) uses WAIT seats only,
  writes no ledger line and never shows the set to a policy.
