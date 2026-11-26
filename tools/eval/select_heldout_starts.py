"""The written selection rule for H6-5 to H6-8 (decision #74), as code.

    python3 tools/eval/select_heldout_starts.py                 # print the new starts as JSON
    python3 tools/eval/select_heldout_starts.py --write PATH    # H6-1..4 of the current file + new starts

The rule is in docs/final/evaluation/PROTOCOL.md section 3.1 and was committed
before this file existed. It reads only the arena map and the lists of cells and
guard posts already in use. It never reads a policy, a baseline or any run data,
and no start may be kept or dropped for how a controller plays it. Candidates are
ordered by a SHA-256 of their coordinates, so the choice is fixed, unbiased and
reproducible by anyone. The test `tests/test_eval_t08fix1_h6.py` regenerates the
frozen starts from H6-1 to H6-4 and compares them.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from evaluation import manifest, spec  # noqa: E402
from pop import arena  # noqa: E402
from tools.rl.env import TUNING_STARTS  # noqa: E402

ROOMS = range(1, 7)
ROW = 2
SPAN_WIDTHS = (2, 3, 4)          # columns a patrol covers
FIRST_NEW = 5


def h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def used_cells(base_starts: list[dict]) -> set[tuple[int, int, int]]:
    cells = {tuple(s[:3]) for pair in TUNING_STARTS for s in pair}
    cells |= {tuple(v[:3]) for v in arena.STARTS.values()}
    for sc in manifest.load_tuning().values():
        for st in sc.starts:
            cells |= {tuple(r[:3]) for r in st.rivals.values()}
    for st in base_starts:
        cells |= {tuple(r[:3]) for r in st["rivals"].values()}
    return cells


def used_posts(base_starts: list[dict]) -> set[tuple[int, int, tuple[int, int]]]:
    posts = {(g[0], g[1], tuple(g[2])) for g in arena.GUARD_POSTS.values()}
    for sc in manifest.load_tuning().values():
        for st in sc.starts:
            posts |= {(g[0], g[1], g[2]) for g in st.guards.values()}
    for st in base_starts:
        posts |= {(g[0], g[1], tuple(g[2])) for g in st["guards"].values()}
    return posts


def cell_candidates(used: set) -> list[tuple[int, int, int]]:
    free = [(r, ROW, c) for r in ROOMS for c in range(10)
            if spec._floor_ok(r, ROW, c) and (r, ROW, c) not in used]
    return sorted(free, key=lambda x: h("h6x|cell|%d|%d|%d" % x))


def post_candidates(posts: set) -> list[tuple[int, int, tuple[int, int]]]:
    found = []
    for r in ROOMS:
        for w in SPAN_WIDTHS:
            for c0 in range(10 - w + 1):
                c1 = c0 + w - 1
                if all(spec._floor_ok(r, ROW, c) for c in range(c0, c1 + 1)) \
                        and (r, ROW, (c0, c1)) not in posts:
                    found.append((r, ROW, (c0, c1)))
    return sorted(found, key=lambda p: h("h6x|post|%d|%d|%d" % (p[0], p[2][0], p[2][1])))


def face_for_column(col: int) -> int:
    return 1 if col <= 4 else -1


def face_for_post(room: int, c0: int, c1: int) -> int:
    return 1 if int(h("h6x|face|%d|%d|%d" % (room, c0, c1))[:2], 16) % 2 == 0 else -1


def select_extra_starts(base_starts: list[dict], n: int = 4) -> list[dict]:
    """The `n` new starts H6-5, H6-6, ... that follow from the rule and `base_starts`."""
    used = used_cells(base_starts)
    posts = used_posts(base_starts)
    cells = cell_candidates(used)
    taken: set = set()
    out = []
    for k in range(FIRST_NEW, FIRST_NEW + n):
        a = next(c for c in cells if c not in taken)
        taken.add(a)
        b = next(c for c in cells if c not in taken and c[0] != a[0])
        taken.add(b)
        rivals = {"A": [a[0], a[1], a[2], face_for_column(a[2])],
                  "B": [b[0], b[1], b[2], face_for_column(b[2])]}
        own = (a, b)
        usable = [p for p in post_candidates(posts) if p not in posts and not any(
            p[0] == cell[0] and p[1] == cell[1] and p[2][0] <= cell[2] <= p[2][1] for cell in own)]
        g1 = usable[0]
        g2 = next(p for p in usable if p[0] != g1[0])
        posts |= {g1, g2}
        guards = {f"h6{k}-g1": [g1[0], g1[1], [g1[2][0], g1[2][1]], face_for_post(g1[0], *g1[2])],
                  f"h6{k}-g2": [g2[0], g2[1], [g2[2][0], g2[2][1]], face_for_post(g2[0], *g2[2])]}
        out.append({"id": f"H6-{k}", "rivals": rivals, "hearts": {"A": 3, "B": 3},
                    "disguised": {"A": False, "B": False}, "guards": guards})
    # step 4 of the rule: fail rather than adjust
    assert not ({tuple(r[:3]) for s in out for r in s["rivals"].values()} & used)
    return out


def extend_heldout(data: dict, n: int = 4) -> dict:
    """`data` is a parsed H6 file holding H6-1 to H6-4; returns it with the new starts added."""
    scenario = data["scenarios"][0]
    base = scenario["starts"][:FIRST_NEW - 1]
    scenario["starts"] = base + select_extra_starts(base, n)
    return data


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--write" in argv:
        path = Path(argv[argv.index("--write") + 1])
        data = json.loads(manifest.HELDOUT_PATH.read_text())     # only H6-1..4 are used
        path.write_text(json.dumps(extend_heldout(data), indent=1) + "\n")
        print(f"wrote {path}")
        return 0
    base = json.loads(manifest.HELDOUT_PATH.read_text())["scenarios"][0]["starts"][:FIRST_NEW - 1]
    print(json.dumps(select_extra_starts(base), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
