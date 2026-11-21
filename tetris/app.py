"""Pygame application: window lifecycle, input handling and the fixed loop."""

from __future__ import annotations

import pygame

from . import constants
from .game import Game
from .ui import WINDOW_HEIGHT, WINDOW_WIDTH, Renderer


class InputController:
    """Turns key events and held keys into game actions.

    Discrete actions run once per KEYDOWN. Repeating actions are advanced in
    ``update`` with the fixed timestep, so input speed and gravity share one
    clock and a key press is never processed twice.
    """

    def __init__(self, game: Game) -> None:
        self.game = game
        self._left_down = False
        self._right_down = False
        self._horizontal = 0  # -1 left, 1 right, 0 neither.
        self._das_timer = 0.0
        self._arr_armed = False
        self._down_down = False
        self._soft_timer = 0.0

    def handle_keydown(self, key: int) -> None:
        if key == pygame.K_LEFT:
            self._left_down = True
            self._start_horizontal(-1)
        elif key == pygame.K_RIGHT:
            self._right_down = True
            self._start_horizontal(1)
        elif key == pygame.K_DOWN:
            self._down_down = True
            self._soft_timer = 0.0
            self.game.soft_drop()
        elif key == pygame.K_UP:
            self.game.rotate(1)
        elif key == pygame.K_SPACE:
            self.game.hard_drop()
        elif key == pygame.K_c:
            self.game.hold()
        elif key == pygame.K_p:
            self.game.toggle_pause()
        elif key == pygame.K_r:
            self.game.restart()
            self.reset()

    def handle_keyup(self, key: int) -> None:
        if key == pygame.K_LEFT:
            self._left_down = False
            if self._horizontal == -1:
                self._horizontal = 1 if self._right_down else 0
                self._restart_horizontal_timing()
        elif key == pygame.K_RIGHT:
            self._right_down = False
            if self._horizontal == 1:
                self._horizontal = -1 if self._left_down else 0
                self._restart_horizontal_timing()
        elif key == pygame.K_DOWN:
            self._down_down = False
            self._soft_timer = 0.0

    def update(self, dt: float) -> None:
        if self.game.is_game_over:
            self.reset()
            return
        if not self.game.is_playing:
            return

        if self._horizontal:
            self._das_timer += dt
            if not self._arr_armed:
                if self._das_timer >= constants.DAS:
                    self._arr_armed = True
                    self._das_timer -= constants.DAS
                    self.game.move(self._horizontal)
                    while self._das_timer >= constants.ARR:
                        self._das_timer -= constants.ARR
                        self.game.move(self._horizontal)
            else:
                while self._das_timer >= constants.ARR:
                    self._das_timer -= constants.ARR
                    self.game.move(self._horizontal)

        if self._down_down:
            self._soft_timer += dt
            while self._soft_timer >= constants.SOFT_DROP_REPEAT:
                self._soft_timer -= constants.SOFT_DROP_REPEAT
                self.game.soft_drop()

    def reset(self) -> None:
        """Forget held keys and repeat timers (used on restart / game over)."""
        self._left_down = False
        self._right_down = False
        self._horizontal = 0
        self._down_down = False
        self._restart_horizontal_timing()
        self._soft_timer = 0.0

    def _start_horizontal(self, direction: int) -> None:
        self._horizontal = direction
        self._restart_horizontal_timing()
        self.game.move(direction)

    def _restart_horizontal_timing(self) -> None:
        self._das_timer = 0.0
        self._arr_armed = False


def run() -> int:
    """Open the window and run until the player quits. Returns an exit code."""
    try:
        pygame.init()
        pygame.display.set_caption("Tetris")
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    except pygame.error as error:
        print(f"Could not open a game window: {error}")
        print("Tetris needs a graphical display to run.")
        pygame.quit()
        return 1

    # We handle held-key repeat ourselves; disable the OS-level repeats so a
    # key press always produces exactly one KEYDOWN.
    pygame.key.set_repeat(0)

    clock = pygame.time.Clock()
    renderer = Renderer()
    game = Game()
    controls = InputController(game)
    accumulator = 0.0
    running = True
    try:
        while running:
            frame_time = min(
                clock.tick(constants.FPS) / 1000.0, constants.MAX_FRAME_TIME
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if getattr(event, "repeat", False):
                        continue
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        controls.handle_keydown(event.key)
                elif event.type == pygame.KEYUP:
                    controls.handle_keyup(event.key)

            accumulator += frame_time
            while accumulator >= constants.FIXED_TIMESTEP:
                controls.update(constants.FIXED_TIMESTEP)
                game.update(constants.FIXED_TIMESTEP)
                accumulator -= constants.FIXED_TIMESTEP

            renderer.draw(screen, game)
            pygame.display.flip()
    finally:
        pygame.quit()
    return 0
