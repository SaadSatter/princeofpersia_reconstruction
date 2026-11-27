"""T22 Gate 2 (evaluation specialist): the shipped rival behaves in the game as in evaluation.

Same encoder, cadence (6 frames), macro expansion and weights: seat B played by the shipped
PPO rival through `VersusRunner` (what the suite runner and the T09 runs use) and through the
game's seat hook (`agents.modes.step_ai_seat`, what play.py, the page and the server call) must
give the same inputs and the same final snapshot, against the same scripted seat A.
No training, no network, no held-out data.
"""

from __future__ import annotations

import pytest

from agents import modes
from agents.rl import policy
from agents.versus_baseline import make_baseline
from pop.versus import arena_episode
from pop.versus_runner import VersusLimits, VersusRunner, snapshot

SEEDS = (0, 3)
FRAMES = 720


def _runner(seed):
    runner = VersusRunner(
        lambda: arena_episode(seed),
        {"A": make_baseline(),
         "B": policy.make_rl_rival(policy.SHIPPED_WEIGHTS, policy.SHIPPED_SHA256)},
        limits=VersusLimits(max_frames=FRAMES), threaded=False)
    return runner.run(seed)


def _game(seed):
    ep = arena_episode(seed)
    ep.reset(seed)
    a = modes._rival_class()(make_baseline(), "baseline")
    b = modes.make_seat_rival("ai")
    a.reset(seed)
    b.reset(seed)
    inputs = []
    while ep.outcome()["status"] == "ongoing" and ep.outcome()["frames"] < FRAMES:
        frame = ep.outcome()["frames"]
        modes.step_ai_seat(ep, a, "A")
        act = modes.step_ai_seat(ep, b, "B")
        if act is not None:
            inputs.append((frame, act))
        ep.tick()
    return ep, inputs, b


def _game_forwarding_wait(seed):
    """The game's cadence (decide on ticks 0, 6, 12 ...), but WAIT is submitted as the input it is."""
    ep = arena_episode(seed)
    ep.reset(seed)
    ctrls = {"A": make_baseline(),
             "B": policy.make_rl_rival(policy.SHIPPED_WEIGHTS, policy.SHIPPED_SHA256)}
    for c in ctrls.values():
        c.reset(seed)
    while ep.outcome()["status"] == "ongoing" and ep.outcome()["frames"] < FRAMES:
        frame = ep.outcome()["frames"]
        if frame % 6 == 0:
            for seat, c in ctrls.items():
                ep.step(seat, c.decide(ep.observe(seat), tuple(ep.legal_actions(seat))))
        ep.tick()
    return ep


@pytest.mark.parametrize("seed", SEEDS)
def test_cause_is_wait_mapped_to_no_input(seed):
    """Root cause of EVAL-T22-1: forwarding WAIT as the runner does reproduces the runner exactly."""
    res = _runner(seed)
    assert res["final_snapshot"] == snapshot(_game_forwarding_wait(seed))


@pytest.mark.parametrize("seed", SEEDS)
def test_game_path_matches_runner_path_for_the_shipped_rival(seed):
    res = _runner(seed)
    ep, game_b, b = _game(seed)
    # WAIT is filtered from BOTH lists: the runner skips a seat with no legal action, so its trace
    # does not list every frame the game submits WAIT on; the whole final snapshot below is what
    # proves that the WAITs themselves were equal.
    runner_b = [(r["frame"], r["input"]) for r in res["traces"]["B"]
                if r["input"] not in (None, "WAIT")]
    game_acts = [(f, a) for f, a in game_b if a != "WAIT"]
    assert runner_b, "the rival never acted: the comparison would be vacuous"
    assert any(a == "WAIT" for _, a in game_b), "the game must submit WAIT (EVAL-T22-1)"
    assert runner_b == game_acts
    assert res["final_snapshot"] == snapshot(ep)
    assert b.policy_errors == 0 and b.fallback_log == []
