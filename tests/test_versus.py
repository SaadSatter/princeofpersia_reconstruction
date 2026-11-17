"""Two rivals on real-time ticks (pop/versus.py; docs/final/VERSUS_SPEC.md Section 2).

Deterministic, offline. Stage 1: movement only; swordplay, guards and disguise
tests arrive with their stages (strict xfail placeholders below).
"""

from __future__ import annotations

import json

import pytest

from pop import arena
from pop import physics as P
from pop.versus import (FIGURE_KEYS, ME_EXTRA_KEYS, OBSERVATION_KEYS, SEATS, VersusEpisode,
                        arena_episode)


def episode(a=None, b=None, seed=0) -> VersusEpisode:
    starts = dict(arena.STARTS)
    if a:
        starts["A"] = a
    if b:
        starts["B"] = b
    return VersusEpisode(arena.situation("A"), starts, seed)


def run(ep: VersusEpisode, n: int) -> None:
    for _ in range(n):
        ep.tick()


def me(ep, seat):
    return ep.observe(seat)["me"]


# --- ticks and inputs ----------------------------------------------------
def test_rivals_start_at_their_arena_starts():
    ep = arena_episode()
    for seat in SEATS:
        room, row, col, facing = arena.STARTS[seat]
        m = me(ep, seat)
        assert (m["row"], m["col"], m["facing"]) == (row, col, "right" if facing > 0 else "left")
    assert ep.observe("A")["room"] != ep.observe("B")["room"]


def test_both_rivals_move_in_the_same_frames():
    """A move's frames are its length (a run is 4); its arrival is applied when the
    rival is next advanced, at the start of the following frame (pop/versus.py)."""
    ep = arena_episode()
    assert ep.step("A", "RIGHT")["accepted"] and ep.step("B", "LEFT")["accepted"]
    run(ep, P.RUN)
    assert me(ep, "A")["motion"]["frame"] == P.RUN == me(ep, "B")["motion"]["frame"]
    assert me(ep, "A")["col"] == 2 and me(ep, "B")["col"] == 7      # last frame of the run
    run(ep, 1)
    assert me(ep, "A")["col"] == 3 and me(ep, "B")["col"] == 6      # both arrive together


def test_an_input_waits_until_the_rival_is_free_and_a_newer_one_replaces_it():
    ep = arena_episode()
    ep.step("A", "RIGHT")
    run(ep, 1)                                    # the run has started
    ep.step("A", "LEFT")
    ep.step("A", "STEP_RIGHT")                    # replaces LEFT
    run(ep, P.RUN)                                # frame 5: the run lands and the step starts
    assert me(ep, "A")["col"] == 3 and me(ep, "A")["motion"]["effect"] == "moved"
    assert me(ep, "A")["motion"]["frames"] == P.STEP
    run(ep, P.STEP)
    assert me(ep, "A")["col"] == 4 and me(ep, "A")["facing"] == "right"


def test_refused_input_changes_nothing_and_is_counted():
    ep = arena_episode()
    before = ep._duel.snapshot()
    for bad in (7, "FLY", "  "):
        assert not ep.step("A", bad)["accepted"]
    assert ep._duel.snapshot() == before
    assert ep.outcome()["invalid_inputs"] == {"A": 3, "B": 0}
    with pytest.raises(ValueError):
        ep.observe("C")


def test_rivals_cannot_pass_through_each_other():
    ep = episode(a=(2, 0, 3, +1), b=(2, 0, 4, -1))          # face to face, adjacent
    ep.step("A", "RIGHT")
    run(ep, P.RUN)
    assert me(ep, "A")["col"] == 3
    assert ep.observe("A")["last_result"]["effect"] == "bumped"


def test_rivals_running_into_one_cell_at_once_both_stay_out():
    ep = episode(a=(2, 0, 2, +1), b=(2, 0, 4, -1))          # one free cell between them
    ep.step("A", "RIGHT")
    ep.step("B", "LEFT")
    run(ep, P.RUN + 1)
    assert (me(ep, "A")["col"], me(ep, "B")["col"]) == (2, 4)


def test_a_plate_pressed_by_either_rival_slams_its_gate():
    ep = episode(a=(1, 2, 2, +1), b=(2, 1, 2, +1))          # B next to the Gatehouse plate
    assert ep.observe("B")["state"]["gates"][0]["open_pct"] == 100
    ep.step("B", "RIGHT")                                   # onto the drop plate at col 3
    run(ep, P.RUN + 12)
    assert ep.observe("B")["state"]["gates"][0]["open_pct"] < 100


def test_same_seed_and_same_inputs_give_an_identical_trace():
    script = {0: [("A", "RIGHT"), ("B", "LEFT")], 3: [("A", "JUMP_RIGHT")],
              9: [("B", "STEP_LEFT")], 20: [("A", "DOWN"), ("B", "UP")]}

    def trace(seed):
        ep = arena_episode(seed)
        out = []
        for frame in range(60):
            for seat, act in script.get(frame, ()):
                ep.step(seat, act)
            ep.tick()
            out.append(json.dumps(ep._duel.snapshot(), sort_keys=True, default=str))
        return out

    assert trace(3) == trace(3)


# --- endings (GDD 5.3) ---------------------------------------------------
def test_one_death_wins_for_the_other_and_two_are_a_draw():
    ep = arena_episode()
    ep._duel.rivals["A"]._die("died:spikes")
    ep.tick()
    assert ep.outcome()["reason"] == "won:B"
    assert ep.legal_actions("B") == [] and not ep.step("B", "LEFT")["accepted"]
    ep = arena_episode()
    ep._duel.rivals["A"]._die("died:spikes")
    ep._duel.rivals["B"]._die("died:fall")
    ep.tick()
    assert ep.outcome()["reason"] == "draw:both_died"


def test_time_limit_is_a_draw():
    ep = VersusEpisode(arena.situation("A"), arena.STARTS, 0, time_limit_frames=5)
    run(ep, 5)
    assert ep.outcome()["reason"] == "draw:time_up"


# --- what each seat sees (VERSUS_SPEC 6) -----------------------------------
def test_observation_fields():
    ep = episode(a=(2, 0, 2, +1), b=(2, 0, 6, -1))
    obs = ep.observe("A")
    assert set(obs) == OBSERVATION_KEYS
    assert ME_EXTRA_KEYS <= set(obs["me"])
    assert len(obs["figures"]) == 1 and set(obs["figures"][0]) == FIGURE_KEYS
    assert obs["figures"][0]["kind"] == "rival" and obs["figures"][0]["col"] == 6


def test_a_rival_in_another_room_is_not_observed():
    ep = arena_episode()
    for seat in SEATS:
        assert ep.observe(seat)["figures"] == []


def test_observation_names_no_seat_and_shows_no_other_room():
    ep = episode(a=(2, 0, 2, +1), b=(2, 0, 6, -1))
    ep.step("B", "JUMP_LEFT")
    ep.tick()
    text = json.dumps(ep.observe("A"))
    for secret in ('"seat"', '"A"', '"B"', "pending", "plate_links", "seed", "situation"):
        assert secret not in text, secret
    rows = ep.observe("A")["tiles"]
    assert rows == list(arena.ROOMS[2]) or rows == arena.ROOMS[2]


def test_a_move_ending_in_another_room_does_not_show_where():
    ep = episode(a=(1, 0, 9, +1), b=(3, 2, 7, -1))          # A at the West Cells' right edge
    ep.step("A", "RIGHT")                                   # runs into the Gatehouse
    ep.tick()
    motion = me(ep, "A")["motion"]
    assert motion["effect"] == "moved" and motion["to"] is None


def test_the_other_rivals_input_is_never_observed():
    ep = episode(a=(2, 0, 2, +1), b=(2, 0, 6, -1))
    before = ep.observe("A")
    ep.step("B", "RUN_JUMP_LEFT")                           # queued, not started
    assert ep.observe("A") == before


# --- later stages (strict xfail: they must start failing, then be unmarked) --
@pytest.mark.xfail(strict=True, reason="Stage 4: disguise (R-V18) not implemented")
def test_disguised_rival_is_observed_exactly_as_a_guard():
    ep = arena_episode()
    assert hasattr(ep, "take_uniform")


@pytest.mark.xfail(strict=True, reason="Stage 4: suspicion (R-V19) not implemented")
def test_suspicion_is_shown_only_to_the_suspected_seat():
    ep = arena_episode()
    assert ep.observe("A")["suspicion"] != []


# --- local two-player test bench (play.py --versus) --------------------------
@pytest.mark.parametrize("held,shift,expected", [
    ({"right"}, False, "RIGHT"), ({"left"}, True, "STEP_LEFT"),
    ({"up", "right"}, False, "JUMP_RIGHT"), ({"up", "left"}, True, "RUN_JUMP_LEFT"),
    ({"up"}, False, "UP"), ({"down"}, False, "DOWN"), (set(), False, None),
])
def test_versus_keys_map_to_the_same_actions_as_any_seat(held, shift, expected):
    import play
    assert play.versus_input(held, shift) == expected


def test_versus_window_draws_each_seats_own_view(tmp_path):
    pytest.importorskip("pygame")
    import os
    import play
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    shot = tmp_path / "versus.png"
    assert play.main(["ARENA", "--versus", "--screenshot", str(shot),
                      "--keys", "A:RIGHT,B:LEFT"]) == 0
    assert shot.stat().st_size > 0


def test_versus_pose_follows_the_move_in_progress():
    from render import versus_view
    ep = episode(a=(2, 0, 2, +1), b=(2, 0, 7, -1))
    ep.step("A", "RIGHT")
    run(ep, 2)
    obs = ep.observe("B")
    fig = obs["figures"][0]
    p = versus_view.pose(fig, obs["room"])
    assert p.kind == "run" and 2 * 32 + 16 < p.x < 3 * 32 + 16      # on its way to col 3


@pytest.mark.parametrize("held,armed,expected", [
    ({"draw"}, False, "DRAW"), ({"draw"}, True, "SHEATHE"), ({"attack"}, True, "LUNGE"),
    ({"attack", "up"}, True, "THROW"), ({"attack", "down"}, True, "SWEEP"),
    ({"up"}, True, "STANCE_UP"), ({"down"}, True, "STANCE_DOWN"), ({"up"}, False, "UP"),
])
def test_versus_swordplay_keys(held, armed, expected):
    import play
    assert play.versus_input(held, False, armed) == expected


def test_swordplay_is_drawn_from_our_strips():
    from render import versus_view
    counts = {"lunge_high": 8, "lunge_mid": 8, "lunge_low": 8, "throw": 8, "dive_kick": 6,
              "sweep": 7, "take": 5, "stance_mid": 6, "death": 8}
    base = {"row": 0, "col": 3, "facing": "right", "posture": "standing", "armed": True,
            "stance": "high", "motion": None}
    assert versus_view.sprite(base, counts).strip == "stance_high"
    lunging = dict(base, motion={"effect": "lunge", "frame": 4, "frames": 8, "to": [0, 3],
                                 "to_posture": "standing", "to_facing": "right"})
    spr = versus_view.sprite(lunging, counts)
    assert spr.strip == "lunge_high" and spr.index == 3
    assert versus_view.sprite(dict(base, posture="knocked_down"), counts).strip == "death"
    assert versus_view.sprite(dict(base, armed=False, stance=None), counts) is None


def test_guards_are_drawn_from_the_guard_strips():
    from render import versus_view
    counts = {"downed": 8, "walk": 8, "stand": 1, "stance_mid": 6, "stance_high": 6,
              "lunge_high": 8}
    base = {"row": 2, "col": 3, "facing": "left", "posture": "standing", "armed": False,
            "stance": None, "motion": None}
    assert versus_view.guard_sprite(base, counts).strip == "stand"
    walking = dict(base, motion={"effect": "moved", "frame": 4, "frames": 8, "to": [2, 2],
                                 "to_posture": "standing", "to_facing": "left"})
    spr = versus_view.guard_sprite(walking, counts)
    assert spr.strip == "walk" and 2 * 32 + 16 < spr.x < 3 * 32 + 16
    assert versus_view.guard_sprite(dict(base, posture="downed"), counts).index == 7
    assert versus_view.guard_sprite(dict(base, armed=True, stance="high"), counts).strip == "stance_high"
