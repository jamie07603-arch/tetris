import pytest

from tetris.board import Board
from tetris.constants import COLS, VISIBLE_ROWS
from tetris.pieces import Piece


def test_new_board_is_empty_and_has_expected_dimensions():
    board = Board()
    assert board.rows == VISIBLE_ROWS
    assert board.cols == COLS
    assert board.is_empty()
    assert board.full_rows() == []


def test_out_of_bounds_and_occupied_cells_are_not_placeable():
    board = Board()
    assert not board.can_place([(-1, 0)])
    assert not board.can_place([(COLS, 0)])
    assert not board.can_place([(0, VISIBLE_ROWS)])
    assert board.can_place(Piece.spawn("T").cells())

    board.grid[5][5] = "J"
    assert not board.can_place([(5, 5)])
    assert board.can_place([(4, 5)])


def test_lock_writes_the_piece_kind_and_rejects_overlap():
    board = Board()
    piece = Piece("O", x=4, y=18)
    board.lock(piece)
    assert board.grid[18][4] == "O"
    assert board.grid[19][5] == "O"

    with pytest.raises(ValueError):
        board.lock(Piece("T", x=3, y=18))


def test_lock_rejects_a_piece_that_leaves_the_board():
    board = Board()
    with pytest.raises(ValueError):
        board.lock(Piece("I", rotation=0, x=3, y=19))


def test_clear_lines_removes_a_single_full_row():
    rows = ["." * 10 for _ in range(20)]
    rows[19] = "###....###"
    board = Board.from_rows(rows)
    board.lock(Piece("I", rotation=0, x=3, y=18))

    assert board.clear_lines() == 1
    assert board.is_empty()


def test_clear_lines_removes_multiple_rows_at_once():
    rows = ["." * 10 for _ in range(20)]
    rows[18] = "########.."
    rows[19] = "########.."
    board = Board.from_rows(rows)
    board.lock(Piece("O", x=8, y=18))

    assert board.clear_lines() == 2
    assert board.is_empty()


def test_rows_above_the_clear_shift_down():
    rows = ["." * 10 for _ in range(20)]
    rows[18] = "J........."
    rows[19] = "##########"
    board = Board.from_rows(rows)

    assert board.clear_lines() == 1
    assert board.grid[19][0] == "J"
    assert all(cell is None for cell in board.grid[18])


def test_a_row_with_a_gap_is_not_cleared():
    rows = ["." * 10 for _ in range(20)]
    rows[19] = "#########."
    board = Board.from_rows(rows)

    assert board.full_rows() == []
    assert board.clear_lines() == 0
    assert board.grid[19][0] == "#"


def test_drop_distance_stops_on_the_floor_and_on_blocks():
    empty = Board()
    assert empty.drop_distance(Piece.spawn("T")) == 18

    rows = ["." * 10 for _ in range(20)]
    rows[19] = "....#....."
    blocked = Board.from_rows(rows)
    # The T piece's middle column is blocked one row above the floor.
    assert blocked.drop_distance(Piece.spawn("T")) == 17


def test_from_rows_validates_its_input():
    with pytest.raises(ValueError):
        Board.from_rows([])
    with pytest.raises(ValueError):
        Board.from_rows(["...", ".."])
