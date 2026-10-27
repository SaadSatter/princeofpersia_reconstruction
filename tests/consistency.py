"""Physical consistency of the kid's state (used by several tests).

After any step: never inside a wall; standing only where supported;
falling only where unsupported; hanging only from a floor that exists.
"""

from pop import tiles as T


def problems(game) -> list[str]:
    k = game.kid
    if k.posture in ("dead", "won"):
        return []
    out = []
    if game.geom.tile(k.cell) == T.WALL:
        out.append(f"inside a wall at {k.cell}")
    supported = game.geom.supported(k.cell)
    if k.posture == "standing" and not supported:
        out.append(f"standing without support at {k.cell}")
    if k.posture == "falling" and supported:
        out.append(f"falling while supported at {k.cell}")
    if k.posture == "hanging" and (k.hang_ledge is None
                                   or game.geom.tile(k.hang_ledge) not in T.HAS_FLOOR):
        out.append(f"hanging from no floor ({k.hang_ledge})")
    return out


def assert_consistent(game, context: str = "") -> None:
    found = problems(game)
    assert not found, f"{context}: {found}"
