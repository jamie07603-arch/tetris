"""Playfield state: collision detection, locking and line clearing.

The board stores only data; it has no Pygame dependency.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .constants import COLS, VISIBLE_ROWS
from .pieces import Piece

Cell = str | None
CellPosition = tuple[int, int]


class Board:
    """A rectangular grid of locked cells, indexed as ``grid[row][column]``."""

    def __init__(
        self,
        rows: int = VISIBLE_ROWS,
        cols: int = COLS,
        grid: Sequence[Sequence[Cell]] | None = None,
    ) -> None:
        if rows <= 0 or cols <= 0:
            raise ValueError("board dimensions must be positive")
        self.rows = rows
        self.cols = cols
        if grid is None:
            self.grid: list[list[Cell]] = [[None] * cols for _ in range(rows)]
        else:
            if len(grid) != rows or any(len(row) != cols for row in grid):
                raise ValueError("grid dimensions do not match the board")
            self.grid = [list(row) for row in grid]

    @classmethod
    def from_rows(cls, rows: Sequence[str]) -> "Board":
        """Build a board from strings; every character except ``.`` is a cell."""
        if not rows or any(len(row) != len(rows[0]) for row in rows):
            raise ValueError("rows must be non-empty and all the same length")
        grid = [
            [None if character in ". " else character for character in row]
            for row in rows
        ]
        return cls(rows=len(rows), cols=len(rows[0]), grid=grid)

    def in_bounds(self, column: int, row: int) -> bool:
        return 0 <= column < self.cols and 0 <= row < self.rows

    def is_occupied(self, column: int, row: int) -> bool:
        """Out-of-bounds positions count as occupied."""
        return not self.in_bounds(column, row) or self.grid[row][column] is not None

    def can_place(self, cells: Iterable[CellPosition]) -> bool:
        return all(not self.is_occupied(column, row) for column, row in cells)

    def lock(self, piece: Piece) -> None:
        """Write a piece into the grid.

        Raises:
            ValueError: if the piece overlaps another cell or leaves the board.
        """
        cells = piece.cells()
        if not self.can_place(cells):
            raise ValueError("piece cannot be locked in its current position")
        for column, row in cells:
            self.grid[row][column] = piece.kind

    def drop_distance(self, piece: Piece) -> int:
        """How many rows the piece can fall before landing."""
        distance = 0
        while self.can_place(piece.moved(0, distance + 1).cells()):
            distance += 1
        return distance

    def full_rows(self) -> list[int]:
        return [row for row, line in enumerate(self.grid) if all(line)]

    def clear_lines(self) -> int:
        """Remove every full row, shifting the rows above down.

        Returns:
            The number of rows removed.
        """
        remaining = [line for line in self.grid if any(cell is None for cell in line)]
        cleared = self.rows - len(remaining)
        if cleared:
            self.grid = [[None] * self.cols for _ in range(cleared)] + remaining
        return cleared

    def is_empty(self) -> bool:
        return all(cell is None for line in self.grid for cell in line)

    def copy(self) -> "Board":
        return Board(self.rows, self.cols, self.grid)
