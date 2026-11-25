# T01-fix2: flip the stale TAKE assertion (Saad's decision #21)
Assigned agent: `agents/tech-lead.md`. Base: `dc43978` on task/T01-fix1. Work in your own clone: `git clone -q /home/claude/sm/wt/T01-fix1 /home/claude/sm/wt/T01-fix2 && cd ... && git checkout -q -b task/T01-fix2 dc43978`.
Saad (2026-11-23): "Flip it to 'TAKE is legal' (Recommended)". In `tests/test_disguise.py::test_take_needs_a_downed_uniformed_guard_ahead`, change only the stripped-guard assertion to `"TAKE" in ep2.legal_actions("B")`, and add a one-line comment citing R-V26 and the decision. Touch no other line in any existing test.
Acceptance: the full suite is green with no failures; report the result line and the exact diff.
