"""Rule invariants of the engine, each tied to a rule-map id."""

import pytest

from pop import mechanics as M
from pop.engine import Game
from pop.situations import Situation


def sit(rooms, start, links=None, plate_links=None, exits_open=True):
    if isinstance(rooms, tuple):
        rooms = {1: rooms}
    links = links or {r: (0, 0, 0, 0) for r in rooms}
    return Situation(id="fixture", rooms=rooms, links=links, start=start,
                     plate_links=plate_links or {}, exits_open=exits_open)


FLAT = ("##########", "__________", "##########")


def game(rooms=FLAT, start=(1, 1, 0, +1), **kw):
    return Game(sit(rooms, start, **kw))


def pos(g):
    return g.kid.room, g.kid.row, g.kid.col


# --- movement (R-C26, R-D20, R-D01) -----------------------------------

def test_run_moves_one_block_in_four_frames():
    g = game()
    r = g.perform("RIGHT")
    assert pos(g) == (1, 1, 1) and r["frames"] == 4 and r["effect"] == "moved"


def test_reverse_direction_only_turns():
    g = game()
    r = g.perform("LEFT")
    assert pos(g) == (1, 1, 0) and g.kid.facing == -1 and r["effect"] == "turned"


def test_wall_and_level_edge_block_running():
    g = game(("##########", "_#________", "##########"))
    assert g.perform("RIGHT")["effect"] == "bumped" and pos(g) == (1, 1, 0)
    g = game(start=(1, 1, 0, -1))
    assert g.perform("LEFT")["effect"] == "bumped" and pos(g) == (1, 1, 0)


def test_careful_step_stops_at_edge_but_run_falls():
    rooms = ("##########", "__.____ __".replace(" ", "_"), "__________")
    g = game(rooms, start=(1, 1, 1, +1))
    assert g.perform("STEP_RIGHT")["effect"] == "edge" and pos(g) == (1, 1, 1)
    r = g.perform("RIGHT")
    assert pos(g) == (1, 2, 2) and g.kid.posture == "standing" and r["fell_rows"] == 1


def test_standing_jump_lands_three_blocks_ahead():
    g = game()
    g.perform("JUMP_RIGHT")
    assert pos(g) == (1, 1, 3)


def test_running_jump_lands_five_blocks_ahead():
    g = game()
    r = g.perform("RUN_JUMP_RIGHT")
    assert pos(g) == (1, 1, 5) and r["frames"] == 12


def test_jump_stops_before_wall():
    g = game(("##########", "___#______", "##########"))
    g.perform("JUMP_RIGHT")
    assert pos(g) == (1, 1, 2)


def test_running_jump_without_runup_floor_is_a_run_off_the_edge():
    g = game(("##########", "_.________", "__________"))
    g.perform("RUN_JUMP_RIGHT")
    assert pos(g) == (1, 2, 1) and g.kid.posture == "standing"


# --- falling (R-C10 via R-D03, R-D15, R-D17) ----------------------------

TOWER = {
    1: ("__________", "_.________", "_.________"),
    2: ("_.________", "__________", "##########"),
}
TOWER_LINKS = {1: (0, 0, 0, 2), 2: (0, 0, 1, 0)}


@pytest.mark.parametrize("start_row,rows,hp,terminal", [
    (2, 2, 2, None),          # row 2 of room 1 -> row 1 of room 2: 2 rows, -1 HP
    (1, 3, 0, "died:fall"),   # 3 rows: death
])
def test_fall_damage_by_rows(start_row, rows, hp, terminal):
    g = game(TOWER, start=(1, start_row, 0, +1), links=TOWER_LINKS)
    g.perform("RIGHT")
    while g.kid.posture == "falling":
        g.perform("WAIT")
    assert g.kid.hp == hp and g.terminal == terminal


def test_one_row_fall_is_safe():
    g = game(("_.________", "__________", "##########"), start=(1, 0, 0, +1))
    r = g.perform("RIGHT")
    assert pos(g) == (1, 1, 1) and g.kid.hp == 3 and r["fell_rows"] == 1


def test_hang_then_drop_counts_one_row_less():
    g = game(TOWER, start=(1, 2, 0, +1), links=TOWER_LINKS)
    assert g.perform("DOWN")["effect"] == "hanging" and g.kid.posture == "hanging"
    g.perform("DOWN")
    while g.kid.posture == "falling":
        g.perform("WAIT")
    assert pos(g) == (2, 1, 1) and g.kid.hp == 3


def test_hanging_up_climbs_back():
    g = game(TOWER, start=(1, 2, 0, +1), links=TOWER_LINKS)
    g.perform("DOWN")
    g.perform("UP")
    assert pos(g) == (1, 2, 0) and g.kid.posture == "standing"


def test_bottomless_drop_kills():
    g = game(("##########", "_.________", "_.________"))
    g.perform("RIGHT")
    while g.terminal is None:
        g.perform("WAIT")
    assert g.terminal == "died:fall"


# --- spikes (R-C13, R-D19) ------------------------------------------------

SPIKE_ROW = ("##########", "__^^______", "##########")


def test_running_onto_spikes_kills():
    g = game(SPIKE_ROW, start=(1, 1, 1, +1))
    g.perform("RIGHT")
    assert g.terminal == "died:spikes"


def test_careful_steps_across_spikes_are_safe():
    g = game(SPIKE_ROW, start=(1, 1, 1, +1))
    for _ in range(3):
        g.perform("STEP_RIGHT")
    assert pos(g) == (1, 1, 4) and g.terminal is None


def test_spikes_spring_when_near_and_retract_later():
    g = game(SPIKE_ROW, start=(1, 1, 1, +1))
    g.perform("WAIT")
    assert g.mech.spikes[(1, 1, 2)] > 0      # sprung while the kid is next to them
    g.perform("LEFT")                         # turn
    g.perform("LEFT")                         # move to col 0, out of range
    assert g.mech.spikes[(1, 1, 2)] > 0
    for _ in range(3):                        # 18 frames > 15-frame hold
        g.perform("WAIT")
    assert g.mech.spikes[(1, 1, 2)] == 0


def test_jump_landing_on_spikes_kills():
    g = game(("##########", "___^______", "##########"))
    g.perform("JUMP_RIGHT")
    assert g.terminal == "died:spikes"


def test_falling_onto_spikes_kills():
    g = game(("##########", "_.________", "_^________"))
    g.perform("RIGHT")
    assert g.terminal == "died:spikes"


# --- loose floors (R-C14, R-D14) -----------------------------------------

LOOSE_ROW = ("##########", "__L_______", "__________")


def test_loose_floor_falls_ten_frames_after_stepping_on():
    g = game(LOOSE_ROW, start=(1, 1, 1, +1))
    g.perform("STEP_RIGHT")                 # trigger on arrival
    g.perform("WAIT")                        # 6 frames: still there
    assert g.geom.tile((1, 1, 2)) == "L" and g.kid.posture == "standing"
    g.perform("WAIT")                        # frame 10 passes: falls
    assert g.geom.tile((1, 1, 2)) == "."
    assert pos(g) == (1, 2, 2) and g.kid.posture == "standing"
    assert g.geom.tile((1, 2, 2)) == "r"    # rubble below


def test_running_across_loose_floor_is_safe():
    g = game(LOOSE_ROW, start=(1, 1, 1, +1))
    g.perform("RIGHT")
    g.perform("RIGHT")
    for _ in range(3):
        g.perform("WAIT")
    assert pos(g) == (1, 1, 3) and g.geom.tile((1, 1, 2)) == "."


def test_falling_loose_floor_hurts_kid_below():
    # The only trigger in play is the kid himself, so start the loose floor
    # directly and stand the kid under it.
    rooms = ("##########", "___L______", "__________")
    g = game(rooms, start=(1, 2, 3, +1))
    g.mech.touch_loose((1, 1, 3))
    g.perform("WAIT")
    g.perform("WAIT")
    assert g.kid.hp == 2 and g.geom.tile((1, 2, 3)) == "r"


# --- plates, gates, exits (R-C08, R-C09, R-C17, R-C28) -------------------

GATE_ROOM = ("##########", "_u__G___Ee", "##########")
GATE_LINK = {(1, 1, 1): ((1, 1, 4),)}


def test_closed_gate_bars():
    g = game(GATE_ROOM, start=(1, 1, 3, +1), plate_links=GATE_LINK)
    assert g.perform("RIGHT")["effect"] == "bumped"


def test_gate_timing_follows_original_constants():
    g = game(GATE_ROOM, start=(1, 1, 0, +1), plate_links=GATE_LINK)
    gate = g.mech.gates[(1, 1, 4)]
    g.perform("RIGHT")                       # onto plate at frame 4
    g.perform("RIGHT")                       # leave plate
    assert gate.state == "rising"
    rising_frames = 0
    while gate.state == "rising":
        g._tick()
        rising_frames += 1
    assert gate.pos == M.GATE_MAX
    assert gate.state == "holding"
    held = 0
    while gate.state == "holding":
        g._tick()
        held += 1
    assert held == M.GATE_HOLD
    g._tick()
    assert gate.pos == M.GATE_MAX - 1        # lowers 1 per frame


def test_gate_bars_below_pass_height():
    gate = M.Gate(pos=M.GATE_BARS_BELOW - 1)
    assert gate.bars
    gate.pos = M.GATE_BARS_BELOW
    assert not gate.bars


def test_drop_plate_slams_gate():
    rooms = ("##########", "_up_G___Ee", "##########")
    links = {(1, 1, 1): ((1, 1, 4),), (1, 1, 2): ((1, 1, 4),)}
    g = game(rooms, start=(1, 1, 0, +1), plate_links=links)
    g.perform("RIGHT")
    for _ in range(8):
        g.perform("WAIT")
    assert g.mech.gates[(1, 1, 4)].pos == M.GATE_MAX
    g.perform("RIGHT")                       # onto drop plate
    g.perform("WAIT")
    assert g.mech.gates[(1, 1, 4)].pos == 0


def test_closed_exit_does_not_win_and_open_exit_does():
    rooms = ("##########", "_u__Ee____", "##########")
    links = {(1, 1, 1): ((1, 1, 4),)}
    g = game(rooms, start=(1, 1, 3, +1), plate_links=links, exits_open=False)
    g.perform("RIGHT")
    assert g.perform("UP")["effect"] == "none" and g.terminal is None
    g2 = game(rooms, start=(1, 1, 3, +1), plate_links=links, exits_open=True)
    g2.perform("RIGHT")
    g2.perform("UP")
    assert g2.terminal == "won"


def test_exit_never_closes_once_opened():
    rooms = ("##########", "_u__Ee____", "##########")
    g = game(rooms, start=(1, 1, 0, +1), plate_links={(1, 1, 1): ((1, 1, 4),)},
             exits_open=False)
    g.perform("RIGHT")
    for _ in range(40):
        g.perform("WAIT")
    assert g.mech.exits[(1, 1, 4)].open


# --- climbing, potion, clock --------------------------------------------

def test_climb_up_needs_open_space_above_and_ledge_ahead():
    rooms = ("###__#####", "___.______", "##########")
    g = game(rooms, start=(1, 1, 3, +1))
    assert g.perform("UP")["effect"] == "none"   # (0,3) is wall
    rooms = ("###.__####", "__________", "##########")
    g = game(rooms, start=(1, 1, 3, +1))
    assert g.perform("UP")["effect"] == "climbed" and pos(g) == (1, 0, 4)


def test_potion_heals_one_up_to_max():
    rooms = ("##########", "_f________", "##########")
    g = game(rooms, start=(1, 1, 1, +1))
    g.kid.hp = 1
    g.perform("DOWN")
    assert g.kid.hp == 2 and g.geom.tile((1, 1, 1)) == "_"


def test_clock_runs_out():
    g = game()
    g.frames = 60 * 60 * 12 - 3
    g.perform("WAIT")
    assert g.terminal == "time_up"


def test_every_macro_is_at_most_twelve_frames():
    g = game()
    for a in g.legal_actions():
        g2 = game()
        assert g2.perform(a)["frames"] <= 12
