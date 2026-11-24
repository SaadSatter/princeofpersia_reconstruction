"""Success predicates on constructed states (task T08, decision #9).

Each test builds true states by hand and feeds them to a monitor frame by
frame, so the predicate is checked without running a duel. Saad's wording is
quoted in `evaluation/monitors.py`.
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
            "guards": guards or {}, "suspicion": suspicion or {}}


def feed(mon, states):
    for i, s in enumerate(states, 1):
        mon.observe(i, s)
    return mon.result()


# --- D1 ---------------------------------------------------------------------------
def d1_states(other_room=3, took=True, downed=True, a_disguised=True):
    return [state(a=rival(1), b=rival(other_room), guards={"g": guard()}),
            state(a=rival(1, disguised=a_disguised and took), b=rival(other_room),
                  guards={"g": guard(downed=downed, uniform=not took)})]


def test_d1_success_when_guard_downed_uniform_taken_and_other_rival_away():
    res = feed(M.DisguiseMonitor(), d1_states())
    assert res["success"] is True and res["reason"] == "guard_downed_and_uniform_taken"
    assert res["metrics"]["took_guard"] == "g" and res["metrics"]["took_frame"] == 2


def test_d1_fails_when_the_guard_is_downed_but_the_uniform_is_not_taken():
    res = feed(M.DisguiseMonitor(), d1_states(took=False))
    assert res["success"] is False and res["reason"] == "no_uniform_taken"


def test_d1_fails_when_another_rival_took_the_uniform_not_the_agent():
    states = [state(guards={"g": guard()}),
              state(b=rival(3, disguised=True), guards={"g": guard(downed=True, uniform=False)})]
    assert feed(M.DisguiseMonitor(), states)["success"] is False


def test_d1_other_rival_in_the_room_at_any_frame_voids_success_by_default():
    states = d1_states()
    states.append(state(a=rival(1, disguised=True), b=rival(1, col=8),     # walks in afterwards
                        guards={"g": guard(downed=True, uniform=False)}))
    res = feed(M.DisguiseMonitor(), states)
    assert res["success"] is False and res["reason"] == "other_rival_in_room"
    assert res["metrics"]["success_if_until_success"] is True       # the alternative reading
    assert res["metrics"]["success_if_any_frame"] is False


def test_d1_until_success_reading_ignores_a_later_visit():
    states = d1_states()
    states.append(state(a=rival(1, disguised=True), b=rival(1, col=8),
                        guards={"g": guard(downed=True, uniform=False)}))
    assert feed(M.DisguiseMonitor(scope="until_success"), states)["success"] is True


def test_d1_other_rival_present_before_the_take_voids_both_readings():
    states = [state(a=rival(1), b=rival(1, col=8), guards={"g": guard()})] + d1_states()
    for scope in M.D1_SCOPES:
        assert feed(M.DisguiseMonitor(scope=scope), list(states))["success"] is False


def test_d1_rejects_an_unknown_scope():
    with pytest.raises(ValueError):
        M.DisguiseMonitor(scope="whenever")


# --- B2 ---------------------------------------------------------------------------
def b2_states(levels, targets=(), disguised=True):
    out = []
    for i, level in enumerate(levels):
        tgt = "A" if i in targets else None
        out.append(state(a=rival(1, disguised=disguised), guards={"g": guard(target=tgt)},
                         suspicion={("g", "A"): level}))
    return out


def test_b2_success_when_unnoticed_and_suspicion_stays_below_the_threshold():
    res = feed(M.BlendMonitor(), b2_states([0, 10, 49, 20]))
    assert res["success"] is True and res["metrics"]["max_suspicion"] == 49
    assert res["metrics"]["low_threshold_status"] == "pending Saad"


def test_b2_fails_when_suspicion_reaches_the_threshold():
    res = feed(M.BlendMonitor(), b2_states([0, 30, 50]))
    assert res["success"] is False and res["reason"] == "suspicion_not_low"
    assert res["metrics"]["success_if_not_noticed_only"] is True    # the looser reading


def test_b2_threshold_is_a_parameter():
    assert feed(M.BlendMonitor(low=60), b2_states([0, 50]))["success"] is True
    assert feed(M.BlendMonitor(low=20), b2_states([0, 30]))["success"] is False


def test_b2_fails_when_a_guard_targets_the_agent_even_at_low_suspicion():
    res = feed(M.BlendMonitor(), b2_states([0, 5, 5], targets={1}))
    assert res["success"] is False and res["reason"] == "noticed_by_guard"


def test_b2_full_meter_counts_as_noticed():
    res = feed(M.BlendMonitor(), b2_states([0, 100]))
    assert res["success"] is False and res["metrics"]["noticed_frame"] == 2


def test_b2_only_the_agents_meter_counts():
    states = [state(guards={"g": guard()}, suspicion={("g", "B"): 99, ("g", "A"): 1})]
    assert feed(M.BlendMonitor(), states)["success"] is True


def test_b2_do_nothing_passes_as_worded_but_not_the_active_reading():
    still = [state(a=rival(1, disguised=True), guards={"g": guard()}) for _ in range(30)]
    res = feed(M.BlendMonitor(), still)
    assert res["success"] is True and res["metrics"]["success_active"] is False
    moving = [state(a=rival(1, col=c, disguised=True), guards={"g": guard()})
              for c in range(1, 8)]
    assert feed(M.BlendMonitor(), moving)["metrics"]["success_active"] is True


def test_b2_reports_when_the_agent_gave_up_its_own_disguise():
    states = b2_states([0, 0], disguised=True) + b2_states([0], disguised=False)
    res = feed(M.BlendMonitor(), states)
    assert res["metrics"]["disguise_lost_frame"] == 3 and res["success"] is True


# --- I3 ---------------------------------------------------------------------------
def i3(frames):
    """frames: list of (rival_hp, {guard: (downed, knocked)})"""
    out = []
    for hp, gs in frames:
        out.append(state(b=rival(1, hp=hp, disguised=True),
                         guards={n: guard(downed=d, knocked=k) for n, (d, k) in gs.items()}))
    return out


def test_i3_success_when_the_disguised_rival_is_struck_and_no_real_guard():
    res = feed(M.IdentifyMonitor(), i3([(3, {"g": (False, 0)}), (2, {"g": (False, 0)})]))
    assert res["success"] is True and res["metrics"]["first_struck"] == "rival"


def test_i3_fails_when_a_real_guard_is_struck_first():
    res = feed(M.IdentifyMonitor(),
               i3([(3, {"g": (False, 0)}), (3, {"g": (True, 0)}), (2, {"g": (True, 0)})]))
    assert res["success"] is False and res["metrics"]["first_struck"] == "guard"


def test_i3_a_knocked_down_guard_counts_as_struck():
    res = feed(M.IdentifyMonitor(), i3([(3, {"g": (False, 4)}), (2, {"g": (False, 0)})]))
    assert res["success"] is False and res["reason"] == "struck_a_real_guard_first"


def test_i3_striking_nobody_is_not_identification():
    res = feed(M.IdentifyMonitor(), i3([(3, {"g": (False, 0)})] * 5))
    assert res["success"] is False and res["reason"] == "struck_nobody"


def test_i3_same_frame_strike_is_neither_success_nor_a_clean_guard_miss():
    res = feed(M.IdentifyMonitor(), i3([(3, {"g": (False, 0)}), (2, {"g": (True, 0)})]))
    assert res["success"] is False and res["metrics"]["first_struck"] == "both"


def test_i3_uses_the_rivals_starting_hearts():
    states = [state(b=rival(1, hp=2, disguised=True), guards={"g": guard()})]
    assert feed(M.IdentifyMonitor(rival_hp_start=2), states)["success"] is False
    assert feed(M.IdentifyMonitor(rival_hp_start=3), states)["success"] is True


# --- F5 ---------------------------------------------------------------------------
def test_f5_success_when_a_guard_goes_down_and_the_agent_lives():
    states = [state(guards={"g": guard()}), state(guards={"g": guard(downed=True)})]
    res = feed(M.FightMonitor(), states)
    assert res["success"] is True and res["reason"] == "won_against_guard"


def test_f5_success_when_the_rival_dies_and_the_agent_lives():
    states = [state(a=rival(1, hp=1), b=rival(1, hp=1)),
              state(a=rival(1, hp=1), b=rival(1, hp=0, posture="dead"))]
    res = feed(M.FightMonitor(), states)
    assert res["success"] is True and res["reason"] == "won_against_rival"


def test_f5_dying_together_or_first_is_not_a_win():
    both = [state(a=rival(1, hp=0, posture="dead"), b=rival(1, hp=0, posture="dead"))]
    assert feed(M.FightMonitor(), both)["success"] is False
    lost = [state(a=rival(1, hp=0, posture="dead"), guards={"g": guard(downed=True)})]
    assert feed(M.FightMonitor(), lost)["success"] is False


def test_f5_a_guard_downed_before_the_start_does_not_count():
    states = [state(guards={"g": guard(downed=True)})]
    assert feed(M.FightMonitor(downed_at_start=("g",)), states)["success"] is False
    assert feed(M.FightMonitor(), states)["success"] is True


def test_f5_win_against_restricts_the_opponent_kind():
    guard_win = [state(guards={"g": guard(downed=True)})]
    assert feed(M.FightMonitor(win_against="rival"), guard_win)["success"] is False
    rival_win = [state(b=rival(1, hp=0, posture="dead"))]
    assert feed(M.FightMonitor(win_against="guard"), rival_win)["success"] is False
    with pytest.raises(ValueError):
        M.FightMonitor(win_against="anyone")


def test_f5_retreating_without_winning_is_not_success():
    states = [state(a=rival(1, hp=1), guards={"g": guard()}) for _ in range(10)]
    assert feed(M.FightMonitor(), states)["success"] is False


# --- shared -----------------------------------------------------------------------
def test_duel_monitor_has_no_success_flag():
    res = feed(M.DuelMonitor(), [state()])
    assert res["success"] is None and res["reason"] == "outcome_only"


def test_copresence_is_reported_for_every_kind():
    mon = M.DuelMonitor()
    feed(mon, [state(), state(b=rival(1, col=9)), state(b=rival(1, col=8))])
    out = mon.result()["metrics"]
    assert out["copresent_frames"] == 2 and out["first_copresent_frame"] == 2


def test_extract_state_reads_a_real_duel_snapshot():
    ep = arena_episode()
    s = M.extract_state(ep._duel.snapshot())
    assert s["rivals"]["A"]["room"] == 1 and s["rivals"]["B"]["room"] == 3
    assert set(s["guards"]) == {"barracks", "pit_hall"}
    assert s["guards"]["barracks"]["uniform"] is True and s["suspicion"] == {}
    assert s["rivals"]["A"]["disguised"] is False
