"""Scan files for credentials before evidence is committed or published.

Usage (repository root):
    python3 -I tools/evidence/scan_secrets.py <path> [<path> ...]
    python3 -I tools/evidence/scan_secrets.py --known-sha256 <hex> <path> ...

Exit code 0: nothing found. Exit code 1: findings (printed as file:line:kind,
never the matched text). `--known-sha256` additionally looks for one specific
leaked value by hash, so the scanner never has to contain the secret itself;
it checks every UUID- and token-shaped word.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redact import findings  # noqa: E402

TEXT_EXT = {".md", ".json", ".jsonl", ".txt", ".ts", ".js", ".py", ".yml", ".yaml", ".toml", ".html", ".csv", ".svg"}
WORD = re.compile(r"[A-Za-z0-9_\-]{20,}")


def files(paths: list[str]):
    for p in paths:
        if os.path.isfile(p):
            yield p
        for root, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "dist", ".venv", "vendor", "__pycache__"}]
            for n in names:
                yield os.path.join(root, n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--known-sha256", action="append", default=[])
    a = ap.parse_args()
    known = {h.lower() for h in a.known_sha256}
    bad = 0
    scanned = 0
    for f in files(a.paths):
        ext = os.path.splitext(f)[1].lower()
        try:
            raw = open(f, "rb").read()
        except OSError:
            continue
        if ext not in TEXT_EXT:
            # Binary artefacts (video, images): search the bytes for the known value only.
            if known:
                for w in set(re.findall(rb"[A-Za-z0-9_\-]{20,}", raw)):
                    if hashlib.sha256(w).hexdigest() in known:
                        print(f"{f}:0:known-secret"); bad += 1
            continue
        scanned += 1
        text = raw.decode("utf-8", "replace")
        for kind, line in findings(text):
            print(f"{f}:{line}:{kind}"); bad += 1
        if known:
            for lineno, line in enumerate(text.splitlines(), 1):
                for w in WORD.findall(line):
                    if hashlib.sha256(w.encode()).hexdigest() in known:
                        print(f"{f}:{lineno}:known-secret"); bad += 1
    print(f"scanned {scanned} text files; {bad} finding(s)", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
