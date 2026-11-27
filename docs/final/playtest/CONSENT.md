# Playtest consent script

**Status:** Approved by Saad 2026-11-27 (decision #126); frozen from this date — a change is a new version (kit drafted in T11).
Read it aloud, word for word, before any play. The player may ask questions
at any point. Nothing in this kit is filled in: no session has been run.

---

## Text to read aloud

> Thank you for helping. This is a playtest of *Shadow Masque*, a game being
> made for a class project (AI in Practice: Game Design and Development,
> Columbia). It is not a test of you. If something is confusing or feels
> unfair, that is the game's problem, and it is exactly what we want to find.
>
> **What you will do.** You will play a few short rounds, each at most five
> minutes, against a rival. After each round I will ask you a few quick
> questions. At the end I will ask a few more. The whole session takes about
> twenty minutes.
>
> **Anonymous.** I will not write down your name, email or anything else that
> identifies you. You get a player code, like P03, on this card. Keep it: if
> you play in a later session, tell me the code so we know you are the same
> person, without your name.
>
> **You can stop at any time**, for any reason, without explaining. You can
> also skip any question. If you stop, I will ask whether we may keep the
> notes from the part you played; if you say no, I delete them.
>
> **What is recorded.**
> - [READ ONE OF THESE TWO, as marked on the observation sheet header.]
>   **(a)** The game itself does not save anything about the round. Only my
>   written notes and your answers are kept.
>   **(b)** The game saves a file for each round: the keys you pressed as game
>   actions, where the characters were, and what happened in the game. It
>   contains no name and no audio or video. The file lists each game action you take,
>   which room you are in, when you are hurt, when you pause or leave, and how the round
>   ended, with the time of each. It does not contain your name, any address or anything
>   about the other player that your own screen did not show you.
> - I take written notes of what happens on screen and of things you say
>   while playing, word for word when I can, without your name.
> - Your answers to the questions.
>
> **No video or audio recording unless you agree.** I will ask you
> separately now. Saying no changes nothing about the session.
>
> **Where it goes.** The anonymous notes, answers and, if option (b) was read, the round
> files may be put in
> the project's repository and in course reports, which other students,
> course staff and, if the repository is public, anyone can read. Nothing in
> them names you.
>
> **About the rivals.** You will be playing against computer-controlled
> rivals. I will not tell you how each one works until the end, because that
> could change how you play. At the end I will explain everything and answer
> any question.
>
> Do you have any questions? Are you happy to take part?

## Telemetry sentence for option (b)

Approved by Saad 2026-11-27 (decision #126). The sentence is in the read-aloud text
above, at the end of option (b). Source: `docs/final/playtest/TELEMETRY.md`, "Draft for
CONSENT.md" (drafted in T20), moved in unchanged.

## Answers to record (on the observation sheet header, not here)

| Question | Recorded as |
|---|---|
| Round file saved by the build (selects which "What is recorded" option is read) | (a) none: notes and answers only / (b) per-round trace file. Choose (b) only if the facilitator has seen the build write the file (see "Logging rule" below); otherwise (a) |
| Agrees to take part | yes / no (if no, stop; record nothing else) |
| Screen recording | yes / no |
| Audio recording | yes / no |
| Notes may be published anonymously | yes / no (if no: notes stay off the repository; only counts are reported) |
| Has played *Shadow Masque* before (player code if so) | code or "no" |
| Is the player external (not Saad, not on the project, not an agent) | yes / no (facilitator judges; external players count toward the course requirement) |

The facilitator records that the text was read, and by whom (role, not
name), next to the time. The player's own words of agreement are not needed
in writing.

## Logging rule

The consent text must describe exactly what the build used records.

- Do not read option (b) unless the build is known to write a per-round trace
  file. As of this kit, that is **not verified**: the local bench
  (`play.py --versus`) keeps its event log in memory only and writes no file,
  and the per-round trace download in the hosted web build is planned (T14)
  but not yet verified. Until someone has run the build and seen the file,
  read option (a).
- If the build later changes between sessions, the facilitator re-checks and
  records the option on that session's sheet. A player who heard (a) is never
  logged; a file saved after (a) was read is deleted unread and the event
  recorded as a finding.
- The kit never claims a log exists; the sheet's "Round file" column holds
  the actual file name or "none".

## Variant for session (a), human vs human

When two people play each other on the two-panel bench (see
[`PROTOCOL.md`](PROTOCOL.md), session A), replace "About the rivals" with:

> **About the rivals.** You will play against each other. Each of you has
> your own half of the screen. Please look only at your own half.

Both players hear the text and each gets their own code.

## Debrief text (read at the end of every session)

> Thank you. Here is what we were testing: [one sentence from the
> hypotheses in `LOG.md`, read by the facilitator]. In the comparative
> session, one rival was a simple scripted program and the other was a small
> model trained by the project. We wanted to see whether you could tell them
> apart and whether one felt more tense. Do you have any questions? You can
> still ask us to remove your notes.

## Open choices for Saad

- Whether the repository the notes go into is public; the "Where it goes"
  paragraph must match the answer.
- Whether any audio or video recording is wanted at all. If not, remove the
  recording questions.
- Whether to require players to be 18 or older, and to ask.
