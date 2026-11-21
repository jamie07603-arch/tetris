"""Tetromino definitions, rotation states and SRS wall-kick tables.

This module contains no presentation code, so it can be imported and tested
headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass

TETROMINO_KINDS: tuple[str, ...] = ("I", "O", "T", "S", "Z", "J", "L")

# Spawn shapes. Rotation is generated from these matrices, so a single
# definition per piece is enough. Each character is one cell.
_BASE_SHAPES: dict[str, tuple[str, ...]] = {
    "I": ("....", "XXXX", "....", "...."),
    "O": ("XX", "XX"),
    "T": (".X.", "XXX", "..."),
    "S": (".XX", "XX.", "..."),
    "Z": ("XX.", ".XX", "..."),
    "J": ("X..", "XXX", "..."),
    "L": ("..X", "XXX", "..."),
}

# Spawn position of each piece's bounding box. Standard Tetris spawns the
# 3-wide pieces in columns 3-5 and the O piece in columns 4-5.
_SPAWN_X: dict[str, int] = {"I": 3, "O": 4, "T": 3, "S": 3, "Z": 3, "J": 3, "L": 3}
_SPAWN_Y = 0


def _rotate_cw(shape: tuple[str, ...]) -> tuple[str, ...]:
    """Return a square matrix of strings rotated 90 degrees clockwise."""
    size = len(shape)
    return tuple(
        "".join(shape[size - 1 - column][row] for column in range(size))
        for row in range(size)
    )


def _rotation_states(shape: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    states = [shape]
    for _ in range(3):
        states.append(_rotate_cw(states[-1]))
    return tuple(states)


# CELL_OFFSETS[kind][rotation] is a tuple of (column, row) offsets relative to
# the piece's bounding-box origin.
CELL_OFFSETS: dict[str, tuple[tuple[tuple[int, int], ...], ...]] = {}
for _kind, _shape in _BASE_SHAPES.items():
    _states = _rotation_states(_shape)
    CELL_OFFSETS[_kind] = tuple(
        tuple(
            (column, row)
            for row, line in enumerate(state)
            for column, cell in enumerate(line)
            if cell == "X"
        )
        for state in _states
    )
del _kind, _shape, _states

# SRS wall kicks, already converted to screen coordinates (positive y is down).
# Keys are (from_rotation, to_rotation).
_JLSTZ_KICKS: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {
    (0, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (1, 0): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (1, 2): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (2, 1): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (2, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (3, 2): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (3, 0): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (0, 3): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
}

_I_KICKS: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {
    (0, 1): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (1, 0): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (1, 2): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
    (2, 1): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (2, 3): ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    (3, 2): ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    (3, 0): ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)),
    (0, 3): ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
}

_O_KICKS: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {
    (from_rotation, to_rotation): ((0, 0),)
    for from_rotation in range(4)
    for to_rotation in range(4)
}


def kick_offsets(
    kind: str, from_rotation: int, to_rotation: int
) -> tuple[tuple[int, int], ...]:
    """Return the SRS offsets to try, in order, for a rotation."""
    if kind == "I":
        return _I_KICKS[(from_rotation, to_rotation)]
    if kind == "O":
        return _O_KICKS[(from_rotation, to_rotation)]
    return _JLSTZ_KICKS[(from_rotation, to_rotation)]


@dataclass(frozen=True)
class Piece:
    """One tetromino at a position. Rotation 0 is its spawn orientation."""

    kind: str
    rotation: int = 0
    x: int = 0
    y: int = 0

    def __post_init__(self) -> None:
        if self.kind not in CELL_OFFSETS:
            raise ValueError(f"unknown tetromino kind: {self.kind!r}")
        if self.rotation not in (0, 1, 2, 3):
            raise ValueError(f"invalid rotation: {self.rotation!r}")

    @classmethod
    def spawn(cls, kind: str) -> "Piece":
        """Create a piece in its standard spawn position and orientation."""
        return cls(kind, rotation=0, x=_SPAWN_X[kind], y=_SPAWN_Y)

    def cells(self) -> tuple[tuple[int, int], ...]:
        """Absolute (column, row) cells occupied by this piece."""
        return tuple(
            (self.x + column, self.y + row)
            for column, row in CELL_OFFSETS[self.kind][self.rotation]
        )

    def moved(self, dx: int, dy: int) -> "Piece":
        return Piece(self.kind, self.rotation, self.x + dx, self.y + dy)

    def rotated(self, direction: int) -> "Piece":
        """Return this piece with its rotation state changed, without kicks."""
        if direction not in (1, -1):
            raise ValueError("direction must be 1 (clockwise) or -1 (counter-clockwise)")
        return Piece(self.kind, (self.rotation + direction) % 4, self.x, self.y)
