"""Rival-rigged traps, the loose-floor type (docs/final/TRAPS_SPEC.md, R-V27 to R-V34).

Saad's decision #22 (2026-11-23): one-shot, rig the cell ahead, 12-frame kneel,
4 per rival, disguised rigging +3 suspicion per frame in a guard's sight, the
owner can be hurt, double rig allowed. Posts used: the Gatehouse top row (room 2,
row 0) is open floor `___t__t___`, over a middle row `_._p_G_p._`.
"""

from __future__ import annotations

import json

from pop import arena
from pop import versus as V
from pop.guards import Guard
from pop.mechanics import LOOSE_DELAY
from pop.versus import VersusEpisode

X = (2, 0, 2)                      # the cell A rigs from (2, 0, 1) facing right


def episode(a=(2, 0, 1, +1), b=(3, 2, 7, -1), posts=None, seed=0) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), seed,
                         guard_posts=posts)


def run(ep, n):
    for _ in range(n):
        ep.tick()


def rig(ep, seat="A"):
    assert "RIG" in ep.legal_actions(seat)
    assert ep.step(seat, "RIG")["accepted"]
    run(ep, V.RIG_FRAMES + 1)


def mine(ep, seat):
    return ep.observe(seat)["my_traps"]


def hearts(ep, seat):
    return ep.observe(seat)["me"]["hp"]


# R-V27: legality and target ------------------------------------------------
def test_rig_is_legal_on_plain_floor_ahead():
    assert "RIG" in episode().legal_actions("A")


def test_rig_is_refused_on_anything_but_plain_floor_with_a_floor_below():
    assert "RIG" not in episode(a=(2, 0, 2, +1)).legal_actions("A")     # torch ahead (col 3)
    assert "RIG" not in episode(a=(2, 0, 9, +1)).legal_actions("A")     # room edge ahead
    assert "RIG" not in episode(a=(2, 1, 1, +1)).legal_actions("A")     # hole ahead
    assert "RIG" not in episode(a=(2, 1, 2, +1)).legal_actions("A")     # drop plate ahead
    assert "RIG" not in episode(a=(1, 1, 5, +1)).legal_actions("A")     # loose tile ahead
    assert "RIG" not in episode().legal_actions("B")                    # B is on the bottom row
    # Bottom row: the floor below would be in a room the seat cannot see.
    assert "RIG" not in episode(a=(2, 2, 0, +1)).legal_actions("A")


def test_rig_is_refused_on_a_cell_holding_a_body_or_a_landing_cell():
    ep = episode(b=(2, 0, 2, -1))
    assert "RIG" not in ep.legal_actions("A")                           # the other rival stands there
    ep = episode(posts={"g": (2, 0, (2, 2), +1)})
    assert "RIG" not in ep.legal_actions("A")                           # a guard stands there
    ep = episode()
    ep._duel.guards["g"] = guard = Guard.at_post("g", (2, 0, (2, 2), +1))
    guard.knock_out()
    assert "RIG" not in ep.legal_actions("A")                           # a downed guard lies there


def test_rig_is_refused_when_no_traps_are_left_or_already_rigged_by_this_seat():
    ep = episode()
    ep._duel.traps_left["A"] = 0
    assert "RIG" not in ep.legal_actions("A")
    ep = episode()
    rig(ep)
    assert "RIG" not in ep.legal_actions("A")                           # its own rig is there


def test_rig_is_legal_with_a_sword_drawn_or_sheathed_and_stays_as_it_was():
    ep = episode()
    ep.step("A", "DRAW")
    run(ep, V.DRAW_FRAMES + 1)
    assert "RIG" in ep.legal_actions("A")
    rig(ep)
    assert ep.observe("A")["me"]["armed"] is True


# R-V27: the kneel ----------------------------------------------------------
def test_the_kneel_takes_12_frames_and_spends_the_trap_at_its_start():
    ep = episode()
    assert ep.observe("A")["me"]["traps_left"] == 4
    ep.step("A", "RIG")
    run(ep, 1)
    assert ep.observe("A")["me"]["traps_left"] == 3
    run(ep, V.RIG_FRAMES - 1)
    assert mine(ep, "A") == []                                         # not yet rigged
    run(ep, 1)
    assert mine(ep, "A") == [{"row": 0, "col": 2, "kind": "loose"}]
    assert ep.observe("A")["last_result"]["effect"] == "rigged"


def test_a_hit_during_the_kneel_cancels_the_rig_and_still_spends_the_trap():
    ep = episode()
    ep.step("A", "RIG")
    run(ep, 5)
    d = ep._duel
    d._hit(d.rivals["A"], -1, "died:stabbed")
    run(ep, V.RIG_FRAMES + 2)
    assert mine(ep, "A") == []
    assert ep.observe("A")["me"]["traps_left"] == 3
    assert hearts(ep, "A") == 2
    assert not d.rigs


def test_a_knockdown_during_the_kneel_cancels_the_rig_and_still_spends_the_trap():
    ep = episode()
    ep.step("A", "RIG")
    run(ep, 5)
    d = ep._duel
    d.cancel("A")
    d.rivals["A"].knocked_down = V.KNOCKDOWN_FRAMES
    run(ep, V.RIG_FRAMES + V.KNOCKDOWN_FRAMES)
    assert mine(ep, "A") == [] and ep.observe("A")["me"]["traps_left"] == 3


# R-V28, R-V30, R-V32: spring, one-shot, owner and guard --------------------
def walk_onto(ep, seat, steps):
    for action in steps:
        assert ep.step(seat, action)["accepted"]
        run(ep, 8)


def b_in_room(posts=None):
    return episode(b=(2, 0, 4, -1), posts=posts)


def test_a_rig_springs_when_a_body_steps_onto_it_then_the_floor_falls():
    ep = b_in_room()
    rig(ep)
    assert [0, 2] not in ep.observe("B")["state"]["loose_shaking"]
    walk_onto(ep, "B", ["STEP_LEFT", "STEP_LEFT"])                      # col 4 -> 3 -> 2
    assert [0, 2] in ep.observe("B")["state"]["loose_shaking"]
    assert ep.observe("B")["tiles"][0][2] == "_"                        # still a floor while it shakes
    run(ep, LOOSE_DELAY + 2)
    assert ep.observe("B")["me"]["hp"] == 2                             # a sprung trap costs 1 heart
    assert ep._duel.rivals["B"].kid.row == 1                            # it fell to the middle floor


def test_standing_on_a_rig_does_not_spring_it():
    ep = b_in_room()
    d = ep._duel
    d.rivals["B"].kid.col = 2                                           # B already stands on X
    rig_cell = X
    d.place_rig("A", rig_cell)
    run(ep, 30)
    assert rig_cell in d.rigs and hearts(ep, "B") == 3


def test_a_rig_is_one_shot_and_frees_no_trap():
    ep = b_in_room()
    rig(ep)
    walk_onto(ep, "B", ["STEP_LEFT", "STEP_LEFT"])
    run(ep, LOOSE_DELAY + 12)
    assert not ep._duel.rigs and mine(ep, "A") == []
    assert ep.observe("A")["me"]["traps_left"] == 3                     # nothing is refunded


def test_the_owner_can_be_hurt_by_its_own_rig():
    ep = episode()
    rig(ep)
    walk_onto(ep, "A", ["STEP_RIGHT"])                                  # A steps onto X
    run(ep, LOOSE_DELAY + 12)
    assert hearts(ep, "A") == 2


def test_a_guard_springs_a_rig_and_is_downed_when_the_floor_falls():
    ep = episode(a=(1, 2, 2, +1), posts={"g": (2, 0, (2, 5), -1)})      # patrols from col 5 to col 2
    ep._duel.place_rig("A", X)
    run(ep, 120)
    g = ep._duel.guards["g"]
    assert g.downed and X not in ep._duel.rigs


def test_a_double_rig_is_consumed_by_the_first_body():
    ep = episode(b=(2, 0, 3, -1))
    rig(ep, "A")
    rig(ep, "B")                                                        # B rigs the same cell from the right
    assert mine(ep, "A") == mine(ep, "B") == [{"row": 0, "col": 2, "kind": "loose"}]
    walk_onto(ep, "A", ["STEP_RIGHT"])
    assert not ep._duel.rigs and mine(ep, "A") == [] and mine(ep, "B") == []
    run(ep, LOOSE_DELAY + 12)
    assert hearts(ep, "A") == 2 and hearts(ep, "B") == 3                # one fall, not two


# R-V31: budget -------------------------------------------------------------
def test_each_rival_starts_with_four_traps():
    ep = episode()
    assert ep.observe("A")["me"]["traps_left"] == ep.observe("B")["me"]["traps_left"] == 4


# R-V33: disguise -----------------------------------------------------------
def test_rigging_while_disguised_in_a_guards_sight_adds_3_suspicion_per_frame():
    ep = episode(a=(2, 0, 4, +1), posts={"watch": (2, 0, (8, 8), -1)})
    d = ep._duel
    d.guards["watch"].pause = 10_000
    d.rivals["A"].disguised = True
    ep.step("A", "RIG")
    run(ep, V.RIG_FRAMES)
    assert d.suspicion[("watch", "A")] == V.SUSPICION_RIG * V.RIG_FRAMES == 36
    assert d.rivals["A"].disguised is True                              # rigging does not break it by itself


def test_rigging_while_disguised_is_shown_to_the_other_seat_as_standing_still():
    ep = episode(a=(2, 0, 4, +1), b=(2, 0, 8, -1))
    ep._duel.rivals["A"].disguised = True
    ep.step("A", "RIG")
    run(ep, 4)
    (fig,) = [f for f in ep.observe("B")["figures"]]
    assert fig["kind"] == "guard" and fig["motion"] is None


# determinism and schema ----------------------------------------------------
def test_the_same_seed_and_inputs_give_the_same_trace():
    def play():
        ep = b_in_room(posts={"g": (2, 0, (6, 8), -1)})
        out = []
        ep.step("A", "RIG")
        for i in range(60):
            if i == 20:
                ep.step("B", "STEP_LEFT")
            ep.tick()
            out.append(json.dumps(ep._duel.snapshot(), sort_keys=True, default=str))
        return out
    assert play() == play()


def test_both_seats_have_the_same_observation_keys_and_my_traps_in_the_schema():
    ep = episode(b=(2, 0, 4, -1))
    a, b = ep.observe("A"), ep.observe("B")
    assert set(a) == set(b) == V.OBSERVATION_KEYS and "my_traps" in V.OBSERVATION_KEYS
    assert set(a["me"]) == set(b["me"]) and "traps_left" in V.ME_EXTRA_KEYS
    rig(ep)
    assert set(ep.observe("A")) == set(ep.observe("B"))
    assert set(ep.observe("A")["me"]) == set(ep.observe("B")["me"])
    assert ep.observe("A")["tiles"] == ep.observe("B")["tiles"]         # no new tile glyph for anyone


def test_both_seats_use_the_same_rig_interface():
    ep = episode(a=(2, 0, 1, +1), b=(2, 0, 8, -1))
    assert "RIG" in ep.legal_actions("A") and "RIG" in ep.legal_actions("B")
    assert ep.step("A", "RIG")["accepted"] and ep.step("B", " rig ")["accepted"]
