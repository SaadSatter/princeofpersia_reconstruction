"""Build assets/generated/ (the Shadow Masque art pack) from PixelLab downloads.

    uv run --extra play python tools/build_generated_art.py RAW_DIR

Maintainers only; the game and the tests read the committed pack, never this
tool or the network. RAW_DIR holds the PixelLab outputs listed in SOURCES,
downloaded from the PixelLab account (Saad's decision OQ-8, 2026-11-16;
terms of 30 Oct 2026 permit distributing outputs, Saad's reading):

    RAW_DIR/tileset.png, tileset_meta.json          sidescroller tileset (pro)
    RAW_DIR/pillar.png, torch.png, door.png          map objects
    RAW_DIR/rival/Idle/...                           character ZIP, extracted
    RAW_DIR/guard/Idle/...                           character ZIP, extracted

Output (all PNG, plus JSON and a manifest):
    tiles/platform.png + tiles/platform.json         16 corner tiles (dual grid)
    props/{pillar,torch,door}.png
    rival/<anim>.png, guard/<anim>.png               horizontal frame strips, facing right
    sprites.json                                     frame size, count and anchor per strip
    MANIFEST.tsv                                     path, source, bytes, sha256

The hang and climb frames are hand-built here from the standing rival (head,
torso and legs cut from it, arms drawn in its own colours) on a canvas whose
anchor is the ledge corner, so the hands stay on the ledge while the body
rises (render/anim.py: HANG_DROP 33 px, feet 7 px back from the edge).
The gate and spikes are drawn in code (render/dungeon.py), not stored.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "assets" / "generated"

RIVAL_ID = "200624a1-3d6e-4098-b4a6-781eb38a7312"
GUARD_ID = "3e3205ed-340e-4965-a0ca-71cd9d2a4f2a"
SOURCES = {
    "tiles": "PixelLab sidescroller tileset b723a004-aac5-4b9e-8a71-c3742a4a53a7 (pro)",
    "pillar": "PixelLab map object a6907856-2cc4-4fd6-8642-8e96ca3715d5",
    "torch": "PixelLab map object b692d8c1-34ae-4f27-8298-b31f6ecfc8d8",
    "door": "PixelLab map object 5e16db79-5736-4c2c-bc57-5ddc81c4c4d7",
    "rival": f"PixelLab character {RIVAL_ID}",
    "guard": f"PixelLab character {GUARD_ID}",
}
# strip name -> PixelLab animation folder (None: the east rotation)
RIVAL_STRIPS = {"stand": None, "run": "run", "step": "step", "jump": "jump", "leap": "leap",
                "crouch": "crouch", "death": "death", "drink": "drink", "strike": "strike",
                "block": "block", "hit": "hit",
                # swordplay (docs/final/VERSUS_SPEC.md; rules not implemented yet)
                # The sword is drawn along the forearm, so the stances use straight
                # arms (-2/-3 retries); stance-mid-3 came back without a blade, which
                # the build adds by hand (add_blade).
                "stance_high": "stance-high-2", "stance_mid": "stance-mid-3", "stance_low": "stance-low-3",
                "lunge_high": "lunge-high-2", "lunge_mid": "lunge-mid-2", "lunge_low": "lunge-low-2",
                "throw": "sword-throw", "dive_kick": "dive-kick", "sweep": "sweep",
                "take": "take-uniform"}
# The guard also carries the rival's movement strips under the same names, so a
# disguised rival (drawn as a guard, VERSUS_SPEC R-V18) can run, jump and climb
# with the same clips as the rival (render/genart.frame_for). step, death and
# drink reuse the walk, downed and standing frames.
GUARD_STRIPS = {"stand": None, "walk": "patrol-walk-2", "stance": "guard-stance",
                "run": "run", "step": "patrol-walk-2", "jump": "jump", "leap": "leap",
                "crouch": "crouch", "death": "downed", "drink": None,
                "strike": "strike", "hit": "hit", "downed": "downed",
                "stance_high": "stance-high-2", "stance_mid": "stance-mid-3", "stance_low": "stance-low-3",
                "lunge_high": "lunge-high-2", "lunge_mid": "lunge-mid-2", "lunge_low": "lunge-low-2"}

# PixelLab's lunges start and end in a rest pose (blade raised), not in the stance
# they belong to. The build keeps only their thrust frames, where the blade is
# level at the stance's height, and sets them between that stance's own frame
# (compose_lunge). Indices picked by eye from the downloaded clips, 2026-11-17.
LUNGE_THRUST = {
    "rival": {"high": (3, 4), "mid": (4, 5), "low": (5, 5)},
    "guard": {"high": (4, 5), "mid": (4, 5), "low": (4, 5)},
}

# Ledge-anchored canvas for hang/climb frames.
CW, CH = 56, 80
AX, AY = 20, 44            # first ledge column, ledge surface row
HANG_DROP = 33


def build(raw: Path) -> None:
    import pygame
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    files: dict[str, tuple[Path, str]] = {}

    def save(img, rel: str, source: str) -> None:
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(img, str(p))
        files[rel] = (p, source)

    # tiles: keep only what the renderer needs from PixelLab's metadata
    meta = json.loads((raw / "tileset_meta.json").read_text())
    tiles = [{"corners": [t["corners"][k] == "lower" for k in ("NW", "NE", "SW", "SE")],
              "x": t["bounding_box"]["x"], "y": t["bounding_box"]["y"]}
             for t in meta["tileset_data"]["tiles"]]
    save(pygame.image.load(str(raw / "tileset.png")), "tiles/platform.png", SOURCES["tiles"])
    (OUT / "tiles" / "platform.json").write_text(json.dumps(
        {"tile": 32, "corners": "NW NE SW SE, true = stone", "tiles": tiles}, indent=1) + "\n")
    files["tiles/platform.json"] = (OUT / "tiles" / "platform.json", SOURCES["tiles"] + " (corner table)")
    for name in ("pillar", "torch", "door"):
        save(pygame.image.load(str(raw / f"{name}.png")), f"props/{name}.png", SOURCES[name])

    sprites: dict[str, dict] = {"rival": {}, "guard": {}}

    def frames_of(char_dir: Path, anim: str | None):
        if anim is None:
            return [pygame.image.load(str(char_dir / "Idle" / "rotations" / "east.png"))]
        d = char_dir / "Idle" / "animations" / anim / "east"
        return [pygame.image.load(str(d / f)) for f in sorted(os.listdir(d))]

    def strip(who: str, name: str, frames, source: str, anchor: dict | None = None) -> None:
        w = max(f.get_width() for f in frames); h = max(f.get_height() for f in frames)
        s = pygame.Surface((w * len(frames), h), pygame.SRCALPHA)
        for i, f in enumerate(frames):
            s.blit(f, (i * w, 0))
        if anchor is None:
            # feet: lowest pixel over all frames. PixelLab skeleton clips (48 px canvases)
            # keep the body at a fixed canvas spot, so they share x = w // 2 - 1 (a
            # figure-centred x would jump with every sword or cloak that sticks out);
            # the single 32 px rotation uses its figure's centre.
            low = max(f.get_bounding_rect().bottom for f in frames)
            if w == 48:
                ax = w // 2 - 1
            else:
                bb0 = frames[0].get_bounding_rect()
                ax = bb0.x + bb0.w // 2
            anchor = {"type": "feet", "x": ax, "y": low - 1}
        sprites[who][name] = {"file": f"{who}/{name}.png", "w": w, "h": h, "n": len(frames), **anchor}
        save(s, f"{who}/{name}.png", source)

    rival_dir, guard_dir = raw / "rival", raw / "guard"
    for who, char_dir, table in (("rival", rival_dir, RIVAL_STRIPS), ("guard", guard_dir, GUARD_STRIPS)):
        built = {}
        for name, anim in table.items():
            frames = frames_of(char_dir, anim)
            if who == "rival" and name == "stance_mid":
                frames = [add_blade(pygame, f) for f in frames]
            built[name] = frames
        for name, anim in table.items():
            frames = built[name]
            source = SOURCES[who] + (f" animation {anim}" if anim else " rotation east")
            if who == "rival" and name == "stance_mid":
                source += " + blade hand-drawn in tools/build_generated_art.py"
            if name.startswith("lunge_"):
                height = name.split("_")[1]
                a1, a2 = LUNGE_THRUST[who][height]
                frames = compose_lunge(built["stance_" + height][0], frames, a1, a2)
                source += (f" frames {a1},{a2} between stance_{height} frames"
                           " (composed in tools/build_generated_art.py)")
            strip(who, name, frames, source)
    climb = climb_frames(pygame, frames_of(rival_dir, None)[0], frames_of(rival_dir, "climb-skel"))
    strip("rival", "climb", climb,
          "hand-built in tools/build_generated_art.py from the rival rotation + PixelLab animation climb-skel",
          anchor={"type": "ledge", "x": AX, "y": AY})
    gclimb = guard_climb_frames(pygame, frames_of(guard_dir, None)[0], frames_of(guard_dir, "climb-skel"))
    strip("guard", "climb", gclimb,
          "hand-built in tools/build_generated_art.py from the guard rotation + PixelLab animation climb-skel",
          anchor={"type": "ledge", "x": AX, "y": AY})

    (OUT / "sprites.json").write_text(json.dumps(sprites, indent=1, sort_keys=True) + "\n")
    files["sprites.json"] = (OUT / "sprites.json", "tools/build_generated_art.py")
    lines = ["path\tsource\tbytes\tsha256"]
    for rel in sorted(files):
        p, src = files[rel]
        data = p.read_bytes()
        lines.append(f"{rel}\t{src}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}")
    (OUT / "MANIFEST.tsv").write_text("\n".join(lines) + "\n")
    print(f"wrote {len(files)} files to {OUT.relative_to(PROJECT)}")


def compose_lunge(stance, lunge, a1, a2):
    """8 frames, as VERSUS_SPEC R-V04 (2 windup, 2 active, 4 recovery): the stance,
    the two thrust frames, a held thrust, then back to the same stance. So every
    lunge starts and ends exactly in the high, mid or low guard it is made from."""
    return [stance, stance, lunge[a1], lunge[a2], lunge[a2], lunge[a1], stance, stance]


def add_blade(pygame, frame):
    """Draw a level scimitar forward from the fist: the frontmost skin pixel in the
    chest rows. 12 px long, two rows (light edge over steel), tip curving up 1 px,
    a dark crossguard; colours are the rival's own sword colours."""
    SKIN = {(241, 157, 115), (219, 125, 87), (195, 93, 69)}
    EDGE, STEEL, DARK = (220, 231, 236, 255), (135, 139, 142, 255), (69, 78, 106, 255)
    f = frame.copy()
    bb = f.get_bounding_rect()
    rows = range(bb.y + bb.h // 4, bb.y + bb.h // 2)
    hand = max(((x, y) for y in rows for x in range(f.get_width())
                if f.get_at((x, y)).a and tuple(f.get_at((x, y)))[:3] in SKIN), default=None)
    if hand is None:
        return f
    hx, hy = hand
    for y in (hy - 1, hy, hy + 1):                   # crossguard
        f.set_at((hx + 1, y), DARK)
    for i in range(2, 14):
        lift = 1 if i >= 10 else 0                   # the curve near the tip
        f.set_at((hx + i, hy - lift), EDGE)
        if i < 13:
            f.set_at((hx + i, hy + 1 - lift), STEEL)
    return f


def guard_climb_frames(pygame, base, skel):
    """The guard's hang, pull and press, hand-built like the rival's (PixelLab's
    skeleton hang draws no raised arms at 32 px). The guard's cloak and sword
    make it impractical to cut into head/torso/legs, so the whole standing
    guard is the body, with its diagonal blade erased (it hangs by both hands)
    and two raised arms drawn in its own mail-sleeve colours. Then crouch,
    rise and stand on the ledge from its PixelLab climb (frames 4, 5, 7)."""
    OUTLINE = (0, 0, 0, 255)
    MAIL, MAIL_DK, GLOVE = (140, 150, 171, 255), (86, 95, 119, 255), (40, 42, 59, 255)
    body = base.copy()
    for y in range(20, body.get_height()):              # the blade runs down-right from the fist
        for x in range(19, body.get_width()):
            body.set_at((x, y), (0, 0, 0, 0))
    bb = body.get_bounding_rect()
    feet_x0 = 15                                       # boots at cols 12-18 of the rotation
    shoulder0 = (17, 13)                               # front shoulder in the rotation

    def place(c, feet_x, feet_y, lean=0):
        """Blit the body with its feet at (feet_x, feet_y); `lean` shears the upper
        body forward (rows above the hips move further)."""
        ox, oy = feet_x - feet_x0, feet_y - (bb.bottom - 1)
        hips = 20
        for y in range(bb.top, bb.bottom):
            dx = round(lean * (hips - y) / (hips - bb.top)) if y < hips else 0
            c.blit(body, (ox + dx, oy + y), area=pygame.Rect(0, y, body.get_width(), 1))
        return (ox + shoulder0[0] + lean, oy + shoulder0[1])

    def limb(c, pts, color):
        def thick(offsets, col):
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                n = max(abs(x1 - x0), abs(y1 - y0), 1)
                for i in range(n + 1):
                    x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
                    for dx, dy in offsets:
                        if col != OUTLINE or c.get_at((x + dx, y + dy)).a == 0:
                            c.set_at((x + dx, y + dy), col)
        thick([(dx, dy) for dx in (-1, 0, 1, 2) for dy in (-1, 0, 1)], OUTLINE)
        thick([(0, 0), (1, 0)], color)

    def fist(c, x, y):
        for dx in (-1, 0, 1, 2):
            for dy in (-1, 0, 1, 2):
                if c.get_at((x + dx, y + dy)).a == 0:
                    c.set_at((x + dx, y + dy), OUTLINE)
        for dx in (0, 1):
            for dy in (0, 1):
                c.set_at((x + dx, y + dy), GLOVE)

    new = lambda: pygame.Surface((CW, CH), pygame.SRCALPHA)
    out = []
    hx, hy = AX - 2, AY + 1
    f = new()                                          # hang: feet HANG_DROP below the surface
    sh = place(f, AX - 7, AY + HANG_DROP)
    limb(f, [(sh[0] - 3, sh[1]), (hx - 1, hy + 2)], MAIL_DK)
    limb(f, [sh, (hx, hy + 2)], MAIL)
    fist(f, hx - 1, hy); fist(f, hx, hy)
    out.append(f)
    f = new(); feet_y = AY + HANG_DROP - 10            # pull: elbows bent back
    sh = place(f, AX - 7, feet_y)
    limb(f, [(sh[0] - 3, sh[1]), (sh[0] - 6, sh[1] + 3), (hx - 1, hy + 2)], MAIL_DK)
    limb(f, [sh, (sh[0] - 3, sh[1] + 4), (hx, hy + 2)], MAIL)
    fist(f, hx - 1, hy); fist(f, hx, hy)
    out.append(f)
    f = new(); feet_y = AY + 12                        # press: chest over the ledge
    sh = place(f, AX - 7, feet_y, lean=6)
    px, py = sh[0] + 3, AY - 2
    limb(f, [(sh[0] - 2, sh[1]), (px - 1, py)], MAIL_DK)
    limb(f, [sh, (px, py)], MAIL)
    out.append(f)
    for i, x_to in ((4, AX + 9), (5, AX + 13), (7, AX + 16)):
        img = skel[i]; b2 = img.get_bounding_rect()
        f = new(); f.blit(img, (x_to - (b2.x + b2.w // 2), AY - b2.bottom))
        out.append(f)
    return out


def climb_frames(pygame, base, skel):
    """hang, pull, press (hand-built), then crouch, rise, stand on the ledge (PixelLab)."""
    OUTLINE = (0, 0, 0, 255)
    SKIN, SKIN_MID, SKIN_DK = (241, 157, 115, 255), (219, 125, 87, 255), (195, 93, 69, 255)
    NAVY, NAVY_DK = (37, 45, 82, 255), (27, 33, 66, 255)
    HAND_X, TROUSER = (206, 105, 75, 255), (145, 162, 178, 255)

    def part(rect):
        return base.subsurface(pygame.Rect(rect)).copy()

    # Cut from the 32 px standing rival (rows: head 2-8, torso 9-16, legs 17-29).
    head, torso, legs = part((11, 2, 9, 7)), part((12, 9, 10, 8)), part((9, 17, 11, 13))
    for y in range(torso.get_height()):          # paint the hanging arm out of the torso
        for x in range(6):
            if tuple(torso.get_at((x, y))) in (SKIN, SKIN_MID):
                torso.set_at((x, y), NAVY if (x + y) % 3 else NAVY_DK)
    for y in range(3):                           # and its hand out of the thighs
        for x in range(legs.get_width()):
            if tuple(legs.get_at((x, y))) == HAND_X:
                legs.set_at((x, y), TROUSER)

    def body(c, feet_x, feet_y, lean=0, head_dx=0):
        lx = feet_x - 7
        c.blit(legs, (lx, feet_y - 12))
        th = torso.get_height()
        for y in range(th):                      # upper rows lean further forward
            dx = round(lean * (th - y) / th)
            c.blit(torso, (lx + 3 + dx, feet_y - 20 + y), area=pygame.Rect(0, y, torso.get_width(), 1))
        c.blit(head, (lx + 2 + lean + head_dx, feet_y - 27))
        return (lx + 7 + lean, feet_y - 20)      # near shoulder

    def limb(c, pts, color):
        def thick(offsets, col):
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                n = max(abs(x1 - x0), abs(y1 - y0), 1)
                for i in range(n + 1):
                    x = round(x0 + (x1 - x0) * i / n); y = round(y0 + (y1 - y0) * i / n)
                    for dx, dy in offsets:
                        if col != OUTLINE or c.get_at((x + dx, y + dy)).a == 0:
                            c.set_at((x + dx, y + dy), col)
        thick([(dx, dy) for dx in (-1, 0, 1, 2) for dy in (-1, 0, 1)], OUTLINE)
        thick([(0, 0), (1, 0)], color)

    def fist(c, x, y, color):
        for dx in (-1, 0, 1, 2):
            for dy in (-1, 0, 1, 2):
                if c.get_at((x + dx, y + dy)).a == 0:
                    c.set_at((x + dx, y + dy), OUTLINE)
        for dx in (0, 1):
            for dy in (0, 1):
                c.set_at((x + dx, y + dy), color)

    new = lambda: pygame.Surface((CW, CH), pygame.SRCALPHA)
    out = []
    hx, hy = AX - 2, AY + 1                      # grip on the lip, just behind the corner
    # hang: feet HANG_DROP below the surface and 7 px back from the edge
    f = new()
    limb(f, [(AX - 9, AY + HANG_DROP - 21), (hx - 1, hy + 2)], SKIN_DK)
    sh = body(f, AX - 7, AY + HANG_DROP, head_dx=-2)
    limb(f, [sh, (hx, hy + 2)], SKIN)
    fist(f, hx - 1, hy, SKIN_DK); fist(f, hx, hy, SKIN)
    out.append(f)
    # pull: body 10 px up, elbows bent back
    f = new(); feet_y = AY + HANG_DROP - 10
    limb(f, [(AX - 8, feet_y - 20), (AX - 11, feet_y - 17), (hx - 1, hy + 2)], SKIN_DK)
    sh = body(f, AX - 7, feet_y, head_dx=-1)
    limb(f, [sh, (sh[0] - 3, sh[1] + 4), (hx, hy + 2)], SKIN)
    fist(f, hx - 1, hy, SKIN_DK); fist(f, hx, hy, SKIN)
    out.append(f)
    # press: hips at the lip, chest over the ledge, arms locked down onto it
    f = new(); feet_y = AY + 12; lean = 6
    sh = (AX - 7 + lean + 1, feet_y - 20)
    px, py = sh[0] + 3, AY - 2
    limb(f, [(sh[0] - 1, sh[1]), (px - 1, py)], SKIN_DK)
    body(f, AX - 7, feet_y, lean=lean, head_dx=1)
    limb(f, [sh, (px, py)], SKIN)
    out.append(f)
    # crouch, rise, stand on the ledge: PixelLab skeleton frames 4, 5, 7, feet on the surface,
    # stepping toward the ledge cell's centre (edge + 16)
    for i, x_to in ((4, AX + 9), (5, AX + 13), (7, AX + 16)):
        img = skel[i]; bb = img.get_bounding_rect()
        f = new(); f.blit(img, (x_to - (bb.x + bb.w // 2), AY - bb.bottom))
        out.append(f)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(Path(sys.argv[1]))
