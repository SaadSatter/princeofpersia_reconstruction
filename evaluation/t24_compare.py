"""T24 Gate 2: like t19_compare, but also counts DOWN-takes (the T24 path) in every duel.

Run from a project root (the post-T24 tree or an extracted 1a515ca tree), tuning starts only:
    PYTHONPATH=. python evaluation/t24_compare.py ppo|mirror SEEDS vary > out.json
`down_takes` is the number of times a DOWN input became a uniform take (always 0 on the
base engine, which has no such path). Macro rivals never press DOWN over a body on purpose,
so any non-zero count is an unintended disguise.
"""
from __future__ import annotations

import json
import sys
import time

from pop import versus
from evaluation import t19_compare

COUNT = {"down_takes": 0, "down_sword": 0}
if hasattr(versus.Rival, "_kneel_target"):
    _orig = versus.Rival._kneel

    def _counting(self):
        which = self._kneel_target()
        COUNT["down_takes" if which == "uniform" else "down_sword"] += 1
        return _orig(self)

    versus.Rival._kneel = _counting

if __name__ == "__main__":
    t = time.time()
    res = t19_compare.run(sys.argv[1], int(sys.argv[2]))
    res.update(COUNT)
    res["has_kneel_path"] = hasattr(versus.Rival, "_kneel_target")
    res["wall_s"] = round(time.time() - t, 1)
    print(json.dumps(res))
