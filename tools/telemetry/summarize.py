"""Summarize a directory of playtest telemetry logs (T20, decision #67). Standard library only.

    python3 tools/telemetry/summarize.py traces/playtest [--out DIR]

Reads every `*.jsonl` in the directory (the per-seat logs `server/telemetry.py` writes;
`*-host.json` summaries are not read) and writes `summary.json` and `summary.md` to
`--out` (default: the same directory). The output depends only on the logs: sorted,
no clock, no absolute paths, so two runs on the same input are byte-identical. This is
the tool the T21 analyst runs. It reports facts, never an interpretation.

Per seat and per duel:
* stalls: idle spells (no accepted action for IDLE_THRESHOLD_S, from the log), runs of
  refused actions, and time spent in one room.
* quits: disconnects, reconnects, forfeits, no rematch, a duel abandoned.
* mechanics never used or used once: TAKE, RIG, flip, block, draw, sheathe, sword pickup
  (plus the strikes and the disguise, for context).

Mechanics are read from what the seat's own log shows. A use is counted once, when the
engine started the move (a `move` row, schema 2). A key held down is one use: the engine
starts the input queued while a move runs once that move ends, and that start carries
`repeat` (same held key as the last start of the same move) and is not counted. A key
queued while a move runs is the move it starts, never the running move. `block` is a stance change while armed (STANCE_UP or
STANCE_DOWN), the choice that blocks; a block that actually stopped a blow is not a fact
a seat's own view carries. `flip` is a started move whose own effect is "flipped" (a jump,
a running jump or a hop turned into a flip). A direction that a jump cancelled inside the
R-V35 grace window (the jump's `grace` marker) is dropped from `moves`. "Accepted" is not
"executed": the engine drops a few accepted inputs unstarted, and they are not uses. Logs
of schema 1 (no `move` rows) are read the old way, per accepted action.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Decision #83 (Saad): a run of at least this many refused ticks in a row is a stall signal
# (12 ticks = 1 s; a shorter run is the engine's fixed 3-tick window, not a stall); the
# idle spell is 3 s (server/telemetry.py IDLE_THRESHOLD_S); "stuck" is 60 s in one room.
REFUSED_RUN_MIN = 12
STUCK_ROOM_S = 60.0

# name -> (how it is counted from an event, required by the brief)
MECHANICS = {
    "TAKE": True, "RIG": True, "flip": True, "block": True, "draw": True, "sheathe": True,
    "sword_pickup": True, "lunge": False, "throw": False, "kick": False, "sweep": False,
    "disguise": False,
}
_BY_ACTION = {"TAKE": "TAKE", "RIG": "RIG", "DRAW": "draw", "SHEATHE": "sheathe",
              "STANCE_UP": "block", "STANCE_DOWN": "block", "LUNGE": "lunge", "THROW": "throw",
              "KICK": "kick", "SWEEP": "sweep"}


def read_logs(directory: Path) -> list[tuple[str, list[dict]]]:
    """[(file name, rows)], sorted by name. A line that is not JSON is skipped."""
    out = []
    for path in sorted(directory.glob("*.jsonl")):
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
        if rows and rows[0].get("type") == "header":
            out.append((path.name, rows))
    return out


def moves_started(events: list[dict]) -> dict[str, int]:
    """Moves the engine started, by name, minus a direction a grace jump cancelled (R-V35,
    decision #82). The log stays append-only: the direction row is there, the jump row
    carries `grace`, and the nearest earlier same-side direction is dropped here."""
    started = [e for e in events if e["type"] == "move"]
    dropped: set[int] = set()
    for i, e in enumerate(started):
        if e.get("grace"):
            side = e["move"][len("JUMP_"):]
            for j in range(i - 1, -1, -1):
                if started[j]["move"] in (side, "STEP_" + side) and j not in dropped:
                    dropped.add(j)
                    break
    counts: dict[str, int] = {}
    for i, e in enumerate(started):
        if i not in dropped:
            counts[e["move"]] = counts.get(e["move"], 0) + 1
    return dict(sorted(counts.items()))


def mechanics_used(events: list[dict]) -> dict[str, int]:
    used = {name: 0 for name in MECHANICS}
    if any(e["type"] == "move" for e in events):       # schema 2: count starts, once each
        for e in events:
            if e["type"] == "move" and not e.get("repeat"):
                name = _BY_ACTION.get(e["move"])
                if name:
                    used[name] += 1
                if e.get("effect") == "flipped":
                    used["flip"] += 1
            elif e["type"] == "sword_pickup":
                used["sword_pickup"] += 1
            elif e["type"] == "disguise_on":
                used["disguise"] += 1
        return used
    for e in events:
        if e["type"] == "action" and e.get("accepted"):
            name = _BY_ACTION.get(e["action"])
            if name:
                used[name] += 1
            if e.get("effect") == "flipped":
                used["flip"] += 1
        elif e["type"] == "sword_pickup":
            used["sword_pickup"] += 1
        elif e["type"] == "disguise_on":
            used["disguise"] += 1
    return used


def refused_runs(events: list[dict]) -> list[dict]:
    """Runs of at least REFUSED_RUN_MIN refused actions in a row (no accepted one between)."""
    runs, cur = [], None
    for e in events:
        if e["type"] != "action":
            continue
        if e["accepted"]:
            cur = None
        elif cur is not None and cur["action"] == e["action"]:
            cur["length"] += 1
            cur["end_t"] = e["t"]
        else:
            cur = {"action": e["action"], "start_t": e["t"], "end_t": e["t"], "length": 1}
            runs.append(cur)
    return [r for r in runs if r["length"] >= REFUSED_RUN_MIN]


def room_times(events: list[dict], tps: int) -> dict[str, float]:
    """Seconds spent in each room (by its label), from duel start to the duel's end."""
    end_t = max((e["t"] for e in events), default=0)
    visits: list[tuple[str, int]] = []
    for e in events:
        if e["type"] in ("duel_start", "room"):
            visits.append((e["room"], e["t"]))
    totals: dict[str, float] = {}
    for i, (room, t) in enumerate(visits):
        stop = visits[i + 1][1] if i + 1 < len(visits) else end_t
        totals[room] = totals.get(room, 0.0) + (stop - t) / tps
    return {r: round(v, 3) for r, v in sorted(totals.items())}


def summarize_seat(name: str, rows: list[dict]) -> dict:
    head, events = rows[0], rows[1:]
    tps = head.get("ticks_per_second", 12)
    used = mechanics_used(events)
    idle = [{"since_t": e["since_t"]} for e in events if e["type"] == "idle" and e["phase"] == "start"]
    spells = []
    for e in events:
        if e["type"] == "idle" and e["phase"] == "end":
            spells.append({"seconds": e["seconds"], "end_t": e["t"]})
    rooms = room_times(events, tps)
    end = next((e for e in events if e["type"] == "duel_end"), None)
    forfeits = [e["by"] for e in events if e["type"] == "forfeit"]
    rematch = [e["pressed"] for e in events if e["type"] == "rematch"]
    return {
        "file": name, "room": head["room"], "duel": head["duel"], "seat": head["seat"],
        "rival": head["rival"], "build": head.get("build"),
        "duration_s": round(max((e["t"] for e in events), default=0) / tps, 3),
        "result": end["result"] if end else None,
        "end_reason": end["reason"] if end else None,
        "stalls": {
            "idle_spells": len(spells), "idle_total_s": round(sum(s["seconds"] for s in spells), 3),
            "idle": spells, "idle_unfinished": max(0, len(idle) - len(spells)),
            "refused_runs": refused_runs(events),
            "rooms_s": rooms,
            "longest_room_s": max(rooms.values(), default=0.0),
            "stuck_rooms": sorted(r for r, v in rooms.items() if v >= STUCK_ROOM_S),
        },
        "quits": {
            "disconnects": sum(1 for e in events if e["type"] == "disconnect"),
            "reconnects": sum(1 for e in events if e["type"] == "reconnect"),
            "forfeit": forfeits[0] if forfeits else None,
            "no_rematch": False in rematch and True not in rematch,
            "rematch_pressed": True in rematch,
            "duel_abandoned": bool(end and end["reason"] in ("abandoned", "room_failed")),
            "no_duel_end": end is None,
        },
        "mechanics": used,
        "moves": moves_started(events),
        "events": {t: sum(1 for e in events if e["type"] == t)
                   for t in sorted({e["type"] for e in events})},
    }


def summarize(directory: Path) -> dict:
    seats = [summarize_seat(n, r) for n, r in read_logs(directory)]
    seats.sort(key=lambda s: (s["room"], s["duel"], s["seat"], s["file"]))
    duels: dict[tuple, dict] = {}
    for s in seats:
        d = duels.setdefault((s["room"], s["duel"]), {"room": s["room"], "duel": s["duel"],
                                                       "seats": {}})
        d["seats"][s["seat"]] = {"result": s["result"], "end_reason": s["end_reason"],
                                 "duration_s": s["duration_s"],
                                 "quits": s["quits"]}
    totals = {name: sum(s["mechanics"][name] for s in seats) for name in MECHANICS}
    per_seat_use = {name: sum(1 for s in seats if s["mechanics"][name]) for name in MECHANICS}
    return {
        "thresholds": {"refused_run_min": REFUSED_RUN_MIN, "stuck_room_s": STUCK_ROOM_S},
        "logs": len(seats),
        "duels": [duels[k] for k in sorted(duels)],
        "seats": seats,
        "mechanics": {
            "required": sorted(n for n, req in MECHANICS.items() if req),
            "totals": totals, "seat_logs_using": per_seat_use,
            "never_used": sorted(n for n, v in totals.items() if v == 0 and MECHANICS[n]),
            "used_once": sorted(n for n, v in totals.items() if v == 1 and MECHANICS[n]),
            "per_seat_log_never": {s["file"]: sorted(n for n, v in s["mechanics"].items() if v == 0
                                                     and MECHANICS[n]) for s in seats},
            "per_seat_log_once": {s["file"]: sorted(n for n, v in s["mechanics"].items() if v == 1
                                                    and MECHANICS[n]) for s in seats},
        },
    }


def markdown(doc: dict) -> str:
    out = ["# Playtest telemetry summary", "",
           f"{doc['logs']} seat log(s). Thresholds (decision #83):"
           f"{doc['thresholds']['refused_run_min']} refused ticks in a row, "
           f"{doc['thresholds']['stuck_room_s']:g} s in one room.", "",
           "## Mechanics, all logs", "", "| mechanic | uses | seat logs using it |", "|---|---|---|"]
    m = doc["mechanics"]
    for name in MECHANICS:
        out.append(f"| {name} | {m['totals'][name]} | {m['seat_logs_using'][name]} |")
    out += ["", f"Never used: {', '.join(m['never_used']) or 'none'}.",
            f"Used once: {', '.join(m['used_once']) or 'none'}.", "", "## Duels", ""]
    for d in doc["duels"]:
        out.append(f"### {d['room']} duel {d['duel']}")
        out.append("")
        for seat, v in sorted(d["seats"].items()):
            q = v["quits"]
            flags = [k for k in ("duel_abandoned", "no_rematch", "no_duel_end") if q[k]]
            if q["forfeit"]:
                flags.append(f"forfeit ({q['forfeit']})")
            if q["disconnects"]:
                flags.append(f"{q['disconnects']} disconnect(s), {q['reconnects']} reconnect(s)")
            out.append(f"- Seat {seat}: result {v['result']}, reason {v['end_reason']}, "
                       f"{v['duration_s']:g} s. Quits: {', '.join(flags) or 'none'}.")
        out.append("")
    out += ["## Seats", ""]
    for s in doc["seats"]:
        st = s["stalls"]
        out.append(f"### {s['file']}")
        out.append("")
        out.append(f"- Idle: {st['idle_spells']} spell(s), {st['idle_total_s']:g} s in all"
                   + (f", {st['idle_unfinished']} unfinished" if st["idle_unfinished"] else "") + ".")
        runs = ", ".join(f"{r['action']} x{r['length']} from t={r['start_t']}"
                         for r in st["refused_runs"])
        out.append(f"- Refused runs: {runs or 'none'}.")
        out.append(f"- Longest time in one room: {st['longest_room_s']:g} s"
                   + (f"; stuck in {', '.join(st['stuck_rooms'])}" if st["stuck_rooms"] else "") + ".")
        used = ", ".join(f"{n} {v}" for n, v in s["mechanics"].items() if v) or "none"
        never = ", ".join(n for n, v in s["mechanics"].items() if v == 0 and MECHANICS[n]) or "none"
        once = ", ".join(n for n, v in s["mechanics"].items() if v == 1 and MECHANICS[n]) or "none"
        out.append(f"- Mechanics used: {used}. Never used: {never}. Used once: {once}.")
        if s["moves"]:
            out.append("- Moves started (a grace-cancelled direction dropped): "
                       + ", ".join(f"{n} {v}" for n, v in s["moves"].items()) + ".")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("directory", help="a directory of *.jsonl telemetry logs")
    ap.add_argument("--out", default=None, help="where to write summary.json and summary.md")
    args = ap.parse_args(argv)
    src = Path(args.directory)
    if not src.is_dir():
        print(f"error: {src} is not a directory", file=sys.stderr)
        return 2
    doc = summarize(src)
    out = Path(args.out) if args.out else src
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    (out / "summary.md").write_text(markdown(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
