import pytest

from tetris import constants
from tetris.board import Board
from tetris.game import Game, GameState, gravity_interval
from tetris.pieces import Piece


def _empty_rows() -> list[str]:
    return ["." * constants.COLS for _ in range(constants.VISIBLE_ROWS)]


def _force_game_over(game: Game) -> None:
    """Fill the next piece's spawn cells and let the game try to deal it."""
    spawn = Piece.spawn(game.next_queue[0])
    for column, row in spawn.cells():
        game.board.grid[row][column] = "X"
    game.current = None
    game.state = GameState.PLAYING
    game._spawn_piece()


def test_initial_state():
    game = Game(seed=1)
    assert game.state is GameState.PLAYING
    assert game.score == 0
    assert game.level == 1
    assert game.lines == 0
    assert game.board.is_empty()
    assert game.current is not None
    assert len(game.next_queue) == 1
    assert game.hold_kind is None
    assert game.can_hold is True


def test_horizontal_movement_stops_at_the_walls():
    game = Game(seed=1)
    game.current = Piece("T", rotation=0, x=3, y=0)

    assert game.move(-1) is True
    assert game.move(-1) is True
    assert game.move(-1) is True
    assert game.current.x == 0
    assert game.move(-1) is False
    assert game.current.x == 0

    for _ in range(7):
        assert game.move(1) is True
    assert game.current.x == 7
    assert game.move(1) is False
    assert game.current.x == 7


def test_soft_drop_scores_one_point_per_row():
    game = Game(seed=1)
    game.current = Piece("T", rotation=0, x=3, y=0)

    assert game.soft_drop() is True
    assert game.current.y == 1
    assert game.soft_drop() is True
    assert game.current.y == 2
    assert game.score == 2


def test_hard_drop_scores_two_points_per_row_and_locks():
    game = Game(seed=1)
    game.current = Piece("T", rotation=0, x=3, y=0)

    distance = game.hard_drop()

    assert distance == 18
    assert game.score == 36
    assert not game.board.is_empty()
    assert game.board.grid[19][4] == "T"
    # A fresh piece has been spawned and can still be played.
    assert game.current is not None
    assert game.current.y == 0
    assert game.is_playing


def test_ghost_piece_shows_the_landing_position_without_moving_the_piece():
    game = Game(seed=1)
    game.current = Piece("T", rotation=0, x=3, y=0)

    ghost = game.ghost_piece()

    assert game.ghost_y() == 18
    assert ghost == Piece("T", rotation=0, x=3, y=18)
    assert game.current == Piece("T", rotation=0, x=3, y=0)
    assert game.board.can_place(ghost.cells())


def test_hold_stores_a_piece_and_can_only_be_used_once_per_piece():
    game = Game(seed=1)
    first_kind = game.current.kind
    next_kind = game.next_queue[0]

    assert game.hold() is True
    assert game.hold_kind == first_kind
    assert game.current.kind == next_kind
    assert game.can_hold is False
    assert game.hold() is False

    game.hard_drop()
    assert game.can_hold is True

    new_kind = game.current.kind
    assert game.hold() is True
    assert game.hold_kind == new_kind
    assert game.current.kind == first_kind


def test_gravity_moves_pieces_and_speeds_up_with_level():
    game = Game(seed=1)
    game.current = Piece("O", rotation=0, x=4, y=0)
    slow_interval = game.gravity_interval

    game.update(slow_interval)
    assert game.current.y == 1

    game.level = 5
    assert game.gravity_interval < slow_interval
    assert gravity_interval(20) == pytest.approx(constants.MIN_GRAVITY)
    for level in (1, 2, 3, 5, 10, 15):
        assert gravity_interval(level + 1) < gravity_interval(level)


def test_grounded_piece_locks_after_the_lock_delay():
    game = Game(seed=1)
    game.current = Piece("O", rotation=0, x=4, y=18)

    game.update(constants.LOCK_DELAY / 2)
    assert game.board.is_empty()

    game.update(constants.LOCK_DELAY / 2 + 0.01)
    assert game.board.grid[18][4] == "O"
    assert game.current is not None
    assert game.current.y == 0


def test_moving_a_grounded_piece_restarts_its_lock_delay():
    game = Game(seed=1)
    game.current = Piece("O", rotation=0, x=4, y=18)

    game.update(constants.LOCK_DELAY * 0.8)
    assert game.move(1) is True
    game.update(constants.LOCK_DELAY * 0.8)
    assert game.board.is_empty()

    game.update(constants.LOCK_DELAY * 0.3)
    assert game.board.grid[18][5] == "O"


def test_pause_freezes_gravity_and_gameplay_actions():
    game = Game(seed=1)
    game.current = Piece("T", rotation=0, x=3, y=0)
    game.gravity_timer = 0.0

    assert game.toggle_pause() is True
    assert game.is_paused

    game.update(10.0)
    assert game.current.y == 0
    assert game.move(1) is False
    assert game.rotate(1) is False
    assert game.soft_drop() is False
    assert game.hard_drop() == 0
    assert game.hold() is False

    assert game.toggle_pause() is False
    game.update(game.gravity_interval)
    assert game.current.y == 1


def test_single_line_clear_scores_at_the_current_level():
    game = Game(seed=1)
    rows = _empty_rows()
    rows[19] = "###....###"  # Columns 3-6 are empty.
    game.board = Board.from_rows(rows)
    game.current = Piece("I", rotation=0, x=3, y=18)

    assert game.hard_drop() == 0
    assert game.lines == 1
    assert game.score == 100
    assert game.level == 1
    assert game.board.is_empty()


def test_double_line_clear_scores_300_times_level():
    game = Game(seed=1)
    rows = _empty_rows()
    rows[18] = "########.."
    rows[19] = "########.."
    game.board = Board.from_rows(rows)
    game.current = Piece("O", rotation=0, x=8, y=18)

    assert game.hard_drop() == 0
    assert game.lines == 2
    assert game.score == 300
    assert game.board.is_empty()


def test_four_line_clear_scores_800_times_level():
    game = Game(seed=1)
    rows = _empty_rows()
    for row in range(16, 20):
        rows[row] = "#########."
    game.board = Board.from_rows(rows)
    game.current = Piece("I", rotation=1, x=7, y=16)

    assert game.hard_drop() == 0
    assert game.lines == 4
    assert game.score == 800
    assert game.level == 1
    assert game.board.is_empty()


def test_line_clear_uses_the_level_it_happened_at():
    game = Game(seed=1)
    rows = _empty_rows()
    rows[19] = "###....###"
    game.board = Board.from_rows(rows)
    game.current = Piece("I", rotation=0, x=3, y=18)
    game.lines = 10
    game.level = 2

    assert game.hard_drop() == 0
    assert game.score == 200
    assert game.lines == 11
    assert game.level == 2


def test_level_increases_every_ten_lines():
    game = Game(seed=1)
    rows = _empty_rows()
    rows[19] = "###....###"
    game.board = Board.from_rows(rows)
    game.current = Piece("I", rotation=0, x=3, y=18)
    game.lines = 9
    game.level = 1

    assert game.hard_drop() == 0
    assert game.lines == 10
    assert game.level == 2
    assert game.score == 100


def test_game_over_when_a_new_piece_cannot_enter_and_restart_clears_state():
    game = Game(seed=1)
    _force_game_over(game)

    assert game.state is GameState.GAME_OVER
    assert game.is_game_over
    assert game.current is None
    assert game.move(1) is False
    assert game.rotate(1) is False
    assert game.soft_drop() is False
    assert game.hard_drop() == 0
    assert game.hold() is False
    assert game.toggle_pause() is False
    game.update(5.0)
    assert game.state is GameState.GAME_OVER

    game.restart()
    assert game.state is GameState.PLAYING
    assert game.board.is_empty()
    assert game.current is not None
    assert game.score == 0
    assert game.level == 1
    assert game.lines == 0
    assert game.hold_kind is None
    assert game.can_hold is True
