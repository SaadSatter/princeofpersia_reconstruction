"""PPO trainer for the Shadow Masque rival (docs/final/RL_POLICY.md, task T07).

    python -m tools.rl.train --out tools/rl/logs/run-0 --seed 0 --seconds 5100

Opponents per episode: the scripted baseline, or an earlier snapshot of the
learner (a 50/50 mix once a snapshot exists). The learner's seat, start pair
and which start it takes cycle every episode. Only the tuning starts are used.
Every update is logged to `<out>/log.jsonl`. Training stops at the time cap or
`max_iters`; the final weights are exported as they are (no checkpoint is
picked by score). Rollouts run on 1..N forked worker processes.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from agents.rl.encoder import MACRO_SLOTS, N_FEATURES
from agents.rl.policy import file_sha256, load_net, make_rl_rival
from tools.rl import env, ppo


@dataclass
class TrainConfig:
    seed: int = 0
    total_seconds: float = 5100.0          # 85 min; the course cap is 90
    episodes_per_iter: int = 16
    workers: int = 2
    max_iters: int | None = None
    max_frames: int | None = None          # None: full 5-minute duels
    out_dir: Path | str = "tools/rl/logs/run-0"
    hidden: tuple = (64, 64)
    gamma: float = 0.995
    lam: float = 0.95
    lr: float = 5e-4
    clip: float = 0.2
    epochs: int = 4
    minibatch: int = 256
    vf: float = 0.5
    ent: float = 0.01
    snapshot_every: int = 5                # updates between snapshots added to the pool
    snapshot_pool: int = 6
    snapshot_prob: float = 0.5
    eval_episodes: int = 8                 # greedy episodes vs the baseline per update
    final_eval_seeds: int = 4              # seeds per combo for the pure-Python final check
    shaping: bool = True


def _run(task):
    return env.play_episode(**task)


def _combo(i):
    p, seat, first = env.COMBOS[i % len(env.COMBOS)]
    return env.TUNING_STARTS[p], seat, first


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _batch(episodes, gamma, lam):
    xs, ms, acts, lps, advs, rets = [], [], [], [], [], []
    for ep in episodes:
        if not ep["actions"]:
            continue
        adv, ret = ppo.gae(np.array(ep["rewards"]), np.array(ep["values"]), 0.0, gamma, lam)
        xs.append(ep["features"]); ms.append(ep["masks"]); acts += ep["actions"]
        lps += ep["logps"]; advs.append(adv); rets.append(ret)
    adv = np.concatenate(advs)
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    return {"x": np.concatenate(xs), "mask": np.concatenate(ms), "a": np.array(acts),
            "logp": np.array(lps), "adv": adv, "ret": np.concatenate(rets)}


def final_check(path, sha, seeds: int) -> dict:
    """The exported weights, loaded through the pure-Python path, against the
    baseline on the tuning starts (every combo, `seeds` seeds each)."""
    from pop.versus import VersusEpisode
    from pop.versus_runner import VersusRunner
    from agents.versus_baseline import make_baseline
    from pop import arena
    w = d = l = 0
    for i in range(len(env.COMBOS)):
        (starts, seat, first) = _combo(i)
        for s in range(seeds):
            a, b = starts
            mine, theirs = (a, b) if first else (b, a)
            other = "B" if seat == "A" else "A"
            place = {seat: mine, other: theirs}
            rival = make_rl_rival(path, sha)
            res = VersusRunner(lambda: VersusEpisode(arena.situation("A"), place, 0, 3600,
                                                     arena.GUARD_POSTS),
                               {seat: rival, other: make_baseline()}, copy_mode="json",
                               threaded=False, clock=lambda: 0.0).run(10_000 + s)
            r = env.terminal_reward(res["outcome"]["reason"], seat)
            w += r > 0; l += r < 0; d += r == 0
    n = w + d + l
    return {"episodes": n, "wins": int(w), "draws": int(d), "losses": int(l),
            "win_rate": w / n if n else None}


def train(cfg: TrainConfig) -> dict:
    out = Path(cfg.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(asdict(cfg), default=str, indent=1))
    sizes = (N_FEATURES,) + tuple(cfg.hidden) + (len(MACRO_SLOTS),)
    params = ppo.init_params(sizes, cfg.seed)
    reward = env.RewardConfig(shaping=cfg.shaping)
    rng = np.random.default_rng(cfg.seed)
    pool: list[dict] = []
    ctx = mp.get_context("fork")
    pw = ctx.Pool(cfg.workers) if cfg.workers > 1 else None
    mapper = (lambda tasks: pw.map(_run, tasks, chunksize=1)) if pw else (lambda t: [_run(x) for x in t])
    t0 = time.time()
    steps = episodes = update = 0
    log_f = (out / "log.jsonl").open("w")
    stopped = "time_cap"
    try:
        while True:
            if cfg.max_iters is not None and update >= cfg.max_iters:
                stopped = "max_iters"
                break
            if time.time() - t0 >= cfg.total_seconds:
                break
            tasks, mix = [], {"baseline": 0, "snapshot": 0}
            for k in range(cfg.episodes_per_iter):
                i = episodes + k
                starts, seat, first = _combo(i)
                use_snap = bool(pool) and rng.random() < cfg.snapshot_prob
                opp = env.snapshot_opponent(pool[int(rng.integers(len(pool)))]) if use_snap \
                    else env.baseline_opponent()
                mix[opp["kind"]] += 1
                tasks.append(dict(params=params, opponent=opp, starts=starts, seed=cfg.seed * 100003 + i,
                                  learner_seat=seat, rng_seed=cfg.seed * 7919 + i,
                                  max_frames=cfg.max_frames, learner_first=first, reward=reward))
            eps = mapper(tasks)
            episodes += len(eps)
            steps += sum(len(e["actions"]) for e in eps)
            batch = _batch(eps, cfg.gamma, cfg.lam)
            stats = ppo.update(params, batch, cfg.lr, cfg.clip, cfg.epochs, cfg.minibatch,
                               cfg.vf, cfg.ent, seed=cfg.seed * 31 + update)
            update += 1
            returns = [sum(e["rewards"]) for e in eps]
            vs_base = [e for e in eps if e["opponent"] == "baseline"]
            train_wr = (sum(e["terminal"] > 0 for e in vs_base) / len(vs_base)) if vs_base else None
            ev = None
            if cfg.eval_episodes:
                etasks = []
                for k in range(cfg.eval_episodes):
                    starts, seat, first = _combo(k)
                    etasks.append(dict(params=params, opponent=env.baseline_opponent(),
                                       starts=starts, seed=900_000 + k // len(env.COMBOS),
                                       learner_seat=seat, rng_seed=0, max_frames=cfg.max_frames,
                                       learner_first=first, reward=env.RewardConfig(shaping=False),
                                       greedy=True))
                evs = mapper(etasks)
                ev = {"wins": sum(e["terminal"] > 0 for e in evs),
                      "draws": sum(e["terminal"] == 0 for e in evs),
                      "losses": sum(e["terminal"] < 0 for e in evs), "n": len(evs)}
            row = {"update": update, "steps": steps, "episodes": episodes,
                   "mean_return": float(np.mean(returns)),
                   "mean_terminal": float(np.mean([e["terminal"] for e in eps])),
                   "train_win_rate_vs_baseline": train_wr,
                   "win_rate_vs_baseline_tuning": None if ev is None else ev["wins"] / ev["n"],
                   "eval_vs_baseline_tuning": ev, "opponent_mix": mix,
                   "fallbacks": int(sum(e["fallbacks"] for e in eps)),
                   "elapsed_s": round(time.time() - t0, 1), **{k: round(v, 5) for k, v in stats.items()}}
            log_f.write(json.dumps(row) + "\n"); log_f.flush()
            if update % cfg.snapshot_every == 0:
                pool.append(ppo.actor_dict(params))
                pool = pool[-cfg.snapshot_pool:]
    finally:
        log_f.close()
        if pw:
            pw.close(); pw.join()
    sha = ppo.export_json(params, out / "weights.json")
    final = final_check(out / "weights.json", sha, cfg.final_eval_seeds) if cfg.final_eval_seeds else None
    summary = {"commit": _git_head(), "seed": cfg.seed, "updates": update, "episodes": episodes,
               "steps": steps, "wall_seconds": round(time.time() - t0, 1), "stopped": stopped,
               "weights_sha256": sha, "checkpoint_chosen_by_score": False,
               "final_check_vs_baseline_tuning_pure_python": final}
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="tools/rl/logs/run-0")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--seconds", type=float, default=5100.0)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--no-shaping", action="store_true")
    a = ap.parse_args()
    print(json.dumps(train(TrainConfig(seed=a.seed, total_seconds=a.seconds, workers=a.workers,
                                       out_dir=a.out, shaping=not a.no_shaping)), indent=1))


if __name__ == "__main__":
    main()
