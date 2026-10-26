"""Episode runner: owns the Episode and enforces the runner limits.

A player is any object with:
    name: str
    source: str          # "baseline", "model", "scripted", ...
    uses_model: bool     # if True, every decide() call counts as a model call
    decide(observation: dict, legal_actions: list[str]) -> str | Decision
    commit(observation, action, source, error)   # optional memory hook

The runner gives the player copies only, times each decision, counts model
calls (failed ones included), substitutes a WAIT labeled "fallback" when a
decision fails or times out, and records a trace.

Each failed call gets a short `error_kind` (e.g. "auth_missing", "timeout",
"unparseable_reply") and error text with anything key-shaped redacted.

A timed-out decision thread cannot be killed, so its reply may still arrive.
The runner never reads it into the episode or the trace; it only logs the
reply's tokens and cost under `late_replies` (they are billed). A player that
keeps memory must write it only in `commit`, which the runner calls in its
own thread after each step with what was actually submitted (audit F-1).
"""

from __future__ import annotations

import copy
import json
import re
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
    # Set when the player made a call but produced no usable action (R-D22).
    fallback_reason: str | None = None
    error_kind: str | None = None              # e.g. "unparseable_reply" (R-D25)


@dataclass
class Limits:
    max_actions: int | None = None       # None: the situation's value
    max_calls: int | None = None         # None: the situation's value
    call_timeout_s: float = DEFAULT_CALL_TIMEOUT_S
    max_consecutive_invalid: int = 5


# Anything shaped like an API key or bearer token is cut from error text.
_SECRET = re.compile(r"sk-ant-[A-Za-z0-9_\-]+|(?i:bearer\s+)[A-Za-z0-9._\-]{8,}")
MAX_ERROR_CHARS = 300


def safe_error_text(exc: BaseException) -> str:
    """Error text for traces: secrets redacted, length capped (R-D25)."""
    text = _SECRET.sub("[redacted]", f"{type(exc).__name__}: {exc}")
    return text if len(text) <= MAX_ERROR_CHARS else text[:MAX_ERROR_CHARS] + "..."


def _call_with_timeout(fn, args, timeout_s):
    """Run fn(*args) in a daemon thread. Returns (value, error, error_kind, late).

    A player may tag a raised exception with `error_kind`; untagged ones are
    "player_error". On timeout `late` is (thread, box): the box may fill in
    later and is only ever read for usage accounting."""
    box: dict = {}

    def target():
        try:
            box["value"] = fn(*args)
        except Exception as exc:  # noqa: BLE001 - any player failure is a failed call
            box["error"] = safe_error_text(exc)
            box["kind"] = getattr(exc, "error_kind", None) or "player_error"

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout_s)
    if thread.is_alive():
        return None, "timeout", "timeout", (thread, box)
    if "error" in box:
        return None, box["error"], box["kind"], None
    return box.get("value"), None, None, None


def _late_reply(i: int, late) -> dict:
    """Usage of an abandoned call, read once at the end of the episode.

    arrived: a reply came back (billed; its meta has tokens and cost).
    failed:  the call raised (treated like any failed call: no usage).
    pending: still running, so its cost is unknown (None), never $0."""
    thread, box = late
    if thread.is_alive():
        return {"i": i, "status": "pending", "tokens_in": 0, "tokens_out": 0,
                "cost_usd": None}
    if "value" not in box:
        return {"i": i, "status": "failed", "tokens_in": 0, "tokens_out": 0,
                "cost_usd": 0.0}
    value = box["value"]
    meta = value.meta if isinstance(value, Decision) else {}
    return {"i": i, "status": "arrived", "tokens_in": meta.get("tokens_in", 0),
            "tokens_out": meta.get("tokens_out", 0), "cost_usd": meta.get("cost_usd", 0.0)}


def _sum_cost(metas: list[dict]) -> float | None:
    """Total cost, or None if any call's price is unknown (audit F-2)."""
    costs = [m["cost_usd"] for m in metas if "cost_usd" in m]
    if any(c is None for c in costs):
        return None
    return round(sum(costs), 6)


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
    abandoned: list[tuple[int, tuple]] = []      # (step index, (thread, box))
    started = time.time()

    while ep.outcome()["status"] == "ongoing":
        if player.uses_model and calls >= max_calls:
            ep.terminate("call_limit")
            break
        obs = ep.observe(PLAYER_ID)
        obs["calls_left"] = (max_calls - calls) if player.uses_model else None
        legal = ep.legal_actions(PLAYER_ID)

        t0 = time.perf_counter()
        value, error, error_kind, late = _call_with_timeout(player.decide,
                                                (copy.deepcopy(obs), list(legal)),
                                                limits.call_timeout_s)
        if late is not None:
            abandoned.append((len(trace), late))
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
            if isinstance(value, Decision) and value.fallback_reason is not None:
                failed_calls += 1                      # R-D22
                fallbacks += 1
                error = value.fallback_reason
                error_kind = value.error_kind or "fallback"
                action, source = FALLBACK_ACTION, "fallback"

        result = ep.step(PLAYER_ID, action)
        if hasattr(player, "commit"):
            player.commit(copy.deepcopy(obs), action if isinstance(action, str) else repr(action),
                          source, error)
        after = result["observation"]
        trace.append({
            "i": len(trace),
            "action": action if isinstance(action, str) else repr(action),
            "source": source,
            "accepted": result["accepted"],
            "error": error or result.get("error"),
            "error_kind": error_kind,                  # failed-call category, or None
            "effect": result.get("effect"),
            "frames": result["frames"],
            "latency_ms": latency_ms,
            "meta": meta,
            "kid": after["kid"],
            "room": after["room"],
        })

    out = ep.outcome()
    kinds: dict[str, int] = {}
    for r in trace:
        if r["error_kind"]:
            kinds[r["error_kind"]] = kinds.get(r["error_kind"], 0) + 1
    latencies = [r["latency_ms"] for r in trace] or [0.0]
    # Late replies are read once, here, after the episode is over.
    late_replies = [_late_reply(i, late) for i, late in abandoned]
    metas = [r["meta"] for r in trace] + late_replies
    usage = {"tokens_in": sum(m.get("tokens_in", 0) for m in metas),
             "tokens_out": sum(m.get("tokens_out", 0) for m in metas),
             "cost_usd": _sum_cost(metas)}
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
        "failed_call_kinds": dict(sorted(kinds.items())),
        "usage": usage,
        "late_replies": late_replies,
        "latency_ms": {"mean": round(sum(latencies) / len(latencies), 1),
                       "max": max(latencies)},
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
