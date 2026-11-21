#!/usr/bin/env python3
"""Entry point for the Tetris game."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        import pygame  # noqa: F401
    except ImportError:
        print(
            "Pygame is required to run Tetris.\n"
            "Install it with: pip install pygame",
            file=sys.stderr,
        )
        return 1

    from tetris.app import run

    return run()


if __name__ == "__main__":
    raise SystemExit(main())
