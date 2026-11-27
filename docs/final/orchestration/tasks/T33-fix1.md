# T33-fix1: presentation fixes from Gate 1 and the audit

- Assigned: tech-lead; then qa (Gate 1 re-check); Gate 3. Corrective attempt 1 of 2.
- Base: `task/T33` b64f58c. Branch `task/T33-fix1`. Permitted write paths: `presentation/**` (a `presentation/.gitignore` may un-ignore the one MP4) and the report.
- Findings to fix: `reports/T33-qa.md`@e90a0e2 (gate/T33-qa) F1–F4, F6, F7; `reports/T33-requirements-auditor.md`@c3ba2b0 (audit/T33) PARTIAL rows that are fixable.
  1. F1 blocker: the shipped .pptx must open in Keynote with its speaker notes and the embedded video (fix the notes master python-pptx writes, or post-process the package). Verify by opening it in Keynote via osascript and counting slides, notes and the movie object.
  2. F2: `render_replay.py` option bug and default start; the README rebuild command must work end to end.
  3. F3: track `out/xgjt-001-segment.mp4` (presentation-local un-ignore only; root `.gitignore` untouched).
  4. F4 wording on slide 3; F6 slide 6 Out list from SCOPE_LOCK in full, and fallbacks grouped by source; F7 audit wording; slide 3 footer must not say "48 trial rows"; slide 1 caption must not call a rehearsal still "a real game frame" unless it is labelled as rehearsal.
  5. Decision #138: speaker notes and NARRATION.md mark when to start the clip and what to say over it; slide 4 about 45 s; total near 4:30.
  6. Decision #136: keep "localhost only, not on two machines".
  7. Add `presentation/COVERAGE.md` from the auditor's matrix (copy, cite the source sha).
- Re-render slides and PDF; re-inspect every slide image.
