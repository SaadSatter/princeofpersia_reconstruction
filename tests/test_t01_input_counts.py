"""T01 (AUDIT-B F3): queued inputs that never start are counted per seat in
`outcome()`, for reporting only (no gameplay change). Proposal awaiting
Saad's ruling (DECISIONS-2026-11-23 #4); kept in its own commits.

- replaced: a newer input replaced one still pending (the latest press wins).
- stale: a pending input was dropped because it was no longer legal when the
  rival became free.
"""

from __future__ import annotations

import json

from pop import arena
from pop.versus import VersusEpisode


def episode(a, b=(3, 2, 7, -1)):
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0, guard_posts={})


def run(ep, n):
    for _ in range(n):
        ep.tick()


def test_outcome_reports_zero_counts_for_both_seats_at_start():
    out = episode((2, 0, 5, -1)).outcome()
    assert out["stale_inputs"] == {"A": 0, "B": 0}
    assert out["replaced_inputs"] == {"A": 0, "B": 0}


def test_a_newer_input_replacing_a_pending_one_is_counted():
    ep = episode((2, 0, 5, -1))
    ep.step("A", "STEP_LEFT")
    ep.step("A", "STEP_RIGHT")                          # replaces STEP_LEFT before any tick
    run(ep, 1)
    assert ep._duel.motion("A")["facing"] == +1            # the latest press won
    assert ep.outcome()["replaced_inputs"] == {"A": 1, "B": 0}
    assert ep.outcome()["stale_inputs"] == {"A": 0, "B": 0}


def test_an_input_that_is_no_longer_legal_when_it_would_start_is_counted_stale():
    ep = episode((1, 0, 7, +1))                         # hole ahead at col 8
    ep.step("A", "DOWN")                                # lowers itself to hang
    run(ep, 1)
    assert ep.step("A", "LEFT")["accepted"]             # legal now, while still standing
    run(ep, 10)
    assert ep._duel.rivals["A"].kid.posture == "hanging"
    out = ep.outcome()
    assert out["stale_inputs"] == {"A": 1, "B": 0}
    assert out["inputs"]["A"] == 2 and out["invalid_inputs"]["A"] == 0


def test_counts_never_reach_either_seats_observation():
    ep = episode((2, 0, 5, -1), b=(2, 1, 0, +1))
    ep.step("A", "STEP_LEFT")
    ep.step("A", "WAIT")
    run(ep, 1)
    for seat in ("A", "B"):
        text = json.dumps(ep.observe(seat))
        assert "stale" not in text and "replaced" not in text


def test_reset_clears_the_counts():
    ep = episode((2, 0, 5, -1))
    ep.step("A", "STEP_LEFT")
    ep.step("A", "WAIT")
    ep.reset(0)
    assert ep.outcome()["replaced_inputs"] == {"A": 0, "B": 0}
