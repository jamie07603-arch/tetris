#!/usr/bin/env python3
"""Render representative game frames headlessly for the README and PR.

Usage:
    python scripts/capture_screenshots.py [output-directory]

The script uses SDL's dummy video driver, so it never opens a window. The
images are produced by the same ``tetris.ui.Renderer`` the game uses at runtime.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Must be set before pygame is imported.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pygame  # noqa: E402

from tetris.board import Board  # noqa: E402
from tetris.game import Game, GameState  # noqa: E402
from tetris.pieces import Piece  # noqa: E402
from tetris.ui import WINDOW_HEIGHT, WINDOW_WIDTH, Renderer  # noqa: E402


def make_demo_game() -> Game:
    """Build a deterministic mid-game scene with a visible ghost piece."""
    game = Game(seed=2024)
    rows = ["." * 10 for _ in range(20)]
    rows[13] = "....S....."
    rows[14] = "....SS...."
    rows[15] = "....LLL..."
    rows[16] = "..J.JLL..."
    rows[17] = ".JJ.LLLZ.."
    rows[18] = "JJJOOOZZ.."
    rows[19] = "SSSOOIIII."
    game.board = Board.from_rows(rows)
    game.current = Piece("T", rotation=0, x=3, y=6)
    game.hold_kind = "S"
    game.can_hold = True
    game.next_queue = ["L"]
    game.score = 12480
    game.level = 5
    game.lines = 43
    game.state = GameState.PLAYING
    return game


def main() -> int:
    output_dir = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / "docs" / "screenshots"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    renderer = Renderer()
    game = make_demo_game()

    renderer.draw(screen, game)
    pygame.image.save(screen, output_dir / "gameplay.png")

    game.toggle_pause()
    renderer.draw(screen, game)
    pygame.image.save(screen, output_dir / "paused.png")

    game.state = GameState.GAME_OVER
    game.current = None
    renderer.draw(screen, game)
    pygame.image.save(screen, output_dir / "game-over.png")

    pygame.quit()
    print(f"Saved screenshots to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
