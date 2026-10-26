"""Interim terminal frontend: play a situation through the five operations.

    uv run python play_text.py [S3]

The Pygame frontend (play.py) replaces this for the finished game. Keys map
to the same actions agents use.
"""

from __future__ import annotations

import sys

from pop.interface import PLAYER_ID, Episode
from pop.tiles import LEGEND

KEYS = {
    "d": "RIGHT", "a": "LEFT", "sd": "STEP_RIGHT", "sa": "STEP_LEFT",
    "jd": "JUMP_RIGHT", "ja": "JUMP_LEFT", "rd": "RUN_JUMP_RIGHT", "ra": "RUN_JUMP_LEFT",
    "w": "UP", "s": "DOWN", ".": "WAIT",
}


def render(obs: dict) -> str:
    kid = obs["kid"]
    rows = [list(r) for r in obs["tiles"]]
    rows[kid["row"]][kid["col"]] = ">" if kid["facing"] == "right" else "<"
    left = "|" if not obs["edges"]["left"] else " "
    right = "|" if not obs["edges"]["right"] else " "
    lines = [f"{left}{''.join(r)}{right}" for r in rows]
    st = obs["state"]
    info = [f"{obs['room']}  hp {kid['hp']}/{kid['max_hp']}  {kid['posture']}  "
            f"actions left {obs['actions_left']}  minutes left {obs['minutes_left']}"]
    for g in st["gates"]:
        info.append(f"gate ({g['row']},{g['col']}) {g['open_pct']}% {'bars' if g['bars'] else 'passable'}")
    for e in st["exits"]:
        info.append(f"exit ({e['row']},{e['col']}) {e['open_pct']}% {'OPEN' if e['open'] else 'closed'}")
    if st["spikes_sprung"]:
        info.append(f"spikes out at {st['spikes_sprung']}")
    if st["loose_shaking"]:
        info.append(f"loose floor shaking at {st['loose_shaking']}")
    if obs["last_result"]:
        info.append(f"last: {obs['last_result']}")
    return "\n".join(lines + info)


def main() -> None:
    sid = sys.argv[1] if len(sys.argv) > 1 else "S3"
    ep = Episode(sid, max_actions=None)
    ep.reset(0)
    print("Legend:", ", ".join(f"{k} {v}" for k, v in LEGEND.items()))
    print("Keys:", ", ".join(f"{k}={v}" for k, v in KEYS.items()), ", r=restart, q=quit")
    while True:
        print()
        print(render(ep.observe(PLAYER_ID)))
        out = ep.outcome()
        if out["status"] == "terminal":
            print(f"*** {out['reason']} (score {out['score']}) — r to restart, q to quit")
        key = input("> ").strip()
        if key == "q":
            return
        if key == "r":
            ep.reset(0)
            continue
        res = ep.step(PLAYER_ID, KEYS.get(key, key))
        if not res["accepted"]:
            print("refused:", res["error"])


if __name__ == "__main__":
    main()
