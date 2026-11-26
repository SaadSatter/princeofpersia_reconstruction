"""Pure-Python inference for the PPO rival (docs/final/RL_POLICY.md, task T07).

Standard library only: it must load inside the browser build. The weights are
a plain JSON file of lists of floats; its SHA-256 is checked at load
(`load_net(path, sha256)`; the expected value is recorded in RL_POLICY.md and
there is no way to load without one). `PolicyMacro` is the macro policy that
plugs into `agents.macros.MacroController`; `make_rl_rival` builds the seat
controller, labelled `policy`.

The rival sees one seat's observation and legal tuple, as every controller
does. It picks a macro about every `MACRO_EVERY` runner decisions (2 s at the
6-frame cadence) and at once when the last macro is no longer running. The
macro's target is the nearest figure that is not downed (a fixed rule on
observed positions; the learned part is when to strike, follow or flee).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from agents.macros import MacroController
from agents.rl.encoder import MACRO_SLOTS, N_FEATURES, Encoder, macro_mask

MACRO_EVERY = 4
FORMAT = "sm-ppo-mlp-1"
NEG = -1e9

# The weights shipped with the game (PPO run 1, decision #51; docs/final/RL_POLICY.md).
SHIPPED_WEIGHTS = Path(__file__).resolve().parent / "weights" / "ppo-run-1.json"
SHIPPED_SHA256 = "80e4a1100fddbdbbb8a4504fc8f7a2aa1b6d8a28bb4b053519634d742b5aba4c"


class WeightsError(ValueError):
    """The weights file is missing its hash, fails it, or does not fit this encoder."""


def file_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Net:
    """tanh MLP actor. `layers[i] = (w, b)` with w as rows of inputs."""

    def __init__(self, sizes, layers) -> None:
        self.sizes = tuple(sizes)
        self.layers = [([list(r) for r in w], list(b)) for w, b in layers]

    def logits(self, x) -> list[float]:
        h = list(x)
        last = len(self.layers) - 1
        for i, (w, b) in enumerate(self.layers):
            out = list(b)
            for xi, row in zip(h, w):
                if xi != 0.0:
                    for j, wj in enumerate(row):
                        out[j] += xi * wj
            h = out if i == last else [math.tanh(v) for v in out]
        return h

    def act(self, x, mask) -> int:
        """Argmax over the allowed macros (lowest index wins a tie)."""
        z = self.logits(x)
        best, best_v = -1, None
        for i, ok in enumerate(mask):
            if ok and (best_v is None or z[i] > best_v):
                best, best_v = i, z[i]
        return best if best >= 0 else MACRO_SLOTS.index("WAIT")


def load_net(path, sha256: str | None) -> Net:
    if not sha256:
        raise WeightsError("an expected SHA-256 is required to load weights")
    got = file_sha256(path)
    if got != str(sha256).lower():
        raise WeightsError(f"weights hash mismatch: file {got}, expected {sha256}")
    data = json.loads(Path(path).read_text())
    if data.get("format") != FORMAT:
        raise WeightsError("unknown weights format")
    sizes = data["sizes"]
    if sizes[0] != N_FEATURES or sizes[-1] != len(MACRO_SLOTS) or data["macros"] != list(MACRO_SLOTS):
        raise WeightsError("weights do not fit this encoder or macro vocabulary")
    layers = [(l["w"], l["b"]) for l in data["layers"]]
    for (w, b), n_in, n_out in zip(layers, sizes, sizes[1:]):
        if len(w) != n_in or any(len(r) != n_out for r in w) or len(b) != n_out:
            raise WeightsError("layer shape does not match sizes")
    return Net(sizes, layers)


class PolicyMacro:
    """Macro policy for MacroController: `choose(obs, legal, status)`."""

    def __init__(self, net: Net, macro_every: int = MACRO_EVERY, decision_every: int = 6) -> None:
        self.net, self.macro_every = net, macro_every
        self.encoder = Encoder(decision_every)
        self.errors = 0
        self.picks: list[dict] = []
        self._since = 0

    def reset(self, seed: int) -> None:
        self.encoder.reset()
        self.errors, self.picks, self._since = 0, [], 0

    def choose(self, obs: dict, legal: tuple, status: dict):
        try:
            self.encoder.update(obs)
            target = nearest_target(obs)
            self._since += 1
            if (status["state"] == "running" and status["macro"] in MACRO_SLOTS
                    and self._since < self.macro_every):
                return status["macro"], {"suspects": target}
            x = self.encoder.features(obs, legal, status)
            a = self.net.act(x, macro_mask(obs, legal))
            self._since = 0
            self.picks.append({"macro": MACRO_SLOTS[a]})
            return MACRO_SLOTS[a], {"suspects": target}
        except Exception:                      # a controller error must not stop the seat
            self.errors += 1
            return "WAIT"


def nearest_target(obs: dict) -> list:
    """The nearest figure that is not downed or dead, as a one-cell suspect list."""
    me = obs["me"]
    live = [f for f in obs["figures"] if f["posture"] not in ("downed", "dead")]
    if not live:
        return []
    f = min(live, key=lambda f: (abs(f["row"] - me["row"]) * 4 + abs(f["col"] - me["col"]),
                                 f["row"], f["col"], f["kind"], f["facing"]))
    return [(f["row"], f["col"])]


def make_rl_rival(path, sha256: str, name: str | None = None, decision_every: int = 6,
                  macro_every: int = MACRO_EVERY) -> MacroController:
    net = load_net(path, sha256)
    pm = PolicyMacro(net, macro_every, decision_every)
    ctrl = MacroController(pm, name=name or f"ppo-{sha256[:8]}", kind="policy",
                           decision_every=decision_every, macro_every=1)
    # T07-E4: an inference error is answered with WAIT (the seat must not stop), so the count
    # has to be readable by whoever runs the seat; a silent WAIT would look like a passive policy.
    ctrl.policy_macro = pm
    ctrl.policy_errors = lambda: pm.errors
    return ctrl
