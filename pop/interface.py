"""The five-operation machine-playable interface.

    reset(seed)               -> initial observation
    observe(player_id)        -> what the kid may know (pop/observation.py)
    legal_actions(player_id)  -> actions allowed in the current posture only
    step(player_id, action)   -> validated transition and visible result
    outcome()                 -> ongoing / terminal, with reason and score

The Episode holds the authoritative Game. Players never receive it; the
runner (pop/runner.py) passes them copies of observe() and legal_actions().
"""

from __future__ import annotations

from . import observation
from .engine import ACTIONS, Game
from .situations import SITUATIONS

PLAYER_ID = "kid"
MAX_CONSECUTIVE_INVALID = 5          # R-D12

SITUATION_DEFAULT = object()          # use the situation's declared action limit

INVALID_NOT_TEXT = "action must be a string"
INVALID_UNKNOWN = "unknown action"
INVALID_NOT_NOW = "action not legal in the current posture"
EPISODE_OVER = "episode is over"


class Episode:
    def __init__(self, situation_id: str, max_actions=SITUATION_DEFAULT,
                 max_consecutive_invalid: int = MAX_CONSECUTIVE_INVALID):
        """max_actions: an int, None for no limit (human play), or the default."""
        self.situation = SITUATIONS[situation_id]
        self.max_actions = (self.situation.max_actions if max_actions is SITUATION_DEFAULT
                            else max_actions)
        self.max_consecutive_invalid = max_consecutive_invalid
        self.reset(0)

    # 1 ---------------------------------------------------------------
    def reset(self, seed: int) -> dict:
        self.seed = seed
        self._game = Game(self.situation, seed)
        self.actions = 0
        self.invalid_actions = 0
        self._consecutive_invalid = 0
        self._limit_reason: str | None = None
        self._last_result: dict | None = None
        return self.observe(PLAYER_ID)

    # 2 ---------------------------------------------------------------
    def observe(self, player_id: str) -> dict:
        _check_player(player_id)
        left = None if self.max_actions is None else self.max_actions - self.actions
        return observation.build(self._game, left, self._last_result)

    # 3 ---------------------------------------------------------------
    def legal_actions(self, player_id: str) -> list[str]:
        _check_player(player_id)
        if self._reason() is not None:
            return []
        return list(self._game.legal_actions())

    # 4 ---------------------------------------------------------------
    def step(self, player_id: str, action: object) -> dict:
        _check_player(player_id)
        if self._reason() is not None:
            return self._refuse(EPISODE_OVER, count=False)
        if not isinstance(action, str):
            return self._refuse(INVALID_NOT_TEXT)
        name = action.strip().upper()
        if name not in ACTIONS:
            return self._refuse(INVALID_UNKNOWN)
        if name not in self._game.legal_actions():
            return self._refuse(INVALID_NOT_NOW)
        self._consecutive_invalid = 0
        self.actions += 1
        result = self._game.perform(name)
        self._last_result = result
        if (self._game.terminal is None and self.max_actions is not None
                and self.actions >= self.max_actions):
            self._limit_reason = "step_limit"
        return {"accepted": True, "action": name, **{k: result[k] for k in observation.RESULT_KEYS},
                "observation": self.observe(player_id)}

    # 5 ---------------------------------------------------------------
    def outcome(self) -> dict:
        reason = self._reason()
        return {
            "status": "ongoing" if reason is None else "terminal",
            "reason": reason,
            "score": 1 if reason == "won" else 0,
            "actions": self.actions,
            "invalid_actions": self.invalid_actions,
            "frames": self._game.frames,
        }

    # runner-only -------------------------------------------------------
    def terminate(self, reason: str) -> None:
        """Called by the runner to end an episode on a runner limit."""
        if self._reason() is None:
            self._limit_reason = reason

    def _reason(self) -> str | None:
        return self._game.terminal or self._limit_reason

    def _refuse(self, error: str, count: bool = True) -> dict:
        if count:
            self.invalid_actions += 1
            self._consecutive_invalid += 1
            if self._consecutive_invalid >= self.max_consecutive_invalid:
                self._limit_reason = "invalid_limit"
        return {"accepted": False, "error": error, "frames": 0,
                "observation": self.observe(PLAYER_ID)}


def _check_player(player_id: str) -> None:
    if player_id != PLAYER_ID:
        raise ValueError(f"This game has one player, {PLAYER_ID!r}.")
