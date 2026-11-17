"""Poses for a versus seat's view (pure Python, no pygame).

Reads only one seat's observation (pop/versus.py `observe`): its own rival
(`me`) and the figures in its room, each with an optional `motion` (the move
in progress: effect, frames done, length, planned end if in this room). A
move is shown with the same clips as single-player play (render/anim.py
`clip`), built once for the whole move and indexed by its progress, so the
picture keeps up with the duel's real-time ticks.
"""

from __future__ import annotations

from pop import physics as P

from .anim import AnimState, Pose, Step, clip, idle_pose


def _dir(facing: str) -> str:
    return "RIGHT" if facing == "right" else "LEFT"


def action_for(motion: dict, posture: str, facing: str) -> str:
    """The input that produces this move (anim.clip branches on action and effect)."""
    e, n = motion["effect"], motion["frames"]
    d = _dir(facing)
    if e == "turned":
        return _dir(motion["to_facing"])
    if e == "moved":
        return "STEP_" + d if n == P.STEP else d
    if e == "jumped":
        return "JUMP_" + d
    if e in ("bumped", "edge"):
        return "JUMP_" + d if n == P.JUMP_IN_PLACE else d
    if e in ("climbed", "won"):
        return "UP"
    if e in ("hanging", "drank", "took_sword", "dropped"):
        return "DOWN"
    if e == "none":
        return "DOWN" if n == P.CROUCH else "UP"
    return "WAIT"


def _kid(view: dict) -> dict:
    return {"row": view["row"], "col": view["col"], "facing": view["facing"],
            "posture": view["posture"]}


def pose(view: dict, room: str, cache: dict | None = None, key: object = None) -> Pose:
    """This frame's pose for `view` (obs["me"] or one of obs["figures"]).
    cache/key: optional memo so a move's clip is built once."""
    m = view.get("motion")
    if not m or m["frames"] <= 0:
        return idle_pose(_kid(view))
    before = _kid(view)
    after = dict(before)
    if m["to"] is not None:
        after["row"], after["col"] = m["to"]
    elif m["effect"] == "moved":                       # leaving the room: run off the edge
        after["col"] = view["col"] + (1 if view["facing"] == "right" else -1)
    after["posture"] = m["to_posture"] if m["to_posture"] != "won" else "standing"
    after["facing"] = m["to_facing"]
    action = action_for(m, view["posture"], view["facing"])
    sig = (key, view["row"], view["col"], view["facing"], view["posture"],
           m["effect"], m["frames"], tuple(m["to"] or ()), m["to_facing"])
    poses = cache.get(sig) if cache is not None else None
    if poses is None:
        step = Step(action=action, before=before, after=after, before_room=room,
                    after_room=room, effect=m["effect"], frames=m["frames"])
        poses = clip(step, AnimState())
        if cache is not None:
            cache.clear() if len(cache) > 64 else None
            cache[sig] = poses
    return poses[max(0, min(len(poses), m["frame"]) - 1)]
