import re

EMPTY = '.'
BLACK = 'x'
WHITE = 'o'

PASS = -1
RESIGN = -2

NODE_BLACK = 'B'
NODE_WHITE = 'W'
NODE_EDIT = 'E'

SYMBOL_TRIANGLE = 'TR'
SYMBOL_SQUARE = 'SQ'
SYMBOL_CIRCLE = 'CR'


def coord2d(x, y, size=9):
    return (y-1)*size + (x-1)


def coord_to_2d(coord, size):
    y = int(coord / size)
    x = coord - y*size
    return (x+1), (y+1)


def coord_from_sgf(coord, size):
    start = ord('a')
    sgf = coord.lower()

    if len(sgf) < 2:
        raise ValueError('invalid coord: {}'.format(coord))

    x = ord(sgf[0]) - start + 1
    y = ord(sgf[1]) - start + 1

    return coord2d(x, y, size)


def coord_to_sgf(coord, size):
    x, y = coord_to_2d(coord, size)
    return chr(ord('a')+x-1) + chr(ord('a')+y-1)


def neighbors(coord, size):
    x, y = coord_to_2d(coord, size)
    x -= 1
    y -= 1
    n = []

    if y > 0:
        n.append(coord - size)
    if y < size-1:
        n.append(coord + size)
    if x > 0:
        n.append(coord - 1)
    if x < size-1:
        n.append(coord + 1)

    return n


def opposite(color):
    if color == EMPTY:
        return EMPTY
    return BLACK if color == WHITE else WHITE


def validate_move(move, size):
    if move < RESIGN or move >= size*size:
        raise ValueError('invalid move: {}'.format(move))


class Node:
    def __init__(self):
        self.id = None
        self.parent_id = None
        self.children = []

        self.action = None
        self.move = None  # Used for actions NODE_BLACK and NODE_WHITE
        self.edits = {}  # Used for action NODE_EDIT

        self.captures = []  # Only set for actions NODE_BLACK and NODE_WHITE
        self.marked_dead = {}
        self.score_points = []
        self.labels = {}
        self.symbols = {}

    def to_dict(self):
        data = {
            'id': self.id,
            'parent_id': self.parent_id,
            'children': self.children,
            'action': self.action,
            'move': self.move,
        }

        skip_empty = ['edits', 'captures', 'marked_dead',
                      'score_points', 'labels', 'symbols']
        for field in skip_empty:
            val = getattr(self, field)
            if val:
                data[field] = val

        return data

    def toggle_symbol(self, coord, symbol):
        coord = str(coord)

        if not self.symbols:
            self.symbols = {}

        if coord in self.labels:
            del self.labels[coord]

        if coord not in self.symbols or not self.symbols[coord]:
            self.symbols[coord] = symbol
        elif self.symbols[coord] == symbol:
            del self.symbols[coord]
        else:
            self.symbols[coord] = symbol

    def toggle_label(self, coord):
        self._toggle_label(coord, 26, lambda i: chr(ord('A')+i))

    def toggle_number(self, coord):
        self._toggle_label(coord, 19*19, lambda i: str(i+1))

    def _toggle_label(self, coord, range_max, idx_to_lbl):
        coord = str(coord)

        if not self.labels:
            self.labels = {}

        if coord in self.symbols:
            del self.symbols[coord]

        if coord in self.labels:
            del self.labels[coord]
        else:
            for i in range(range_max):
                label = idx_to_lbl(i)
                if self.label_is_unused(label):
                    self.labels[str(coord)] = label
                    break

    def label_is_unused(self, label):
        return label not in self.labels.values()


class IllegalMoveError(Exception):
    pass


class Board:
    def __init__(self, size=9, handicap=0):
        self.size = size
        self.handicap = handicap
        self.tree = []
        self.current_node_id = None
        self._pos = [EMPTY]*size*size
        self._pos_node_id = None

        if self.handicap > 0:
            self.place_handicap(self.handicap)

    def __str__(self):
        board = ''

        for i, c in enumerate(self.pos):
            board += c

            if (i+1) % self.size == 0:
                board += '\n'

        return board

    def to_dict(self):
        return {
            'size': self.size,
            'handicap': self.handicap,
            'current': self.current,
            'tree': [n.to_dict() for n in self.tree],
            'current_node_id': self.current_node_id,
        }

    @property
    def length(self):
        return self.size*self.size

    @property
    def pos(self):
        if self._pos_node_id != self.current_node_id:
            self._rebuild_pos()
        return self._pos

    def at(self, coord):
        return self.pos[coord]

    @property
    def current_node(self) -> Node:
        return self.tree[self.current_node_id] if self.current_node_id is not None else None

    @property
    def current(self):
        """Returns the current color based on the previous move."""
        node = self.current_node
        if not node:
            return BLACK

        while node:
            if node.action == NODE_BLACK:
                return WHITE
            elif node.action == NODE_WHITE:
                return BLACK

            if node.parent_id is None:
                # Handicap game
                return WHITE

            node = self.tree[node.parent_id]

    @current.setter
    def current(self, color):
        """Sets the current color by playing a PASS if necessary."""
        if color != self.current:
            self.play(PASS)

    @property
    def ko(self) -> int:
        if not self.current_node:
            return None

        if len(self.current_node.captures) == 1:
            return self.current_node.captures[0]
        return None

    @property
    def both_passed(self):
        if len(self.tree) < 2:
            return False

        if self.current_node.parent_id is None or self.current_node.move != PASS:
            return False

        return self.tree[self.current_node.parent_id].move == PASS

    @property
    def moves_played(self):
        return len(self.tree)

    def play(self, move):
        validate_move(move, self.size)

        if move in [PASS, RESIGN]:
            self._add_move(move)
            return

        caps = self._find_captures(move)

        self._validate_legal(move, caps)

        for c in caps:
            self.pos[c] = EMPTY

        self.pos[move] = self.current
        self._add_move(move, caps)

    def _validate_legal(self, coord, captures):
        """Checks if the given move is valid for the current player.

        A non-passing move is legal if the point is unoccupied, the point is not illegal due to the Ko rule, and the
        move is not suicide.
        """
        if self.at(coord) != EMPTY:
            raise IllegalMoveError('coordinate is not empty')

        if len(captures) == 1 and coord == self.ko:
            raise IllegalMoveError('coordinate is a ko point')

        if self.is_suicide(coord, self.current):
            raise IllegalMoveError('coordinate is a suicide')

    def is_suicide(self, coord, color=None):
        """Checks if the given move is a suicide for the current player.
        A move is not suicide if any of the following conditions holds true:
        - any neighboring point is empty
        - any neighboring point is the same color and has more than one liberty
        - any neighboring point is a different color and has only one liberty
        """
        if not color:
            color = self.current

        for n in neighbors(coord, self.size):
            n_color = self.at(n)

            if n_color == EMPTY:
                return False

            chain = self.chain_at(n)
            libs = len(self.chain_liberties(chain))

            if n_color == color and libs > 1:
                return False

            if n_color != color and libs == 1:
                return False

        return True

    def _find_captures(self, coord, color=None):
        if not color:
            color = self.current

        caps = set()

        for n in neighbors(coord, self.size):
            if self.at(n) == EMPTY or self.at(n) == color:
                continue

            chain = self.chain_at(n)
            if len(self.chain_liberties(chain)) <= 1:
                caps |= chain

        return caps

    def chain_at(self, coord) -> set:
        chain = set()
        color = self.at(coord)

        if color == EMPTY:
            return chain

        def populate(c):
            for n in neighbors(c, self.size):
                if self.at(n) == color and n not in chain:
                    chain.add(n)
                    populate(n)

        chain.add(coord)
        populate(coord)
        return chain

    def loose_chain_at(self, coord) -> set:
        """Returns all stones loosely connected to the given coordinate.

        A stone is loosely connected if it is either connected directly or can be reached by only passing empty spaces.
        """
        chain = set()
        visited = set()
        color = self.at(coord)

        if color == EMPTY:
            return chain

        def populate(c):
            for n in neighbors(c, self.size):
                if n in visited:
                    continue

                visited.add(n)

                if self.at(n) == color:
                    chain.add(n)

                if self.at(n) in [color, EMPTY]:
                    populate(n)

        populate(coord)
        return chain

    def chain_liberties(self, chain) -> set:
        libs = set()

        for c in chain:
            for n in neighbors(c, self.size):
                if self.at(n) == EMPTY:
                    libs.add(n)

        return libs

    def _add_move(self, move, caps=None):
        node = Node()
        node.action = NODE_BLACK if self.current == BLACK else NODE_WHITE
        node.move = move
        node.captures = list(caps) if caps else []

        self._add_node(node)

    def add_edits(self, black, white, empty):
        node = Node()
        node.action = NODE_EDIT
        node.edits = {}

        node.edits.update({str(c): BLACK for c in black})
        node.edits.update({str(c): WHITE for c in white})
        node.edits.update({str(c): EMPTY for c in empty})

        self._add_node(node)

    def _add_node(self, node):
        node.id = len(self.tree)

        if self.current_node_id is not None:
            node.parent_id = self.current_node_id
            self.tree[node.parent_id].children.append(node.id)

        self.tree.append(node)
        self.current_node_id = node.id

    def _rebuild_pos(self):
        """Rebuilds the current position based on the tree data."""
        if self.current_node_id is None:
            return

        path = self._node_path(self.current_node_id)
        self._pos = [EMPTY]*self.length

        for node in path:
            if node.action == NODE_BLACK and node.move not in [PASS, RESIGN]:
                self._pos[node.move] = BLACK
            elif node.action == NODE_WHITE and node.move not in [PASS, RESIGN]:
                self._pos[node.move] = WHITE
            elif node.action == NODE_EDIT:
                for coord, color in node.edits.items():
                    self._pos[int(coord)] = color

            for c in node.captures:
                self._pos[c] = EMPTY

        self._pos_node_id = self.current_node_id

    def _node_path(self, node_id):
        path = []
        node = self.tree[node_id]

        while node:
            path.append(node)
            node = self.tree[node.parent_id] if node.parent_id is not None else None

        path.reverse()
        return path

    def is_marked_dead(self, coord):
        if not self.current_node or not self.current_node.marked_dead:
            return False

        return self.current_node.marked_dead.get(str(coord), False)

    def mark_dead(self, coord):
        if self.at(coord) == EMPTY or not self.current_node:
            return

        for c in self.loose_chain_at(coord):
            self.current_node.marked_dead[str(c)] = True

    def toggle_marked_dead(self, coord):
        if self.at(coord) == EMPTY or not self.current_node:
            return

        marked_dead = self.current_node.marked_dead.get(str(coord), False)

        for c in self.loose_chain_at(coord):
            if marked_dead:
                self.current_node.marked_dead.pop(str(c), None)
            else:
                self.current_node.marked_dead[str(c)] = True

    def place_handicap(self, hc):
        if hc < 2:
            return

        self.add_edits(handicap_coords(self.size, hc), [], [])

    def toggle_edit(self, coord, color):
        if color == EMPTY:
            return

        # In edit-mode we allow to play on ko points and non-empty points, but don't allow suicide.
        if self.is_suicide(coord, color):
            return

        if not self.current_node or self.current_node.action != NODE_EDIT:
            self.add_edits([], [], [])

        node = self.current_node

        if self.at(coord) == color:
            node.edits[str(coord)] = EMPTY
        else:
            # Setting to EMPTY is necessary to find the correct captures
            node.edits[str(coord)] = EMPTY
            self._pos[coord] = EMPTY

            for c in self._find_captures(coord, color):
                node.edits[str(c)] = EMPTY

            node.edits[str(coord)] = color

        self._rebuild_pos()

    def edit_cycle(self, coord):
        """Cycles through BLACK, WHITE, EMPTY as edits on the given coordinate."""
        if not self.current_node or self.current_node.action != NODE_EDIT:
            self.add_edits([], [], [])

        node = self.current_node
        current_color = self.at(coord)

        if current_color == BLACK:
            new_color = WHITE if not self.is_suicide(coord, WHITE) else EMPTY
        elif current_color == WHITE:
            new_color = EMPTY
        else:
            new_color = BLACK if not self.is_suicide(coord, BLACK) else WHITE

        if new_color != EMPTY:
            # Setting to EMPTY is necessary to find the correct captures
            node.edits[str(coord)] = EMPTY
            self._pos[coord] = EMPTY

            for c in self._find_captures(coord, new_color):
                node.edits[str(c)] = EMPTY

        node.edits[str(coord)] = new_color

        self._rebuild_pos()


def board_from_string(pos, size=9) -> Board:
    pos = re.sub(r'\s', '', pos)

    if len(pos) != size*size:
        raise ValueError(
            'board string has incorrect length: {}'.format(len(pos)))

    board = Board(size)

    black = [coord for coord, color in enumerate(list(pos)) if color == BLACK]
    white = [coord for coord, color in enumerate(list(pos)) if color == WHITE]

    board.add_edits(black, white, [])

    return board


def board_from_dict(data) -> Board:
    board = Board(data['size'])
    board.handicap = data.get('handicap', 0)
    board.current_node_id = data['current_node_id']
    board.tree = [node_from_dict(n) for n in data['tree']]
    return board


def node_from_dict(data) -> Node:
    node = Node()
    node.__dict__.update(data)
    return node


def handicap_coords(size, hc):
    if hc < 2:
        return []
    if hc > 9:
        raise ValueError('invalid handicap count: {}'.format(hc))

    dist = (2 if size == 9 else 3)
    middle = int((size + 1) / 2)
    tengen = coord2d(middle, middle, size)

    corners = [
        coord2d(size-dist, dist+1, size),
        coord2d(dist+1, size-dist, size),
        coord2d(size-dist, size-dist, size),
        coord2d(dist+1, dist+1, size),
    ]

    left_right = [
        coord2d(dist+1, middle, size),
        coord2d(size-dist, middle, size),
    ]

    top_bottom = [
        coord2d(middle, size-dist, size),
        coord2d(middle, dist+1, size),
    ]

    if hc <= 4:
        return corners[:hc]

    if hc == 5:
        return corners + [tengen]

    clr = corners + left_right

    if hc == 6:
        return clr

    if hc == 7:
        return clr + [tengen]

    if hc == 8:
        return clr + top_bottom

    return clr + [tengen] + top_bottom
