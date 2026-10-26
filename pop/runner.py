"""Episode runner: owns the Episode and enforces the runner limits.

A player is any object with:
    name: str
    source: str          # "baseline", "model", "scripted", ...
    uses_model: bool     # if True, every decide() call counts as a model call
    decide(observation: dict, legal_actions: list[str]) -> str | Decision

The runner gives the player copies only, times each decision, counts model
calls (failed ones included), substitutes a WAIT labeled "fallback" when a
decision fails or times out, and records a trace.
"""

from __future__ import annotations

import copy
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import GAME_VERSION
from .interface import PLAYER_ID, SITUATION_DEFAULT, Episode

DEFAULT_CALL_TIMEOUT_S = 20.0
FALLBACK_ACTION = "WAIT"


@dataclass
class Decision:
    action: object
    meta: dict = field(default_factory=dict)   # tokens, raw text, model id, ...


@dataclass
class Limits:
    max_actions: int | None = None       # None: the situation's value
    max_calls: int | None = None         # None: the situation's value
    call_timeout_s: float = DEFAULT_CALL_TIMEOUT_S
    max_consecutive_invalid: int = 5


def _call_with_timeout(fn, args, timeout_s):
    """Run fn(*args) in a daemon thread. Returns (value, error_string)."""
    box: dict = {}

    def target():
        try:
            box["value"] = fn(*args)
        except Exception as exc:  # noqa: BLE001 - any player failure is a failed call
            box["error"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive():
        return None, "timeout"
    if "error" in box:
        return None, box["error"]
    return box.get("value"), None


def run_episode(player, situation_id: str, seed: int, limits: Limits | None = None) -> dict:
    limits = limits or Limits()
    ep = Episode(situation_id,
                 max_actions=(SITUATION_DEFAULT if limits.max_actions is None
                              else limits.max_actions),
                 max_consecutive_invalid=limits.max_consecutive_invalid)
    ep.reset(seed)
    max_calls = limits.max_calls if limits.max_calls is not None else ep.situation.max_calls
    calls = failed_calls = fallbacks = 0
    trace: list[dict] = []
    started = time.time()

    while ep.outcome()["status"] == "ongoing":
        if player.uses_model and calls >= max_calls:
            ep.terminate("call_limit")
            break
        obs = ep.observe(PLAYER_ID)
        obs["calls_left"] = (max_calls - calls) if player.uses_model else None
        legal = ep.legal_actions(PLAYER_ID)

        t0 = time.perf_counter()
        value, error = _call_with_timeout(player.decide, (copy.deepcopy(obs), list(legal)),
                                          limits.call_timeout_s)
        latency_ms = round(1000 * (time.perf_counter() - t0), 1)
        if player.uses_model:
            calls += 1                                 # failed calls count too
        meta: dict = {}
        if error is not None:
            failed_calls += 1
            fallbacks += 1
            action, source = FALLBACK_ACTION, "fallback"
        else:
            if isinstance(value, Decision):
                action, meta = value.action, dict(value.meta)
            else:
                action = value
            source = player.source

        result = ep.step(PLAYER_ID, action)
        after = result["observation"]
        trace.append({
            "i": len(trace),
            "action": action if isinstance(action, str) else repr(action),
            "source": source,
            "accepted": result["accepted"],
            "error": error or result.get("error"),
            "effect": result.get("effect"),
            "frames": result["frames"],
            "latency_ms": latency_ms,
            "meta": meta,
            "kid": after["kid"],
            "room": after["room"],
        })

    out = ep.outcome()
    return {
        "situation": situation_id,
        "seed": seed,
        "player": player.name,
        "game_version": GAME_VERSION,
        "started_unix": round(started, 3),
        "outcome": out,
        "model_calls": calls,
        "failed_calls": failed_calls,
        "fallbacks": fallbacks,
        "limits": {"max_actions": ep.max_actions, "max_calls": max_calls,
                   "call_timeout_s": limits.call_timeout_s,
                   "max_consecutive_invalid": limits.max_consecutive_invalid},
        "trace": trace,
    }


def save_trace(result: dict, path: str | Path) -> None:
    """One JSON header line, then one line per step."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {k: v for k, v in result.items() if k != "trace"}
    with path.open("w") as f:
        f.write(json.dumps({"type": "episode", **header}) + "\n")
        for rec in result["trace"]:
            f.write(json.dumps({"type": "step", **rec}) + "\n")


class ScriptedPlayer:
    """Plays a fixed list of actions, then WAITs. For tests and demos."""

    uses_model = False
    source = "scripted"

    def __init__(self, actions: list[str], name: str = "scripted"):
        self.name = name
        self._actions = list(actions)

    def decide(self, observation: dict, legal_actions: list[str]) -> str:
        return self._actions.pop(0) if self._actions else "WAIT"
