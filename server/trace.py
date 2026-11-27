"""Replay a server input trace through `VersusEpisode` (T13, determinism).

The trace never leaves the server. It is the resolved inputs of every tick
(`[[seat, action], ...]` per tick), the human seats released each tick (`releases`, decision
#93: a release clears that seat's queued input, so the engine state depends on it) and the seed; replaying it gives the duel's
outcome and state hash again.
"""

from __future__ import annotations

from pop.versus import arena_episode
from pop.versus_runner import digest, snapshot


def state_hash(episode) -> str:
    return digest(snapshot(episode))


def replay(trace: dict) -> tuple[dict, str]:
    """(outcome, state hash) after replaying `trace` on a fresh arena episode."""
    ep = arena_episode(trace["seed"])
    releases = trace.get("releases") or [[] for _ in trace["ticks"]]   # older traces have none
    for tick, released in zip(trace["ticks"], releases):
        for seat, action in tick:
            if not ep.step(seat, action)["accepted"]:
                raise ValueError(f"trace input {seat} {action} was refused on replay")
        for seat in released:                     # a seat is either stepped or released in a tick
            ep.release(seat)
        ep.tick()
    return ep.outcome(), state_hash(ep)
