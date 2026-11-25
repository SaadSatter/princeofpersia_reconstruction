"""T19 Gate 2: seat-swapped comparison on the TUNING starts only (never held-out).

Run from a project root (the post-T19 tree or an extracted pre-T19 tree):
    PYTHONPATH=. python evaluation/t19_compare.py ppo|mirror|ppo_rand|base_rand SEEDS [vary]  > out.json
Conditions: `ppo` = shipped PPO rival vs scripted baseline, learner seat and start
order swapped over all 32 tuning combos; `mirror` = baseline vs baseline on the same
combos (a control: whether the seat that holds the first start wins).
Every episode is reported, including draws and fallbacks. Not a strength claim.
"""
from __future__ import annotations

import json
import sys
import time

from agents.rl.policy import SHIPPED_SHA256, SHIPPED_WEIGHTS, make_rl_rival
from agents.versus_baseline import make_baseline
from pop import arena
from pop.seats import RandomController
from pop.versus import VersusEpisode
from pop.versus_runner import VersusRunner
from tools.rl import env


VARY = len(sys.argv) > 3 and sys.argv[3] == "vary"   # engine seed = s (default 0, as in training)


def run(kind: str, seeds: int) -> dict:
    rows = []
    for i, (p, seat, first) in enumerate(env.COMBOS):
        a, b = env.TUNING_STARTS[p]
        mine, theirs = (a, b) if first else (b, a)
        other = "B" if seat == "A" else "A"
        place = {seat: mine, other: theirs}
        for s in range(seeds):
            me = make_rl_rival(SHIPPED_WEIGHTS, SHIPPED_SHA256) if kind.startswith("ppo") else make_baseline()
            res = VersusRunner(lambda: VersusEpisode(arena.situation("A"), place, s if VARY else 0, 3600,
                                                     arena.GUARD_POSTS),
                               {seat: me, other: (RandomController() if kind.endswith("rand") else make_baseline())}, copy_mode="json",
                               threaded=False, clock=lambda: 0.0).run(10_000 + s)
            reason = res["outcome"]["reason"]
            rows.append({"combo": i, "seat": seat, "seed": s, "reason": reason,
                         "r": env.terminal_reward(reason, seat),
                         "aborted": res["status"].startswith("aborted"),
                         "frames": res["frames"],
                         "fallbacks": sum(res["seats"][x]["fallbacks"] for x in "AB"),
                         "sha": res["final_snapshot_sha256"][:12]})
    out = {"kind": kind, "episodes": len(rows),
           "fallbacks": sum(r["fallbacks"] for r in rows),
           "mean_frames": round(sum(r["frames"] for r in rows) / len(rows), 1),
           "distinct_final_states": len({r["sha"] for r in rows}),
           "sha_first_seed": [r["sha"] for r in rows if r["seed"] == 0],
           "wins": sum(r["r"] > 0 for r in rows), "draws": sum(r["r"] == 0 for r in rows),
           "losses": sum(r["r"] < 0 for r in rows),
           "aborted": sum(r["aborted"] for r in rows), "reasons": {}}
    for r in rows:
        out["reasons"][r["reason"]] = out["reasons"].get(r["reason"], 0) + 1
    out["by_seat_wdl"] = {sd: [sum(r["r"] > 0 for r in rows if r["seat"] == sd),
                               sum(r["r"] == 0 for r in rows if r["seat"] == sd),
                               sum(r["r"] < 0 for r in rows if r["seat"] == sd)] for sd in "AB"}
    return out


if __name__ == "__main__":
    t = time.time()
    res = run(sys.argv[1], int(sys.argv[2]))
    res["wall_s"] = round(time.time() - t, 1)
    print(json.dumps(res))
