"""T07-fix1 (decision #44): tuning starts are disjoint from every held-out list on this base."""

from __future__ import annotations

import tests.test_versus_baseline as vb
from tools.rl import env

# Decision #44 asked for about 8 starts including lower floors.


def _cells(pairs):
    return {(s[0], s[1], s[2]) for pair in pairs for s in pair}      # room, row, col


def test_there_are_about_eight_tuning_starts_with_the_midterm_two_first():
    assert len(env.TUNING_STARTS) == 8
    assert env.TUNING_STARTS[0] == (vb.TUNING_STARTS[0]) and env.TUNING_STARTS[1] == vb.TUNING_STARTS[1]


def test_new_starts_include_lower_floor_rooms_and_different_rooms_per_pair():
    new = env.TUNING_STARTS[2:]
    assert len(new) == 6
    assert any(s[0] in (4, 5, 6) for pair in new for s in pair)
    assert all(a[0] != b[0] for a, b in env.TUNING_STARTS)


def test_new_starts_share_no_pair_and_no_start_cell_with_any_held_out_list():
    held = list(vb.HELD_OUT_STARTS) + list(vb.LOWER_HELD_OUT_STARTS)
    new = env.TUNING_STARTS[2:]
    held_pairs = {(a, b) for a, b in held} | {(b, a) for a, b in held}
    assert not [p for p in new if p in held_pairs]
    assert _cells(new).isdisjoint(_cells(held)), _cells(new) & _cells(held)


def test_new_starts_share_no_cell_with_the_candidate_h6_starts_recorded_here():
    # Candidate H6 (orch/wip-T08 @ 25e4587, unreviewed): the cells are copied as facts to
    # check against, not the file. If T08 freezes a different H6 this list must be re-checked.
    h6 = [((4, 2, 8, -1), (5, 2, 1, 1)), ((1, 2, 5, 1), (4, 2, 2, -1)),
          ((5, 2, 7, -1), (3, 2, 4, 1)), ((3, 2, 5, -1), (1, 2, 3, 1))]
    assert _cells(env.TUNING_STARTS[2:]).isdisjoint(_cells(h6))


def test_every_start_is_playable_for_a_short_episode():
    from agents.rl.encoder import MACRO_SLOTS, N_FEATURES
    from tools.rl import ppo
    params = ppo.init_params((N_FEATURES, 8, len(MACRO_SLOTS)), seed=0)
    for starts in env.TUNING_STARTS[2:]:
        ep = env.play_episode(params, env.baseline_opponent(), starts, seed=2, learner_seat="B",
                              rng_seed=2, max_frames=120)
        assert ep["status"] and ep["policy_errors"] == 0
