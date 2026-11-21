"""The seven-bag randomizer used to deal tetrominoes."""

from __future__ import annotations

import random

from .pieces import TETROMINO_KINDS


class SevenBag:
    """Deal every piece exactly once per bag, shuffling a fresh bag each time."""

    def __init__(self, rng: random.Random | None = None, seed: int | None = None) -> None:
        self._rng = rng if rng is not None else random.Random(seed)
        self._bag: list[str] = []

    def next_piece(self) -> str:
        if not self._bag:
            self._bag = list(TETROMINO_KINDS)
            self._rng.shuffle(self._bag)
        return self._bag.pop()
