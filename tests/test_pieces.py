import pytest

from tetris.board import Board
from tetris.game import Game
from tetris.pieces import CELL_OFFSETS, TETROMINO_KINDS, Piece


def test_there_are_seven_unique_tetrominoes():
    assert set(TETROMINO_KINDS) == {"I", "O", "T", "S", "Z", "J", "L"}
    assert len(TETROMINO_KINDS) == 7


@pytest.mark.parametrize("kind", TETROMINO_KINDS)
def test_every_rotation_has_four_distinct_cells(kind):
    for rotation in range(4):
        cells = CELL_OFFSETS[kind][rotation]
        assert len(cells) == 4
        assert len(set(cells)) == 4


@pytest.mark.parametrize("kind", TETROMINO_KINDS)
def test_four_rotations_return_to_spawn_shape(kind):
    piece = Piece.spawn(kind)
    for _ in range(4):
        piece = piece.rotated(1)
    assert piece.cells() == Piece.spawn(kind).cells()


def test_all_pieces_spawn_inside_the_board():
    board = Board()
    for kind in TETROMINO_KINDS:
        assert board.can_place(Piece.spawn(kind).cells())


def test_rotated_rejects_180_degree_direction():
    with pytest.raises(ValueError):
        Piece.spawn("T").rotated(2)


def test_i_piece_kicks_off_the_floor():
    game = Game(seed=1)
    game.current = Piece("I", rotation=0, x=3, y=18)

    assert game.rotate(1) is True

    # SRS 0->R: the last kick moves the piece up two rows.
    assert game.current == Piece("I", rotation=1, x=4, y=16)
    assert game.board.can_place(game.current.cells())


def test_i_piece_kicks_away_from_the_left_wall():
    game = Game(seed=1)
    game.current = Piece("I", rotation=1, x=-2, y=0)

    assert game.rotate(1) is True

    # SRS R->2 kicks the vertical I two columns to the right.
    assert game.current == Piece("I", rotation=2, x=0, y=0)
    assert game.board.can_place(game.current.cells())


def test_t_piece_kicks_up_from_the_floor():
    game = Game(seed=1)
    game.current = Piece("T", rotation=0, x=3, y=18)

    # The right-facing T is three rows tall, so the floor forces a kick up.
    assert game.rotate(1) is True
    assert game.current == Piece("T", rotation=1, x=2, y=17)
    assert game.rotate(1) is True
    assert game.current == Piece("T", rotation=2, x=2, y=17)
    assert game.board.can_place(game.current.cells())


def test_blocked_rotation_keeps_the_piece_in_place():
    game = Game(seed=1)
    rows = ["." * 10 for _ in range(20)]
    rows[17] = "......X..."  # Blocks the only kick that would fit.
    game.board = Board.from_rows(rows)
    game.current = Piece("I", rotation=0, x=3, y=18)

    assert game.rotate(1) is False
    assert game.current == Piece("I", rotation=0, x=3, y=18)
