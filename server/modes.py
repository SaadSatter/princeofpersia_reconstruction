"""The online server's room modes (T22, decisions #87 and #88): the shared mode list
(agents/modes.py) mapped to a `Match`.

    ai        a room whose seat B is the shipped PPO rival (0.04 s budget, #45)
    baseline  a room whose seat B is the scripted baseline
    human     a two-person room (room codes, either control set per seat)

An AI room labels its rival with the honest mode name (#88) unless `neutral`.
Fallbacks stay on the server (trace and log, `"source": "fallback"`, #49).
"""

from __future__ import annotations

from agents.modes import MODE_IDS, ModeError, get

from .match import Match

__all__ = ["MODE_IDS", "rival_for", "make_match"]


def rival_for(mode_id: str) -> str | None:
    """The `Match.rival` value of a mode: "ai", "baseline" or None (two humans)."""
    return get(mode_id).id if get(mode_id).ai else None


def make_match(mode_id: str, **kw) -> Match:
    """A fresh `Match` for a mode. Extra keywords go to `Match` (seed, on_finish, neutral, ...)."""
    kw.setdefault("honest", True)
    return Match(rival=rival_for(mode_id), **kw)
