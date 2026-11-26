"""Gate 1 (QA) tests for T07 (PPO stack). Needs the `train` extra (numpy)."""

from __future__ import annotations

import copy
import json

import pytest

np = pytest.importorskip("numpy")

from agents.rl.encoder import MACRO_SLOTS, N_FEATURES, Encoder  # noqa: E402
from agents.rl.policy import load_net  # noqa: E402
from agents.versus_baseline import make_baseline  # noqa: E402
from pop import arena  # noqa: E402
from pop.versus import VersusEpisode  # noqa: E402
from pop.versus_runner import VersusLimits, VersusRunner  # noqa: E402
from tools.rl import env, ppo, train  # noqa: E402

SIZES = (N_FEATURES, 64, 64, len(MACRO_SLOTS))


class Rec:
    kind, name = "scripted", "rec"

    def __init__(self):
        self.inner, self.seen = make_baseline(), []

    def reset(self, seed):
        self.inner.reset(seed)

    def decide(self, obs, legal):
        self.seen.append((copy.deepcopy(obs), legal))
        return self.inner.decide(obs, legal)


def test_parity_holds_over_200_observations_collected_across_several_seeds(tmp_path):
    """The minimal correct fix for the known T07 failure: one baseline duel ends after
    ~145 decisions since T05-fix1, so collect over several seeds and encode each
    duel with its own Encoder."""
    params = ppo.init_params(SIZES, seed=5)
    path = tmp_path / "w.json"
    net = load_net(path, ppo.export_json(params, path))
    worst, n = 0.0, 0
    for seed in range(6):
        rec = Rec()
        VersusRunner(lambda: VersusEpisode(arena.situation("A"), arena.STARTS, 0, 3600,
                                           arena.GUARD_POSTS),
                     {"A": rec, "B": make_baseline()}, copy_mode="json", threaded=False,
                     limits=VersusLimits(max_frames=3600)).run(seed)
        enc = Encoder()
        for obs, legal in rec.seen:
            x = enc.encode(obs, legal)
            want = ppo.actor_logits(params, np.array([x]))[0]
            worst = max(worst, float(np.max(np.abs(want - np.array(net.logits(x))))))
            n += 1
    assert n >= 200, n
    assert worst < 1e-9, worst


def test_gae_with_discount_and_bootstrap_matches_a_hand_computation():
    r, v = np.array([1.0, 0.0]), np.array([0.5, 0.25])
    adv, ret = ppo.gae(r, v, last_value=2.0, gamma=0.9, lam=0.5)
    d1 = 0.0 + 0.9 * 2.0 - 0.25
    d0 = 1.0 + 0.9 * 0.25 - 0.5
    assert np.allclose(adv, [d0 + 0.9 * 0.5 * d1, d1])
    assert np.allclose(ret, adv + v)


def _batch(n=32, adv=1.0, old_shift=0.0):
    rng = np.random.default_rng(0)
    x = rng.standard_normal((n, 4))
    mask = np.ones((n, 3), bool)
    mask[:, 2] = False
    return x, mask


def test_a_clipped_sample_gives_the_actor_no_gradient():
    params = ppo.init_params((4, 8, 8, 3), seed=0)
    x, mask = _batch()
    a = np.zeros(len(x), int)
    cur = ppo.logp(params, x, mask, a)
    # old logp far below the current: ratio >> 1+clip with positive advantage -> clipped
    batch = {"x": x, "mask": mask, "a": a, "logp": cur - 5.0, "adv": np.ones(len(x)),
             "ret": np.zeros(len(x))}
    before = copy.deepcopy(params["actor"])
    ppo.update(params, batch, lr=1e-2, clip=0.2, epochs=1, minibatch=64, vf=0.5, ent=0.0, seed=0)
    for (w0, b0), (w1, b1) in zip(before, params["actor"]):
        assert np.allclose(w0, w1) and np.allclose(b0, b1)


def test_a_masked_macro_keeps_probability_zero_through_training():
    params = ppo.init_params((4, 8, 8, 3), seed=0)
    x, mask = _batch()
    a = np.zeros(len(x), int)
    batch = {"x": x, "mask": mask, "a": a, "logp": ppo.logp(params, x, mask, a),
             "adv": np.ones(len(x)), "ret": np.ones(len(x))}
    for i in range(5):
        ppo.update(params, batch, lr=1e-2, clip=0.2, epochs=2, minibatch=16, vf=0.5, ent=0.05, seed=i)
    lp = ppo._masked_log_softmax(ppo.actor_logits(params, x), mask)
    assert np.exp(lp[:, 2]).max() < 1e-12
    assert np.isclose(np.exp(lp).sum(axis=1), 1.0).all()


def test_batch_advantages_are_normalised_over_the_whole_batch():
    params = ppo.init_params(SIZES, seed=1)
    eps = [env.play_episode(params, env.baseline_opponent(), env.TUNING_STARTS[0], seed=s,
                            learner_seat="A", rng_seed=s, max_frames=600) for s in (1, 2)]
    b = train._batch(eps, 0.995, 0.95)
    assert abs(float(b["adv"].mean())) < 1e-9 and abs(float(b["adv"].std()) - 1.0) < 1e-6
    assert len(b["a"]) == len(b["x"]) == len(b["mask"]) == len(b["ret"])


def test_shaping_credit_never_changes_what_the_learner_does_in_an_episode():
    """on_frame's true state feeds reward only: the same seed with shaping on and off
    must give identical features, actions and log-probs."""
    params = ppo.init_params(SIZES, seed=3)
    runs = [env.play_episode(params, env.baseline_opponent(), env.TUNING_STARTS[1], seed=7,
                             learner_seat="B", rng_seed=5, max_frames=900,
                             reward=env.RewardConfig(shaping=s)) for s in (True, False)]
    a, b = runs
    assert a["actions"] == b["actions"] and a["snapshot_sha"] == b["snapshot_sha"]
    assert np.array_equal(a["features"], b["features"]) and a["logps"] == b["logps"]


def test_env_reads_the_true_snapshot_only_inside_the_shaper():
    import inspect
    src = inspect.getsource(env)
    assert src.count(".snapshot()") == 1
    assert "snapshot()" in inspect.getsource(env._Shaper.__call__)


def test_training_is_identical_with_one_and_two_workers(tmp_path):
    def go(workers, name):
        cfg = train.TrainConfig(seed=2, total_seconds=300, episodes_per_iter=4, workers=workers,
                                max_iters=2, max_frames=240, out_dir=tmp_path / name,
                                eval_episodes=0, final_eval_seeds=0)
        return train.train(cfg)["weights_sha256"]
    assert go(1, "w1") == go(2, "w2")


def test_training_twice_with_the_same_seed_gives_the_same_weights(tmp_path):
    def go(name):
        cfg = train.TrainConfig(seed=4, total_seconds=300, episodes_per_iter=4, workers=1,
                                max_iters=2, max_frames=240, out_dir=tmp_path / name,
                                eval_episodes=0, final_eval_seeds=0)
        return train.train(cfg)["weights_sha256"]
    assert go("x") == go("y")


def test_tuning_start_code_paths_do_not_mention_heldout():
    import inspect
    for mod in (env, train, ppo):
        src = inspect.getsource(mod).lower()
        assert "heldout" not in src.replace("held-out", "") and "evaluation/" not in src
