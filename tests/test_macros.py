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
        key = None if m is None else m["effect"]
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
