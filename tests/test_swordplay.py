"""Swordplay, R-V01 to R-V12 (docs/final/VERSUS_SPEC.md Section 3), one test or more per rule.

Rivals are placed in the Gatehouse's top row (room 2, row 0: open floor,
cols 0-9) unless a test needs otherwise.
"""

from __future__ import annotations

import pytest

from pop import arena
from pop.versus import VersusEpisode
from pop import versus as V


def duel(a=(2, 0, 3, +1), b=(2, 0, 4, -1), seed=0, armed=True) -> VersusEpisode:
    starts = dict(arena.STARTS, A=a, B=b)
    ep = VersusEpisode(arena.situation("A"), starts, seed)
    if armed:
        for seat in ("A", "B"):
            ep.step(seat, "DRAW")
        run(ep, V.DRAW_FRAMES + 1)
    return ep


def run(ep, n):
    for _ in range(n):
        ep.tick()


def me(ep, seat):
    return ep.observe(seat)["me"]


def rival(ep, seat):
    return ep._duel.rivals[seat]


def set_stance(ep, seat, stance):
    rival(ep, seat).stance = stance


def lunge_until_active_end(ep, seat):
    ep.step(seat, "LUNGE")
    run(ep, V.LUNGE_WINDUP + V.LUNGE_ACTIVE + 1)


# R-V02 -------------------------------------------------------------------
def test_rivals_start_sheathed_and_draw_to_mid_in_3_frames():
    ep = duel(armed=False)
    assert me(ep, "A")["armed"] is False and me(ep, "A")["stance"] is None
    assert "LUNGE" not in ep.legal_actions("A") and "DRAW" in ep.legal_actions("A")
    ep.step("A", "DRAW")
    run(ep, V.DRAW_FRAMES)
    assert me(ep, "A")["armed"] is False                   # the draw's frames are still running
    run(ep, 1)
    assert me(ep, "A")["armed"] is True and me(ep, "A")["stance"] == "mid"
    assert V.DRAW_FRAMES == 3


def test_a_drawn_sword_frees_up_down_for_stances_and_sheathing_frees_them_again():
    ep = duel()
    legal = ep.legal_actions("A")
    assert "STANCE_UP" in legal and "STANCE_DOWN" in legal and "UP" not in legal and "DOWN" not in legal
    ep.step("A", "SHEATHE")
    run(ep, V.SHEATHE_FRAMES + 1)
    assert "UP" in ep.legal_actions("A") and me(ep, "A")["armed"] is False


# R-V03 -------------------------------------------------------------------
def test_stance_change_lands_after_2_frames_even_mid_move():
    ep = duel()
    ep.step("A", "STEP_LEFT")                               # turn: a move in progress
    run(ep, 1)
    ep.step("A", "STANCE_UP")
    run(ep, V.STANCE_FRAMES - 1)
    assert me(ep, "A")["stance"] == "mid"
    run(ep, 1)
    assert me(ep, "A")["stance"] == "high"
    assert V.STANCE_FRAMES == 2
    assert "STANCE_UP" not in ep.legal_actions("A")         # nothing above high


# R-V04, R-V06 ------------------------------------------------------------
def test_lunge_timing_and_a_clean_hit_costs_one_heart_and_pushes_back():
    assert (V.LUNGE_WINDUP, V.LUNGE_ACTIVE, V.LUNGE_RECOVERY) == (2, 2, 4)
    ep = duel()
    set_stance(ep, "B", "low")                              # mismatched: A lunges mid
    ep.step("A", "LUNGE")
    run(ep, V.LUNGE_WINDUP)
    assert me(ep, "B")["hp"] == 3                           # no hit during the windup
    run(ep, 1)
    assert me(ep, "B")["hp"] == 2 and me(ep, "B")["col"] == 5      # hit and pushed back 1


def test_hit_gives_12_frames_of_invulnerability():
    assert V.INVULNERABLE_FRAMES == 12
    ep = duel(b=(2, 0, 4, -1))
    set_stance(ep, "B", "low")
    lunge_until_active_end(ep, "A")
    assert me(ep, "B")["hp"] == 2
    rival(ep, "B").kid.col = 4                              # put B back in reach at once
    run(ep, V.LUNGE_RECOVERY)
    ep.step("A", "LUNGE")
    run(ep, V.LUNGE_WINDUP + 1)
    assert me(ep, "B")["hp"] == 2                           # still invulnerable (12 frames)


def test_a_lunge_out_of_reach_hits_nothing():
    ep = duel(b=(2, 0, 6, -1))
    set_stance(ep, "B", "low")
    lunge_until_active_end(ep, "A")
    assert me(ep, "B")["hp"] == 3


def test_three_hits_kill_and_win_for_the_other_rival():
    ep = duel()
    rival(ep, "B").kid.hp = 1
    set_stance(ep, "B", "low")
    lunge_until_active_end(ep, "A")
    assert ep.outcome()["reason"] == "won:A"


# R-V05 -------------------------------------------------------------------
def test_matching_stance_blocks_and_pushes_the_attacker_back():
    ep = duel()                                             # both mid, facing each other
    lunge_until_active_end(ep, "A")
    assert me(ep, "B")["hp"] == 3
    assert me(ep, "A")["col"] == 2                          # attacker pushed back 1 cell


def test_no_block_when_facing_away():
    ep = duel(b=(2, 0, 4, +1))                              # B has its back to A
    lunge_until_active_end(ep, "A")
    assert me(ep, "B")["hp"] == 2


# R-V07 -------------------------------------------------------------------
def test_a_stance_change_landing_after_the_windup_is_too_late():
    ep = duel()
    set_stance(ep, "A", "high")
    ep.step("A", "LUNGE")
    run(ep, 2)
    ep.step("B", "STANCE_UP")                               # lands on the 2nd active frame
    run(ep, V.LUNGE_WINDUP + V.LUNGE_ACTIVE)
    assert me(ep, "A")["armed"] is True                     # no disarm
    assert me(ep, "B")["hp"] == 2                           # and B was still mid at the first active frame


def test_disarm_knocks_the_sword_one_or_two_cells_behind_the_attacker():
    ep = duel()
    set_stance(ep, "A", "high")
    set_stance(ep, "B", "mid")
    ep.step("B", "STANCE_UP")                               # lands 2 frames from now
    ep.step("A", "LUNGE")                                   # windup frames 1-2: the change lands in it
    run(ep, V.STANCE_FRAMES)
    assert me(ep, "A")["armed"] is False and rival(ep, "A").sword == "none"
    swords = ep.observe("A")["swords"]
    assert len(swords) == 1 and swords[0]["col"] in (1, 2) and swords[0]["flying"] is False
    assert me(ep, "B")["hp"] == 3


# R-V08 -------------------------------------------------------------------
def test_thrown_sword_hits_the_first_rival_in_the_row_for_one_heart():
    ep = duel(a=(2, 0, 1, +1), b=(2, 0, 8, -1))
    set_stance(ep, "B", "low")
    ep.step("A", "THROW")
    run(ep, V.THROW_RELEASE + 4)
    assert me(ep, "B")["hp"] == 2
    assert rival(ep, "A").sword == "none" and me(ep, "A")["armed"] is False
    assert [(s["col"], s["flying"]) for s in ep.observe("A")["swords"]] == [(8, False)]
    assert V.THROW_SPEED == 2


def test_thrown_sword_is_deflected_by_the_throwers_stance():
    ep = duel(a=(2, 0, 1, +1), b=(2, 0, 8, -1))             # both mid, facing
    ep.step("A", "THROW")
    run(ep, V.THROW_RELEASE + 4)
    assert me(ep, "B")["hp"] == 3
    assert len(ep.observe("A")["swords"]) == 1


def test_thrown_sword_stops_at_the_room_edge():
    ep = duel(a=(2, 0, 7, +1), b=(1, 2, 2, +1))
    ep.step("A", "THROW")
    run(ep, V.THROW_RELEASE + 4)
    swords = ep.observe("A")["swords"]
    assert len(swords) == 1 and swords[0]["col"] == 9 and not swords[0]["flying"]


# R-V09 -------------------------------------------------------------------
def test_unarmed_cannot_lunge_throw_or_block_but_picks_a_sword_up():
    ep = duel(a=(2, 0, 7, +1), b=(1, 2, 2, +1))
    ep.step("A", "THROW")
    run(ep, V.THROW_RELEASE + V.THROW_RECOVERY + 4)
    legal = ep.legal_actions("A")
    assert "LUNGE" not in legal and "THROW" not in legal and "SWEEP" in legal
    rival(ep, "A").kid.col = 9                              # stand on the sword
    ep.step("A", "DOWN")
    run(ep, V.PICKUP_FRAMES + 1)
    assert me(ep, "A")["armed"] is True and ep.observe("A")["swords"] == []
    assert V.PICKUP_FRAMES == 6


def test_unarmed_defender_cannot_block():
    ep = duel()
    rival(ep, "B").sword, rival(ep, "B").stance = "none", None
    set_stance(ep, "A", "mid")
    lunge_until_active_end(ep, "A")
    assert me(ep, "B")["hp"] == 2


# R-V10 -------------------------------------------------------------------
def _jump_then_kick(ep, seat):
    ep.step(seat, "JUMP_RIGHT")
    run(ep, 7)                                              # past the jump's departure frame
    assert "KICK" in ep.legal_actions(seat)
    ep.step(seat, "KICK")
    run(ep, V.KICK_FRAMES + 2)


def test_dive_kick_disarms_and_knocks_down_without_a_heart():
    ep = duel(a=(2, 0, 2, +1), b=(2, 0, 4, -1))
    _jump_then_kick(ep, "A")
    b = me(ep, "B")
    assert b["hp"] == 3 and b["armed"] is False and b["knocked_down_frames"] > 0
    assert me(ep, "A")["col"] == 3                          # landed 1 cell ahead
    assert V.KNOCKDOWN_FRAMES == 10


def test_dive_kick_is_blocked_by_a_high_stance():
    ep = duel(a=(2, 0, 2, +1), b=(2, 0, 4, -1))
    set_stance(ep, "B", "high")
    _jump_then_kick(ep, "A")
    assert me(ep, "B")["armed"] is True and me(ep, "B")["knocked_down_frames"] == 0


def test_kick_is_only_legal_in_the_air():
    ep = duel()
    assert "KICK" not in ep.legal_actions("A")
    assert not ep.step("A", "KICK")["accepted"]


# R-V11 -------------------------------------------------------------------
def test_sweep_knocks_down_without_a_heart():
    ep = duel()
    ep.step("A", "SWEEP")
    run(ep, V.SWEEP_FRAMES + 1)
    assert me(ep, "B")["knocked_down_frames"] > 0 and me(ep, "B")["hp"] == 3
    assert V.SWEEP_FRAMES == 6


def test_sweep_is_avoided_by_a_low_stance():
    ep = duel()
    set_stance(ep, "B", "low")
    ep.step("A", "SWEEP")
    run(ep, V.SWEEP_FRAMES + 1)
    assert me(ep, "B")["knocked_down_frames"] == 0


# R-V12 -------------------------------------------------------------------
def test_knocked_down_cannot_act_and_a_lunge_always_hits():
    ep = duel()
    rival(ep, "B").knocked_down = 8
    assert ep.legal_actions("B") == []
    assert ep.observe("A")["figures"][0]["posture"] == "knocked_down"
    lunge_until_active_end(ep, "A")                        # B is mid like A: still hits
    assert me(ep, "B")["hp"] == 2


def test_swordplay_is_deterministic():
    import json

    def trace():
        ep = duel(seed=5)
        script = {0: ("A", "STANCE_UP"), 3: ("A", "LUNGE"), 4: ("B", "STANCE_UP"),
                  20: ("B", "THROW"), 40: ("A", "SWEEP")}
        out = []
        for f in range(70):
            if f in script:
                ep.step(*script[f])
            ep.tick()
            out.append(json.dumps(ep._duel.snapshot(), sort_keys=True, default=str))
        return out

    assert trace() == trace()
