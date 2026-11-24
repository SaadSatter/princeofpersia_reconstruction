"""Controller registry for the suite: fresh instances per trial (decision #24).

Letters of a configuration (SvS, MvS, SvM, MvM): `S` is the scripted baseline
(`agents/versus_baseline.py`), `M` is the learned policy (PPO, T07), supplied
by `--policy-factory module:callable`. This module never imports a provider
SDK and never makes a network call; the PPO rival's provider, token and cost
fields are N/A.

Stand-ins, forced by a scenario start's `other_controller` so the other seat
cannot confound the measurement:
  wait   always WAIT (pop/seats.py WaitController), labelled kind "fallback"
  decoy  a disguised rival that paces its stretch with careful steps
"""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

from pop.seats import WAIT, RandomController, WaitController

ROOT = Path(__file__).resolve().parent.parent
SCRIPTED_SOURCES = ("agents/versus_baseline.py", "agents/macros.py", "agents/baseline.py")
PACE = ("STEP_RIGHT", "STEP_RIGHT", WAIT, WAIT, "STEP_LEFT", "STEP_LEFT", WAIT, WAIT)


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


def load_factory(spec: str):
    """`module:callable` -> the callable. Evaluator-side only."""
    module, _, attr = spec.partition(":")
    if not module or not attr:
        raise ValueError("policy factory must look like module:callable")
    return getattr(importlib.import_module(module), attr)


def make_scripted(name: str = "versus-baseline"):
    from agents.versus_baseline import make_baseline
    return make_baseline(name)


def build(kind: str, policy_factory=None, name: str | None = None):
    """A fresh controller. `kind`: scripted, policy, wait, decoy, random."""
    if kind == "scripted":
        return make_scripted(name or "versus-baseline")
    if kind == "policy":
        if policy_factory is None:
            raise ValueError("a policy (M) seat needs --policy-factory")
        return policy_factory()
    if kind == "wait":
        return WaitController(name or "wait")
    if kind == "decoy":
        return DecoyController(name or "decoy")
    if kind == "random":
        return RandomController(name or "random")
    raise ValueError(f"unknown controller kind {kind!r}")


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
