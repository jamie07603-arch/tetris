from tetris.pieces import TETROMINO_KINDS
from tetris.randomizer import SevenBag


def test_each_bag_deals_every_piece_exactly_once():
    bag = SevenBag(seed=123)
    for _ in range(5):
        drawn = [bag.next_piece() for _ in range(7)]
        assert sorted(drawn) == sorted(TETROMINO_KINDS)


def test_same_seed_produces_the_same_sequence():
    first = SevenBag(seed=7)
    second = SevenBag(seed=7)
    assert [first.next_piece() for _ in range(21)] == [
        second.next_piece() for _ in range(21)
    ]


def test_different_seeds_produce_different_sequences():
    first = SevenBag(seed=1)
    second = SevenBag(seed=999)
    assert [first.next_piece() for _ in range(70)] != [
        second.next_piece() for _ in range(70)
    ]
