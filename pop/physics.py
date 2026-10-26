"""Room geometry: cell lookup across room links, support, and constants."""

from __future__ import annotations

from . import tiles as T

COLS, ROWS = 10, 3

# Frame durations (12 frames = 1 s of game time, R-A01).
RUN = 4            # one block; R-C26 (26 units / 8 frames ~ 14 units / 4 frames)
STEP = 8           # careful step (design)
TURN = 4           # R-D20
BUMP = 2
JUMP = 12          # standing jump, 3 blocks (R-C27 via R-D01)
JUMP_SPAN = 3
RUN_JUMP_FLIGHT = 8  # after the 4-frame run-up; lands 5 blocks from start
RUN_JUMP_SPAN = 4    # blocks of flight after the run-up block
JUMP_IN_PLACE = 8
CLIMB_UP = 12
HANG_DOWN = 6
HANG_UP = 8
CROUCH = 4
DRINK = 8
STAIRS = 12
WAIT = 6
FALL_PER_ROW = 4   # R-D16
MAX_FRAMES = 12    # macro cap (R-D05)

GAME_FRAMES = 60 * 60 * 12  # 60-minute clock (R-C24)

SIDE, TOP, BOTTOM = "side", "top", "bottom"

Cell = tuple[int, int, int]


class Geometry:
    """Mutable tile grids plus room links. Missing links: R-D15."""

    def __init__(self, rooms: dict[int, tuple[str, str, str]],
                 links: dict[int, tuple[int, int, int, int]]):
        self.grid = {room: [list(row) for row in rows] for room, rows in rooms.items()}
        self.links = dict(links)

    def norm(self, room: int, row: int, col: int) -> Cell | str:
        """Map a possibly out-of-room coordinate to a real cell, or SIDE/TOP/BOTTOM."""
        while col < 0:
            room = self.links[room][0]
            col += COLS
            if not room:
                return SIDE
        while col >= COLS:
            room = self.links[room][1]
            col -= COLS
            if not room:
                return SIDE
        while row < 0:
            room = self.links[room][2]
            row += ROWS
            if not room:
                return TOP
        while row >= ROWS:
            room = self.links[room][3]
            row -= ROWS
            if not room:
                return BOTTOM
        return (room, row, col)

    def tile(self, where: Cell | str) -> str | None:
        """Tile at a cell. Sides and top of the level are wall; below is void (None)."""
        if where == BOTTOM:
            return None
        if where in (SIDE, TOP):
            return T.WALL
        room, row, col = where
        return self.grid[room][row][col]

    def set_tile(self, cell: Cell, sym: str) -> None:
        room, row, col = cell
        self.grid[room][row][col] = sym

    def offset(self, cell: Cell, drow: int, dcol: int) -> Cell | str:
        room, row, col = cell
        return self.norm(room, row + drow, col + dcol)

    def supported(self, where: Cell | str) -> bool:
        """A cell supports the kid if it has a floor or a wall directly below (R-D04)."""
        t = self.tile(where)
        if t is None or t == T.WALL:
            return False
        if t in T.HAS_FLOOR:
            return True
        return self.tile(self.offset(where, 1, 0)) == T.WALL

    def rows(self, room: int) -> list[str]:
        return ["".join(r) for r in self.grid[room]]
