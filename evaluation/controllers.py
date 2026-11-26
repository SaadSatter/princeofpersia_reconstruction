"""Controller registry for the suite: fresh instances per trial (decision #24).

Letters of a configuration (SvS, MvS, SvM, MvM), one per seat (A then B): `S`
is the scripted baseline (`agents/versus_baseline.py`), `M` is the PPO rival
built from the shipped weights (`agents.rl.policy.SHIPPED_WEIGHTS`, hash
checked at load through `SHIPPED_SHA256`). This module never imports a
provider SDK and never makes a network call; the PPO rival's provider, token
and cost fields are N/A (as in PR #64).

Stand-ins, forced by a scenario start's `other_controller` so the other seat
cannot confound the measurement:
  wait   always WAIT (pop/seats.py WaitController), labelled kind "fallback"
  decoy  a disguised rival that paces its stretch with careful steps
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from pop.seats import WAIT, RandomController, WaitController

ROOT = Path(__file__).resolve().parent.parent
SCRIPTED_SOURCES = ("agents/versus_baseline.py", "agents/macros.py", "agents/baseline.py")
PACE = ("STEP_RIGHT", "STEP_RIGHT", WAIT, WAIT, "STEP_LEFT", "STEP_LEFT", WAIT, WAIT)
POLICY_VERSION = "ppo-run-1"          # decision #51; docs/final/RL_POLICY.md


class DecoyController:
    """Paces back and forth with careful steps and short pauses, the way a
    patrolling guard looks from a distance. A scripted stand-in for the other
    rival in I3: it never attacks, never runs, never jumps. It is not
    calibrated to a guard's real stride, which is a stated confound of I3."""

    kind = "scripted"

    def __init__(self, name: str = "decoy") -> None:
        self.name = name
        self._i = 0

    def reset(self, seed: int) -> None:
        self._i = 0

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str:
        want = PACE[self._i % len(PACE)]
        self._i += 1
        return want if want in legal else WAIT


def source_sha256(paths=SCRIPTED_SOURCES) -> str:
    h = hashlib.sha256()
    for rel in paths:
        h.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes())
    return h.hexdigest()


def make_scripted(name: str = "versus-baseline"):
    from agents.versus_baseline import make_baseline
    return make_baseline(name)


def make_shipped_policy():
    """A fresh PPO rival from the shipped weights. Loading checks the hash."""
    from agents.rl.policy import SHIPPED_SHA256, SHIPPED_WEIGHTS, make_rl_rival
    ctrl = make_rl_rival(SHIPPED_WEIGHTS, SHIPPED_SHA256)
    ctrl.weights_sha256 = SHIPPED_SHA256
    ctrl.version = POLICY_VERSION
    return ctrl


def build(kind: str, policy_factory=None, name: str | None = None):
    """A fresh controller. `kind`: scripted, policy, wait, decoy, random.
    `policy_factory` builds a policy seat (default: the shipped weights)."""
    if kind == "scripted":
        return make_scripted(name or "versus-baseline")
    if kind == "policy":
        return (policy_factory or make_shipped_policy)()
    if kind == "wait":
        return WaitController(name or "wait")
    if kind == "decoy":
        return DecoyController(name or "decoy")
    if kind == "random":
        return RandomController(name or "random")
    raise ValueError(f"unknown controller kind {kind!r}")


def policy_errors_of(ctrl) -> int | None:
    """Inference errors a policy seat swallowed into WAIT (T08-fix2, decision #84).
    An integer for a policy seat that exposes `policy_errors()`, else None (not a policy seat,
    or no counter, which a reader must not mistake for zero)."""
    fn = getattr(ctrl, "policy_errors", None)
    if getattr(ctrl, "kind", None) != "policy" or not callable(fn):
        return None
    return int(fn())


def describe(ctrl) -> dict:
    """What a result row records about a controller. Provider, token and cost
    fields are N/A for scripted and PPO controllers."""
    kind = getattr(ctrl, "kind", "?")
    out = {"name": getattr(ctrl, "name", "?"), "kind": kind,
           "version": getattr(ctrl, "version", None),
           "weights_sha256": getattr(ctrl, "weights_sha256", None),
           "provider": "N/A", "tokens": "N/A", "cost_usd": "N/A"}
    if out["version"] is None and kind == "scripted" and out["name"].startswith("versus-baseline"):
        out["version"] = "source:" + source_sha256()[:16]
    return out
