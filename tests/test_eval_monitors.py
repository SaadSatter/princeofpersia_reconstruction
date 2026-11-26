"""T08: success predicates on constructed states (decisions #9, #58, #59).

Each test builds true states by hand and feeds them to a monitor frame by
frame, so a predicate is checked without running a duel. Saad's words, quoted
by decision #9 and fixed by #58 (B2 "low" = below 50 of 100) and #59 (D1 "on
screen" = the other rival is in the agent's room at no frame of the scenario):

  D1  "Success if the agent kills a guard and picks up the disguise when no
       other player is on screen."
  B2  "Blend if another guard doesn't notice it or keeps low suspicion."
  I3  "Identify if the agent can distinguish between player guard and real
       guard."
  F5  "Fight or retreat if it wins a duel against a player or guard."
"""

from __future__ import annotations

import pytest

from evaluation import monitors as M
from pop.versus import arena_episode


def rival(room=1, col=2, hp=3, posture="standing", disguised=False, row=2):
    return {"room": room, "row": row, "col": col, "hp": hp, "posture": posture,
            "disguised": disguised}


def guard(room=1, col=5, downed=False, uniform=True, knocked=0, target=None):
    return {"room": room, "row": 2, "col": col, "downed": downed, "uniform": uniform,
            "knocked_down": knocked, "target": target}


def state(a=None, b=None, guards=None, suspicion=None, frames=0):
    return {"frames": frames, "terminal": None,
            "rivals": {"A": a or rival(1), "B": b or rival(3)},
            "guards": guards if guards is not None else {}, "suspicion": suspicion or {}}


def feed(mon, states):
    for i, s in enumerate(states, 1):
        mon.observe(i, s)
    return mon.result()


# --- D1 ------------------------------------------------------------------------------
def d1_states(other_room=3, took=True, downed=True):
    return [state(a=rival(1), b=rival(other_room), guards={"g": guard()}),
            state(a=rival(1, disguised=took), b=rival(other_room),
                  guards={"g": guard(downed=downed, uniform=not took)})]


def test_d1_succeeds_when_a_guard_is_downed_the_uniform_is_taken_and_the_other_rival_is_away():
    res = feed(M.DisguiseMonitor(), d1_states())
    assert res["success"] is True and res["reason"] == "guard_downed_and_uniform_taken"
    assert res["metrics"]["took_guard"] == "g" and res["metrics"]["took_frame"] == 2


def test_d1_fails_when_the_guard_is_downed_but_the_uniform_is_not_taken():
    res = feed(M.DisguiseMonitor(), d1_states(took=False))
    assert res["success"] is False and res["reason"] == "no_uniform_taken"


def test_d1_fails_when_the_other_rival_took_the_uniform_not_the_agent():
    states = [state(guards={"g": guard()}),
              state(b=rival(3, disguised=True), guards={"g": guard(downed=True, uniform=False)})]
    assert feed(M.DisguiseMonitor(), states)["success"] is False


def test_d1_fails_when_the_uniform_is_taken_from_a_guard_that_was_not_downed():
    states = [state(guards={"g": guard()}),
              state(a=rival(1, disguised=True), guards={"g": guard(downed=False, uniform=False)})]
    assert feed(M.DisguiseMonitor(), states)["success"] is False


def test_d1_other_rival_in_the_agents_room_at_any_frame_voids_success():
    """#59: 'never in the agent's room at any frame', so a visit after the take counts."""
    states = d1_states()
    states.append(state(a=rival(1, disguised=True), b=rival(1, col=8),
                        guards={"g": guard(downed=True, uniform=False)}))
    res = feed(M.DisguiseMonitor(), states)
    assert res["success"] is False and res["reason"] == "other_rival_in_room"
    assert res["metrics"]["copresent_frames"] == 1


def test_d1_other_rival_present_before_the_take_voids_success():
    states = [state(a=rival(1), b=rival(1, col=8), guards={"g": guard()})] + d1_states()
    assert feed(M.DisguiseMonitor(), states)["success"] is False


def test_d1_other_rival_in_a_neighbouring_room_does_not_void_success():
    assert feed(M.DisguiseMonitor(), d1_states(other_room=2))["success"] is True


# --- B2 ------------------------------------------------------------------------------
def b2_states(levels, target_at=None):
    out = []
    for i, level in enumerate(levels, 1):
        out.append(state(a=rival(1, disguised=True), guards={"g": guard(
            target="A" if target_at == i else None)}, suspicion={("g", "A"): level}))
    return out


def test_b2_threshold_is_50_of_100_a_named_parameter():
    assert M.B2_LOW_THRESHOLD == 50 and M.SUSPICION_MAX == 100
    assert M.BlendMonitor().low == 50


def test_b2_succeeds_while_suspicion_stays_below_50():
    res = feed(M.BlendMonitor(), b2_states([0, 20, 49, 10]))
    assert res["success"] is True and res["reason"] == "unnoticed_and_low"
    assert res["metrics"]["max_suspicion"] == 49


def test_b2_fails_at_exactly_50():
    res = feed(M.BlendMonitor(), b2_states([0, 50]))
    assert res["success"] is False and res["reason"] == "suspicion_not_low"


def test_b2_fails_when_a_guard_notices_the_agent():
    res = feed(M.BlendMonitor(), b2_states([0, 10, 10], target_at=2))
    assert res["success"] is False and res["reason"] == "noticed_by_guard"


def test_b2_fails_when_suspicion_fills_to_100():
    res = feed(M.BlendMonitor(), b2_states([0, 100]))
    assert res["success"] is False and res["metrics"]["noticed_frame"] == 2


def test_b2_ignores_the_other_rivals_suspicion_meter():
    states = [state(a=rival(1, disguised=True), suspicion={("g", "B"): 99})]
    assert feed(M.BlendMonitor(), states)["success"] is True


def test_b2_threshold_can_be_overridden_by_name_for_a_sensitivity_check():
    res = feed(M.BlendMonitor(low=20), b2_states([0, 30]))
    assert res["success"] is False and res["metrics"]["low_threshold"] == 20


def test_b2_standing_still_passes_so_the_row_also_reports_activity():
    """A seat that never moves is never noticed: the extra reading `success_active` says so."""
    res = feed(M.BlendMonitor(min_cells=3), b2_states([0, 0, 0]))
    assert res["success"] is True and res["metrics"]["success_active"] is False
    moving = [state(a=rival(1, col=c, disguised=True)) for c in (1, 2, 3, 4)]
    assert feed(M.BlendMonitor(min_cells=3), moving)["metrics"]["success_active"] is True


# --- I3 ------------------------------------------------------------------------------
def i3_state(rival_hp=3, guard_downed=False, guard_knocked=0):
    return state(a=rival(1), b=rival(1, col=7, hp=rival_hp, disguised=True),
                 guards={"g": guard(col=3, downed=guard_downed, knocked=guard_knocked)})


def test_i3_succeeds_when_the_first_strike_lands_on_the_disguised_rival():
    res = feed(M.IdentifyMonitor(), [i3_state(), i3_state(rival_hp=2)])
    assert res["success"] is True and res["metrics"]["first_struck"] == "rival"


def test_i3_fails_when_a_real_guard_is_struck_first():
    res = feed(M.IdentifyMonitor(), [i3_state(), i3_state(guard_knocked=8), i3_state(rival_hp=2)])
    assert res["success"] is False and res["metrics"]["first_struck"] == "guard"


def test_i3_a_downed_guard_counts_as_a_strike_on_a_guard():
    res = feed(M.IdentifyMonitor(), [i3_state(), i3_state(guard_downed=True)])
    assert res["success"] is False and res["reason"] == "struck_a_real_guard_first"


def test_i3_fails_when_nobody_is_struck():
    res = feed(M.IdentifyMonitor(), [i3_state(), i3_state()])
    assert res["success"] is False and res["reason"] == "struck_nobody"


def test_i3_a_strike_on_both_in_one_frame_is_not_a_success():
    res = feed(M.IdentifyMonitor(), [i3_state(), i3_state(rival_hp=2, guard_knocked=8)])
    assert res["success"] is False and res["metrics"]["first_struck"] == "both"


def test_i3_counts_hearts_from_the_start_value_given():
    res = feed(M.IdentifyMonitor(rival_hp_start=2), [i3_state(rival_hp=2), i3_state(rival_hp=1)])
    assert res["success"] is True


# --- F5 ------------------------------------------------------------------------------
def test_f5_guard_win_counts_when_the_agent_is_alive():
    res = feed(M.FightMonitor(), [state(guards={"g": guard()}),
                                  state(guards={"g": guard(downed=True)})])
    assert res["success"] is True and res["reason"] == "won_against_guard"


def test_f5_rival_win_counts_when_the_other_rival_dies_and_the_agent_lives():
    res = feed(M.FightMonitor(), [state(), state(b=rival(3, hp=0, posture="dead"))])
    assert res["success"] is True and res["reason"] == "won_against_rival"


def test_f5_no_win_when_the_agent_is_dead_even_if_the_guard_is_down():
    res = feed(M.FightMonitor(), [state(guards={"g": guard()}),
                                  state(a=rival(1, hp=0, posture="dead"),
                                        guards={"g": guard(downed=True)})])
    assert res["success"] is False and res["reason"] == "no_duel_won"


def test_f5_nothing_happens_is_a_failure():
    assert feed(M.FightMonitor(), [state(), state()])["success"] is False


def test_f5_win_against_restricts_which_win_counts():
    states = [state(guards={"g": guard()}), state(guards={"g": guard(downed=True)})]
    assert feed(M.FightMonitor(win_against="rival"), states)["success"] is False
    with pytest.raises(ValueError):
        M.FightMonitor(win_against="nobody")


# --- H6 and the true-state extractor ------------------------------------------------
def test_duel_monitor_has_no_success_flag_only_the_outcome_counts():
    res = feed(M.DuelMonitor(), [state(), state()])
    assert res["success"] is None and res["reason"] == "outcome_only"


def test_every_scenario_kind_has_a_monitor():
    assert set(M.MONITORS) == {"disguise", "blend", "identify", "fight", "duel"}


def test_extract_state_reads_a_real_snapshot_and_hides_nothing_it_needs():
    ep = arena_episode()
    snap = ep._duel.snapshot()
    st = M.extract_state(snap)
    assert set(st["rivals"]) == {"A", "B"} and st["rivals"]["A"]["room"] == 1
    assert st["rivals"]["A"]["hp"] == 3 and st["rivals"]["B"]["disguised"] is False
    assert set(st["guards"]) == {"barracks", "pit_hall"}
    assert st["guards"]["barracks"]["downed"] is False
