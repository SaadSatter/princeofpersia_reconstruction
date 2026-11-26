"""Replay a server input trace through `VersusEpisode` (T13, determinism).

The trace never leaves the server. It is the resolved inputs of every tick
(`[[seat, action], ...]` per tick) and the seed; replaying it gives the duel's
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
    for tick in trace["ticks"]:
        for seat, action in tick:
            if not ep.step(seat, action)["accepted"]:
                raise ValueError(f"trace input {seat} {action} was refused on replay")
        ep.tick()
    return ep.outcome(), state_hash(ep)
