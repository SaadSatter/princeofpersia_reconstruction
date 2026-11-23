"""Seat controllers: who decides a seat's next input (docs/final/VERSUS_RUNNER.md).

A controller is anything with `name`, `kind` and
`decide(observation: dict, legal: tuple[str, ...]) -> str`, plus an optional
`reset(seed)`. The versus runner (pop/versus_runner.py) is the only caller.
It hands a controller deep copies of its own seat's observation and legal list,
and never the episode, the duel, the other seat or the episode seed. `reset`
gets `controller_seed(seed, seat)`, a number derived from the episode seed, so
a controller cannot rebuild the engine's random stream from it.

Kinds: "human" (input queued by a frontend), "scripted" (baselines and test
scripts), "policy" (a trained or generative model) and "fallback" (always WAIT).
"""

from __future__ import annotations

import hashlib
import random
from typing import Callable, Protocol, runtime_checkable

KINDS = ("human", "scripted", "policy", "fallback")
WAIT = "WAIT"


@runtime_checkable
class SeatController(Protocol):
    name: str
    kind: str

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str: ...


def controller_seed(seed: int, seat: str) -> int:
    """A per-seat seed derived from the episode seed by a one-way hash."""
    digest = hashlib.sha256(f"shadow-masque:controller:{seed}:{seat}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


class HumanController:
    """A person at a keyboard. The frontend calls `queue`; the runner takes the
    latest queued input at the seat's next decision (a newer input replaces an
    older one, as in the duel), or WAIT if nothing was queued."""

    kind = "human"

    def __init__(self, name: str = "human") -> None:
        self.name = name
        self._latest: str | None = None

    def queue(self, action: str) -> None:
        self._latest = action

    def reset(self, seed: int) -> None:
        self._latest = None

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str:
        action, self._latest = self._latest, None
        return WAIT if action is None else action


class ScriptedController:
    """A fixed list of inputs, then WAIT. Copies the list: no shared state."""

    kind = "scripted"

    def __init__(self, inputs: list[str], name: str = "scripted") -> None:
        self.name = name
        self._script = tuple(inputs)
        self._left = list(self._script)

    def reset(self, seed: int) -> None:
        self._left = list(self._script)

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str:
        return self._left.pop(0) if self._left else WAIT


class RandomController:
    """A uniformly random legal input from its own seeded stream. A test and
    sanity baseline, labelled scripted; not the competent baseline (T05)."""

    kind = "scripted"

    def __init__(self, name: str = "random") -> None:
        self.name = name
        self._rng = random.Random(0)

    def reset(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str:
        return self._rng.choice(legal)


class PolicyController:
    """Wraps a policy function `(observation, legal) -> input` (for example a
    trained PPO policy behind a macro layer)."""

    kind = "policy"

    def __init__(self, policy: Callable[[dict, tuple[str, ...]], str],
                 name: str = "policy", reset: Callable[[int], None] | None = None) -> None:
        self.name = name
        self._policy = policy
        self._reset = reset

    def reset(self, seed: int) -> None:
        if self._reset is not None:
            self._reset(seed)

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str:
        return self._policy(observation, legal)


class WaitController:
    """Always WAIT: the labelled fallback seat (for example when the AI seat is
    unavailable)."""

    kind = "fallback"

    def __init__(self, name: str = "wait") -> None:
        self.name = name

    def decide(self, observation: dict, legal: tuple[str, ...]) -> str:
        return WAIT
