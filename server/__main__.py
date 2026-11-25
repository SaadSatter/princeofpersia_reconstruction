"""python -m server [--host 0.0.0.0] [--port N] [--seed N] [--rival baseline]

Run with `uv run --extra online python -m server`. Prints the LAN URL.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def lan_ip() -> str:
    """The address other machines on the Wi-Fi would use (no packet is sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def trace_name(code: str, n: int, seed: int) -> str:
    """The input trace's file name: the room's code keeps rooms' traces apart (T18)."""
    return f"duel-{code}-{n:03d}-seed{seed}.json"


async def serve_forever(args) -> None:
    from tools.web import build
    from .app import OnlineServer
    from .match import Match

    trace_dir = Path(args.trace_dir) if args.trace_dir else None
    count = [0]

    def make_match(code: str) -> Match:
        """One fresh `Match` per room; its trace file name carries the room's code."""
        def write_trace(trace: dict) -> None:
            if trace["fallbacks"]:
                print(f"Room {code}, AI seat B: {len(trace['fallbacks'])} fallback(s) this duel "
                      f"(source: fallback), see the trace", flush=True)
            if trace_dir is None:
                return
            trace_dir.mkdir(parents=True, exist_ok=True)
            count[0] += 1
            path = trace_dir / trace_name(code, count[0], trace["seed"])
            path.write_text(json.dumps(trace, separators=(",", ":")))

        return Match(seed=args.seed, rival=None if args.rival == "none" else args.rival,
                     on_finish=write_trace, neutral=args.neutral)

    with tempfile.TemporaryDirectory() as site:
        manifest = build.build(Path(site))
        # The code-less default room (decision #56): a join with no code enters it.
        srv = OnlineServer(make_match("HOME"), site_dir=Path(site), match_factory=make_match)
        server = await srv.start(args.host, args.port)
        port = server.sockets[0].getsockname()[1]
        print(f"Shadow Masque online, build {manifest['build']}", flush=True)
        print(f"Players open:  http://{lan_ip()}:{port}/", flush=True)
        print(f"This machine:  http://127.0.0.1:{port}/", flush=True)
        print("The page loads Phaser from a CDN: every player needs internet. Ctrl-C stops.")
        await srv.run_ticks()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m server", description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rival", choices=("none", "baseline"), default="none",
                    help="baseline: the server plays seat B (one human can test alone)")
    ap.add_argument("--neutral", action="store_true",
                    help="with --rival baseline, label the AI seat just \"Rival\" (blind playtests)")
    ap.add_argument("--trace-dir", default="traces/online",
                    help="where each finished duel's input trace is written (server only)")
    args = ap.parse_args(argv)
    try:
        asyncio.run(serve_forever(args))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
