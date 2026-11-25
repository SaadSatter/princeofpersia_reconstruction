"""T08-fix1: the monitor changes. QA F-1 (D1 attribution), decision #76 (B2 and the
disguise), decision #66 (`success_active` is reported, never scored), and monitors
for a subject in seat B (decision #65).
"""

from __future__ import annotations

from evaluation import monitors as M


def rival(room=1, col=2, hp=3, posture="standing", disguised=False, row=2):
    return {"room": room, "row": row, "col": col, "hp": hp, "posture": posture,
            "disguised": disguised}


def guard(room=1, col=5, downed=False, uniform=True, knocked=0, target=None):
    return {"room": room, "row": 2, "col": col, "downed": downed, "uniform": uniform,
            "knocked_down": knocked, "target": target}


def state(a, b, guards, suspicion=None):
    return {"frames": 0, "terminal": None, "rivals": {"A": a, "B": b}, "guards": guards,
            "suspicion": suspicion or {}}


def feed(mon, states):
    for i, s in enumerate(states, 1):
        mon.observe(i, s)
    return mon.result()


# --- D1 (QA F-1) ----------------------------------------------------------------------------
def test_d1_credits_a_guard_downed_while_the_agent_was_in_its_room():
    res = feed(M.DisguiseMonitor(), [
        state(rival(4), rival(2), {"g": guard(4)}),
        state(rival(4), rival(2), {"g": guard(4, downed=True)}),
        state(rival(4, disguised=True), rival(2), {"g": guard(4, downed=True, uniform=False)})])
    assert res["success"] is True and res["metrics"]["took_guard"] == "g"


def test_d1_credits_a_guard_the_agent_struck_before_leaving_the_room():
    """Struck = the agent was in the guard's room when the guard first went down or was
    knocked down. Here the agent knocks it down, and the guard is downed after the agent
    stepped out and came back; the knock-down frame had the agent in the room."""
    res = feed(M.DisguiseMonitor(), [
        state(rival(4), rival(2), {"g": guard(4)}),
        state(rival(4), rival(2), {"g": guard(4, knocked=1)}),       # the agent's strike
        state(rival(3), rival(2), {"g": guard(4, downed=True)}),     # downed after it left
        state(rival(4), rival(2), {"g": guard(4, downed=True)}),
        state(rival(4, disguised=True), rival(2), {"g": guard(4, downed=True, uniform=False)})])
    assert res["success"] is True


def test_d1_does_not_credit_a_guard_downed_with_the_agent_in_another_room():
    res = feed(M.DisguiseMonitor(), [
        state(rival(3), rival(4), {"g": guard(4)}),
        state(rival(3), rival(4), {"g": guard(4, downed=True)}),     # the other rival downs it
        state(rival(4, disguised=True), rival(5), {"g": guard(4, downed=True, uniform=False)})])
    assert res["success"] is False
    assert res["reason"] == "no_uniform_taken"
    assert res["metrics"]["credited_guards"] == []


def test_d1_one_credited_guard_is_enough_when_two_guards_are_downed():
    res = feed(M.DisguiseMonitor(), [
        state(rival(4), rival(2), {"g1": guard(4), "g2": guard(5)}),
        state(rival(4), rival(2), {"g1": guard(4, downed=True), "g2": guard(5, downed=True)}),
        state(rival(4, disguised=True), rival(2),
              {"g1": guard(4, downed=True, uniform=False), "g2": guard(5, downed=True)})])
    assert res["success"] is True and res["metrics"]["took_guard"] == "g1"
    assert res["metrics"]["credited_guards"] == ["g1"]


def test_d1_a_subject_in_seat_b_is_credited_by_its_own_room():
    res = feed(M.DisguiseMonitor("B"), [
        state(rival(2), rival(4), {"g": guard(4)}),
        state(rival(2), rival(4), {"g": guard(4, downed=True)}),
        state(rival(2), rival(4, disguised=True), {"g": guard(4, downed=True, uniform=False)})])
    assert res["success"] is True
    other = feed(M.DisguiseMonitor("B"), [
        state(rival(4), rival(3), {"g": guard(4)}),                  # seat A in the guard's room
        state(rival(4), rival(3), {"g": guard(4, downed=True)}),
        state(rival(4), rival(4, disguised=True), {"g": guard(4, downed=True, uniform=False)})])
    assert other["success"] is False                                 # A was in the room with B at the end


# --- B2 (decision #76) ------------------------------------------------------------------------
def b2_states(final_disguised=True, level=10, lost_midway=False):
    out = [state(rival(1, disguised=True), rival(3), {"g": guard(1)}, {("g", "A"): level})]
    if lost_midway:
        out.append(state(rival(1, disguised=False), rival(3), {"g": guard(1)}, {("g", "A"): level}))
    out.append(state(rival(1, disguised=final_disguised), rival(3), {"g": guard(1)},
                     {("g", "A"): level}))
    return out


def test_b2_succeeds_when_unnoticed_low_and_still_disguised_at_the_end():
    res = feed(M.BlendMonitor(), b2_states())
    assert res["success"] is True and res["reason"] == "unnoticed_and_low"
    assert res["metrics"]["subject_disguised_end"] is True


def test_b2_fails_when_the_disguise_is_gone_at_the_end_even_if_nobody_noticed():
    res = feed(M.BlendMonitor(), b2_states(final_disguised=False))
    assert res["success"] is False and res["reason"] == "disguise_lost"
    assert res["metrics"]["disguise_lost_frame"] == 2


def test_b2_still_passes_if_the_disguise_was_lost_midway_but_is_worn_again_at_the_end():
    """#76 says the rival must be *still disguised at the end*. A mid-way loss is recorded
    (`disguise_lost_frame`) but the end state decides."""
    res = feed(M.BlendMonitor(), b2_states(lost_midway=True))
    assert res["success"] is True and res["metrics"]["disguise_lost_frame"] == 2


def test_b2_a_noticing_guard_is_reported_before_the_disguise():
    res = feed(M.BlendMonitor(), [
        state(rival(1, disguised=True), rival(3), {"g": guard(1, target="A")}),
        state(rival(1, disguised=False), rival(3), {"g": guard(1, target="A")})])
    assert res["success"] is False and res["reason"] == "noticed_by_guard"


def test_b2_threshold_stays_a_named_parameter_of_50():
    assert M.B2_LOW_THRESHOLD == 50
    assert feed(M.BlendMonitor(), b2_states(level=49))["success"] is True
    assert feed(M.BlendMonitor(), b2_states(level=50))["success"] is False
    assert feed(M.BlendMonitor(low=60), b2_states(level=55))["success"] is True


def test_b2_success_active_is_reported_but_never_scored():
    still = feed(M.BlendMonitor(), b2_states())
    assert still["success"] is True and still["metrics"]["success_active"] is False
    walker = M.BlendMonitor()
    walk = [state(rival(1, col=c, disguised=True), rival(3), {"g": guard(1)}) for c in range(1, 9)]
    res = feed(walker, walk)
    assert res["success"] is True and res["metrics"]["success_active"] is True
    # losing the disguise turns both off: success_active needs the success
    lost = [state(rival(1, col=c, disguised=c < 8), rival(3), {"g": guard(1)}) for c in range(1, 9)]
    res = feed(M.BlendMonitor(), lost)
    assert res["success"] is False and res["metrics"]["success_active"] is False


def test_b2_reads_the_subjects_suspicion_for_a_subject_in_seat_b():
    s = [state(rival(3), rival(1, disguised=True), {"g": guard(1)},
               {("g", "B"): 20, ("g", "A"): 99})]
    assert feed(M.BlendMonitor("B"), s)["success"] is True


# --- I3 and F5 for a subject in seat B ------------------------------------------------------------
def test_i3_for_a_subject_in_seat_b_reads_seat_a_as_the_rival():
    mon = M.IdentifyMonitor("B", rival_hp_start=3)
    res = feed(mon, [state(rival(1, hp=3, disguised=True), rival(1), {"g": guard(1)}),
                     state(rival(1, hp=2, disguised=True), rival(1), {"g": guard(1)})])
    assert res["success"] is True and res["reason"] == "struck_the_disguised_rival_first"


def test_f5_for_a_subject_in_seat_b_needs_seat_b_alive():
    win = feed(M.FightMonitor("B"), [state(rival(1), rival(4), {"g": guard(4)}),
                                     state(rival(1), rival(4), {"g": guard(4, downed=True)})])
    assert win["success"] is True
    dead = feed(M.FightMonitor("B"), [state(rival(1), rival(4, posture="dead"),
                                            {"g": guard(4, downed=True)})])
    assert dead["success"] is False
