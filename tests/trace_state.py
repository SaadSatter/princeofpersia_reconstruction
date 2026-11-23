"""Canonical fingerprint of the complete authoritative state (tests only).

Covers the kid (cell, facing, posture, HP, hang ledge, fall progress, sword),
the frame counter, terminal status, every room's tiles, every gate, exit,
plate, spike and loose-floor timer, and the episode's counters. Written to
work with the engine at any commit since the suite was recorded, so golden
fingerprints can be made with the engine that recorded each trace.
"""

import hashlib
import json


def canonical(ep) -> dict:
    g = ep._game
    k = g.kid
    m = g.mech
    cells = lambda d, f: [[list(c), *f(v)] for c, v in sorted(d.items())]  # noqa: E731
    return {
        "kid": [k.room, k.row, k.col, k.facing, k.posture, k.hp, k.max_hp,
                list(k.hang_ledge) if k.hang_ledge else None,
                k.fall_timer, k.fall_rows, k.fall_from_hang, getattr(k, "sword", False)],
        "frames": g.frames,
        "terminal": g.terminal,
        "grid": {str(r): g.geom.rows(r) for r in sorted(g.geom.grid)},
        "gates": cells(m.gates, lambda x: (x.pos, x.state, x.hold)),
        "exits": cells(m.exits, lambda x: (x.pos, x.opening)),
        "plates": cells(m.plates, lambda x: (x,)),
        "spikes": cells(m.spikes, lambda x: (x,)),
        "loose": cells(m.loose, lambda x: (x,)),
        "episode": [ep.actions, ep.invalid_actions, ep.outcome()["status"], ep.outcome()["reason"]],
    }


def fingerprint(ep) -> str:
    return hashlib.sha256(json.dumps(canonical(ep), sort_keys=True).encode()).hexdigest()[:16]


def load_trace(path):
    header, steps = None, []
    for line in open(path):
        if line.strip():
            rec = json.loads(line)
            if rec.get("type") == "episode":
                header = rec
            elif rec.get("type") == "step":
                steps.append(rec)
    return header, steps


def episode_kwargs(header) -> dict:
    limits = header.get("limits") or {}
    return {k: limits[k] for k in ("max_actions", "max_consecutive_invalid") if k in limits}


def replay_fingerprints(Episode, path) -> list[str]:
    """Fingerprint after reset and after every recorded step."""
    header, steps = load_trace(path)
    ep = Episode(header["situation"], **episode_kwargs(header))
    ep.reset(header["seed"])
    out = [fingerprint(ep)]
    for rec in steps:
        ep.step("kid", rec["action"])
        out.append(fingerprint(ep))
    return out
