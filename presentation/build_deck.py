"""Build the G2/G3 First Playable deck (7 slides) and the narration script.

    uv run --with python-pptx python presentation/build_deck.py

Writes presentation/out/ShadowMasque-G2G3.pptx and presentation/NARRATION.md.
Facts on every slide come from committed records; each is cited in the speaker notes
and the narration. Saad's own words (LOG.md, the Student decision) are quoted
verbatim and labelled; nothing here is written in his voice.
"""

from __future__ import annotations


import os
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "shots"
OUT = ROOT / "out"

BG = RGBColor(0x0C, 0x0D, 0x12)
PANEL = RGBColor(0x1A, 0x1C, 0x27)
STONE = RGBColor(0x2C, 0x30, 0x40)
GOLD = RGBColor(0xE8, 0xC4, 0x60)
PARCH = RGBColor(0xF0, 0xE8, 0xCC)
DIM = RGBColor(0xB4, 0xB6, 0xC2)
CRIMSON = RGBColor(0xD4, 0x4A, 0x4A)
INDIGO = RGBColor(0x8A, 0x98, 0xF0)
GREEN = RGBColor(0x6F, 0xC2, 0x8A)
SERIF = "Georgia"
SANS = "Helvetica Neue"

REPO = "https://github.com/columbia-university-ai-games/final-saadsatter"
_sf = Path(__file__).resolve().parent / "SUITE_RESULT.txt"
SUITE_LINE = _sf.read_text().strip().splitlines()[-1] if _sf.exists() else "pending"
PLAY_CMD = "uv run --extra play python play.py ARENA --mode ai --seed 0 --scale 3"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
NARRATION: list[tuple[str, str, str]] = []     # (title, timing, script)


def new_slide(title: str, kicker: str = "") -> object:
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    bar.fill.solid(); bar.fill.fore_color.rgb = GOLD; bar.line.fill.background()
    text(s, 0.55, 0.25, 12.2, 0.8, title, 34, GOLD, font=SERIF, bold=True)
    if kicker:
        text(s, 0.55, 0.98, 12.2, 0.4, kicker, 16, DIM)
    return s


def text(s, x, y, w, h, content, size=18, color=PARCH, font=SANS, bold=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """`content` is a string or a list of strings / (string, {opts}) paragraphs."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    paras = [content] if isinstance(content, (str, tuple)) else content
    for i, p in enumerate(paras):
        opts = {}
        if isinstance(p, tuple):
            p, opts = p
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = opts.get("align", align)
        para.space_after = Pt(opts.get("after", 3))
        r = para.add_run()
        r.text = p
        r.font.size = Pt(opts.get("size", size))
        r.font.bold = opts.get("bold", bold)
        r.font.italic = opts.get("italic", False)
        r.font.name = opts.get("font", font)
        r.font.color.rgb = opts.get("color", color)
    return tb


def box(s, x, y, w, h, fill=PANEL, line=STONE, lw=1.5, shape=MSO_SHAPE.RECTANGLE):
    b = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    b.fill.solid(); b.fill.fore_color.rgb = fill
    if line is None:
        b.line.fill.background()
    else:
        b.line.color.rgb = line; b.line.width = Pt(lw)
    b.shadow.inherit = False
    return b


def labelled(s, x, y, w, h, label, content, size=15, accent=GOLD, fill=PANEL):
    box(s, x, y, w, h, fill=fill, line=accent)
    text(s, x + 0.12, y + 0.06, w - 0.24, 0.35, label, 13, accent, bold=True)
    text(s, x + 0.12, y + 0.4, w - 0.24, h - 0.45, content, size)


def arrow(s, x, y, w=0.45, h=0.4, color=GOLD):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = color; a.line.fill.background()


def down_arrow(s, x, y, w=0.4, h=0.3, color=GOLD):
    a = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = color; a.line.fill.background()


def picture(s, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    p = s.shapes.add_picture(str(SHOTS / name), Inches(x), Inches(y), **kw)
    p.line.color.rgb = STONE; p.line.width = Pt(1.5)
    return p


# Narration, trimmed to each slide's time slot at about 150 words a minute (the live demo and the
# video play without speech). Overrides the longer draft passed to notes().
SCRIPT = {
    "Shadow Masque":
        "This is Shadow Masque, a two-player stealth platformer. Rival swordsmen disguise themselves as "
        "guards, set traps, and try to eliminate each other. Is that figure a guard, or my rival? "
        "I'm Saad Satter, and this is the G2/G3 first playable.",
    "First Playable: live demo":
        "Now the game itself. The loop is: I act, the game responds, I interpret, and I choose my next action. "
        "I move into the Barracks, draw my sword, defeat a scripted guard and take its uniform. Now I'm "
        "disguised, and acting oddly raises the guard's suspicion. Then I look for the rival, the trained PPO "
        "policy. Whatever it does decides what I do next. I'm playing this live, so its moves are its own.",
    "The AI rival: learned vs scripted":
        "The rival is a small PPO policy we trained. It sees only its own partial observation, picks a legal "
        "macro action, and the one game engine runs it. Held out against the scripted baseline: 16 duels, 13 "
        "wins, 2 draws, 1 loss. We pre-registered 14 wins, so the verdict is not supported. That means the "
        "improvement wasn't shown at that bar, not that the rival is weak. Three trials of each duel were "
        "identical, so the real sample is about eight starts. How players experience it, harder to read, more "
        "tense, is untested. Training took 80 minutes on a local CPU, with no API cost.",
    "External playtest: Human vs AI":
        "SAY BEFORE PLAYING (about 9 s): One external player, one duel against the trained rival. The clip is "
        "replayed from the logged inputs.\n"
        "[CLICK PLAY NOW. The clip runs 22 s. Say over it, about 20 s:] This is the player's view. Three hits "
        "land on the player. The rival wins, two hearts to none. The only dropped sword is the player's own "
        "throw. A guard goes down at frame 327; the log does not say who did it.\n"
        "[CLIP ENDS. Say after it, about 15 s:] My observer notes, in my own words, are on the right. The replay "
        "supports strong combat, not every item in them. My open question: can players develop "
        "counterstrategies, or does combat need balancing?",
    "Production agent team":
        "I'm the Student and Creative Director. An Opus orchestrator routes work to Sonnet agents. Two are the "
        "formal course agents: the Tech Lead builds and the QA agent verifies independently. The others are "
        "supporting workers, and the PPO rival is a game feature, not a production agent. Our real handoff, "
        "T02: QA found that a disguised player who waited could be told apart from a paused guard, through "
        "unintended motion data. I approved the fix, including hops raising suspicion. The Tech Lead fixed "
        "it, QA verified, 650 passed, 12 skipped, 2 unrelated expected failures, and I accepted it.",
    "Verification and scope lock":
        "Our deterministic suite passes and development CI is green. The official repository's CI run was still "
        "queued on the course runner when I checked, so I'm not claiming it passed. In scope: the duel, "
        "disguise, scripted guards, six rooms, loose-floor traps, the trained rival and the baseline. Out: "
        "gate plates, public servers, sound. Deferred until evidence and my approval: retraining and AI traps. "
        "If time runs out we cut rooms first, then the suspicion meter; never the duel or the disguise. "
        "Limits: the rival missed its bar, and online play is localhost-tested only.",
    "Road to Gold and approval requested":
        "Alpha is Wednesday, December 2; Beta, Friday, December 4; Gold, Saturday, December 5. These "
        "acceptance checks are proposals for my approval. I'm asking for G2: accept the first playable and "
        "its agent implementation. And G3: accept the scope, fallbacks and these milestone checks. A hold "
        "applies if the official CI stays queued, or the rival, the single playtest or online testing "
        "remain unresolved. The official repository is on screen.",
}


def notes(s, title, timing, script, extra=""):
    script = SCRIPT.get(title, script)
    NARRATION.append((title, timing, script))
    if os.environ.get("NO_NOTES"):       # Keynote cannot import python-pptx's notes master; render copy only
        return
    s.notes_slide.notes_text_frame.text = (
        f"[{timing}]\n\nNARRATION\n{script}\n" + (f"\n{extra}" if extra else ""))


# ---------------------------------------------------------------- slide 1
s = new_slide("SHADOW MASQUE", "A competitive two-player stealth platformer")
picture(s, "rehearsal-guard-down.jpg", 6.35, 1.55, w=6.45)
text(s, 6.35, 5.62, 6.45, 0.5,
     "Rehearsal frame (scripted input, the game's own renderer and art): the player has struck down a palace guard.", 13, DIM)
text(s, 0.55, 1.6, 5.6, 2.3,
     [("Two rival swordsmen share one palace.", {"size": 26, "font": SERIF}),
      ("Each can disguise himself as a guard, set traps, and try to eliminate the other.",
       {"size": 20})], 20)
for i, w in enumerate(["Tension", "Deception", "Uncertainty", "Tactical combat"]):
    box(s, 0.55 + (i % 2) * 2.85, 4.0 + (i // 2) * 0.75, 2.7, 0.6, fill=STONE, line=GOLD)
    text(s, 0.55 + (i % 2) * 2.85, 4.0 + (i // 2) * 0.75, 2.7, 0.6, w, 18, PARCH, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.55, 5.75, 6.0, 1.2,
     [("Saad Satter", {"size": 26, "bold": True, "color": GOLD, "font": SERIF}),
      ("G2/G3 First Playable", {"size": 20})])
text(s, 6.35, 6.2, 6.45, 1.0,
     [("Intended player experience: you cannot tell a rival from a guard until it is too late.",
       {"size": 16, "color": DIM, "italic": True})])
notes(s, "Shadow Masque", "0:00 to 0:15 (15 s)",
      "This is Shadow Masque, a competitive two-player stealth platformer built on a reconstruction of "
      "Prince of Persia's first level. Two rival swordsmen share one palace. Each can disguise himself "
      "as a guard, set traps in the floor, and try to eliminate the other. What I want a player to feel is "
      "tension and uncertainty: is that figure a guard, or my rival? I'm Saad Satter, and this is the G2/G3 "
      "first playable.",
      "Image: presentation/shots/rehearsal-guard-down.jpg, a scripted rehearsal frame (AI Model mode, seed 0), real renderer, generated art. Title menu art: presentation/shots/menu.jpg.")

# ---------------------------------------------------------------- slide 2
s = new_slide("First Playable: Live Gameplay Demo", "Switching to the game now")
labels = ["Act", "Game responds", "Interpret", "Next action"]
for i, l in enumerate(labels):
    x = 0.55 + i * 3.1
    box(s, x, 1.55, 2.55, 0.75, fill=STONE, line=GOLD)
    text(s, x, 1.55, 2.55, 0.75, l, 22, GOLD, font=SERIF, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        arrow(s, x + 2.62, 1.73, 0.4, 0.38)
shots = [("rehearsal-guard-room.jpg", "1  Move through the palace"),
         ("rehearsal-guard-down.jpg", "2  Beat a scripted guard, take its uniform"),
         ("rehearsal-disguised.jpg", "3  Disguised: guards grow suspicious")]
for i, (f, cap) in enumerate(shots):
    x = 0.55 + i * 4.15
    picture(s, f, x, 2.65, w=3.95)
    text(s, x, 5.08, 3.95, 0.5, cap, 16, PARCH, bold=True)
box(s, 0.55, 5.75, 12.25, 0.95, fill=PANEL, line=CRIMSON)
text(s, 0.7, 5.8, 12.0, 0.9,
     [("4  Meet the PPO-controlled rival: combat, evasion or a trap. Its move decides mine.",
       {"size": 20, "bold": True, "color": CRIMSON})], 20, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.55, 6.8, 12.25, 0.5,
     "Stills: a scripted rehearsal in the demo configuration (AI Model mode, seed 0), real renderer. "
     "The live demo is played by hand.", 12, DIM)
notes(s, "First Playable: live demo", "0:15 to 1:15 (60 s)",
      "Here is the loop I will show live: I act, the game responds, I interpret what I see, and choose my "
      "next action. I'll start the game in AI Model mode. I move through the palace and drop into the "
      "Barracks, where a scripted guard patrols. I draw my sword, strike the guard down, and take its "
      "uniform. Now I'm disguised, and the guard's suspicion rises if I behave oddly, for example if I hop. "
      "Then I go looking for the rival. This rival is the trained PPO policy, and it only sees what my "
      "character's side of the game shows it. When it appears, I decide whether to fight, flee or use a "
      "loose-floor trap, and what it does next changes what I do. Note: I'm playing this live, so what the "
      "rival does is whatever the policy decides in that moment; the screenshots are a scripted rehearsal "
      "and I will say so if I use them.",
      f"LAUNCH (from the repository root):\n  {PLAY_CMD}\n"
      "Keys: arrows or WASD move, F lunge, G draw or sheathe, T take uniform. See presentation/DEMO_RUNBOOK.md "
      "for the route, expected beats and the fallback.\n"
      "Do not describe the live rival's moves as scripted; do not describe the rehearsal stills as the demo.")

# ---------------------------------------------------------------- slide 3
s = new_slide("The AI Rival: Learned vs. Scripted", "A small PPO policy we trained, next to a scripted baseline")
steps = ["Partial observation\n(its own seat only)", "PPO policy\n(small MLP)", "Legal action\n(macro, from a legal list)",
         "Game engine\n(one simulation)"]
for i, st in enumerate(steps):
    x = 0.55 + i * 3.1
    box(s, x, 1.55, 2.6, 1.0, fill=STONE, line=INDIGO if i < 3 else GOLD)
    text(s, x, 1.55, 2.6, 1.0, st.split("\n"), 17, PARCH, bold=False, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        arrow(s, x + 2.65, 1.85, 0.4, 0.38, INDIGO)
labelled(s, 0.55, 2.8, 6.0, 3.15, "OBSERVED (held-out T09, scripted baseline as opponent)",
         [("16 duels: 13 wins, 2 draws, 1 loss", {"size": 22, "bold": True}),
          ("Pre-registered bar: 14 wins", {"size": 20}),
          ("NOT SUPPORTED", {"size": 26, "bold": True, "color": CRIMSON}),
          ("It won most duels but fell under the bar set in advance. The 3 trials per duel were identical, so effective "
           "n is about 8 starts. 0 aborted duels.", {"size": 14, "color": DIM})], 18, accent=GREEN)
labelled(s, 6.75, 2.8, 6.05, 3.15, "NOT OBSERVED (hypotheses, untested)",
         [("H1: players misidentify the disguised learned rival more often than the scripted one.",
           {"size": 16}),
          ("H2: rounds against the learned rival feel more tense.", {"size": 16}),
          ("No recorded comparison with a human yet, so what a player would lose "
           "without the learned rival is an open question.", {"size": 16, "bold": True})], 16, accent=GOLD)
box(s, 0.55, 6.1, 12.25, 0.95, fill=PANEL, line=STONE)
text(s, 0.7, 6.13, 12.0, 0.9,
     ["Cost: PPO trained on local CPU in 80 minutes (1.49 M steps), $0 API. Final-project paid LLM calls: none; "
      "the under-$1 smoke budget is unspent.",
      "Failures: 0 aborted duels, 0 runner fallbacks (16 duels, 3 identical trials each). The policy's own inference errors were not recorded."],
     14, DIM)
notes(s, "The AI rival: learned vs scripted", "1:15 to 1:55 (40 s)",
      "The rival is a small PPO policy that I trained, and it sits on the same interface as a scripted "
      "baseline. It sees only its own seat's partial observation, chooses a macro action from the legal "
      "list, and the one game engine runs it. On the held-out evaluation, 16 duels, the learned rival won "
      "13, drew 2 and lost 1 against the scripted baseline. The bar we registered in advance was 14 wins, "
      "so the verdict is not supported. That means the improvement was not shown at this bar, not that the "
      "rival is weak. Also, the three trials of each duel were identical, so the effective sample is closer "
      "to eight starts. What I observed is that strength. What I have not observed is what players "
      "experience: that it is harder to read when disguised, or more tense, are hypotheses I have not "
      "tested. Cost: training ran locally on CPU in about 80 minutes, with no API spend, and no paid model "
      "call has been made in the final project.",
      "SOURCES (all at ab395fc unless noted; Evaluation Specialist fact sheet reports/T33-evaluation-specialist.md@0d73e48):\n"
      "- 13/2/1 of 16, bar 14, NOT SUPPORTED: evaluation/results/T09/analysis.txt; docs/final/evaluation/RESULTS-T09.md; decision #77.\n"
      "- Identical trials, effective n about 8: analysis.txt 'Distinct outcomes per condition'.\n"
      "- Training 4812.6 s, 1,487,955 steps, local CPU, policy_errors 0 in training: tools/rl/runs/run-1/summary.json.\n"
      "- Paid calls: PPO rows have cost N/A; decision #8 smoke budget unspent (fact sheet section 4). Midterm LLM dev trials (Oct 2026, about $0.02 estimated) are a different line and not part of this evaluation.\n"
      "- Do NOT say: 48 trials; 120/8/0 beside this headline (tuning starts, trained on, not held-out); 0 policy errors on the held-out run; no paid call has ever been made.\n"
      "- H1, H2: docs/final/playtest/LOG.md section 1; untested (Session B not run).")

# ---------------------------------------------------------------- slide 4
s = new_slide("External Playtest: Human vs. AI", "One external player, one duel (room XGJT, duel 1)")

vid = None if os.environ.get("NO_VIDEO") else s.shapes.add_movie(str(OUT / "xgjt-001-segment.mp4"), Inches(0.55), Inches(1.5), Inches(5.0),
                         Inches(3.5), poster_frame_image=str(SHOTS / "xgjt/t420.jpg"), mime_type="video/mp4")
labelled(s, 0.55, 5.1, 5.0, 2.15, "REPLAY SHOWS (verified frame by frame)",
         ["Three hits on the human: frames 417, 441, 465.",
          "AI won, 2 hearts to 0, in 465 frames.",
          "Only sword drop: the human's own THROW (input 463, drop 465).",
          "A guard went down at frame 327; attacker not recorded."], 12.5, accent=GREEN)
labelled(s, 5.75, 1.5, 7.05, 1.95, "OBSERVER NOTES (Saad), LOG.md section 4, verbatim",
         [("“The human player was able to identify the AI rival, and the AI was also able to locate the "
           "human player. The AI demonstrated strong combat abilities, particularly in disarming opponents "
           "and executing consecutive attacks. It was also effective at defeating scripted guards. The human "
           "player struggled to counter the AI's attacks and interrupt its attack sequences.”",
           {"size": 12.5, "italic": True})], 12.5, accent=INDIGO)
labelled(s, 5.75, 3.55, 7.05, 1.65, "INTERPRETATION (Saad), LOG.md section 6, verbatim",
         [("“The trained PPO rival appears to be particularly effective in combat. However, its ability "
           "to repeatedly disarm and attack opponents may create an imbalance that makes combat frustrating "
           "for human players. Further playtesting should investigate whether players can develop effective "
           "counterstrategies or whether combat balancing is necessary.”",
           {"size": 12.5, "italic": True})], 12.5, accent=GOLD)
box(s, 5.75, 5.3, 7.05, 1.95, fill=STONE, line=CRIMSON, lw=2.5)
text(s, 5.9, 5.35, 6.8, 1.9,
     [("OPEN QUESTION", {"size": 13, "bold": True, "color": CRIMSON}),
      ("Can human players develop effective counterstrategies against the trained rival, or does combat "
       "need balancing?", {"size": 20, "bold": True}),
      ("Published with the player's consent (option b). One player, one duel: not a finding yet.",
       {"size": 12, "color": DIM})], 18)
notes(s, "External playtest: Human vs AI", "1:55 to 2:40 (45 s)",
      "This is the one external playtest so far: a player outside the team played against the trained "
      "rival in a hosted duel, with the host logging telemetry. I've reconstructed the clip from the logged "
      "inputs. It is a replay, not a recording: the game engine is deterministic, so replaying the logged "
      "inputs gives the same duel, and I checked the final state against the log's hash. The label says so. "
      "Here are my observer notes, in my words from the playtest log: the player could identify the rival "
      "and the rival could locate the player, strong combat, effective against guards, and the player "
      "struggled to counter it. Beside them, what the replay itself shows: three hits on the human, at "
      "frames 417, 441 and 465; the AI won with two hearts left; the only dropped sword is the human's own "
      "throw in the last moments; and a guard goes down at frame 327 with no attacker recorded. So the "
      "replay supports the strong-combat impression, and not every item in my notes. My interpretation was "
      "that combat might need balancing, but this is one player and one duel. The open question: can "
      "players develop counterstrategies against this rival, or does combat need balancing?",
      "PROVENANCE: docs/final/playtest/telemetry/2026-11-27/online/duel-XGJT-001-seed0.json replayed with server/trace.py replay: "
      "state hash 5dadb78e1da67d1fb312711bd48dbc60a2a4f71f5000fb00b14ec1463572a910 = recorded; outcome won:B at 465 frames. "
      "Video: ticks 216 to 465 (20.8 s of play) plus a 2 s hold, rendered by presentation/render_replay.py with the pygame renderer and "
      "generated art (the hosted page used a Phaser client; the engine state is identical, the drawing is not the same program).\n"
      "Consent: LOG.md section 3 (option b, decision #130, notes publishable yes). Observer and interpretation text: LOG.md sections 4 and 6, verbatim; decision #135.\n"
      "The video shows seat A (the human) view only, as the player saw it; captions state only replay facts.\n"
      "If the video does not play in your presentation tool: presentation/out/xgjt-001-segment.mp4.")

# ---------------------------------------------------------------- slide 5
s = new_slide("Production Agent Team", "Two tailored course agents, one genuine handoff")
# hierarchy
box(s, 0.55, 1.5, 3.6, 0.7, fill=STONE, line=GOLD)
text(s, 0.55, 1.5, 3.6, 0.7, ["Student (Saad)", ("Executive Producer / Creative Director", {"size": 12, "color": DIM})],
     16, GOLD, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
down_arrow(s, 2.2, 2.22, 0.3, 0.25)
box(s, 0.55, 2.5, 3.6, 0.55, fill=STONE, line=DIM)
text(s, 0.55, 2.5, 3.6, 0.55, "Opus Orchestrator", 16, PARCH, bold=True, align=PP_ALIGN.CENTER,
     anchor=MSO_ANCHOR.MIDDLE)
down_arrow(s, 2.2, 3.07, 0.3, 0.25)
box(s, 0.55, 3.35, 1.75, 0.95, fill=PANEL, line=GOLD, lw=3)
text(s, 0.55, 3.35, 1.75, 0.95, ["Sonnet", "Tech Lead", ("course agent", {"size": 11, "color": GOLD})], 14,
     PARCH, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
box(s, 2.4, 3.35, 1.75, 0.95, fill=PANEL, line=GOLD, lw=3)
text(s, 2.4, 3.35, 1.75, 0.95, ["Sonnet", "QA", ("course agent", {"size": 11, "color": GOLD})], 14,
     PARCH, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
box(s, 0.55, 4.4, 3.6, 0.6, fill=PANEL, line=STONE)
text(s, 0.55, 4.4, 3.6, 0.6, "Supporting workers: Evaluation Specialist, Requirements Auditor, rules reviewer",
     11, DIM, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
box(s, 0.55, 5.1, 3.6, 0.55, fill=PANEL, line=CRIMSON)
text(s, 0.55, 5.1, 3.6, 0.55, "In-game PPO rival: a game feature, not a production agent", 11, CRIMSON,
     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.55, 5.75, 3.6, 1.5,
     [("Tech Lead: implementation, engine, agent interface, builds, technical evidence.", {"size": 12}),
      ("QA: independent verification, reproducible failures, regression tests, observation-boundary checks.",
       {"size": 12})], 12, DIM)
# chain
chain = [("QA finds the leak", "T02-F1: a disguised WAIT shows motion 'waited'; a paused guard shows none", INDIGO),
         ("Student approves the fix", "Hop +6 suspicion per frame (48 per hop, #18); DOWN reads as standing still", GOLD),
         ("Tech Lead fixes", "T01: 558ef6d, failing tests first a1100f6", INDIGO),
         ("QA verifies independently", "T02-close 72f6552: 5 xfails removed; 650 passed, 12 skipped, 2 xfailed", INDIGO),
         ("Student accepts", "“I consider this handoff complete.” (7c4fc1d)", GOLD)]
text(s, 4.5, 1.45, 8.3, 0.4, "The T02 handoff: QA to Tech, 2026-11-24", 16, GOLD, bold=True)
for i, (h, d, c) in enumerate(chain):
    y = 1.9 + i * 0.98
    box(s, 4.5, y, 8.3, 0.88, fill=PANEL, line=c, lw=2)
    text(s, 4.62, y + 0.02, 8.1, 0.85, [(h, {"size": 16, "bold": True, "color": c}), (d, {"size": 13})], 13)
text(s, 4.5, 6.85, 8.3, 0.5,
     "Why it mattered: a disguised player waiting could be told apart from a paused guard by motion metadata. "
     "Reviewed 13c7488; decisions #4, #7, #18, #120.", 12, DIM)
notes(s, "Production agent team", "2:40 to 3:20 (40 s)",
      "Production runs on a clear chain. I'm the Student, Executive Producer and Creative Director. An Opus "
      "orchestrator routes work to Sonnet agents. Two of them are the formal course agents: the Tech Lead, "
      "who implements the engine, agent interface, builds and technical evidence, and QA, who verifies "
      "independently, reproduces failures and checks the observation boundary. The Evaluation Specialist, "
      "Requirements Auditor and rules reviewer are supporting workers, and the in-game PPO rival is a game "
      "feature, not a production agent. The real handoff is T02. QA found that a disguised player who "
      "waited could be told apart from a paused guard, because of unintended motion metadata. That would "
      "break the core stealth idea. I approved the fix, including hopping raising suspicion, six per frame, "
      "forty-eight per hop, and treating DOWN as standing still. The Tech Lead fixed it, QA independently "
      "verified it with 650 tests passing, 12 skipped and 2 unrelated expected failures, and I accepted it.",
      "SOURCES: docs/final/orchestration/handoff-drafts/2026-11-24-qa-to-tech.md (findings, closing evidence, Student decision, quoted verbatim "
      "'I consider this handoff complete'); reviewed commit 13c7488; fix 558ef6d; failing tests a1100f6; T02-close 72f6552; Student decision committed 7c4fc1d (decision #120); "
      "decisions #4 (hop raises suspicion), #7, #18 (+6 per frame on each of 8 hop frames = 48) in DECISIONS-2026-11-23.md; REVIEW_LOG row 2026-11-24 T02 handoff closed.\n"
      "650 passed, 12 skipped, 2 xfailed is the T02-close figure at that commit; the 2 xfails are open T04 gate findings, not T02. Today's suite is on slide 6.\n"
      "Repo: https://github.com/SaadSatter/shadow_masque (development); official: " + REPO)

# ---------------------------------------------------------------- slide 6
s = new_slide("Verification and Scope Lock", "Approved by Saad 2026-11-27 (decision #127)")
labelled(s, 0.55, 1.45, 3.6, 2.6, "VERIFICATION",
         [("Dev CI: green", {"size": 16, "bold": True, "color": GREEN}),
          ("Deterministic checks, run 46065581056, success", {"size": 12}),
          ("Local suite: " + SUITE_LINE, {"size": 12}),
          ("Official repo CI: not passed", {"size": 16, "bold": True, "color": CRIMSON}),
          ("\"Final\" workflow queued on the course runner (run 46058158697) at last check.", {"size": 12})],
         12, accent=GREEN)
labelled(s, 4.3, 1.45, 3.9, 2.6, "IN SCOPE",
         ["Duel, disguise, suspicion, scripted guards", "Six-room arena, 5-minute duels",
          "Loose-floor traps (4 each)", "Trained PPO rival + scripted baseline",
          "Three modes (AI, Baseline, Human vs Human) in pygame, hosted page, LAN server"], 13, accent=GOLD)
labelled(s, 8.35, 1.45, 4.45, 2.6, "OUT OF SCOPE, THEN DEFERRED",
         [("Out for G2/G3: gate-plate trap; accounts; matchmaking; public-internet server (not excluded "
           "forever, #123); levels 2 to 14; original level data; sound; adaptive guards; more than two "
           "players; LLM rival in the game.", {"size": 12.5}),
          ("Deferred, needs approval (#123): retraining the PPO rival; the AI rigging traps; movement "
           "changes or a side-scroll view; other gameplay improvements.",
           {"size": 12.5, "color": INDIGO})], 12.5, accent=CRIMSON)
labelled(s, 0.55, 4.2, 7.65, 3.05, "FALLBACKS: trigger, then action",
         [("Scope lock, cut order. Trigger: time runs out.", {"size": 14, "bold": True, "color": GOLD}),
          ("1 rooms 6 to 3; 2 suspicion meter to yes/no; 3 one trap type (already so); 4 AI vs AI "
           "test-only; 5 public hosting to LAN (already so). Never cut the duel or the disguise.", {"size": 14}),
          ("GDD section 5, runtime. Trigger: the event.", {"size": 14, "bold": True, "color": GOLD}),
          ("AI seat times out: labelled WAIT, counted. An evaluation run over its limit is aborted; online "
           "it is logged and never aborts (#49). Human disconnects: pause 15 s, then forfeit.", {"size": 14})],
         12, accent=GOLD)
labelled(s, 8.35, 4.2, 4.45, 3.05, "LIMITATIONS",
         [("Rival missed the pre-registered bar (13 of 16, bar 14).", {"size": 13}),
          ("Online play tested on localhost only, not on two machines; no latency measurement.", {"size": 13}),
          ("Hosted page runs the engine in the browser (devtools can read hidden state).", {"size": 13})],
         13, accent=CRIMSON)
notes(s, "Verification and scope lock", "3:20 to 4:00 (40 s)",
      "On verification: the deterministic test suite passes, and the development repository's continuous "
      "integration is green. The official repository's CI workflow was still queued on the course runner "
      "when I last checked, so I am not claiming it passed. On scope, the lock I approved: the duel, "
      "disguise, suspicion and scripted guards; the six-room arena with five-minute duels; loose-floor "
      "traps; the trained rival and the scripted baseline; and the three modes. Out of scope: the gate-plate "
      "trap, accounts, a public server, further levels, original level data, sound and an LLM rival. "
      "Deferred, pending evidence and my approval: retraining, the rival setting traps, and movement "
      "changes. If time runs out, the cut order is rooms first, then the suspicion meter, then AI-versus-AI "
      "as test-only. We never cut the duel or the disguise. Limitations I should be plain about: the rival "
      "missed its pre-registered bar, and online play has only been tested on localhost.",
      "SOURCES: docs/final/SCOPE_LOCK.md (in scope, out of scope, deferred #123, cut order, known limitations; decision #127). Runtime fallbacks: docs/final/GDD.md section 5 failure table (AI timeout, disconnect). "
      "The scope lock's own 'fallbacks' are the cut order; its trigger is 'if time runs out' (GDD section 8). "
      "Dev CI: gh run 46065581056 'Deterministic checks (dev)' on main 43e9ce1, success (checked 2026-11-27 15:56 ET). "
      "Official CI: gh run 46058158697 'Final' on columbia-university-ai-games/final-saadsatter main (a251335), queued; re-check status before recording and say what you see. "
      "Local suite line: see presentation/SUITE_RESULT.txt.")

# ---------------------------------------------------------------- slide 7
s = new_slide("Road to Gold and Approval Requested", "Milestone checks are PROPOSED for Saad's approval")
ms = [("ALPHA", "Wed Dec 2",
       ["Dev CI green on main", "All three modes launch from the menu", "A full 5-minute duel vs the AI ends with 0 aborted",
        "Combat-balance question has a test plan"]),
      ("BETA", "Fri Dec 4",
       ["Second external player, post-Alpha playtest, logged before interpretation",
        "Findings triaged; each approved fix verified by test or trace", "Fuller live suite, within the approved budget"]),
      ("GOLD", "Sat Dec 5",
       ["Playable end to end, deterministic fallback, replay instructions, archived runnable release",
        "Final GDD and Configuration update", "Gold recording submitted"])]
for i, (n, d, checks) in enumerate(ms):
    x = 0.55 + i * 4.15
    box(s, x, 1.5, 3.95, 0.62, fill=GOLD, line=None)
    text(s, x, 1.5, 3.95, 0.62, f"{n}  {d}", 20, BG, font=SERIF, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    box(s, x, 2.12, 3.95, 2.3, fill=PANEL, line=GOLD)
    text(s, x + 0.1, 2.17, 3.75, 2.2, ["• " + c for c in checks], 16)
    text(s, x, 4.43, 3.95, 0.3, "Proposed, not yet approved", 11, INDIGO, align=PP_ALIGN.CENTER)
labelled(s, 0.55, 4.8, 4.0, 2.0, "G2 APPROVAL",
         "Accept the integrated first playable and its agent implementation; authorize production.", 14, accent=GREEN)
labelled(s, 4.7, 4.8, 4.0, 2.0, "G3 APPROVAL",
         "Accept the scope, exclusions, fallbacks and the milestone checks above.", 14, accent=GREEN)
labelled(s, 8.85, 4.8, 3.95, 2.0, "HOLD, if",
         "Open now: official CI still queued; rival under its bar; one external player; online not on 2 machines. "
         "Resolve each before approval.", 14, accent=CRIMSON)
text(s, 0.55, 6.9, 12.25, 0.45, "Official repository: " + REPO + "   (G2/G3 commit a251335)", 14, GOLD)
notes(s, "Road to Gold and approval requested", "4:00 to 4:30 (30 s)",
      "Next are three milestones: Alpha on Wednesday, December 2; Beta on Friday, December 4; Gold on "
      "Saturday, December 5. The acceptance checks on this slide are proposals, not approved checks. Alpha "
      "is a stable build and a complete duel against the AI. Beta is a second external playtest, triage, and "
      "verified fixes. Gold is the end-to-end release with the final documents. I'm asking for two things. "
      "G2: accept the integrated first playable and its agent implementation, and authorize production. "
      "G3: accept the scope, exclusions, fallbacks and these milestone checks. A hold would apply if any "
      "of these stay unresolved: the official repository's CI run is still queued, the rival missed its "
      "pre-registered bar, there is only one external player so far, or online play has not been tried on "
      "two machines. The official repository is on screen.",
      "The records contain no approved Alpha or Beta acceptance checks (PROJECT_PLAN.md and SCOPE_LOCK.md name only 'Sat 5 Dec Gold build recording'; "
      "Dec 2 and Dec 4 come from your request). The checks are drawn from the G4 checklist in docs/final/orchestration/inputs/FINAL_REQUIREMENTS.md section 6 "
      "(end-to-end playable game, deterministic fallback, CI evidence, replay instructions, archived runnable release, final dated GDD/config, "
      "post-Alpha external playtest, triage and verified fixes, fuller live suite) and the SCOPE_LOCK known limitations. All three are marked 'Proposed, not yet approved'. "
      "Hold items are facts from the records, listed as candidates; you decide whether any of them is a hold.")

OUT.mkdir(parents=True, exist_ok=True)
target = OUT / os.environ.get("DECK_NAME", "ShadowMasque-G2G3.pptx")
prs.save(str(target))
if not os.environ.get("NO_NOTES"):
    import sys
    sys.path.insert(0, str(ROOT))
    import fix_notes_master
    print("notes master", "fixed" if fix_notes_master.fix(target) else "unchanged")   # Keynote needs notesMasterIdLst

lines = ["# Shadow Masque G2/G3: narration script", "",
         "Target 4:30 including the video and the live demo. Slide 4 marks when to click play on the clip and what to say over it (decision #138). Generated by `presentation/build_deck.py` from the slide notes; the same text is in the speaker notes.", ""]
for i, (title, timing, script) in enumerate(NARRATION, 1):
    lines += [f"## Slide {i}: {title}  [{timing}]", "", script, ""]
(ROOT / "NARRATION.md").write_text("\n".join(lines))
print("saved", OUT / "ShadowMasque-G2G3.pptx")
