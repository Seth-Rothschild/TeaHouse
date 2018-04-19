from datetime import datetime

from weiqi.board import coord_from_sgf, coord2d, Board, BLACK, WHITE
from weiqi.models import Game
from weiqi.sgf import (Reader, parse_property_name, parse_property_value, parse_sgf, game_from_sgf, game_to_sgf,
                       sgf_part_from_node)


def test_property_name():
    tests = [
        ['prop', 'prop'],
        ['prop[val]', 'prop']
    ]

    for t in tests:
        assert parse_property_name(Reader(t[0])) == t[1]


def test_property_value():
    tests = [
        ['[val]', 'val'],
        ['[val]rest', 'val'],
        ['[val\\]more]', 'val]more'],
        ['[val\\more]', 'val\\more'],
    ]

    for t in tests:
        assert parse_property_value(Reader(t[0])) == t[1]


def test_parse_sgf():
    node = parse_sgf('(;SZ[9]EV[event]KM[7.5];B[qd];W[dc];B[pq];W[dp])')

    assert node.prop_one('sz') == '9'
    assert node.prop_one('ev') == 'event'
    assert node.prop_one('km') == '7.5'

    moves = [
        ['B', 'qd'],
        ['W', 'dc'],
        ['B', 'pq'],
        ['W', 'dp'],
    ]

    for move in moves:
        assert len(node.children) == 1

        node = node.children[0]
        assert len(node.props) == 1
        assert node.prop_one(move[0]) == move[1]


def test_parse_variations():
    node = parse_sgf('(;B[qd](;W[dc];B[pq])(;W[dp];B[pp]))')

    assert node.prop_one('b') == 'qd'
    assert len(node.children) == 2

    assert node.children[0].prop_one('w') == 'dc'
    assert len(node.children[0].children) == 1
    assert node.children[0].children[0].prop_one('b') == 'pq'

    assert node.children[1].prop_one('w') == 'dp'
    assert len(node.children[1].children) == 1
    assert node.children[1].children[0].prop_one('b') == 'pp'


def test_game_info():
    game = game_from_sgf(
        """
        (;GM[1]FF[4]CA[UTF-8]AP[CGoban:3]ST[2]
        RU[Japanese]SZ[9]HA[2]KM[6.50]RE[B+R]EV[event]
        PW[White]PB[Black]AB[gc][cg]
        (;W[gg]
        ;B[ff])
        (;W[ee]
        ;B[gg]))
        """)

    assert game.result == 'B+R'
    assert game.komi == 6.5
    assert game.black_display == 'Black'
    assert game.white_display == 'White'
    assert game.title == 'event'


def test_game_board():
    game = game_from_sgf(
        """
        (;GM[1]FF[4]CA[UTF-8]AP[CGoban:3]ST[2]
        RU[Japanese]SZ[9]HA[2]KM[6.50]
        PW[White]PB[Black]AB[gc][cg]
        (;W[gg]
        ;B[ff]
        ;W[dd])
        (;W[ee]
        ;B[gg]))
        """)

    assert len(game.board.tree) == 6
    assert game.board.current_node_id == 0
    assert len(game.board.current_node.children) == 2
    assert game.board.current_node.action == 'E'

    child = game.board.tree[game.board.current_node.children[0]]
    grand_child = game.board.tree[child.children[0]]
    assert child.action == 'W'
    assert child.move == coord_from_sgf('gg', game.board.size)
    assert grand_child.action == 'B'
    assert grand_child.move == coord_from_sgf('ff', game.board.size)

    child = game.board.tree[game.board.current_node.children[1]]
    grand_child = game.board.tree[child.children[0]]
    assert child.action == 'W'
    assert child.move == coord_from_sgf('ee', game.board.size)
    assert grand_child.action == 'B'
    assert grand_child.move == coord_from_sgf('gg', game.board.size)


def test_game_board_setup_stones():
    game = game_from_sgf('(;AB[dd][de]AW[qq][qr])')

    assert len(game.board.tree) == 1

    node = game.board.tree[0]
    assert len(node.children) == 0
    assert len(node.edits.items()) == 4
    assert node.edits.get(str(coord_from_sgf('dd', 19))) == BLACK
    assert node.edits.get(str(coord_from_sgf('de', 19))) == BLACK
    assert node.edits.get(str(coord_from_sgf('qq', 19))) == WHITE
    assert node.edits.get(str(coord_from_sgf('qr', 19))) == WHITE


def test_game_to_sgf_basic():
    game = Game(board=Board(19),
                black_display='black',
                white_display='white',
                created_at=datetime(2016, 5, 7),
                result='B+1.5',
                komi=7.5)

    game.board.play(coord2d(4, 4, 19))
    game.board.play(coord2d(16, 17, 19))

    sgf = game_to_sgf(game)
    expected = '(;SO[weiqi.gs]FF[4]DT[2016-05-07]PW[white]PB[black]KM[7.5]SZ[19]RE[B+1.5];B[dd];W[pq])'

    assert sgf.replace('\n', '') == expected


def test_game_to_sgf_part_variations():
    board = Board(19)
    board.play(coord2d(4, 4, 19))
    board.play(coord2d(16, 17, 19))
    board.current_node_id = 0
    board.play(coord2d(17, 16, 19))

    sgf = sgf_part_from_node(board, 0)

    assert sgf == ';B[dd](;W[pq])(;W[qp])'


def test_game_to_sgf_part_handicap():
    board = Board(19, 2)
    board.play(coord2d(10, 10, 19))

    sgf = sgf_part_from_node(board, 0)

    assert (sgf == ';AB[dp][pd];W[jj]' or sgf == ';AB[pd][dp];W[jj]')


def test_game_to_sgf_part_symbols():
    board = Board(19)
    board.play(coord2d(10, 10, 19))
    board.current_node.toggle_symbol(180, 'TR')
    board.current_node.toggle_symbol(181, 'TR')
    board.current_node.toggle_symbol(182, 'SQ')

    sgf = sgf_part_from_node(board, 0)

    assert (sgf == ';B[jj]TR[jj][kj]SQ[lj]' or sgf == ';B[jj]TR[kj][jj]SQ[lj]')


def test_game_to_sgf_part_labels():
    board = Board(19)
    board.play(coord2d(10, 10, 19))
    board.current_node.toggle_label(180)
    board.current_node.toggle_label(181)

    sgf = sgf_part_from_node(board, 0)

    assert (sgf == ';B[jj]LB[jj:A][kj:B]' or sgf == ';B[jj]LB[kj:B][jj:A]')
