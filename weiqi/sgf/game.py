from collections import defaultdict

from weiqi.board import (Board, coord_from_sgf, coord_to_sgf, BLACK, WHITE, EMPTY, NODE_WHITE, NODE_BLACK, NODE_EDIT,
                         SYMBOL_TRIANGLE, SYMBOL_SQUARE, SYMBOL_CIRCLE)
from weiqi.models import Game
from weiqi.sgf import parse_sgf


def game_from_sgf(sgf):
    node = parse_sgf(sgf)
    return game_from_node(node)


def game_from_node(node):
    game = Game(is_demo=True)
    game.board = Board(int(node.prop_one('SZ', '19')))
    game.komi = float(node.prop_one('KM', 6.5))
    game.result = node.prop_one('RE')
    game.black_display = node.prop_one('PB')
    game.white_display = node.prop_one('PW')
    game.title = node.prop_one('EV')

    _replay_game(game.board, node)

    if game.board.tree:
        game.board.current_node_id = 0

    return game


def _replay_game(board, node):
    if node.props.get('AB') or node.props.get('AW') or node.props.get('AE'):
        board.add_edits(_prop_coords(node.props.get('AB'), board.size),
                        _prop_coords(node.props.get('AW'), board.size),
                        _prop_coords(node.props.get('AE'), board.size))

    if node.prop_one('B'):
        board.current = BLACK
        board.play(coord_from_sgf(node.prop_one('B'), board.size))

    if node.prop_one('W'):
        board.current = WHITE
        board.play(coord_from_sgf(node.prop_one('W'), board.size))

    current_node_id = board.current_node_id

    for child in node.children:
        board.current_node_id = current_node_id
        _replay_game(board, child)


def _prop_coords(coords, size):
    if not coords:
        return []
    return [coord_from_sgf(c, size) for c in coords]


def game_to_sgf(game):
    sgf = '(;SO[weiqi.gs]\nFF[4]\nDT[%(dt)s]\nPW[%(pw)s]\nPB[%(pb)s]\nKM[%(km).1f]\nSZ[%(sz)d]\n' % {
        'dt': game.created_at.date().isoformat(),
        'pw': game.white_display,
        'pb': game.black_display,
        'km': game.komi,
        'sz': game.board.size
    }

    if game.result:
        sgf += 'RE[%s]\n' % game.result

    if len(game.board.tree) > 0:
        sgf += sgf_part_from_node(game.board, 0)

    sgf += ')'

    return sgf


def sgf_part_from_node(board, node_id):
    part = ';'
    node = board.tree[node_id]

    if node.action == NODE_BLACK:
        part += 'B[%s]' % coord_to_sgf(node.move, board.size)
    elif node.action == NODE_WHITE:
        part += 'W[%s]' % coord_to_sgf(node.move, board.size)
    elif node.action == NODE_EDIT:
        edits = defaultdict(list)
        for coord, color in node.edits.items():
            edits[color].append(coord_to_sgf(int(coord), board.size))

        ab = ''.join('[%s]' % c for c in edits[BLACK])
        aw = ''.join('[%s]' % c for c in edits[WHITE])
        ae = ''.join('[%s]' % c for c in edits[EMPTY])

        if ab:
            part += 'AB%s' % ab
        if aw:
            part += 'AW%s' % aw
        if ae:
            part += 'AE%s' % ae

    part += _part_symbols(board, node, SYMBOL_TRIANGLE)
    part += _part_symbols(board, node, SYMBOL_SQUARE)
    part += _part_symbols(board, node, SYMBOL_CIRCLE)
    part += _part_labels(board, node)

    for child in node.children:
        p = sgf_part_from_node(board, child)

        if len(node.children) == 1:
            part += p
        else:
            part += '(' + p + ')'

    return part


def _part_symbols(board, node, symbol):
    symbols = ['[%s]' % coord_to_sgf(int(coord), board.size)
               for coord, sym in node.symbols.items() if sym == symbol]
    return (symbol + ''.join(symbols)) if symbols else ''


def _part_labels(board, node):
    labels = ['[%s:%s]' % (coord_to_sgf(int(coord), board.size), lbl)
              for coord, lbl in node.labels.items()]
    return ('LB' + ''.join(labels)) if labels else ''
