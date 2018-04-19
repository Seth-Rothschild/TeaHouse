from weiqi.board import board_from_string, BLACK, WHITE, EMPTY, coord2d
from weiqi.scoring import count_score, can_reach_only


def test_can_reach_only():
    board = board_from_string(
        '.....x.o.'
        '.....x.o.'
        '.....x.o.'
        '.....xo..'
        '.....xo..'
        '....xxo..'
        'xxxx..o..'
        'ooooo.o..'
        '.....o...')

    assert can_reach_only(board, coord2d(1, 1), BLACK)[0]
    assert not can_reach_only(board, coord2d(1, 1), WHITE)[0]

    assert can_reach_only(board, coord2d(9, 9), WHITE)[0]
    assert not can_reach_only(board, coord2d(9, 9), BLACK)[0]

    assert not can_reach_only(board, coord2d(6, 7), BLACK)[0]
    assert not can_reach_only(board, coord2d(6, 7), WHITE)[0]


def test_basic():
    board = board_from_string(
        '.....xo..'
        '.....xo..'
        '.....xo..'
        '.....xo..'
        '.....xo..'
        '.....xo..'
        'xxxxxxo..'
        'ooooooo..'
        '.........')

    score = count_score(board, 7.5)

    assert score.black == 42
    assert score.white == 39 + 7.5
    assert score.winner == WHITE
    assert score.win_by == 4.5


def test_handicap():
    board = board_from_string(
        '.....xo..'
        '.....xo..'
        '.....xo..'
        '.....xo..'
        '.....xo..'
        '.....xo..'
        'xxxxxxo..'
        'ooooooo..'
        '.........')

    board.handicap = 4

    score = count_score(board, 0.5)

    assert score.black == 42
    assert score.white == 39 + 4 + 0.5
    assert score.winner == WHITE
    assert score.win_by == 1.5


def test_multiple_groups():
    board = board_from_string(
        '..xo.....'
        '..xoooo..'
        '..xxxxooo'
        '.....xxxx'
        'xxxx.....'
        'ooox.xxxx'
        '..ox.xooo'
        '..ox.xo..'
        '..ox.xo..')

    score = count_score(board, 7.5)

    assert score.black == 45
    assert score.white == 36 + 7.5
    assert score.winner == BLACK
    assert score.win_by == 1.5


def test_marked_dead():
    board = board_from_string(
        '.ox......'
        '.oxxx....'
        '.oooxxxxx'
        'xxxoooooo'
        '.x....oxx'
        'xooooox..'
        'xoooxxxx.'
        '.oxxxooox'
        '.ox.xo.o.')

    board.mark_dead(coord2d(1, 4))
    board.mark_dead(coord2d(8, 9))

    score = count_score(board, 7.5)

    assert score.black == 43
    assert score.white == 38 + 7.5
    assert score.winner == WHITE
    assert score.win_by == 2.5


def test_neutral_points():
    board = board_from_string(
        '.....x.o.'
        '.....x.o.'
        '.....x.o.'
        '.....xo..'
        '.....xo..'
        '....xxo..'
        'xxxx..o..'
        'ooooo.o..'
        '.....o...')

    score = count_score(board, 7.5)

    assert score.black == 40
    assert score.white == 35 + 7.5
    assert score.winner == WHITE
    assert score.win_by == 2.5
    assert score.points[coord2d(7, 1)] == EMPTY
    assert score.points[coord2d(7, 2)] == EMPTY
    assert score.points[coord2d(7, 3)] == EMPTY
    assert score.points[coord2d(5, 7)] == EMPTY
    assert score.points[coord2d(6, 7)] == EMPTY
    assert score.points[coord2d(6, 8)] == EMPTY
