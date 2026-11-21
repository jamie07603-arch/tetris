"""Pygame rendering for the Tetris board and side panel."""

from __future__ import annotations

import pygame

from . import constants
from .game import Game
from .pieces import CELL_OFFSETS, Piece

# Layout --------------------------------------------------------------------
CELL = 30
BOARD_X = 40
BOARD_Y = 80
BOARD_WIDTH = constants.COLS * CELL
BOARD_HEIGHT = constants.VISIBLE_ROWS * CELL

PANEL_X = 380
PANEL_WIDTH = 260
WINDOW_WIDTH = 680
WINDOW_HEIGHT = 740

PREVIEW_CELL = 22

# Palette -------------------------------------------------------------------
BACKGROUND = (13, 16, 24)
BOARD_BACKGROUND = (20, 24, 35)
GRID_COLOR = (33, 38, 54)
BOARD_BORDER = (66, 74, 96)
PANEL_BACKGROUND = (23, 27, 39)
PANEL_BORDER = (45, 52, 70)
TEXT = (232, 237, 247)
MUTED_TEXT = (138, 148, 170)
ACCENT = (94, 234, 212)

PIECE_COLORS: dict[str, tuple[int, int, int]] = {
    "I": (34, 211, 238),
    "O": (250, 204, 21),
    "T": (168, 85, 247),
    "S": (34, 197, 94),
    "Z": (239, 68, 68),
    "J": (59, 130, 246),
    "L": (249, 115, 22),
}

CONTROL_LINES: tuple[tuple[str, str], ...] = (
    ("Left / Right", "Move"),
    ("Up", "Rotate"),
    ("Down", "Soft drop"),
    ("Space", "Hard drop"),
    ("C", "Hold"),
    ("P", "Pause"),
    ("R", "Restart"),
    ("Esc", "Quit"),
)


def _lighten(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(min(255, channel + amount) for channel in color)


def _darken(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(max(0, channel - amount) for channel in color)


def _blend(
    first: tuple[int, int, int], second: tuple[int, int, int], amount: float
) -> tuple[int, int, int]:
    return tuple(
        int(first_channel * amount + second_channel * (1.0 - amount))
        for first_channel, second_channel in zip(first, second)
    )


class Renderer:
    """Draws a ``Game``. Owns only cached fonts; all game state lives in Game."""

    def __init__(self) -> None:
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._fonts:
            font = pygame.font.Font(None, size)
            font.set_bold(bold)
            self._fonts[key] = font
        return self._fonts[key]

    # -- Public drawing entry point ------------------------------------

    def draw(self, surface: pygame.Surface, game: Game) -> None:
        surface.fill(BACKGROUND)
        self._draw_title(surface)
        self._draw_board(surface, game)
        self._draw_panel(surface, game)
        if game.is_paused:
            self._draw_overlay(surface, "PAUSED", "Press P to resume")
        elif game.is_game_over:
            self._draw_overlay(
                surface, "GAME OVER", f"Score {game.score}", "Press R to restart"
            )

    # -- Board ---------------------------------------------------------

    def _draw_title(self, surface: pygame.Surface) -> None:
        title = self._font(42, bold=True).render("TETRIS", True, TEXT)
        surface.blit(title, (BOARD_X, 26))
        self._text(
            surface,
            "PYGAME EDITION",
            self._font(16, bold=True),
            ACCENT,
            (BOARD_X + title.get_width() + 14, 48),
        )

    def _draw_board(self, surface: pygame.Surface, game: Game) -> None:
        board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_WIDTH, BOARD_HEIGHT)
        pygame.draw.rect(surface, BOARD_BACKGROUND, board_rect)

        for column in range(1, constants.COLS):
            x = BOARD_X + column * CELL
            pygame.draw.line(
                surface, GRID_COLOR, (x, BOARD_Y), (x, BOARD_Y + BOARD_HEIGHT)
            )
        for row in range(1, constants.VISIBLE_ROWS):
            y = BOARD_Y + row * CELL
            pygame.draw.line(
                surface, GRID_COLOR, (BOARD_X, y), (BOARD_X + BOARD_WIDTH, y)
            )

        for row, line in enumerate(game.board.grid):
            for column, kind in enumerate(line):
                if kind is None:
                    continue
                self._draw_block(
                    surface,
                    BOARD_X + column * CELL,
                    BOARD_Y + row * CELL,
                    CELL,
                    PIECE_COLORS.get(kind, MUTED_TEXT),
                )

        ghost = game.ghost_piece()
        if ghost is not None:
            self._draw_ghost(surface, ghost)

        if game.current is not None:
            for column, row in game.current.cells():
                if 0 <= row < constants.VISIBLE_ROWS:
                    self._draw_block(
                        surface,
                        BOARD_X + column * CELL,
                        BOARD_Y + row * CELL,
                        CELL,
                        PIECE_COLORS[game.current.kind],
                    )

        pygame.draw.rect(surface, BOARD_BORDER, board_rect, width=2)

    def _draw_block(
        self,
        surface: pygame.Surface,
        left: int,
        top: int,
        size: int,
        color: tuple[int, int, int],
    ) -> None:
        rect = pygame.Rect(left + 1, top + 1, size - 2, size - 2)
        radius = max(2, size // 8)
        pygame.draw.rect(surface, color, rect, border_radius=radius)

        light = _lighten(color, 45)
        dark = _darken(color, 55)
        pygame.draw.line(
            surface, light, (rect.left + 2, rect.top + 2), (rect.right - 3, rect.top + 2), 2
        )
        pygame.draw.line(
            surface, light, (rect.left + 2, rect.top + 2), (rect.left + 2, rect.bottom - 3), 2
        )
        pygame.draw.line(
            surface,
            dark,
            (rect.left + 2, rect.bottom - 3),
            (rect.right - 3, rect.bottom - 3),
            2,
        )
        pygame.draw.line(
            surface,
            dark,
            (rect.right - 3, rect.top + 2),
            (rect.right - 3, rect.bottom - 3),
            2,
        )

    def _draw_ghost(self, surface: pygame.Surface, ghost: Piece) -> None:
        color = PIECE_COLORS[ghost.kind]
        fill = _blend(color, BOARD_BACKGROUND, 0.22)
        outline = _blend(color, BOARD_BACKGROUND, 0.6)
        for column, row in ghost.cells():
            if not 0 <= row < constants.VISIBLE_ROWS:
                continue
            rect = pygame.Rect(
                BOARD_X + column * CELL + 2,
                BOARD_Y + row * CELL + 2,
                CELL - 4,
                CELL - 4,
            )
            pygame.draw.rect(surface, fill, rect, border_radius=2)
            pygame.draw.rect(surface, outline, rect, width=2, border_radius=2)

    # -- Side panel ----------------------------------------------------

    def _draw_panel(self, surface: pygame.Surface, game: Game) -> None:
        self._draw_card(surface, pygame.Rect(PANEL_X, 80, PANEL_WIDTH, 128), "HOLD")
        self._draw_card(surface, pygame.Rect(PANEL_X, 224, PANEL_WIDTH, 128), "NEXT")
        self._draw_card(surface, pygame.Rect(PANEL_X, 368, PANEL_WIDTH, 148), "STATS")
        self._draw_card(
            surface, pygame.Rect(PANEL_X, 532, PANEL_WIDTH, 168), "CONTROLS"
        )

        hold_box = pygame.Rect(PANEL_X + 14, 118, PANEL_WIDTH - 28, 78)
        if game.hold_kind is not None:
            color = PIECE_COLORS[game.hold_kind]
            if not game.can_hold:
                color = _blend(color, PANEL_BACKGROUND, 0.45)
            self._draw_piece_preview(surface, game.hold_kind, hold_box, color)
        else:
            self._centered_text(
                surface, "EMPTY", self._font(16), MUTED_TEXT, hold_box.center
            )

        next_box = pygame.Rect(PANEL_X + 14, 262, PANEL_WIDTH - 28, 78)
        if game.next_queue:
            self._draw_piece_preview(
                surface,
                game.next_queue[0],
                next_box,
                PIECE_COLORS[game.next_queue[0]],
            )

        self._draw_stats(surface, game)
        self._draw_controls(surface)

    def _draw_card(
        self, surface: pygame.Surface, rect: pygame.Rect, title: str
    ) -> None:
        pygame.draw.rect(surface, PANEL_BACKGROUND, rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER, rect, width=1, border_radius=10)
        self._text(
            surface,
            title,
            self._font(17, bold=True),
            MUTED_TEXT,
            (rect.x + 14, rect.y + 10),
        )

    def _draw_piece_preview(
        self,
        surface: pygame.Surface,
        kind: str,
        box: pygame.Rect,
        color: tuple[int, int, int],
    ) -> None:
        offsets = CELL_OFFSETS[kind][0]
        min_column = min(column for column, _ in offsets)
        max_column = max(column for column, _ in offsets)
        min_row = min(row for _, row in offsets)
        max_row = max(row for _, row in offsets)
        width = (max_column - min_column + 1) * PREVIEW_CELL
        height = (max_row - min_row + 1) * PREVIEW_CELL
        origin_x = box.centerx - width // 2
        origin_y = box.centery - height // 2
        for column, row in offsets:
            self._draw_block(
                surface,
                origin_x + (column - min_column) * PREVIEW_CELL,
                origin_y + (row - min_row) * PREVIEW_CELL,
                PREVIEW_CELL,
                color,
            )

    def _draw_stats(self, surface: pygame.Surface, game: Game) -> None:
        x = PANEL_X + 16
        y = 368
        self._text(surface, "SCORE", self._font(15, bold=True), MUTED_TEXT, (x, y + 36))
        self._text(
            surface, f"{game.score:06d}", self._font(34, bold=True), TEXT, (x, y + 54)
        )
        self._text(surface, "LEVEL", self._font(15, bold=True), MUTED_TEXT, (x, y + 102))
        self._text(
            surface, f"{game.level:02d}", self._font(27, bold=True), TEXT, (x, y + 118)
        )
        self._text(
            surface,
            "LINES",
            self._font(15, bold=True),
            MUTED_TEXT,
            (PANEL_X + 140, y + 102),
        )
        self._text(
            surface,
            f"{game.lines:03d}",
            self._font(27, bold=True),
            TEXT,
            (PANEL_X + 140, y + 118),
        )

    def _draw_controls(self, surface: pygame.Surface) -> None:
        x = PANEL_X + 16
        y = 532 + 34
        font = self._font(15)
        for index, (key, action) in enumerate(CONTROL_LINES):
            line_y = y + index * 16
            self._text(surface, key, font, ACCENT, (x, line_y))
            self._text(surface, action, font, TEXT, (x + 108, line_y))

    # -- Overlays ------------------------------------------------------

    def _draw_overlay(
        self, surface: pygame.Surface, title: str, *lines: str
    ) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 7, 12, 190))
        surface.blit(overlay, (0, 0))

        panel = pygame.Rect(BOARD_X + 16, BOARD_Y + 190, BOARD_WIDTH - 32, 210)
        pygame.draw.rect(surface, (18, 22, 33), panel, border_radius=12)
        pygame.draw.rect(surface, ACCENT, panel, width=2, border_radius=12)

        center_x = panel.centerx
        title_surface = self._font(48, bold=True).render(title, True, TEXT)
        surface.blit(
            title_surface, title_surface.get_rect(center=(center_x, panel.top + 62))
        )
        for index, line in enumerate(lines):
            color = ACCENT if index == len(lines) - 1 else MUTED_TEXT
            font = self._font(18 if index == len(lines) - 1 else 26, bold=index == 0)
            line_surface = font.render(line, True, color)
            surface.blit(
                line_surface,
                line_surface.get_rect(center=(center_x, panel.top + 116 + index * 36)),
            )

    # -- Text helpers --------------------------------------------------

    def _text(
        self,
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
    ) -> None:
        surface.blit(font.render(text, True, color), position)

    def _centered_text(
        self,
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        center: tuple[int, int],
    ) -> None:
        rendered = font.render(text, True, color)
        surface.blit(rendered, rendered.get_rect(center=center))
