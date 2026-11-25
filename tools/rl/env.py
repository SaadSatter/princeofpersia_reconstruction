"""Training environment for the PPO rival (docs/final/RL_POLICY.md, task T07).

One episode = one duel run by `VersusRunner` on the trusted fast path
(`copy_mode="json"`, `threaded=False`), with fresh controllers every time. The
learner is a `MacroController` around `TrainPolicy`, which sees exactly what
the shipped rival sees (the same encoder and mask) and records its choices.

Reward: terminal +1 win, -1 loss, 0 draw. Optional shaping, each term
documented and switchable in `RewardConfig`. Shaping reads hearts and the
disguise flag from the runner's `on_frame` view (trusted, training only); the
policy never sees them.

Starts: ONLY the tuning starts below: the two docs/final/MACROS.md records, plus six
added in T07-fix1 (decision #44) that share no start with any held-out list (see
docs/final/RL_POLICY.md and tests/test_rl_fix1_starts.py). The held-out H6 starts
belong to the Evaluation Specialist (T08) and are not used here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from agents.macros import MacroController
from agents.rl.encoder import MACRO_SLOTS, Encoder, macro_mask
from agents.rl.policy import MACRO_EVERY, PolicyMacro, Net, nearest_target
from agents.versus_baseline import make_baseline
from pop import arena
from pop.versus import VersusEpisode
from pop.versus_runner import VersusLimits, VersusRunner, digest

EVERY = 6
TUNING_STARTS = [
    (arena.STARTS["A"], arena.STARTS["B"]),
    ((1, 2, 3, +1), (3, 2, 6, -1)),
    # T07-fix1 (#44). Hand-picked floor cells (row 2) in cells no held-out start uses, so that
    # three pairs reach the lower rooms 4, 5 and 6.
    ((1, 2, 8, -1), (4, 2, 4, +1)),
    ((2, 2, 6, -1), (5, 2, 4, +1)),
    ((3, 2, 1, +1), (6, 2, 6, -1)),
    ((4, 2, 9, -1), (2, 2, 1, +1)),
    ((5, 2, 5, -1), (1, 2, 9, -1)),
    ((6, 2, 3, +1), (3, 2, 0, +1)),
]
COMBOS = [(p, seat, first) for p in range(len(TUNING_STARTS)) for seat in ("A", "B")
          for first in (True, False)]          # 8 (start pair, learner seat, which start)


@dataclass(frozen=True)
class RewardConfig:
    """Shaping terms (per event); `shaping=False` leaves only the terminal reward."""
    shaping: bool = True
    heart_dealt: float = 0.1          # opponent lost a heart
    heart_taken: float = -0.1         # I lost a heart
    disguise: float = 0.05            # I became disguised (took a uniform)

    def shape(self, hearts_dealt: int, hearts_taken: int, disguise_gained: bool) -> float:
        if not self.shaping:
            return 0.0
        return (self.heart_dealt * hearts_dealt + self.heart_taken * hearts_taken
                + (self.disguise if disguise_gained else 0.0))


def terminal_reward(reason: str | None, seat: str) -> float:
    if reason and reason.startswith("won:"):
        return 1.0 if reason.endswith(seat) else -1.0
    return 0.0


# ------------------------------------------------------------------ opponents
def baseline_opponent() -> dict:
    return {"kind": "baseline"}


def snapshot_opponent(net_dict: dict) -> dict:
    return {"kind": "snapshot", "net": net_dict}


def net_from_arrays(layers, sizes) -> Net:
    return Net(sizes, [(w.tolist(), b.tolist()) for w, b in layers])


def make_opponent(opp: dict):
    if opp["kind"] == "baseline":
        return make_baseline("baseline")
    net = Net(opp["net"]["sizes"], [(l["w"], l["b"]) for l in opp["net"]["layers"]])
    ctrl = MacroController(PolicyMacro(net), name="ppo-snapshot", kind="policy",
                           decision_every=EVERY, macro_every=1)
    return ctrl


# -------------------------------------------------------------------- learner
class TrainPolicy:
    """Macro policy that samples (or takes the argmax) from the numpy actor and
    records one transition per choice. Same cadence rules as `PolicyMacro`."""

    def __init__(self, params, rng_seed: int, greedy: bool = False,
                 macro_every: int = MACRO_EVERY) -> None:
        from tools.rl import ppo
        self.ppo, self.params, self.greedy = ppo, params, greedy
        self.rng = np.random.default_rng(rng_seed)
        self.macro_every = macro_every
        self.encoder = Encoder(EVERY)
        self.steps: list[dict] = []
        self.errors = 0                      # T07-E4: counted, logged, and fatal for a real run
        self.pending = 0.0
        self._since = 0

    def reset(self, seed: int) -> None:
        self.encoder.reset()
        self.steps, self.pending, self._since = [], 0.0, 0   # `errors` is kept across a reset

    def credit(self, r: float) -> None:
        self.pending += r

    def choose(self, obs, legal, status):
        try:
            return self._choose(obs, legal, status)
        except Exception:                     # keep the episode alive, but never hide it
            self.errors += 1
            return "WAIT"

    def _choose(self, obs, legal, status):
        self.encoder.update(obs)
        target = nearest_target(obs)
        self._since += 1
        if (status["state"] == "running" and status["macro"] in MACRO_SLOTS
                and self._since < self.macro_every):
            return status["macro"], {"suspects": target}
        x = np.array(self.encoder.features(obs, legal, status))
        mask = np.array(macro_mask(obs, legal))
        z = self.ppo.actor_logits(self.params, x[None])
        lp = self.ppo._masked_log_softmax(z, mask[None])[0]
        if self.greedy:
            a = int(np.argmax(np.where(mask, z[0], -np.inf)))
        else:
            p = np.exp(lp) * mask
            a = int(self.rng.choice(len(p), p=p / p.sum()))
        v = float(self.ppo.critic_value(self.params, x[None])[0])
        if self.steps:
            self.steps[-1]["r"] += self.pending
        self.pending = 0.0
        self.steps.append({"x": x, "mask": mask, "a": a, "logp": float(lp[a]), "v": v, "r": 0.0})
        self._since = 0
        return MACRO_SLOTS[a], {"suspects": target}


class _Shaper:
    """on_frame hook: turns hearts and disguise changes into shaping credit."""

    def __init__(self, seat, other, policy, reward) -> None:
        self.seat, self.other, self.policy, self.reward = seat, other, policy, reward
        self.hp = None
        self.disguised = False

    def __call__(self, frame, view) -> None:
        if not self.reward.shaping or frame % EVERY:
            return
        snap = view.snapshot()
        me = snap["rivals"][self.seat]["kid"]["hp"]
        opp = snap["rivals"][self.other]["kid"]["hp"]
        dis = bool(snap["disguised"][self.seat])
        if self.hp is not None:
            self.policy.credit(self.reward.shape(max(0, self.hp[1] - opp), max(0, self.hp[0] - me),
                                                 dis and not self.disguised))
        self.hp, self.disguised = (me, opp), dis


def play_episode(params, opponent: dict, starts, seed: int, learner_seat: str, rng_seed: int,
                 max_frames: int | None = None, learner_first: bool = True,
                 reward: RewardConfig = RewardConfig(), greedy: bool = False,
                 time_limit: int = 3600) -> dict:
    a, b = starts
    mine, theirs = (a, b) if learner_first else (b, a)
    other = "B" if learner_seat == "A" else "A"
    place = {learner_seat: mine, other: theirs}
    factory = lambda: VersusEpisode(arena.situation("A"), place, 0, time_limit, arena.GUARD_POSTS)
    pol = TrainPolicy(params, rng_seed, greedy)
    learner = MacroController(pol, name="ppo-train", kind="policy", decision_every=EVERY,
                              macro_every=1)
    opp_ctrl = make_opponent(opponent)
    ctrls = {learner_seat: learner, other: opp_ctrl}
    runner = VersusRunner(factory, ctrls, decision_every=EVERY, copy_mode="json", threaded=False,
                          limits=VersusLimits(max_frames=max_frames),
                          on_frame=_Shaper(learner_seat, other, pol, reward),
                          clock=lambda: 0.0)
    res = runner.run(seed)
    # Learner errors, plus errors inside a snapshot opponent (its PolicyMacro swallows them).
    policy_errors = pol.errors + getattr(getattr(opp_ctrl, "policy", None), "errors", 0)
    reason = res["outcome"]["reason"]
    term = terminal_reward(reason, learner_seat)
    steps = pol.steps
    if steps:
        steps[-1]["r"] += pol.pending + term
    n = len(steps)
    from agents.rl.encoder import N_FEATURES
    return {"features": (np.array([s["x"] for s in steps]) if n else np.zeros((0, N_FEATURES))),
            "masks": (np.array([s["mask"] for s in steps], bool) if n
                      else np.zeros((0, len(MACRO_SLOTS)), bool)),
            "actions": [s["a"] for s in steps], "logps": [s["logp"] for s in steps],
            "values": [s["v"] for s in steps], "rewards": [s["r"] for s in steps],
            "outcome": reason, "status": res["status"], "terminal": term, "frames": res["frames"],
            "snapshot_sha": res["final_snapshot_sha256"], "learner_seat": learner_seat,
            "fallbacks": res["seats"][learner_seat]["fallbacks"], "policy_errors": policy_errors,
            "opponent": opponent["kind"]}
