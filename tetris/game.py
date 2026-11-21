"""Game rules and state transitions.

The whole module is independent of Pygame: it owns the board, the active
piece, scoring, levels and timing. The presentation layer only reads this
state and forwards player intents.
"""

from __future__ import annotations

import random
from enum import Enum, auto

from . import constants
from .board import Board
from .pieces import Piece, kick_offsets
from .randomizer import SevenBag


class GameState(Enum):
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


def gravity_interval(level: int) -> float:
    """Seconds per fall step at ``level`` (level 1 is the slowest)."""
    if level < 1:
        raise ValueError("level must be at least 1")
    return max(
        constants.MIN_GRAVITY,
        constants.BASE_GRAVITY * constants.GRAVITY_FACTOR ** (level - 1),
    )


class Game:
    """A single Tetris game, including the randomizer and the active piece."""

    NEXT_QUEUE_SIZE = 1

    def __init__(
        self, seed: int | None = None, rng: random.Random | None = None
    ) -> None:
        # Keep one RNG for the game's whole lifetime so that a restart deals a
        # fresh (but still seed-reproducible) sequence.
        self._rng = rng if rng is not None else random.Random(seed)
        self.restart()

    # -- Setup ---------------------------------------------------------

    def restart(self) -> None:
        """Reset every part of the game and deal a fresh first piece."""
        self.board = Board()
        self.bag = SevenBag(rng=self._rng)
        self.next_queue: list[str] = []
        self._refill_queue()
        self.current: Piece | None = None
        self.hold_kind: str | None = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 1
        self.gravity_timer = 0.0
        self.lock_timer = 0.0
        self.lock_resets = 0
        self.state = GameState.PLAYING
        self._spawn_piece()

    def _refill_queue(self) -> None:
        while len(self.next_queue) < self.NEXT_QUEUE_SIZE:
            self.next_queue.append(self.bag.next_piece())

    def _spawn_piece(self, kind: str | None = None) -> None:
        if kind is None:
            kind = self.next_queue.pop(0)
            self._refill_queue()
        piece = Piece.spawn(kind)
        self.gravity_timer = 0.0
        self.lock_timer = 0.0
        self.lock_resets = 0
        if self.board.can_place(piece.cells()):
            self.current = piece
        else:
            # The stack reached the spawn area: the new piece cannot enter.
            self.current = None
            self.state = GameState.GAME_OVER

    # -- State queries -------------------------------------------------

    @property
    def is_playing(self) -> bool:
        return self.state is GameState.PLAYING

    @property
    def is_paused(self) -> bool:
        return self.state is GameState.PAUSED

    @property
    def is_game_over(self) -> bool:
        return self.state is GameState.GAME_OVER

    @property
    def gravity_interval(self) -> float:
        return gravity_interval(self.level)

    def _is_grounded(self) -> bool:
        if self.current is None:
            return False
        return not self.board.can_place(self.current.moved(0, 1).cells())

    def ghost_y(self) -> int | None:
        """Row of the active piece's landing position, or ``None``."""
        if self.current is None:
            return None
        return self.current.y + self.board.drop_distance(self.current)

    def ghost_piece(self) -> Piece | None:
        if self.current is None:
            return None
        landing_row = self.ghost_y()
        if landing_row is None:
            return None
        return Piece(
            self.current.kind,
            self.current.rotation,
            self.current.x,
            landing_row,
        )

    # -- Player actions ------------------------------------------------

    def move(self, dx: int) -> bool:
        """Shift the active piece horizontally. Returns whether it moved."""
        if not self.is_playing or self.current is None:
            return False
        candidate = self.current.moved(dx, 0)
        if not self.board.can_place(candidate.cells()):
            return False
        self.current = candidate
        self._reset_lock_after_action()
        return True

    def rotate(self, direction: int = 1) -> bool:
        """Rotate the active piece using SRS kicks.

        Args:
            direction: 1 for clockwise, -1 for counter-clockwise.
        """
        if not self.is_playing or self.current is None:
            return False
        if direction not in (1, -1):
            raise ValueError("direction must be 1 or -1")
        from_rotation = self.current.rotation
        to_rotation = (from_rotation + direction) % 4
        for dx, dy in kick_offsets(self.current.kind, from_rotation, to_rotation):
            candidate = Piece(
                self.current.kind,
                to_rotation,
                self.current.x + dx,
                self.current.y + dy,
            )
            if self.board.can_place(candidate.cells()):
                self.current = candidate
                self._reset_lock_after_action()
                return True
        return False

    def soft_drop(self) -> bool:
        """Move down one row for a scoring point. Returns whether it moved."""
        if not self.is_playing or self.current is None:
            return False
        candidate = self.current.moved(0, 1)
        if not self.board.can_place(candidate.cells()):
            return False
        self.current = candidate
        self.score += constants.SOFT_DROP_POINTS
        self._reset_lock_after_action()
        return True

    def hard_drop(self) -> int:
        """Drop to the landing position, score it and lock immediately."""
        if not self.is_playing or self.current is None:
            return 0
        distance = self.board.drop_distance(self.current)
        if distance:
            self.current = self.current.moved(0, distance)
            self.score += distance * constants.HARD_DROP_POINTS
        self._lock_current()
        return distance

    def hold(self) -> bool:
        """Store or swap the active piece. One hold per spawned piece."""
        if not self.is_playing or self.current is None or not self.can_hold:
            return False
        current_kind = self.current.kind
        self.can_hold = False
        if self.hold_kind is None:
            self.hold_kind = current_kind
            self._spawn_piece()
        else:
            swap = self.hold_kind
            self.hold_kind = current_kind
            self._spawn_piece(swap)
        return True

    def toggle_pause(self) -> bool:
        """Toggle pause; returns whether the game is now paused."""
        if self.state is GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state is GameState.PAUSED:
            self.state = GameState.PLAYING
        return self.is_paused

    # -- Time-driven behaviour ----------------------------------------

    def update(self, dt: float) -> None:
        """Advance gravity and lock timing by ``dt`` seconds."""
        if dt <= 0 or not self.is_playing or self.current is None:
            return
        if self._is_grounded():
            self.lock_timer += dt
            if self.lock_timer >= constants.LOCK_DELAY:
                self._lock_current()
            return

        self.lock_timer = 0.0
        self.gravity_timer += dt
        interval = self.gravity_interval
        while self.gravity_timer >= interval:
            self.gravity_timer -= interval
            if not self._step_down():
                break

    def _step_down(self) -> bool:
        if self.current is None:
            return False
        candidate = self.current.moved(0, 1)
        if not self.board.can_place(candidate.cells()):
            return False
        self.current = candidate
        return True

    def _reset_lock_after_action(self) -> None:
        # Only grounded pieces have a running lock timer. The reset counter
        # stops a player from stalling a piece at the bottom indefinitely.
        if not self._is_grounded():
            return
        if self.lock_resets >= constants.MAX_LOCK_RESETS:
            return
        self.lock_timer = 0.0
        self.lock_resets += 1

    def _lock_current(self) -> None:
        if self.current is None:
            return
        self.board.lock(self.current)
        cleared = self.board.clear_lines()
        if cleared:
            # Score uses the level the clear happened at, then the level rises.
            self.score += constants.LINE_SCORES[cleared] * self.level
            self.lines += cleared
            self.level = 1 + self.lines // constants.LINES_PER_LEVEL
        self.can_hold = True
        self._spawn_piece()
