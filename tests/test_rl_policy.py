"""Pure-Python inference, weight hash and the PolicyMacro adapter (T07)."""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from agents.rl import encoder as enc_mod
from agents.rl import policy as pol
from agents.rl.encoder import MACRO_SLOTS, N_FEATURES, Encoder, macro_mask
from agents.rl.policy import WeightsError, file_sha256, load_net, make_rl_rival
from agents.versus_baseline import make_baseline
from pop import arena
from pop.seats import WaitController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner
from tools.rl import ppo

SIZES = (N_FEATURES, 64, 64, len(MACRO_SLOTS))


class Recorder:
    kind, name = "scripted", "recorder"

    def __init__(self, inner):
        self.inner, self.seen = inner, []

    def reset(self, seed):
        self.inner.reset(seed)
        self.seen = []

    def decide(self, obs, legal):
        self.seen.append((obs, legal))
        return self.inner.decide(obs, legal)


def _record_duels(seeds=range(6)):
    """One list of (obs, legal) per duel. A baseline duel now ends after about 145
    decisions (T05-fix1 ended the mirror deadlock), so 200 observations need several
    seeds; each duel is encoded with its own Encoder (T07-QA-1, decision #42)."""
    duels = []
    for seed in seeds:
        rec = Recorder(make_baseline())
        ep = lambda: VersusEpisode(arena.situation("A"), arena.STARTS, 0, 3600, arena.GUARD_POSTS)
        VersusRunner(ep, {"A": rec, "B": make_baseline()}, copy_mode="json", threaded=False,
                     limits=VersusLimits(max_frames=3600)).run(seed)
        duels.append([(copy.deepcopy(o), l) for o, l in rec.seen])
    return duels


def _record(n=200):
    seen = [x for duel in _record_duels() for x in duel]
    assert len(seen) >= n
    return seen[:n]


@pytest.fixture()
def weights(tmp_path):
    params = ppo.init_params(SIZES, seed=5)
    path = tmp_path / "w.json"
    sha = ppo.export_json(params, path)
    return params, path, sha


def test_pure_python_logits_equal_the_numpy_forward_pass_on_200_observations(weights):
    params, path, sha = weights
    net = load_net(path, sha)
    worst, n = 0.0, 0
    for duel in _record_duels():
        enc = Encoder()                          # fresh history for each duel
        for obs, legal in duel:
            x = enc.encode(obs, legal)
            want = ppo.actor_logits(params, np.array([x]))[0]
            got = net.logits(x)
            worst = max(worst, float(np.max(np.abs(want - np.array(got)))))
            n += 1
    assert n >= 200, n
    assert worst < 1e-9, worst


def test_masked_argmax_never_picks_a_masked_macro(weights):
    _, path, sha = weights
    net = load_net(path, sha)
    enc = Encoder()
    for obs, legal in _record(60):
        mask = macro_mask(obs, legal)
        a = net.act(enc.encode(obs, legal), mask)
        assert mask[a] and MACRO_SLOTS[a] != "RIG_TRAP"


def test_weight_hash_is_checked_at_load(weights, tmp_path):
    _, path, sha = weights
    load_net(path, sha)
    with pytest.raises(WeightsError):
        load_net(path, "0" * 64)
    data = json.loads(path.read_text())
    data["layers"][0]["b"][0] += 1e-6
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(data))
    with pytest.raises(WeightsError):
        load_net(bad, sha)
    assert file_sha256(bad) != sha


def test_a_missing_hash_is_refused_not_skipped(weights):
    _, path, _ = weights
    with pytest.raises(WeightsError):
        load_net(path, None)


def test_weights_file_is_plain_json_lists_of_numbers(weights):
    _, path, _ = weights
    data = json.loads(path.read_text())
    assert data["sizes"] == list(SIZES) and data["macros"] == list(MACRO_SLOTS)
    for layer in data["layers"]:
        assert all(isinstance(r, list) and all(type(v) is float for v in r) for r in layer["w"])
        assert all(type(v) is float for v in layer["b"])


def test_inference_modules_are_stdlib_only():
    for mod in (pol, enc_mod):
        tree = ast.parse(Path(mod.__file__).read_text())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
                 for a in n.names} | {(n.module or "").split(".")[0] for n in ast.walk(tree)
                                       if isinstance(n, ast.ImportFrom)}
        assert not (names & {"numpy", "pygame", "anthropic", "torch"}), names


def test_rl_rival_is_a_labelled_policy_controller_and_is_deterministic(weights):
    _, path, sha = weights

    def go():
        rival = make_rl_rival(path, sha)
        assert rival.kind == "policy" and rival.name.startswith("ppo")
        res = VersusRunner(lambda: VersusEpisode(arena.situation("A"), arena.STARTS, 0, 3600,
                                                 arena.GUARD_POSTS),
                           {"A": rival, "B": WaitController()}, copy_mode="json",
                           threaded=False, limits=VersusLimits(max_frames=900)).run(1)
        return res["final_snapshot_sha256"], res["seats"]["A"]["fallbacks"], rival.log
    a, b = go(), go()
    assert a == b and a[1] == 0 and a[2]


def test_an_inference_error_becomes_a_wait_macro_not_a_crash(weights):
    _, path, sha = weights
    pm = pol.PolicyMacro(load_net(path, sha))
    pm.reset(0)
    assert pm.choose({"bad": 1}, ("WAIT",), {"macro": None, "state": "idle", "reason": None}) == "WAIT"
    assert pm.errors == 1
