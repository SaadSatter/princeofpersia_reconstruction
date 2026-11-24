"""Environment, reward and trainer (T07). Everything here is offline and short."""

from __future__ import annotations

import json
import time

import numpy as np

from agents.rl.encoder import MACRO_SLOTS, N_FEATURES
from agents.rl.policy import file_sha256, load_net
from tools.rl import env, ppo, train

SIZES = (N_FEATURES, 64, 64, len(MACRO_SLOTS))


def test_tuning_starts_are_only_the_two_midterm_tuning_starts():
    assert len(env.TUNING_STARTS) == 2
    assert all(a[0] != b[0] for a, b in env.TUNING_STARTS)        # different rooms


def test_rollout_is_deterministic_for_a_seed():
    params = ppo.init_params(SIZES, seed=1)
    runs = [env.play_episode(params, env.baseline_opponent(), env.TUNING_STARTS[0],
                             seed=4, learner_seat="A", rng_seed=11, max_frames=720)
            for _ in range(2)]
    a, b = runs
    assert a["snapshot_sha"] == b["snapshot_sha"]
    assert a["actions"] == b["actions"] and a["rewards"] == b["rewards"]
    assert np.array_equal(a["features"], b["features"])
    assert len(a["actions"]) > 5 and a["features"].shape[1] == N_FEATURES


def test_terminal_reward_is_win_loss_draw_and_shaping_is_switchable():
    assert env.terminal_reward("won:A", "A") == 1.0
    assert env.terminal_reward("won:B", "A") == -1.0
    assert env.terminal_reward("draw:time_up", "A") == 0.0
    off = env.RewardConfig(shaping=False)
    on = env.RewardConfig(shaping=True)
    assert off.shape(hearts_dealt=1, hearts_taken=1, disguise_gained=True) == 0.0
    assert on.shape(hearts_dealt=1, hearts_taken=0, disguise_gained=False) > 0
    assert on.shape(hearts_dealt=0, hearts_taken=1, disguise_gained=False) < 0
    assert on.shape(hearts_dealt=0, hearts_taken=0, disguise_gained=True) > 0


def test_shaping_is_small_next_to_the_terminal_reward():
    on = env.RewardConfig(shaping=True)
    assert on.shape(2, 0, True) < 0.5


def test_gae_matches_a_hand_computation():
    r = np.array([0.0, 0.0, 1.0]); v = np.array([0.5, 0.4, 0.3])
    adv, ret = ppo.gae(r, v, last_value=0.0, gamma=1.0, lam=1.0)
    assert np.allclose(adv, [1 - 0.5, 1 - 0.4, 1 - 0.3])
    assert np.allclose(ret, adv + v)


def test_ppo_update_moves_probability_toward_a_rewarded_action():
    params = ppo.init_params((4, 8, 8, 3), seed=0)
    x = np.ones((64, 4)); mask = np.ones((64, 3), bool)
    acts = np.zeros(64, int); adv = np.ones(64); ret = np.ones(64)
    logp0 = ppo.logp(params, x, mask, acts)
    for _ in range(30):
        ppo.update(params, dict(x=x, mask=mask, a=acts, logp=logp0, adv=adv, ret=ret),
                   lr=3e-3, clip=0.2, epochs=1, minibatch=64, vf=0.5, ent=0.0, seed=0)
    assert ppo.logp(params, x, mask, acts).mean() > logp0.mean() + 0.05


def test_smoke_training_runs_logs_exports_and_loads_back(tmp_path):
    cfg = train.TrainConfig(seed=0, total_seconds=40, episodes_per_iter=4, workers=1,
                            max_iters=2, max_frames=900, out_dir=tmp_path, hidden=(16, 16),
                            eval_episodes=2, snapshot_every=1)
    t0 = time.time()
    summary = train.train(cfg)
    assert time.time() - t0 < 60
    log = [json.loads(l) for l in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert len(log) == 2
    for row in log:
        assert {"update", "steps", "episodes", "mean_return", "win_rate_vs_baseline_tuning",
                "elapsed_s", "opponent_mix"} <= set(row)
    w = tmp_path / "weights.json"
    assert summary["weights_sha256"] == file_sha256(w)
    net = load_net(w, summary["weights_sha256"])
    assert net.sizes[0] == N_FEATURES and net.sizes[-1] == len(MACRO_SLOTS)
    assert summary["stopped"] in ("max_iters", "time_cap")
    assert summary["checkpoint_chosen_by_score"] is False


def test_training_is_reproducible_with_a_fixed_seed(tmp_path):
    def go(sub):
        cfg = train.TrainConfig(seed=3, total_seconds=40, episodes_per_iter=2, workers=1,
                                max_iters=1, max_frames=600, out_dir=tmp_path / sub,
                                hidden=(8, 8), eval_episodes=0, snapshot_every=1)
        return train.train(cfg)["weights_sha256"]
    assert go("a") == go("b")
