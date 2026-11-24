# Shadow Masque playtest log

> **Proposal for Saad (answers CQ-6, "Playtest log format").** Drafted by the
> Evaluation Specialist subagent for task T11; not approved. Saad decides the
> format, writes or approves the hypotheses, and writes every interpretation.
> No session has been run: every table below is empty on purpose.

This log is the course's playtest log (FINAL_REQUIREMENTS section 5,
[R]: hypotheses, consent, anonymous observations before interpretation,
build/config versions, changes, verification and future recommendations).
It is started for G2/G3 ("Initial Playtest Log") and updated at G4 and G5.
Materials: [`CONSENT.md`](CONSENT.md), [`PROTOCOL.md`](PROTOCOL.md),
[`QUESTIONNAIRE.md`](QUESTIONNAIRE.md),
[`OBSERVATION_TEMPLATE.md`](OBSERVATION_TEMPLATE.md). Raw sheets go in
`sessions/`, one file per session.

**Authorship.** Each section says who may write it. Agents may copy facts
(commits, counts from sheets and traces) into the factual sections and must
say so. Only Saad writes section 6 (interpretation) and decisions; nothing is
written in his voice by anyone else.

---

## 1. Hypotheses (written and committed before the first session)

Written by: Saad · Commit that froze them: ______ · Date: ______

Drafts for Saad to accept, change or reject (from the G1 configuration A7
and the GDD section 2 motivations; the AI rival is now the trained PPO
policy, decision of 2026-11-23 #3):

| Id | Hypothesis (draft) | Session | Measure (PROTOCOL section 3) |
|---|---|---|---|
| H1 | Players misidentify the disguised policy rival more often than the disguised scripted rival | B | Missed + false identifications per condition |
| H2 | Players rate rounds against the policy rival as more tense (1–7) than rounds against the scripted rival | B | R1 |
| H3 | Players can follow the core loop (take a uniform, blend, strike or trap, reveal) without help after one round | A | Sheet: UNI, RS/GS, STUCK, Q |
| M1 | Competition: a player asks for a rematch within 30 s of a round | A, B | `R30` |
| M2 | Mastery: after a loss, the player tries a different approach | A, B | `CA`, E1 |
| M3 | Thrill: at least one spoken reveal reaction per round with an encounter | A, B | `RV` |

The rival does not need to win, and no hypothesis needs to be confirmed.

## 2. Build and configuration per session

| Session | Build commit (full sha) | Launch command | Time limit (frames) | Baseline version | Policy weights hash | Seeds | Other config |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Condition-code mapping for Session B (X/Y to rival type): sealed until the
tallies in section 5 are written; then recorded here with who sealed it.

| Sealed by (role) | Date sealed | Date opened | X = | Y = |
|---|---|---|---|---|
| | | | | |

## 3. Sessions and consent

| Session | Date | Gate | Type (A1/A2/R/B) | Player code(s) | External? | Consent read (time, by role) | Recording | Notes publishable | Completed / stopped at |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

**Distinct external players across G2–G4** (course requires at least two):

| Player code | First session | Later sessions | External |
|---|---|---|---|
| | | | |

## 4. Observations (before interpretation)

Written by: the observer (sheets), copied unchanged. One row per session
linking the sheet; key observations quoted from it, each with round and time.

| Session | Sheet | Key observations (verbatim from the sheet, with round and time) |
|---|---|---|
| | `sessions/` | |

## 5. Tallies

Written by: whoever counts (agent or Saad), naming themselves; every number
traceable to a sheet row or trace.

| Session | Round | Condition | Opportunities (decoy/solo) | Correct id | Missed | False id | Guard strikes, other intent | Unknown intent | Tension R1 | Fairness R4 | R30 (s) | CA | RV | Outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | | |

No-encounter rounds are listed with zero opportunities, not dropped.

## 6. Interpretation

Written by: Saad · Date: ______

(What the observations mean for each hypothesis; cite section 4 and 5 rows.)

## 7. Changes made because of playtests

| Finding (section 4/6 reference) | Decision (Saad, date) | Change | Commit / PR | Task |
|---|---|---|---|---|
| | | | | |

## 8. Verification of changes

| Change | How verified (test, trace, re-playtest session) | Evidence (commit, test output, session id) | Result |
|---|---|---|---|
| | | | |

## 9. Future recommendations

| Recommendation | Source (row) | For (gate or after the course) |
|---|---|---|
| | | |

## 10. Protocol versions

| Version | Date | Change | Approved by Saad (date) | Sessions run under it |
|---|---|---|---|---|
| 0 (draft, T11) | 2026-11-23 | Initial kit | not yet | none |
