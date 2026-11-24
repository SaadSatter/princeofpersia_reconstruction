"""Leak tests for rigged traps (docs/final/TRAPS_SPEC.md Section 6, R-V34).

A rig is a fact only its owner may know: ownership and position never reach the
other seat's observation, legal actions or prompt.
"""

from __future__ import annotations

import copy
import json
import re

from pop import arena
from pop import versus as V
from pop.versus import VersusEpisode

X = (0, 2)                                    # row, col rigged by A from (2, 0, 1) facing right


def episode(a=(2, 0, 1, +1), b=(2, 0, 8, -1), posts=None) -> VersusEpisode:
    return VersusEpisode(arena.situation("A"), dict(arena.STARTS, A=a, B=b), 0, guard_posts=posts)


def run(ep, n):
    for _ in range(n):
        ep.tick()


def rig(ep, seat):
    assert ep.step(seat, "RIG")["accepted"]
    run(ep, V.RIG_FRAMES + 1)


def own(obs):
    """An observation without the two fields that are the seat's own budget."""
    obs = copy.deepcopy(obs)
    obs.pop("my_traps")
    obs["me"].pop("traps_left")
    return obs


# 1. A rigged tile is a normal tile, field for field --------------------------
def test_the_other_seat_sees_nothing_different_after_a_rig():
    rigged, control = episode(), episode()
    rigged.step("A", "RIG")
    for _ in range(V.RIG_FRAMES + 1):
        rigged.tick(), control.tick()
        r, c = rigged.observe("B"), control.observe("B")
        for key in ("tiles", "state", "motion", "edges", "swords", "suspicion"):
            if key in r:
                assert r[key] == c[key], key
    assert rigged.observe("B") == control.observe("B")                  # whole, once the kneel is over
    assert rigged.observe("B")["tiles"] == control.observe("B")["tiles"]


def test_the_owner_sees_a_normal_tile_too():
    ep = episode()
    before = ep.observe("A")["tiles"]
    rig(ep, "A")
    assert ep.observe("A")["tiles"] == before


# 2. The owner sees only its own rigs ----------------------------------------
def test_each_seat_lists_only_its_own_rigs():
    ep = episode(b=(2, 0, 8, -1))
    rig(ep, "A")
    assert ep.observe("A")["my_traps"] == [{"row": 0, "col": 2, "kind": "loose"}]
    assert ep.observe("B")["my_traps"] == []
    rig(ep, "B")                                                        # B rigs col 7 ahead of it
    assert ep.observe("B")["my_traps"] == [{"row": 0, "col": 7, "kind": "loose"}]
    assert ep.observe("A")["my_traps"] == [{"row": 0, "col": 2, "kind": "loose"}]


def test_a_rig_is_listed_only_while_its_owner_is_in_that_room():
    ep = episode()
    rig(ep, "A")
    ep._duel.rivals["A"].kid.room = 1
    assert ep.observe("A")["my_traps"] == []


# 3. Legal actions are identical ---------------------------------------------
def test_the_other_seats_legal_actions_do_not_change_when_a_rig_appears():
    rigged, control = episode(), episode()
    before = rigged.legal_actions("B")
    rig(rigged, "A")
    run(control, V.RIG_FRAMES + 1)
    assert rigged.legal_actions("B") == before == control.legal_actions("B")


# 4. Double rig --------------------------------------------------------------
def test_rigging_a_cell_the_other_seat_rigged_looks_exactly_like_an_unrigged_cell():
    rigged, control = episode(b=(2, 0, 3, -1)), episode(b=(2, 0, 3, -1))
    rig(rigged, "A")
    run(control, V.RIG_FRAMES + 1)
    assert "RIG" in rigged.legal_actions("B") and "RIG" in control.legal_actions("B")
    assert rigged.legal_actions("B") == control.legal_actions("B")
    rigged.step("B", "RIG"), control.step("B", "RIG")
    for _ in range(V.RIG_FRAMES + 1):
        rigged.tick(), control.tick()
        assert rigged.observe("B") == control.observe("B")
        assert rigged.legal_actions("B") == control.legal_actions("B")
    assert rigged.observe("B")["me"]["traps_left"] == 3
    assert rigged.observe("B")["my_traps"] == control.observe("B")["my_traps"]


# 5. A spring does not name the owner -----------------------------------------
LEAK_WORDS = re.compile(r"\b(trap|traps|rig|rigs|rigged|rigging|owner|owned)\b", re.I)


def assert_unnamed(obs):
    plain = own(obs)
    plain.pop("task")
    text = json.dumps(plain)
    assert not LEAK_WORDS.search(text), LEAK_WORDS.search(text).group(0)
    assert '"A"' not in text and '"B"' not in text


def test_springing_a_rig_names_no_owner_and_no_trap_to_the_victim():
    ep = episode(b=(2, 0, 4, -1))
    rig(ep, "A")
    for _ in range(2):
        ep.step("B", "STEP_LEFT")
        for _ in range(8):
            ep.tick()
            assert_unnamed(ep.observe("B"))
    for _ in range(20):
        ep.tick()
        obs = ep.observe("B")
        assert_unnamed(obs)
    assert obs["me"]["hp"] == 2 and obs["last_result"]["effect"] in ("hurt", "landed", "fell")


def test_a_guard_springing_a_rig_names_no_owner_either():
    ep = episode(a=(1, 2, 2, +1), b=(2, 0, 7, -1), posts={"g": (2, 0, (2, 5), -1)})
    ep._duel.place_rig("A", (2, 0, 2))
    for _ in range(120):
        ep.tick()
        assert_unnamed(ep.observe("B"))
    assert ep._duel.guards["g"].downed


# 6. The message and the AI seat's prompt --------------------------------------
def test_the_ai_prompt_for_the_other_seat_is_unchanged_by_a_rig():
    from agents.model_player import ModelPlayer

    class Silent:
        def complete(self, system, user):
            raise AssertionError("no call")

    rigged, control = episode(), episode()
    rig(rigged, "A")
    run(control, V.RIG_FRAMES + 1)
    obs_r, obs_c = rigged.observe("B"), control.observe("B")
    p_r = ModelPlayer(Silent()).build_user_prompt(obs_r, rigged.legal_actions("B"))
    p_c = ModelPlayer(Silent()).build_user_prompt(obs_c, control.legal_actions("B"))
    assert p_r == p_c


def test_observe_is_the_whole_message_for_a_seat_and_adds_nothing_from_the_other():
    ep = episode()
    rig(ep, "A")
    b = ep.observe("B")
    assert set(b) == V.OBSERVATION_KEYS
    assert json.dumps(b) == json.dumps(ep.observe("B"))                 # pure read, no hidden state
    assert b["my_traps"] == [] and b["me"]["traps_left"] == 4


# 7. Owner can be hurt (kept beside the leak tests, as the spec says) -----------
def test_the_owner_loses_a_heart_stepping_on_its_own_rig():
    ep = episode(b=(3, 2, 7, -1))
    rig(ep, "A")
    ep.step("A", "STEP_RIGHT")
    run(ep, 30)
    assert ep.observe("A")["me"]["hp"] == 2
