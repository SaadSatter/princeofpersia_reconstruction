"""A time limit for the server's own rival seat (T13; GATE-wave3 QA finding on `SeatControllerRival`).

`web/bridge.py` calls its rival hook synchronously with no limit. On the
server that would stall the 12 Hz loop for the human too. This wrapper runs
the hook on one daemon worker thread and waits at most `budget_s` (well under
one tick, 1/12 s). A slower answer is replaced by "no input" (WAIT) for that
tick, counted (server trace and log only, never the client's label), and is dropped when it arrives, so a
stale action is never applied. While an answer is still pending no new
question is asked. The seat still sees only its own observation and legal
list. The trace records the inputs actually applied, so replays stay exact.
"""

from __future__ import annotations

import queue
import threading

DEFAULT_BUDGET_S = 0.04


class TimeLimitedRival:
    def __init__(self, inner, budget_s: float = DEFAULT_BUDGET_S):
        self.inner = inner
        self.budget_s = budget_s
        self.slow = 0                              # answers replaced by WAIT
        self._jobs: queue.Queue = queue.Queue()
        self._busy = threading.Event()             # set while the worker holds a question
        threading.Thread(target=self._work, daemon=True).start()

    @property
    def label(self) -> str:
        """Static: the bridge's label counts fallbacks, and those stay on the server
        (they go to the trace and the log, never to the human's client)."""
        c = getattr(self.inner, "controller", None)
        if c is None:
            return getattr(self.inner, "label", "AI rival")
        return f"AI rival: {getattr(c, 'name', 'controller')} ({getattr(c, 'kind', 'unknown')})"

    def reset(self, seed: int) -> None:
        """Take effect even while the worker is busy: queued behind the running question,
        so it runs before any later question (the late answer is dropped anyway)."""
        if not hasattr(self.inner, "reset"):
            return
        if self._busy.is_set():
            self._jobs.put(("reset", seed))
        else:
            self.inner.reset(seed)

    def close(self) -> None:
        """Stop the worker thread (a sentinel); safe to call twice."""
        self._jobs.put(None)

    def _work(self) -> None:
        while True:
            job = self._jobs.get()
            if job is None:
                return
            if job[0] == "reset":
                try:
                    self.inner.reset(job[1])
                except Exception:
                    pass
                continue
            obs, legal, box, done = job
            try:
                box.append(self.inner(obs, legal))
            except Exception:
                box.append(None)
            finally:
                self._busy.clear()
                done.set()

    def __call__(self, observation: dict, legal: list[str]):
        if self._busy.is_set():                    # still thinking about an older question
            self.slow += 1
            return None
        box: list = []
        done = threading.Event()
        self._busy.set()
        self._jobs.put((observation, legal, box, done))
        if done.wait(self.budget_s):
            return box[0] if box else None
        self.slow += 1
        return None                                # WAIT; the late answer is dropped
