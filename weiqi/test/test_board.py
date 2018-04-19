import pytest
from weiqi.board import (Board, Node, coord2d, coord_to_2d, BLACK, WHITE, EMPTY, NODE_BLACK, NODE_WHITE,
                         board_from_string, IllegalMoveError, PASS, RESIGN, board_from_dict, neighbors, coord_from_sgf,
                         coord_to_sgf)


def test_coord_to_2d():
    coord = coord2d(4, 5, 9)
    x, y = coord_to_2d(coord, 9)
    assert x == 4
    assert y == 5


def test_coord_from_sgf():
    assert coord_from_sgf("Aa", 19) == coord2d(1, 1, 19)
    assert coord_from_sgf("Ca", 19) == coord2d(3, 1, 19)
    assert coord_from_sgf("dD", 19) == coord2d(4, 4, 19)
    assert coord_from_sgf("Dp", 19) == coord2d(4, 16, 19)
    assert coord_from_sgf("sS", 19) == coord2d(19, 19, 19)


def test_coord_to_sgf():
    assert coord_to_sgf(coord2d(1, 1, 19), 19) == 'aa'
    assert coord_to_sgf(coord2d(3, 1, 19), 19) == 'ca'
    assert coord_to_sgf(coord2d(4, 4, 19), 19) == 'dd'
    assert coord_to_sgf(coord2d(4, 16, 19), 19) == 'dp'
    assert coord_to_sgf(coord2d(19, 19, 19), 19) == 'ss'


def test_neighbors():
    assert set(neighbors(coord2d(1, 1), 9)) == {coord2d(2, 1), coord2d(1, 2)}
    assert set(neighbors(coord2d(9, 9), 9)) == {coord2d(9, 8), coord2d(8, 9)}
    assert set(neighbors(coord2d(5, 5), 9)) == {coord2d(5, 4), coord2d(5, 6),
                                                coord2d(4, 5), coord2d(6, 5)}


def test_toggle_symbol():
    node = Node()

    node.toggle_symbol(180, 'TR')
    assert node.symbols['180'] == 'TR'

    node.toggle_symbol(180, 'TR')
    assert '180' not in node.symbols

    node.toggle_symbol(180, 'TR')
    node.toggle_symbol(180, 'SQ')
    assert node.symbols['180'] == 'SQ'


def test_toggle_label():
    node = Node()

    node.toggle_label(180)
    node.toggle_label(181)
    node.toggle_label(182)
    assert node.labels['180'] == 'A'
    assert node.labels['181'] == 'B'
    assert node.labels['182'] == 'C'

    node.toggle_label(180)
    assert '180' not in node.labels


def test_toggle_number():
    node = Node()

    node.toggle_number(180)
    node.toggle_number(181)
    node.toggle_number(182)
    assert node.labels['180'] == '1'
    assert node.labels['181'] == '2'
    assert node.labels['182'] == '3'

    node.toggle_label(180)
    assert '180' not in node.labels


def test_from_string():
    board = board_from_string(
        '.........'
        '..x......'
        '.........'
        '.........'
        '.........'
        '.........'
        '.........'
        '.......o.'
        '.........')

    assert board.at(coord2d(3, 2)) == BLACK
    assert board.at(coord2d(8, 8)) == WHITE


def test_board_from_dict():
    board = board_from_string(
        '.........'
        '..x......'
        '.........'
        '..o......'
        '.........'
        '.........'
        '.........'
        '..x....o.'
        '.........')
    board.handicap = 1

    from_dict = board_from_dict(board.to_dict())

    assert str(from_dict) == str(board)
    assert from_dict.handicap == 1


def test_play():
    board = Board()

    assert board.current == BLACK
    board.play(coord2d(4, 4))

    assert board.current == WHITE
    board.play(coord2d(3, 3))

    assert board.current == BLACK
    board.play(coord2d(6, 6))

    assert board.at(coord2d(4, 4)) == BLACK
    assert board.at(coord2d(3, 3)) == WHITE
    assert board.at(coord2d(6, 6)) == BLACK


def test_play_node():
    board = Board()

    assert board.current_node_id is None

    board.play(coord2d(4, 4))
    assert board.current_node_id == 0
    assert board.current_node.parent_id is None
    assert board.current_node.children == []
    assert board.current_node.action == NODE_BLACK
    assert board.current_node.move == coord2d(4, 4)

    board.play(coord2d(5, 5))
    assert board.current_node.id == 1
    assert board.current_node.parent_id == 0
    assert board.current_node.children == []
    assert board.tree[0].children == [1]
    assert board.current_node.action == NODE_WHITE
    assert board.current_node.move == coord2d(5, 5)

    board.play(coord2d(6, 6))
    assert board.current_node_id == 2
    assert board.current_node.parent_id == 1
    assert board.current_node.children == []
    assert board.tree[0].children == [1]
    assert board.tree[1].children == [2]
    assert board.current_node.action == NODE_BLACK
    assert board.current_node.move == coord2d(6, 6)


def test_play_captures():
    board = board_from_string(
        '.........'
        '...xxx...'
        '....oox..'
        '..xoox...'
        '..xox....'
        '...x.....'
        '.........'
        '.........'
        '.........')

    board.current = BLACK
    board.play(coord2d(4, 3))

    expected = board_from_string(
        '.........'
        '...xxx...'
        '...x..x..'
        '..x..x...'
        '..x.x....'
        '...x.....'
        '.........'
        '.........'
        '.........')

    assert str(board) == str(expected)


def test_ko_rule():
    board = board_from_string(
        '.........'
        '.........'
        '...o.....'
        '..oxo....'
        '..x.x....'
        '...x.....'
        '.........'
        '.........'
        '.........')

    board.current = WHITE
    board.play(coord2d(4, 5))

    assert board.ko == coord2d(4, 4)

    with pytest.raises(IllegalMoveError):
        board.play(coord2d(4, 4))


def test_snapback_not_ko():
    board = board_from_string(
        '.........'
        '.........'
        '.........'
        '.........'
        '.........'
        '.........'
        'ooo......'
        'xxo.x....'
        '..xx.....')

    board.current = WHITE
    board.play(coord2d(2, 9))
    board.play(coord2d(1, 9))
    board.play(coord2d(2, 9))

    assert board.at(coord2d(1, 8)) == EMPTY
    assert board.at(coord2d(2, 8)) == EMPTY
    assert board.at(coord2d(2, 9)) == WHITE
    assert board.at(coord2d(1, 9)) == EMPTY


def test_chain():
    board = board_from_string(
        '.........'
        '.........'
        '...oxo...'
        '...xoo...'
        '...xx....'
        '....x....'
        '...x.....'
        '.........'
        '.........')

    chains = [
        [coord2d(4, 4), {coord2d(4, 4), coord2d(
            4, 5), coord2d(5, 5), coord2d(5, 6)}],
        [coord2d(4, 3), {coord2d(4, 3)}],
        [coord2d(5, 3), {coord2d(5, 3)}],
        [coord2d(6, 3), {coord2d(6, 3), coord2d(6, 4), coord2d(5, 4)}],
        [coord2d(4, 7), {coord2d(4, 7)}],
    ]

    for c in chains:
        assert board.chain_at(c[0]) == c[1]


def test_loose_chain():
    board = board_from_string(
        '.........'
        '.x.......'
        '.x.xooooo'
        '..ooxxx..'
        '..ox.....'
        '..o.x...x'
        '..o...oox'
        '..o...ox.'
        '..o...o.x')

    coords = {
        coord2d(5, 4),
        coord2d(6, 4),
        coord2d(7, 4),
        coord2d(4, 5),
        coord2d(5, 6),
        coord2d(9, 6),
        coord2d(9, 7),
        coord2d(8, 8),
        coord2d(9, 9),
    }

    chain = board.loose_chain_at(coord2d(5, 6))

    assert chain == coords


def test_chain_liberties():
    board = board_from_string(
        '.........'
        '.........'
        '...oxo...'
        '...xoo...'
        '...xx....'
        '....x....'
        '...x.....'
        '.........'
        '.........')

    assert len(board.chain_liberties(board.chain_at(coord2d(4, 4)))) == 6
    assert len(board.chain_liberties(board.chain_at(coord2d(5, 4)))) == 4


def test_suicide():
    board = board_from_string(
        '.x.......'
        'x........'
        '...x.....'
        '..x.x....'
        '...x.....'
        '.........'
        '.........'
        '.........'
        '.........')

    board.current = WHITE
    assert board.is_suicide(coord2d(1, 1))
    assert board.is_suicide(coord2d(4, 4))


def test_suicide_capture():
    board = board_from_string(
        '.xo......'
        'xo.......'
        '...xo....'
        '..x.xo...'
        '...xo....'
        '.........'
        '.........'
        '.........'
        '.........')

    board.current = WHITE
    assert not board.is_suicide(coord2d(1, 1))
    assert not board.is_suicide(coord2d(4, 4))


def test_pass():
    board = Board()
    board.play(PASS)

    assert board.tree[0].move == PASS
    assert board.current == WHITE


def test_both_passed():
    board = Board()
    assert not board.both_passed

    board.play(PASS)
    assert not board.both_passed

    board.play(PASS)
    assert board.both_passed


def test_current():
    board = Board()
    assert board.current == BLACK

    board.play(1)
    assert board.current == WHITE

    board.play(2)
    assert board.current == BLACK


def test_current_edits():
    board = Board()
    board.current = BLACK
    board.play(1)

    board.add_edits([3], [], [])
    assert board.current == WHITE

    board.play(2)
    board.add_edits([4], [], [])
    board.add_edits([], [5], [])
    assert board.current == BLACK


def test_current_handicap():
    board = Board(9, 2)
    assert board.current == WHITE

    board.play(1)
    assert board.current == BLACK


def test_rebuild_pos():
    pos = ('.........'
           '.x.......'
           '.x.xooooo'
           '..ooxxx..'
           '..ox.....'
           '..o.x...x'
           '..o...oox'
           '..o...ox.'
           '..o...o.x')
    board = board_from_string(pos)

    board.current = WHITE
    board.play(PASS)
    board.play(RESIGN)
    board._rebuild_pos()

    expected = board_from_string(pos)

    assert str(board) == str(expected)


def test_mark_dead():
    board = board_from_string(
        '..xo.....'
        '..xoooo..'
        '..xxxxooo'
        '.....xxxx'
        'xxxx.....'
        'ooox.xxxx'
        '..ox.xooo'
        '..ox.xo..'
        '..ox.xo.o')

    board.mark_dead(coord2d(7, 7))
    chain = board.loose_chain_at(coord2d(7, 7))

    for coord in range(board.length):
        assert board.is_marked_dead(coord) == (coord in chain)


def test_toggle_marked_dead():
    board = board_from_string(
        '..xo.....'
        '..xoooo..'
        '..xxxxooo'
        '.....xxxx'
        'xxxx.....'
        'ooox.xxxx'
        '..ox.xooo'
        '..ox.xo..'
        '..ox.xo.o')

    coord = coord2d(7, 7)
    board.mark_dead(coord)
    board.toggle_marked_dead(coord)

    chain = board.loose_chain_at(coord2d(1, 6))
    board.toggle_marked_dead(coord2d(1, 6))

    for c in range(board.length):
        assert board.is_marked_dead(c) == (c in chain)


def test_place_hc():
    tests = {
        0: ('.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'),
        1: ('.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'
            '.........'),
        2: ('.........'
            '.........'
            '......x..'
            '.........'
            '.........'
            '.........'
            '..x......'
            '.........'
            '.........'),
        3: ('.........'
            '.........'
            '......x..'
            '.........'
            '.........'
            '.........'
            '..x...x..'
            '.........'
            '.........'),
        4: ('.........'
            '.........'
            '..x...x..'
            '.........'
            '.........'
            '.........'
            '..x...x..'
            '.........'
            '.........'),
        5: ('.........'
            '.........'
            '..x...x..'
            '.........'
            '....x....'
            '.........'
            '..x...x..'
            '.........'
            '.........'),
        6: ('.........'
            '.........'
            '..x...x..'
            '.........'
            '..x...x..'
            '.........'
            '..x...x..'
            '.........'
            '.........'),
        7: ('.........'
            '.........'
            '..x...x..'
            '.........'
            '..x.x.x..'
            '.........'
            '..x...x..'
            '.........'
            '.........'),
        8: ('.........'
            '.........'
            '..x.x.x..'
            '.........'
            '..x...x..'
            '.........'
            '..x.x.x..'
            '.........'
            '.........'),
        9: ('.........'
            '.........'
            '..x.x.x..'
            '.........'
            '..x.x.x..'
            '.........'
            '..x.x.x..'
            '.........'
            '.........'),
    }

    for hc, pos in tests.items():
        board = Board(9)
        board.place_handicap(hc)

        assert str(board) == str(board_from_string(pos))


def test_toggle_edit():
    board = Board(9)

    board.toggle_edit(10, BLACK)
    board.toggle_edit(11, WHITE)
    board.toggle_edit(12, WHITE)

    assert board.at(10) == BLACK
    assert board.at(11) == WHITE
    assert board.at(12) == WHITE

    board.toggle_edit(11, WHITE)
    assert board.at(11) == EMPTY


def test_toggle_edit_remove():
    board = Board(9)
    board.play(10)

    board.toggle_edit(10, BLACK)
    assert board.at(10) == EMPTY


def test_toggle_edit_capture():
    board = board_from_string(
        '.........'
        '.........'
        '..ooo....'
        '..oxo....'
        '..oxo....'
        '..xxx....'
        '.........'
        '.........'
        '.........')

    upper = coord2d(4, 4)
    lower = coord2d(4, 5)

    board.toggle_edit(lower, WHITE)
    assert board.at(upper) == EMPTY
    assert board.at(lower) == WHITE


def test_edit_cycle():
    board = Board(9)
    board.toggle_edit(10, BLACK)
    board.toggle_edit(11, WHITE)

    board.edit_cycle(10)
    board.edit_cycle(11)
    board.edit_cycle(12)

    assert board.at(10) == WHITE
    assert board.at(11) == EMPTY
    assert board.at(12) == BLACK


def test_edit_cycle_capture():
    pos = ('.........'
           '.........'
           '..ooo....'
           '..oxo....'
           '..oxo....'
           '..xxx....'
           '.........'
           '.........'
           '.........')

    board = board_from_string(pos)
    center = coord2d(4, 4)
    lower = coord2d(4, 5)

    board.edit_cycle(lower)

    assert board.at(lower) == WHITE
    assert board.at(center) == EMPTY


def test_edit_cycle_suicide():
    board = board_from_string(
        '.........'
        '.........'
        '..ooo....'
        '..o.o....'
        '..ooo....'
        '.........'
        '..xxx....'
        '..x.x....'
        '..xxx....')

    upper = coord2d(4, 4)
    lower = coord2d(4, 8)

    board.edit_cycle(upper)
    board.edit_cycle(lower)
    assert board.at(upper) == WHITE
    assert board.at(lower) == BLACK

    board.edit_cycle(upper)
    board.edit_cycle(lower)
    assert board.at(upper) == EMPTY
    assert board.at(lower) == EMPTY
