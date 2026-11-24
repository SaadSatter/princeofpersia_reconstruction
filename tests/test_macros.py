"""Macro layer (agents/macros.py; docs/final/MACROS.md, task T05).

Deterministic, offline. The executor turns one macro into per-decision inputs
from one seat's observation and legal list only.
"""

from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from agents.macros import MACROS, RESERVED, MacroController, MacroExecutor
from pop import arena
from pop.versus import VersusEpisode, arena_episode

ROOT = Path(__file__).resolve().parent.parent
EVERY = 6


def episode(a=None, b=None, posts=None, seed=0, limit=3600) -> VersusEpisode:
    starts = dict(arena.STARTS)
    if a:
        starts["A"] = a
    if b:
        starts["B"] = b
    return VersusEpisode(arena.situation("A"), starts, seed, limit, posts or {})


class Fixed:
    """A macro policy that asks for one macro, always."""

    def __init__(self, macro, params=None):
        self.macro, self.params = macro, params or {}

    def reset(self, seed):
        pass

    def choose(self, obs, legal, status):
        return (self.macro, self.params)


def drive(ep, seat, ctrl, frames):
    """Tick `frames` frames, deciding every EVERY frames for `seat` only."""
    seen = []
    for f in range(frames):
        if f % EVERY == 0:
            legal = tuple(ep.legal_actions(seat))
            if legal:
                ep.step(seat, ctrl.decide(copy.deepcopy(ep.observe(seat)), legal))
        ep.tick()
        seen.append(ep.observe(seat)["me"]["motion"])
    return seen


def test_vocabulary_is_the_g1_set_plus_search():
    assert set(MACROS) >= {"BLEND", "DISGUISE", "WAIT", "FOLLOW", "STRIKE", "FLEE", "CLIMB"}
    assert "SEARCH" in MACROS                      # proposed addition: travel between rooms
    assert RESERVED == ("RIG_TRAP",) and "RIG_TRAP" not in MACROS


def test_reserved_macro_is_reported_failed_not_played():
    ex = MacroExecutor(EVERY)
    ex.begin("RIG_TRAP")
    obs = episode().observe("A")
    assert ex.step(obs, tuple(episode().legal_actions("A"))) == "WAIT"
    assert (ex.state, ex.reason) == ("failed", "reserved")


def test_unknown_macro_is_reported_failed():
    ex = MacroExecutor(EVERY)
    ex.begin("DANCE")
    ep = episode()
    ex.step(ep.observe("A"), tuple(ep.legal_actions("A")))
    assert (ex.state, ex.reason) == ("failed", "unknown_macro")


def test_failed_macro_is_reported_once_and_not_looped():
    ep = episode()
    ctrl = MacroController(Fixed("DISGUISE"), decision_every=EVERY)
    inputs = [ctrl.decide(ep.observe("A"), tuple(ep.legal_actions("A"))) for _ in range(5)]
    assert set(inputs) <= set(ep.legal_actions("A"))
    failed = [e for e in ctrl.events if e["event"] == "macro_failed"]
    assert len(failed) == 1 and failed[0]["macro"] == "DISGUISE"
    assert failed[0]["reason"] == "no_target"
    # Every later decision keeps the failed state; the executor is not re-run.
    assert [row["state"] for row in ctrl.log][1:] == ["failed"] * 4


def test_strike_without_a_target_fails_no_target():
    ex = MacroExecutor(EVERY)
    ex.begin("STRIKE")
    ep = episode()
    ex.step(ep.observe("A"), tuple(ep.legal_actions("A")))
    assert (ex.state, ex.reason) == ("failed", "no_target")


def test_executor_input_is_always_legal_over_a_whole_duel_for_every_macro():
    for macro in MACROS:
        ep = arena_episode(2)
        ctrl = MacroController(Fixed(macro), decision_every=EVERY)
        for f in range(0, 600, EVERY):
            legal = tuple(ep.legal_actions("A"))
            if not legal:
                break
            action = ctrl.decide(copy.deepcopy(ep.observe("A")), legal)
            assert action in legal, (macro, f, action)
            ep.step("A", action)
            for _ in range(EVERY):
                ep.tick()


def test_executor_is_deterministic():
    def play():
        ep = arena_episode(5)
        ctrl = MacroController(Fixed("SEARCH"), decision_every=EVERY)
        out = []
        for f in range(0, 300, EVERY):
            action = ctrl.decide(copy.deepcopy(ep.observe("A")), tuple(ep.legal_actions("A")))
            out.append(action)
            ep.step("A", action)
            for _ in range(EVERY):
                ep.tick()
        return out, ctrl.log
    assert play() == play()


def test_disguise_macro_takes_the_nearest_visible_downed_guard():
    ep = episode(posts={"g": (1, 2, (5, 5), +1)})
    ep._duel.guards["g"].knock_out()                 # test setup: a body to take
    ctrl = MacroController(Fixed("DISGUISE"), decision_every=EVERY)
    drive(ep, "A", ctrl, 240)
    assert ep.observe("A")["me"]["disguised"] is True
    assert ctrl.executor.state == "done"


def test_disguise_target_is_chosen_by_observed_attributes_not_kind():
    """A downed figure is picked by posture; its `kind` label is never read."""
    ep = episode(posts={"g": (1, 2, (5, 5), +1)})
    ep._duel.guards["g"].knock_out()
    obs = ep.observe("A")
    relabelled = copy.deepcopy(obs)
    for fig in relabelled["figures"]:
        fig["kind"] = "rival"
    legal = tuple(ep.legal_actions("A"))
    a, b = MacroExecutor(EVERY), MacroExecutor(EVERY)
    a.begin("DISGUISE")
    b.begin("DISGUISE")
    assert a.step(obs, legal) == b.step(relabelled, legal)


def test_no_new_code_reads_figure_ids_or_imports_engine_internals():
    banned = {"pop.versus", "pop.arena", "pop.guards", "pop.situations", "pop.engine"}
    for rel in ("agents/macros.py", "agents/versus_baseline.py"):
        tree = ast.parse((ROOT / rel).read_text())
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
                mods += [f"{node.module}.{a.name}" for a in node.names]
            assert not banned & set(mods), (rel, mods)


def _runs(motions):
    """Run-length list of (effect, length) with None for no motion."""
    out = []
    for m in motions:
        # Another seat sees only guard-like motions; any other move reads as standing still.
        key = None if m is None or m["effect"] == "waited" else m["effect"]
        if out and out[-1][0] == key and not (m and m["frame"] == 1 and key):
            out[-1][1] += 1
        else:
            out.append([key, 1])
    return out


def test_blend_has_no_idle_gap_between_steps_and_matches_a_guard_patrol_shape():
    start = (1, 2, 1, +1)
    far = (3, 2, 7, -1)
    # The blending rival walks room 1's bottom floor; a real guard walks the same stretch.
    blender = episode(a=start, b=far)
    ctrl = MacroController(Fixed("BLEND"), decision_every=EVERY)
    mine = drive(blender, "A", ctrl, 240)
    guard_ep = episode(a=(1, 0, 7, -1), b=far, posts={"g": (1, 2, (1, 6), +1)})
    theirs = []
    for _ in range(240):
        guard_ep.tick()
        fig = guard_ep.observe("A")["figures"]
        theirs.append(fig[0]["motion"] if fig else None)

    def steps_and_gaps(seq):
        runs = _runs(seq)
        moved = [i for i, (e, _) in enumerate(runs) if e == "moved"]
        gaps = [runs[i][1] for i in range(1, len(runs) - 1)
                if runs[i][0] is None and runs[i - 1][0] == "moved" and runs[i + 1][0] == "moved"]
        return runs, moved, gaps
    my_runs, my_moved, my_gaps = steps_and_gaps(mine)
    assert my_moved, "blend never walked"
    assert my_gaps == [], f"idle gap between two steps: {my_runs}"
    # Both show: walk, pause 10-14 frames with no motion, a turn of 4 frames, walk back.
    for runs in (my_runs, steps_and_gaps(theirs)[0]):
        effects = [e for e, _ in runs]
        assert "turned" in effects
        i = effects.index("turned")
        assert effects[i - 1] is None and 10 <= runs[i - 1][1] <= 14, runs


def test_executor_queues_the_next_primitive_from_the_end_of_the_current_move():
    ep = episode(a=(1, 2, 1, +1))
    ex = MacroExecutor(EVERY)
    ex.begin("SEARCH")
    legal = tuple(ep.legal_actions("A"))
    ep.step("A", ex.step(ep.observe("A"), legal))
    for _ in range(EVERY):
        ep.tick()
    obs = ep.observe("A")
    assert obs["me"]["motion"] is not None          # still moving when the next decision is due
    nxt = ex.step(obs, tuple(ep.legal_actions("A")))
    assert nxt in ep.legal_actions("A") and nxt != "WAIT"


# --- T05-fix1: vertical movement (CLIMB both ways, SEARCH, FLEE, DISGUISE) -----------------
import dataclasses                                    # noqa: E402

from pop import observation                           # noqa: E402

ROOM = {n: observation.room_label("ARENA", n) for n in range(1, 7)}


def _room_of(ep, seat="A") -> int:
    return ep._duel.rivals[seat].kid.room


def _hp(ep, seat="A") -> int:
    return ep._duel.rivals[seat].kid.hp


def drive_one(ep, seat, ctrl, frames):
    """Decide every EVERY frames until the first macro event (done or failed), then stop
    ticking, so the asserts see the state the macro ended in, not a later macro's."""
    for f in range(frames):
        if f % EVERY == 0:
            legal = tuple(ep.legal_actions(seat))
            if not legal:
                break
            ep.step(seat, ctrl.decide(copy.deepcopy(ep.observe(seat)), legal))
            if ctrl.events:
                break
        ep.tick()
    return ctrl.events[0] if ctrl.events else None


def _custom(rooms, links, a, b, posts=None):
    sit = dataclasses.replace(arena.situation("A"), rooms=rooms, links=links,
                              plate_links={}, gates_open=())
    return VersusEpisode(sit, {"A": a, "B": b}, 0, 3600, posts or {})


def test_climb_down_drops_one_row_inside_the_room():
    ep = episode(a=(1, 0, 6, +1))                    # row 0, pit at col 8 over the middle floor
    ctrl = MacroController(Fixed("CLIMB", {"direction": "down"}), decision_every=EVERY)
    ev = drive_one(ep, "A", ctrl, 400)
    for _ in range(30):                              # let the fall finish
        ep.tick()
    assert ev["event"] == "macro_done" and ev["reason"] == "dropped"
    assert (_room_of(ep), ep._duel.rivals["A"].kid.row) == (1, 1) and _hp(ep) == 3


def test_climb_down_leaves_the_room_through_a_pit_in_the_bottom_row():
    ep = episode(a=(1, 2, 5, +1))                    # shaft at col 7 down to the Barracks
    ctrl = MacroController(Fixed("CLIMB", {"direction": "down"}), decision_every=EVERY)
    ev = drive_one(ep, "A", ctrl, 400)
    assert ev["event"] == "macro_done" and ev["reason"] == "new_room"
    assert _room_of(ep) == 4 and _hp(ep) == 3


def test_climb_up_leaves_the_room_through_a_shaft_found_by_trying_columns():
    ep = episode(a=(5, 0, 5, +1))                    # the shaft up to the East Tower is at col 2
    ctrl = MacroController(Fixed("CLIMB", {"direction": "up"}), decision_every=EVERY)
    ev = drive_one(ep, "A", ctrl, 1500)
    assert ev["event"] == "macro_done" and ev["reason"] == "new_room"
    assert _room_of(ep) == 3


def test_a_hang_and_drop_saves_the_heart_of_a_two_row_fall():
    rooms = {1: ("#____.____", "#____.____", "#_________"), 2: ("__________",) * 3}
    links = {1: (0, 2, 0, 0), 2: (1, 0, 0, 0)}
    ep = _custom(rooms, links, (1, 0, 3, +1), (2, 2, 5, -1))
    ctrl = MacroController(Fixed("CLIMB", {"direction": "down"}), decision_every=EVERY)
    ev = drive_one(ep, "A", ctrl, 500)
    assert ev["event"] == "macro_done" and ev["reason"] == "dropped"
    assert ep._duel.rivals["A"].kid.row == 2 and _hp(ep) == 3      # a walk-off would cost one


def test_search_visits_every_reachable_room_including_the_lower_floor():
    ep = episode(b=(3, 2, 8, -1))
    ctrl = MacroController(Fixed("SEARCH"), decision_every=EVERY)
    seen = set()
    for f in range(3600):
        if f % EVERY == 0:
            legal = tuple(ep.legal_actions("A"))
            if not legal:
                break
            ep.step("A", ctrl.decide(copy.deepcopy(ep.observe("A")), legal))
        ep.tick()
        seen.add(_room_of(ep))
    assert seen == set(range(1, 7)), seen


def test_flee_leaves_by_a_pit_when_both_sides_are_walls():
    rooms = {1: ("#________#", "#________#", "#____.___#"), 2: ("__________",) * 3}
    links = {1: (0, 0, 0, 2), 2: (0, 0, 1, 0)}
    ep = _custom(rooms, links, (1, 2, 3, +1), (2, 2, 5, -1), {"g": (1, 2, (7, 8), -1)})
    ep._duel.guards["g"].sword = "drawn"             # test setup: an armed guard in the room
    ctrl = MacroController(Fixed("FLEE"), decision_every=EVERY)
    ev = drive_one(ep, "A", ctrl, 500)
    assert ev["event"] == "macro_done" and ev["reason"] == "left_room"
    assert _room_of(ep) == 2


def test_disguise_reports_no_uniform_from_the_take_result_and_remembers_the_cell():
    ep = episode(posts={"g": (1, 2, (5, 5), +1)})
    g = ep._duel.guards["g"]
    g.knock_out()
    g.uniform = False                                # stripped already (R-V26)
    ctrl = MacroController(Fixed("DISGUISE"), decision_every=EVERY)
    inputs = []
    for f in range(240):
        if f % EVERY == 0:
            legal = tuple(ep.legal_actions("A"))
            a = ctrl.decide(copy.deepcopy(ep.observe("A")), legal)
            inputs.append(a)
            ep.step("A", a)
        ep.tick()
    fails = [e for e in ctrl.events if e["event"] == "macro_failed"]
    assert fails and fails[0]["reason"] == "no_uniform"
    assert inputs.count("TAKE") == 1                 # one try, not a retry loop
    assert ctrl.executor.tried
