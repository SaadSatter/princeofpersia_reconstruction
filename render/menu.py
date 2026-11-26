"""The start menu (T22, decision #87): the three modes, in the game's own look.

Drawn on a 320x200 surface with the colours render/draw.py already uses (granite
stone, gold, white) and no new assets; the window scales it like the game. The
entries (mode id, label) are handed in by the caller (`play.menu_entries`, from the
shared mode list), so the menu, the hosted page and the online server offer the same
modes under the same names; render/ imports nothing from the agents. This module only
draws and maps keys; it never starts a game.
"""

from __future__ import annotations

from render import draw

PALETTE = (draw.BG, draw.STONE, draw.STONE_LIGHT, draw.STONE_DARK, draw.WHITE, draw.GOLD)
HINT = "Up/Down choose   Enter start   Esc quit"
ROW_H = 26
ROW_X, ROW_W = 40, 240
TOP = 66


def title_lines() -> list[str]:
    return ["SHADOW MASQUE", "Choose how to play"]


def step(index: int, key: str, entries) -> tuple[int, str | None]:
    """One key press: returns (new index, choice). choice is a mode id, "quit" or None."""
    n = len(entries)
    if key in ("down", "s"):
        return (index + 1) % n, None
    if key in ("up", "w"):
        return (index - 1) % n, None
    if key in ("return", "enter", "space"):
        return index, entries[index][0]
    if key == "escape":
        return index, "quit"
    return index, None


def draw_menu(surface, selected: int, entries) -> None:
    """Draw the whole menu onto `surface` (320x200, unscaled). Exact palette colours only."""
    import pygame
    surface.fill(draw.BG)
    pygame.draw.rect(surface, draw.STONE_DARK, (0, 0, draw.SCREEN_W, 8))
    pygame.draw.rect(surface, draw.STONE_DARK, (0, draw.SCREEN_H - 8, draw.SCREEN_W, 8))
    big = pygame.font.Font(None, 30)
    small = pygame.font.Font(None, 16)

    def centred(font, text, colour, y):
        img = font.render(text, False, colour)                   # no anti-aliasing: palette only
        surface.blit(img, ((draw.SCREEN_W - img.get_width()) // 2, y))

    centred(big, title_lines()[0], draw.GOLD, 20)
    centred(small, title_lines()[1], draw.WHITE, 48)
    for i, (_, label) in enumerate(entries):
        y = TOP + i * ROW_H
        box = (ROW_X, y, ROW_W, ROW_H - 6)
        if i == selected:
            pygame.draw.rect(surface, draw.STONE_LIGHT, box)
            pygame.draw.rect(surface, draw.WHITE, box, 1)
            colour = draw.BG
        else:
            pygame.draw.rect(surface, draw.STONE, box)
            pygame.draw.rect(surface, draw.STONE_DARK, box, 1)
            colour = draw.WHITE
        centred(small, label, colour, y + 5)
    centred(small, HINT, draw.STONE_LIGHT, draw.SCREEN_H - 24)


def run_menu(window, scale: int, entries, scripted: list[str] | None = None) -> str | None:
    """Show the menu in `window` until a mode is chosen. Returns the mode id, or None on
    Esc / closing the window. `scripted` (checks only) replaces the keyboard with key names."""
    import pygame
    surf = pygame.Surface((draw.SCREEN_W, draw.SCREEN_H))
    clock = pygame.time.Clock()
    index = 0
    queue = list(scripted or [])
    while True:
        keys: list[str] = []
        if scripted is not None:
            if not queue:
                return None
            keys.append(queue.pop(0))
        else:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None
                if ev.type == pygame.KEYDOWN:
                    keys.append(pygame.key.name(ev.key))
        for key in keys:
            index, choice = step(index, key, entries)
            if choice == "quit":
                return None
            if choice:
                return choice
        draw_menu(surf, index, entries)
        window.blit(pygame.transform.scale(surf, window.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(30)
