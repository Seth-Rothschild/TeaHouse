from weiqi.board import Board, coord_from_sgf
from weiqi.services import GameService
from weiqi.sgf import parse_sgf
from weiqi.test.factories import GameFactory


def test_play_game(db, socket, benchmark):
    # A game with 194 moves
    sgf = '''
    (;EV[2nd Bailing Cup, semi-final 2]
        DT[2014-09-20]
        PB[Park Jungwhan]BR[9p]
        PW[Ke Jie]WR[4p]
        KM[7.5]RE[W+R]
        SO[Go4Go.net]
        ;B[qd];W[dc];B[pq];W[dp];B[oc];W[qn];B[qp];W[pj];B[fq];W[cn];B[pl]
        ;W[ql];B[pm];W[qm];B[pn];W[qh];B[jp];W[ce];B[fo];W[lq];B[dm];W[dn]
        ;B[em];W[cm];B[dk];W[jr];B[mq];W[lr];B[hq];W[mp];B[nq];W[ko];B[cq]
        ;W[dq];B[dr];W[cl];B[br];W[dl];B[el];W[dj];B[ej];W[ck];B[kp];W[lp]
        ;B[lo];W[ln];B[mo];W[oq];B[qk];W[pk];B[qo];W[no];B[mn];W[or];B[rk]
        ;W[mm];B[nn];W[on];B[nm];W[om];B[nl];W[ol];B[po];W[oo];B[ei];W[jo]
        ;B[io];W[in];B[ip];W[km];B[nk];W[lk];B[ni];W[li];B[ng];W[lg];B[ok]
        ;W[qj];B[rl];W[qe];B[pd];W[oe];B[pe];W[of];B[mf];W[pf];B[qf];W[oh]
        ;B[nh];W[nc];B[kh];W[lh];B[oi];W[ob];B[nd];W[od];B[pc];W[ne];B[re]
        ;W[ph];B[lf];W[md];B[kf];W[kg];B[jg];W[kd];B[jj];W[ki];B[kk];W[kj]
        ;B[jk];W[oj];B[nj];W[ll];B[jd];W[ji];B[jc];W[kc];B[jf];W[hj];B[il]
        ;W[im];B[hk];W[ij];B[op];W[np];B[pr];W[pp];B[ec];W[ed];B[fc];W[dd]
        ;B[op];W[nr];B[di];W[ek];B[fk];W[ik];B[hl];W[jl];B[jb];W[mb];B[pb]
        ;W[ie];B[je];W[pa];B[qa];W[oa];B[rb];W[fd];B[ma];W[la];B[lb];W[na]
        ;B[ka];W[lc];B[ma];W[nb];B[bj];W[gc];B[gb];W[fb];B[hc];W[eb];B[bo]
        ;W[fj];B[dk];W[hd];B[hg];W[fi];B[id];W[ek];B[kb];W[dk];B[ci];W[bh]
        ;B[fl];W[bi];B[cj];W[eh];B[am];W[an];B[eg];W[dh];B[ch];W[cg];B[dg]
        ;W[fh];B[me];W[ri];B[pi];W[rg];B[qi];W[qg])
    '''

    node = parse_sgf(sgf).children[0]

    benchmark(play_one_game, node, db, socket)


def play_one_game(node, db, socket):
    game = GameFactory(board=Board(19))
    svc_black = GameService(db, socket, game.black_user)
    svc_white = GameService(db, socket, game.white_user)

    black_turn = True

    while True:
        coord = node.prop_one('B') if black_turn else node.prop_one('W')
        coord = coord_from_sgf(coord, 19)

        svc = svc_black if black_turn else svc_white
        svc.execute('move', {'game_id': game.id, 'move': coord})

        if not node.children:
            break

        node = node.children[0]
        black_turn = not black_turn
