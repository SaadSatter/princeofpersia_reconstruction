# Saad's request: G2/G3 presentation (2026-11-27), verbatim

Pasted by Saad into the orchestrator session c612c020 as his whole message. Copied unchanged below. It is his specification for task T33.

---

# Shadow Masque — G2/G3 First Playable Presentation

Create a polished, presentation-ready PowerPoint for my G2/G3 recording for AI in Practice: Game Design and Development.

The presentation must be a maximum of **7 slides**, designed for a narrated recording lasting **3–5 minutes**, including gameplay demonstrations.

## 1. Source material and requirements

Use the current Shadow Masque repository as the primary source of evidence:

- Development repository: https://github.com/SaadSatter/shadow_masque
- Official repository: https://github.com/columbia-university-ai-games/final-saadsatter
- Official G2/G3 submission commit: `a251335`
- The submitted game snapshot, approved scope lock, Configuration Document, GDD, evaluation records, playtest kit, LOG.md, telemetry, agent configurations, orchestration reports and formal handoffs.

Read the actual documents and verify the evidence before constructing the presentation.

The recording requirements are:

- The core loop, played: act, respond, interpret, next action, with the in-game agent taking part.
- The agent's contribution and what the player would lose if the scripted baseline replaced it, supported by a trace or result.
- One external playtest, including observed behavior before interpretation and the resulting change or open question.
- Two tailored starter production agents and one genuine handoff, including my student decision.
- Deterministic tests passing in CI and budgeted live evaluation, including trials, outcomes, cost and failures.
- Scope lock, exclusions, and fallbacks with their triggers and actions.
- Acceptance checks for Alpha on December 2, Beta on December 4 and Gold on December 5.
- Explicit G2 and G3 approval requests and what would be required to resolve a Hold.

Do not invent results, evidence, approvals or gameplay behavior.

## 2. Presentation design

Use a cinematic, dark medieval palace theme consistent with Shadow Masque.

Use actual game screenshots, sprites, environments and interface elements wherever appropriate. Do not generate misleading mockups of gameplay.

Use large typography, minimal text, high contrast, consistent layouts and visual evidence. Avoid excessive animations and decorative elements.

The presentation should be understandable to someone who has never played Shadow Masque.

Include detailed speaker notes with a natural narration script and estimated timing for each slide. Target a total duration of 4 minutes and 30 seconds, including video playback and the live demo.

## 3. Slide structure

### Slide 1 — Shadow Masque

Target: 15 seconds.

Introduce the game as a competitive two-player stealth platformer where rival swordsmen disguise themselves as guards, manipulate the environment and attempt to eliminate one another.

Communicate the intended player experience: tension, deception, uncertainty and tactical combat.

Use an actual gameplay screenshot or existing title artwork.

Include my name and G2/G3 First Playable.

### Slide 2 — First Playable: Live Gameplay Demo

Target: 60 seconds.

Create a dedicated slide for transitioning into a live demonstration of the game.

Show a simple representation of the core loop:

Act → Game responds → Interpret → Next action.

Prepare a short demonstration sequence that lets me show:

- Movement through the palace.
- Fighting a scripted guard and taking its uniform.
- Disguise and suspicion.
- Encountering the PPO-controlled rival.
- Combat, evasion or trap usage.
- How the rival's actions influence my next decision.

The slide should contain a gameplay screenshot and a small number of visual cues, not detailed instructions.

Provide the exact command to launch the appropriate demo mode in the speaker notes. Select a reliable demonstration starting configuration using the existing game.

Do not modify gameplay rules or misrepresent a scripted demonstration as spontaneous AI behavior.

### Slide 3 — The AI Rival: Learned vs. Scripted

Target: 40 seconds.

Explain the difference between the trained PPO rival and the scripted baseline.

Use a compact architecture diagram showing:

Partial observation → PPO policy → Legal action → Game engine.

Explain what the learned rival contributes to the player experience and what could be lost with the scripted baseline.

Support the comparison with actual evaluation evidence. Distinguish observed capabilities from hypotheses about player experience.

Include the held-out T09 result:

- 16 trials.
- 13 wins, 2 draws, 1 loss.
- Pre-registered success threshold: 14 wins.
- Conclusion: NOT SUPPORTED.

Verify these numbers against the evaluation record before including them.

Explain that the rival demonstrates strong capabilities but did not meet the pre-registered evaluation threshold.

Include actual evaluation cost, relevant failures and trial counts from the records. Do not confuse local PPO inference or training with paid LLM evaluation.

### Slide 4 — External Playtest: Human vs. AI

Target: 45 seconds, including a short video.

Use the actual external Human vs. AI playtest documented in LOG.md.

My observations were:

- The human player was able to identify the AI rival.
- The AI was also able to locate the human player.
- The AI was skilled at disarming opponents and executing consecutive attacks.
- The AI was effective at defeating scripted guards.
- The human player struggled to stop or counter the AI.

My interpretation was that the PPO rival demonstrates strong combat abilities, but its disarming and attack sequences may create a combat balance issue. Further testing should investigate whether effective counterstrategies exist.

Present observations before interpretation.

Include the open design question:

Can human players develop effective counterstrategies against the trained rival, or does combat need balancing?

Reconstruct a short gameplay video from the actual Human vs. AI playtest telemetry.

#### Video reconstruction requirements

First inspect the telemetry for rooms XGJT and XUKM, LOG.md, the replay infrastructure and the corresponding game configuration.

Identify which room and duel correspond to the documented external Human vs. AI playtest.

Determine whether the telemetry contains sufficient information to reconstruct the original gameplay accurately, including initial state, seed, inputs, timing, AI actions and relevant game events.

If deterministic reconstruction is possible:

- Use the matching game version and configuration.
- Replay the recorded actions.
- Verify reconstructed events against the telemetry.
- Render the replay using the actual game assets and renderer.
- Select a representative 20–25-second segment.
- Prefer a segment showing the rival's combat behavior, disarming, attack sequences or an encounter with a guard, if those events are supported by the recording.
- Add a small label: "External playtest — reconstructed from telemetry."
- Export an MP4 and embed it directly into the PowerPoint slide.

If only partial reconstruction is possible:

- Clearly label the result as a partial reconstruction or telemetry-based visualization.
- Explain which events are directly supported and which cannot be recovered.
- Do not invent missing AI actions or player movements.
- Do not present a newly simulated match as the original external playtest.

If reconstruction is not possible, use a visualization of the actual recorded telemetry and separately identify any illustrative gameplay footage as a new demonstration.

Verify participant consent and publication permissions before embedding or publishing any playtest material. Do not expose personal information or raw private telemetry.

### Slide 5 — Production Agent Team

Target: 40 seconds.

Show the actual production architecture:

Student — Executive Producer / Creative Director
→ Opus Orchestrator
→ Sonnet Tech Lead, QA and supporting specialists.

Distinguish the two formal course production agents from supporting orchestration workers and the in-game PPO rival.

Show the responsibilities of the two formal agents:

- Tech Lead: implementation, engine, agent interface, builds and technical evidence.
- QA: independent verification, reproducible failures, regression testing and observation-boundary checks.

Use the actual T02 QA-to-Tech handoff as the example.

Show the chain:

QA identifies disguise-motion leak
→ Student approves correction
→ Tech Lead implements fixes
→ QA independently verifies
→ Student accepts.

Include the specific design issue: a disguised player waiting could be distinguished from a paused scripted guard because of unintended motion metadata.

Show the relevant student decisions, including hopping raising suspicion and the approved treatment of disguised movement.

Include the actual closing evidence: 650 passed, 12 skipped and 2 unrelated expected failures, subject to verification against the handoff.

Include short commit references or GitHub links as evidence.

### Slide 6 — Verification and Scope Lock

Target: 40 seconds.

Summarize the latest verified deterministic test results and show evidence of green CI from the development repository.

Clearly disclose that the official repository's CI was queued on the course runner at submission time if that is still its status. Do not imply that official CI passed unless it actually did.

Present the approved scope lock using three compact sections:

**In scope**
- Competitive duel, disguise, suspicion and scripted guards.
- Six-room arena and five-minute matches.
- Loose-floor traps.
- Trained PPO rival and scripted baseline.
- Approved playable modes and deployment targets.

**Excluded or deferred**
- Use the actual approved scope lock.
- Distinguish permanently excluded features from improvements deferred pending evidence.

**Fallbacks**
- Extract each approved fallback from the scope lock.
- Show its trigger and corresponding action.
- Do not omit fallbacks or invent new commitments.

Include important limitations, particularly the evaluation threshold not being met and the limitations of online multiplayer testing.

### Slide 7 — Road to Gold and Approval Requested

Target: 30 seconds.

Create a concise timeline:

- Alpha — Wednesday, December 2.
- Beta — Friday, December 4.
- Gold — Saturday, December 5.

Each milestone must include a concrete, observable acceptance check drawn from the approved production plan and scope lock.

If acceptance checks are missing, propose them for my approval rather than representing them as previously approved.

End with explicit decision requests:

**G2 approval:** Accept the integrated first playable and its current agent implementation and authorize progression into production.

**G3 approval:** Accept the proposed scope, exclusions, fallbacks and milestone acceptance checks.

**Hold:** Identify the unresolved blocker, missing evidence or failed acceptance criterion that must be addressed before approval.

Include the official repository link.

## 4. Production workflow

Use the existing orchestrator and native production agents.

The orchestrator should coordinate the presentation work, delegate appropriate evidence collection and verification tasks, and maintain Git-tracked handoffs.

- Tech Lead: inspect replay capabilities, reconstruct the playtest video if feasible, prepare the demonstration and assemble presentation artifacts.
- Evaluation Specialist: verify the PPO results, evaluation methodology, trial counts, costs and limitations.
- QA: independently verify the video reconstruction, factual claims, slide contents, playback and presentation timing.
- Requirements Auditor: map every recording requirement to the slide or speaker notes that satisfies it.

Do not create unnecessary new formal production roles for this task.

Keep the work isolated from the graded game snapshot. Do not change gameplay or merge anything into the official repository without my approval.

## 5. Deliverables

Produce:

1. An editable PowerPoint file, maximum seven slides.
2. A PDF version of the slides.
3. The reconstructed external playtest MP4, or a clearly labeled alternative if accurate reconstruction is impossible.
4. Embedded video playback in the PowerPoint.
5. Speaker notes and a standalone narration script with timestamps.
6. A short live demo runbook with exact launch commands, demonstration steps and a fallback if the live demo fails.
7. A recording-requirements coverage checklist.
8. A QA report verifying evidence accuracy, video provenance, slide readability, playback and total presentation duration.

Keep the editable presentation source and generation scripts in a dedicated presentation directory.

Before handing it back, render every slide and inspect it for clipping, readability and visual consistency. Test video playback where supported and report any environment limitations.

Do not record my final narrated presentation on my behalf. Prepare everything so that I can record it myself in one continuous 3–5-minute session.

Begin by auditing the available evidence and determining whether the external playtest can be accurately reconstructed. Then proceed with presentation production and independent QA. Escalate only decisions that require my approval.
