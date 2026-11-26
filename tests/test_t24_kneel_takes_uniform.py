"""T24 (Saad #94, 2026-11-25): DOWN over, or beside and facing, a downed uniformed
guard takes the uniform like TAKE (amends R-V17). A sword on the cell comes first
(R-V09). Written before the engine change."""
from __future__ import annotations

import json

import pytest

from pop import versus as V
from tests.test_disguise import episode, run


def kneel(ep, seat="A"):
    assert "DOWN" in ep.legal_actions(seat)
    ep.step(seat, "DOWN")


def over(facing=+1):
    return episode(a=(2, 0, 1, facing))                 # on the downed guard's cell


def beside():
    return episode()                                    # one cell away, facing it


@pytest.mark.parametrize("make", [over, beside])
def test_down_takes_the_uniform_in_12_frames(make):
    ep = make()
    kneel(ep)
    run(ep, V.TAKE_FRAMES)
    assert ep.observe("A")["me"]["disguised"] is False
    run(ep, 1)
    me = ep.observe("A")["me"]
    assert me["disguised"] is True and me["armed"] is False
    assert ep._duel.guards["down"].uniform is False
    assert ep.observe("A")["last_result"]["effect"] == "took_uniform"


def test_a_dropped_sword_on_the_cell_is_picked_up_first_then_down_takes_the_uniform():
    ep = over()
    d = ep._duel
    d.rivals["A"].sword = "none"                         # R-V09: only an unarmed rival picks up
    d.swords.append(d.rivals["A"].kid.cell)
    kneel(ep)
    run(ep, V.PICKUP_FRAMES + 1)
    r = d.rivals["A"]
    assert r.sword == "drawn" and d.guards["down"].uniform is True and not r.disguised
    assert ep.observe("A")["last_result"]["effect"] == "took_sword"
    ep.step("A", "SHEATHE")                              # DOWN is a stance change while drawn
    run(ep, V.SHEATHE_FRAMES + 1)
    kneel(ep)
    run(ep, V.TAKE_FRAMES + 1)
    assert r.disguised and d.guards["down"].uniform is False


def test_down_with_nothing_to_take_is_unchanged():
    ep = episode(a=(2, 0, 4, +1))                       # nowhere near the body
    kneel(ep)
    run(ep, 20)
    assert ep.observe("A")["me"]["disguised"] is False
    assert ep._duel.guards["down"].uniform is True
    assert ep.observe("A")["last_result"]["effect"] != "took_uniform"


def test_down_over_a_stripped_body_does_not_report_no_uniform():
    ep = over()
    ep._duel.guards["down"].uniform = False
    kneel(ep)
    run(ep, 20)
    assert ep.observe("A")["last_result"]["effect"] != "no_uniform"
    assert not ep._duel.rivals["A"].disguised


def test_down_when_already_disguised_takes_nothing():
    ep = over()
    r = ep._duel.rivals["A"]
    r.disguised, r.sword = True, "sheathed"
    kneel(ep)
    run(ep, 20)
    assert ep._duel.guards["down"].uniform is True


def test_take_is_unchanged():
    ep = over()
    ep.step("A", "TAKE")
    run(ep, V.TAKE_FRAMES + 1)
    assert ep.observe("A")["me"]["disguised"] is True
    assert ep._duel.guards["down"].uniform is False


@pytest.mark.parametrize("make", [over, beside])
def test_the_other_seat_sees_the_same_for_down_take_and_take(make):
    """R-V25: identical observation of the kneeling rival either way."""
    seen = {}
    for act in ("DOWN", "TAKE"):
        ep = make()
        ep.step("A", act)
        out = []
        for _ in range(V.TAKE_FRAMES + 2):
            ep.tick()
            out.append(json.dumps(ep.observe("B"), sort_keys=True))
        seen[act] = out
    assert seen["DOWN"] == seen["TAKE"]


def test_no_new_action_and_down_stays_legal_where_it_was():
    ep = over()
    legal = ep.legal_actions("A")
    assert "DOWN" in legal and "TAKE" in legal
    assert not any("KNEEL" in a for a in legal)
    nothing = episode(a=(2, 0, 4, +1))
    assert "DOWN" in nothing.legal_actions("A") and "TAKE" not in nothing.legal_actions("A")


def test_a_hanging_rival_over_a_body_still_just_lets_go():
    """Macros issue DOWN only to drop from a ledge; it must never turn into a take."""
    ep = over()
    r = ep._duel.rivals["A"]
    r.kid.posture = "hanging"
    assert r._kneel_target() is None
