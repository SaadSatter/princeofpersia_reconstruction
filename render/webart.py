"""The generated art pack as the web build needs it (pure Python, standard library only).

The pygame renderer (render/dungeon.py) measures a few things on the loaded
images (where a floor slab's cap starts, the door's bounding box) and
recolours the second rival at load time. A browser page cannot run pygame,
so this module does the same with a small PNG reader and writer:

* `art_meta(root)` returns the sprite table (`sprites.json`) plus the measured
  tile numbers that `render/draw_list.py` uses to place the room's pieces.
* `crimson_pixel` is `render/dungeon.py:crimson` for one pixel, so the build
  tool (`tools/web/build.py`) can write the crimson rival's strips once.
* `spike_pixels` is `render/dungeon.py:spikes_image` as a pixel list.

Only 8-bit RGBA, non-interlaced PNGs are read: every file in
`assets/generated/` is one (`tests/test_web_build.py` checks). Nothing here
reads the engine or an observation.
"""

from __future__ import annotations

import colorsys
import json
import struct
import zlib
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
IRON_DK, IRON, IRON_LT, IRON_HI = (20, 22, 30), (52, 57, 70), (100, 107, 122), (150, 157, 170)
RUST = (90, 66, 46)
SHADOW = (14, 15, 20)


# --- PNG ------------------------------------------------------------------
def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != PNG_MAGIC:
        raise ValueError("not a PNG")
    return struct.unpack(">II", data[16:24])


def read_png(data: bytes) -> tuple[int, int, list[bytearray]]:
    """(width, height, rows of RGBA bytes) of an 8-bit RGBA PNG."""
    if data[:8] != PNG_MAGIC:
        raise ValueError("not a PNG")
    pos, idat, ihdr = 8, b"", None
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        pos += 12 + n
    if ihdr is None:
        raise ValueError("PNG without IHDR")
    w, h, depth, colour, _, _, interlace = ihdr
    if (depth, colour, interlace) != (8, 6, 0):
        raise ValueError(f"only 8-bit RGBA non-interlaced PNGs are read, got {ihdr}")
    raw = zlib.decompress(idat)
    stride, bpp = w * 4, 4
    rows: list[bytearray] = []
    prev = bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else b if pb <= pc else c
                line[i] = (line[i] + pred) & 255
            elif f != 0:
                raise ValueError(f"bad PNG filter {f}")
        rows.append(line)
        prev = line
    return w, h, rows


def write_png(w: int, h: int, rows: list[bytes]) -> bytes:
    """An 8-bit RGBA PNG, filter 0, fixed compression: the same pixels always
    give the same bytes (the build is reproducible)."""
    def chunk(kind: bytes, body: bytes) -> bytes:
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + bytes(r) for r in rows)
    return (PNG_MAGIC + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def alpha(rows: list[bytearray], x: int, y: int) -> int:
    return rows[y][4 * x + 3]


# --- recolouring (render/dungeon.py:crimson, one pixel) ---------------------
def crimson_pixel(r: int, g: int, b: int, a: int) -> tuple[int, int, int, int]:
    """The second rival: indigo cloth turned crimson, the red sash turned gold."""
    if not a:
        return r, g, b, a
    hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if 0.55 <= hh <= 0.75 and ss > 0.25:
        hh, ss, vv = 0.98, min(1.0, ss * 1.15), min(1.0, vv * 1.25)
    elif (hh <= 0.03 or hh >= 0.95) and ss > 0.55 and vv > 0.4:
        hh, ss = 0.12, 0.75
    else:
        return r, g, b, a
    rr, gg, bb = colorsys.hsv_to_rgb(hh, ss, vv)
    return round(rr * 255), round(gg * 255), round(bb * 255), a


def crimson_png(data: bytes) -> bytes:
    w, h, rows = read_png(data)
    out = []
    for line in rows:
        o = bytearray(len(line))
        for x in range(w):
            o[4 * x:4 * x + 4] = bytes(crimson_pixel(*line[4 * x:4 * x + 4]))
        out.append(o)
    return write_png(w, h, out)


# --- spikes (render/dungeon.py:spikes_image, as pixels) ---------------------
SPIKE_W, SPIKE_H = 32, 14


def spike_pixels(state: int) -> dict[tuple[int, int], tuple[int, int, int]]:
    """state 0: the slot only; 1: tips showing; 2: fully out. 32 x 14, base row 12."""
    px: dict[tuple[int, int], tuple[int, int, int]] = {}
    for x in range(4, 28):
        px[(x, 12)] = SHADOW
    heights = {0: (0, 0, 0, 0), 1: (4, 5, 4, 5), 2: (10, 12, 9, 11)}[state]
    for i, ht in enumerate(heights):
        if not ht:
            continue
        x = 5 + i * 6
        for k in range(ht):
            y = 11 - k
            w = 3 if k < ht * 0.35 else 2 if k < ht * 0.75 else 1
            x0 = x if w >= 2 else x + 1
            px[(x0, y)] = IRON_HI if w > 1 else IRON_LT
            for j in range(1, w - 1):
                px[(x0 + j, y)] = IRON_LT
            if w > 1:
                px[(x0 + w - 1, y)] = IRON_DK
        px[(x + 1, 12 - ht)] = IRON_HI
        for j in range(3):
            px[(x + j, 11)] = RUST
    return px


def spikes_sheet() -> bytes:
    """The three spike states side by side, 96 x 14."""
    rows = [bytearray(3 * SPIKE_W * 4) for _ in range(SPIKE_H)]
    for state in range(3):
        for (x, y), (r, g, b) in spike_pixels(state).items():
            i = 4 * (state * SPIKE_W + x)
            rows[y][i:i + 4] = bytes((r, g, b, 255))
    return write_png(3 * SPIKE_W, SPIKE_H, rows)


# --- measurements the room layout needs -----------------------------------
def corner_key(corners) -> str:
    return "".join("1" if c else "0" for c in corners)


def art_meta(root: Path) -> dict:
    """Everything render/draw_list.py needs to know about the pack's images."""
    root = Path(root)
    table = json.loads((root / "tiles" / "platform.json").read_text())
    tw, th, trows = read_png((root / "tiles" / "platform.png").read_bytes())
    size = table["tile"]

    def opaque(x0: int, y0: int, cols: range) -> list[int]:
        return [y for y in range(size)
                if any(alpha(trows, x0 + x, y0 + y) for x in cols)]

    wang, col0, rows_any = {}, {}, {}
    for t in table["tiles"]:
        k = corner_key(t["corners"])
        wang[k] = [t["x"], t["y"]]
        rows_any[k] = opaque(t["x"], t["y"], range(size))
        col0[k] = opaque(t["x"], t["y"], range(1))
    props = {}
    for name in ("pillar", "torch", "door"):
        w, h, rows = read_png((root / "props" / f"{name}.png").read_bytes())
        xs = [x for y in range(h) for x in range(w) if alpha(rows, x, y)]
        ys = [y for y in range(h) for x in range(w) if alpha(rows, x, y)]
        props[name] = {"w": w, "h": h, "bbox": [min(xs), min(ys), max(xs) - min(xs) + 1,
                                                 max(ys) - min(ys) + 1]}
    return {
        "tile": size,
        "wang": wang,
        "col0": col0,
        "cap_top": rows_any["0011"][0],      # render/dungeon.py DungeonArt.cap_top
        "base_bot": rows_any["1100"][-1],    # render/dungeon.py DungeonArt.base_bot
        "props": props,
        "sprites": json.loads((root / "sprites.json").read_text()),
    }
