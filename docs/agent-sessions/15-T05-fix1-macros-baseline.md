# Session 15: T05-fix1 (macro reachability and baseline fixes)

Tech Lead worker (Sonnet 5.5), branch `task/T05-fix1` from `0846a16`. Brief: `docs/final/orchestration/tasks/T05-fix1.md`.

- Read: the brief, Gate 2 and Gate 1 findings, `agents/macros.py`, `agents/versus_baseline.py`, `agents/baseline.py`, `pop/engine.py` (fall, hang, climb), `pop/guards.py`, `docs/final/VERSUS_SPEC.md` sections 3 and 4.
- Reused ideas from the untested WIP snapshot `ab78522` (vertical `FieldView`, hang and drop, blind shaft search, `no_uniform` result), then fixed what traces showed: a stale `to` after a wait, an input queued while a move left the room (hop turned into a flip), shaft climbs that depend on facing, a lunge queued too late after a sweep, FLEE from an unarmed rival.
- No engine change. No paid calls. No training.
- Result lines and competence numbers: `docs/final/orchestration/reports/T05-fix1-tech-lead.md`.
