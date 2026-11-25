"""Gate 2 (Evaluation Specialist) probes for T07: held-out separation, target rule,
shaping size, last-weights export, local latency. No training run is started."""

from __future__ import annotations

import ast
import re
import statistics
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RL_FILES = sorted((ROOT / "tools" / "rl").glob("*.py")) + sorted((ROOT / "agents" / "rl").glob("*.py"))


def test_training_code_cannot_reach_the_heldout_set():
    assert RL_FILES
    for f in RL_FILES:
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            assert not any(m.split(".")[0] == "evaluation" for m in mods), (f, mods)
        code = re.sub(r'""".*?"""', "", f.read_text(), flags=re.S)       # docstrings may say "held-out"
        code = "\n".join(ln.split("#")[0] for ln in code.splitlines())
        assert not re.search(r"heldout|held_out|evaluation/|H6", code), f


def test_training_starts_are_exactly_the_two_tuning_starts_and_all_combos_use_only_them():
    from tools.rl import env
    assert len(env.TUNING_STARTS) == 2
    assert {c[0] for c in env.COMBOS} == {0, 1} and len(env.COMBOS) == 8


def test_heldout_starts_if_present_are_disjoint_from_tuning_starts():
    from tools.rl import env
    held = ROOT / "evaluation" / "heldout"
    if not held.exists():
        pytest.skip("evaluation/heldout does not exist on this line (T08 not built)")
    text = "".join(p.read_text() for p in held.rglob("*") if p.is_file())
    for pair in env.TUNING_STARTS:
        for start in pair:
            assert str(tuple(start)) not in text


def test_trainer_exports_the_last_weights_once_and_never_selects_by_score():
    src = (ROOT / "tools" / "rl" / "train.py").read_text()
    assert src.count("export_json(") == 1
    assert src.index("export_json(") > src.index("finally:")          # after the loop, not inside it
    assert '"checkpoint_chosen_by_score": False' in src


def _fig(row, col, kind="guard", posture="standing"):
    return {"kind": kind, "row": row, "col": col, "facing": "left", "posture": posture,
            "stance": None, "armed": False, "motion": None}


def test_nearest_target_rule_makes_a_nearer_guard_the_target_over_a_farther_rival():
    """Characterisation of the documented limit (RL_POLICY.md 'Actions'): the policy
    cannot choose a farther figure, so in I3 a nearer real guard hides a farther
    disguised rival from STRIKE and FOLLOW."""
    from agents.rl.policy import nearest_target
    obs = {"me": {"row": 1, "col": 4}, "figures": [_fig(1, 9), _fig(1, 6), _fig(0, 3)]}
    assert nearest_target(obs) == [(1, 6)]
    obs["figures"].append(_fig(1, 5, posture="downed"))                  # a body is never the target
    assert nearest_target(obs) == [(1, 6)]
    tie = {"me": {"row": 1, "col": 4}, "figures": [_fig(1, 6), _fig(1, 2)]}
    assert nearest_target(tie) == [(1, 2)]                               # equal distance: lower column
    assert nearest_target({"me": {"row": 1, "col": 4}, "figures": []}) == []


def test_shaping_is_small_against_the_terminal_reward_and_hearts_only_move_it():
    pytest.importorskip("numpy")
    from agents.rl.encoder import MACRO_SLOTS, N_FEATURES
    from tools.rl import env, ppo
    p = ppo.init_params((N_FEATURES, 64, 64, len(MACRO_SLOTS)), 0)
    for i in range(6):
        pair, seat, first = env.COMBOS[i]
        e = env.play_episode(p, env.baseline_opponent(), env.TUNING_STARTS[pair], 50 + i, seat, i,
                             learner_first=first)
        shaping = sum(e["rewards"]) - e["terminal"]
        assert abs(shaping) <= 0.5 < abs(e["terminal"]) or e["terminal"] == 0
        assert e["fallbacks"] == 0


def test_the_pure_python_rival_decides_well_inside_one_runner_cadence_on_this_machine(tmp_path):
    pytest.importorskip("numpy")
    from agents.rl import policy as pol
    from agents.rl.encoder import MACRO_SLOTS, N_FEATURES
    from agents.versus_baseline import make_baseline
    from pop import arena
    from pop.versus import VersusEpisode
    from pop.versus_runner import VersusRunner
    from tools.rl import ppo
    path = tmp_path / "w.json"
    sha = ppo.export_json(ppo.init_params((N_FEATURES, 64, 64, len(MACRO_SLOTS)), 0), path)
    lat, orig = [], pol.PolicyMacro.choose

    def timed(self, obs, legal, status):
        t = time.perf_counter()
        try:
            return orig(self, obs, legal, status)
        finally:
            lat.append(time.perf_counter() - t)
    pol.PolicyMacro.choose = timed
    try:
        rival = pol.make_rl_rival(path, sha)
        VersusRunner(lambda: VersusEpisode(arena.situation("A"), dict(arena.STARTS), 0, 3600, arena.GUARD_POSTS),
                     {"A": rival, "B": make_baseline()}, copy_mode="json", threaded=False,
                     clock=lambda: 0.0).run(0)
    finally:
        pol.PolicyMacro.choose = orig
    assert len(lat) > 50
    assert statistics.mean(lat) < 0.01 and max(lat) < 0.1      # a 6-frame cadence is 100 ms at 60 fps
