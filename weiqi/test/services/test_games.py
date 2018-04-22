from datetime import datetime, timedelta

import pytest
from weiqi import settings
from weiqi.board import BLACK, WHITE, EMPTY, PASS, RESIGN, SYMBOL_TRIANGLE
from weiqi.models import Timing
from weiqi.services import GameService, ServiceError
from weiqi.services.games import InvalidPlayerError, InvalidStageError, GameHasNotStartedError, NotAllowedError
from weiqi.test.factories import GameFactory, DemoGameFactory, UserFactory


def test_open(db, socket):
    game = GameFactory()
    user = UserFactory()

    svc = GameService(db, socket, user)
    svc.execute('open_game', {'game_id': game.id})

    assert socket.is_subscribed('game_data/'+str(game.id))
    assert socket.is_subscribed('game_update/'+str(game.id))
    assert socket.is_subscribed('game_info/'+str(game.id))
    assert socket.is_subscribed('demo_current_node_id/'+str(game.id))

    assert socket.is_subscribed('room_message/'+str(game.room_id))
    assert socket.is_subscribed('room_user/'+str(game.room_id))
    assert socket.is_subscribed('room_user_left/'+str(game.room_id))


def test_open_room(db, socket):
    game = GameFactory()
    user = UserFactory()

    svc = GameService(db, socket, user)
    svc.execute('open_game', {'game_id': game.id})

    assert len(user.rooms) == 1
    assert user.rooms[0].room.game == game


def test_open_room_logs(db, socket):
    game = GameFactory()

    svc = GameService(db, socket)
    svc.execute('open_game', {'game_id': game.id})

    assert len(
        list(filter(lambda l: l['method'] == 'room_logs', socket.sent_messages))) == 1


def test_close(db, socket):
    game = GameFactory()
    user = UserFactory()

    svc = GameService(db, socket, user)
    svc.execute('open_game', {'game_id': game.id})
    svc.execute('close_game', {'game_id': game.id})

    assert not socket.is_subscribed('game_data/'+str(game.id))
    assert not socket.is_subscribed('game_update/'+str(game.id))
    assert not socket.is_subscribed('game_info/'+str(game.id))
    assert not socket.is_subscribed('demo_current_node_id/'+str(game.id))

    assert not socket.is_subscribed('room_message/'+str(game.room_id))
    assert not socket.is_subscribed('room_user/'+str(game.room_id))
    assert not socket.is_subscribed('room_user_left/'+str(game.room_id))


def test_open_game_demo(db, socket):
    game = DemoGameFactory()
    socket.subscribe('game_started')

    svc = GameService(db, socket, game.demo_owner)
    svc.execute('open_game', {'game_id': game.id})

    assert len(socket.sent_messages) == 4
    assert socket.sent_messages[0]['method'] == 'room_user'
    assert socket.sent_messages[1]['method'] == 'room_logs'
    assert socket.sent_messages[2]['method'] == 'game_data'
    assert socket.sent_messages[3]['method'] == 'game_started'


def test_open_game_private_as_player(db, socket):
    game = GameFactory(is_private=True)
    socket.subscribe('game_started')

    svc = GameService(db, socket, game.black_user)
    svc.execute('open_game', {'game_id': game.id})

    assert socket.is_subscribed('game_data/'+str(game.id))
    assert socket.is_subscribed('game_update/'+str(game.id))
    assert socket.is_subscribed('game_info/'+str(game.id))
    assert socket.is_subscribed('demo_current_node_id/'+str(game.id))

    assert socket.is_subscribed('room_message/'+str(game.room_id))
    assert socket.is_subscribed('room_user/'+str(game.room_id))
    assert socket.is_subscribed('room_user_left/'+str(game.room_id))


def test_open_game_private_not_player(db, socket):
    game = GameFactory(is_private=True)
    socket.subscribe('game_started')

    random_user = UserFactory()

    svc = GameService(db, socket, random_user)

    with pytest.raises(NotAllowedError) as exinfo:
        svc.execute('open_game', {'game_id': game.id})

    assert 'this game is private' in str(exinfo.value)


def test_close_game_demo(db, socket):
    game = DemoGameFactory()
    socket.subscribe('game_finished')

    svc = GameService(db, socket, game.demo_owner)
    svc.execute('close_game', {'game_id': game.id})

    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'game_finished'


def test_move(db, socket):
    game = GameFactory()

    svc = GameService(db, socket, game.black_user)
    svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.board.at(30) == BLACK
    assert game.board.current == WHITE


def test_move_current_color(db, socket):
    game = GameFactory()
    svc = GameService(db, socket, game.white_user)

    with pytest.raises(InvalidPlayerError):
        svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.board.at(30) == EMPTY


def test_move_counting(db, socket):
    game = GameFactory(stage='counting')
    svc = GameService(db, socket, game.black_user)

    with pytest.raises(InvalidStageError):
        svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.board.at(30) == EMPTY


def test_move_finished(db, socket):
    game = GameFactory(stage='finished')
    svc = GameService(db, socket, game.black_user)

    with pytest.raises(InvalidStageError):
        svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.board.at(30) == EMPTY


def test_resign(db, socket, board):
    game = GameFactory(stage='counting', board=board)
    svc = GameService(db, socket, game.black_user)

    svc.execute('move', {'game_id': game.id, 'move': RESIGN})

    assert game.stage == 'finished'
    assert game.result == 'W+R'


def test_resign_aborted(db, socket):
    game = GameFactory(stage='counting')
    svc = GameService(db, socket, game.black_user)

    svc.execute('move', {'game_id': game.id, 'move': RESIGN})

    assert game.stage == 'finished'
    assert game.result == 'aborted'


def test_resign_counting(db, socket):
    game = GameFactory(stage='counting')
    svc = GameService(db, socket, game.black_user)

    svc.execute('move', {'game_id': game.id, 'move': RESIGN})

    assert game.stage == 'finished'


def test_game_finished(db, socket):
    game = GameFactory()
    socket.subscribe('game_finished')
    socket.subscribe('game_data/'+str(game.id))

    svc = GameService(db, socket, game.black_user)
    svc.execute('move', {'game_id': game.id, 'move': RESIGN})

    assert len(socket.sent_messages) == 2
    assert socket.sent_messages[0]['method'] == 'game_finished'
    assert socket.sent_messages[1]['method'] == 'game_data'


def test_game_finished_user_status(db, socket):
    game = GameFactory()
    socket.subscribe('user_status')

    svc = GameService(db, socket, game.black_user)
    svc.execute('move', {'game_id': game.id, 'move': RESIGN})

    assert len(socket.sent_messages) == 2
    assert socket.sent_messages[0]['method'] == 'user_status'
    assert socket.sent_messages[1]['method'] == 'user_status'


def test_game_finished_correspondence(db, socket, mails):
    game = GameFactory(is_correspondence=True,
                       black_user__is_online=False, white_user__is_online=False)
    svc = GameService(db, socket, game.black_user)
    svc.execute('move', {'game_id': game.id, 'move': RESIGN})

    assert len(mails) == 2
    assert mails[0]['template'] == 'correspondence/game_finished.txt'
    assert mails[1]['template'] == 'correspondence/game_finished.txt'
    assert {mails[0]['to'], mails[1]['to']} == {
        game.black_user.email, game.white_user.email}


def test_stages_playing_counting(db, socket):
    game = GameFactory()
    svc = GameService(db, socket, game.black_user)

    svc.user = game.black_user
    svc.execute('move', {'game_id': game.id, 'move': PASS})
    assert game.stage == 'playing'

    svc.user = game.white_user
    svc.execute('move', {'game_id': game.id, 'move': PASS})
    assert game.stage == 'counting'


def test_resume_from_counting(db, socket):
    game = GameFactory(stage='counting')
    game.board.play(PASS)
    game.board.play(PASS)
    game.apply_board_change()

    socket.subscribe('game_update/'+str(game.id))
    svc = GameService(db, socket, game.black_user)

    svc.execute('resume_from_counting', {'game_id': game.id})

    assert game.stage == 'playing'
    assert not game.board.both_passed
    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'game_update'


def test_resume_from_counting_time(db, socket):
    game = GameFactory(stage='counting')
    svc = GameService(db, socket, game.black_user)

    game.timing.timing_updated_at = datetime.utcnow() - timedelta(minutes=10)
    svc.execute('resume_from_counting', {'game_id': game.id})

    assert (game.timing.timing_updated_at -
            datetime.utcnow()).total_seconds() < 3


def test_resume_counting_other(db, socket):
    game = GameFactory(stage='counting')
    svc = GameService(db, socket, game.white_user)
    svc.execute('resume_from_counting', {'game_id': game.id})
    assert game.stage == 'playing'


def test_resume_counting_invalid_player(db, socket):
    user = UserFactory()
    game = GameFactory(stage='counting')
    svc = GameService(db, socket, user)

    with pytest.raises(InvalidPlayerError):
        svc.execute('resume_from_counting', {'game_id': game.id})

    assert game.stage == 'counting'


def test_toggle_marked_dead(db, socket):
    game = GameFactory(stage='counting')
    svc = GameService(db, socket, game.black_user)
    svc.user = game.black_user
    svc.socket.subscribe('game_update/'+str(game.id))

    game.board.play(30)
    game.apply_board_change()

    svc.execute('toggle_marked_dead', {'game_id': game.id, 'coord': 30})

    assert game.board.is_marked_dead(30)
    assert len(svc.socket.sent_messages) == 1
    assert svc.socket.sent_messages[0]['method'] == 'game_update'


def test_toggle_marked_dead_playing(db, socket):
    game = GameFactory(stage='playing')
    svc = GameService(db, socket, game.black_user)
    svc.user = game.black_user

    with pytest.raises(InvalidStageError):
        svc.execute('toggle_marked_dead', {'game_id': game.id, 'coord': 30})


def test_toggle_marked_dead_finished(db, socket):
    game = GameFactory(stage='finished')
    svc = GameService(db, socket, game.black_user)
    svc.user = game.black_user

    with pytest.raises(InvalidStageError):
        svc.execute('toggle_marked_dead', {'game_id': game.id, 'coord': 30})


def test_confirm_score(db, socket, board):
    game = GameFactory(stage='counting', result='B+1.5', board=board)
    svc = GameService(db, socket, game.black_user)
    svc.socket.subscribe('game_finished')
    svc.socket.subscribe('game_data/'+str(game.id))

    svc.user = game.black_user
    svc.execute('confirm_score', {'game_id': game.id, 'result': 'B+1.5'})

    assert game.result_black_confirmed == 'B+1.5'

    svc.user = game.white_user
    svc.execute('confirm_score', {'game_id': game.id, 'result': 'B+1.5'})

    assert game.result_white_confirmed == 'B+1.5'
    assert game.result == 'B+1.5'
    assert game.stage == 'finished'
    assert len(svc.socket.sent_messages) == 2
    assert svc.socket.sent_messages[0]['method'] == 'game_finished'
    assert svc.socket.sent_messages[1]['method'] == 'game_data'


def test_confirm_score_aborted(db, socket):
    game = GameFactory(stage='counting', result='B+1.5')
    svc = GameService(db, socket, game.black_user)
    svc.socket.subscribe('game_finished')
    svc.socket.subscribe('game_data/'+str(game.id))

    svc.user = game.black_user
    svc.execute('confirm_score', {'game_id': game.id, 'result': 'B+1.5'})
    svc.user = game.white_user
    svc.execute('confirm_score', {'game_id': game.id, 'result': 'B+1.5'})

    assert game.result == 'aborted'
    assert game.stage == 'finished'
    assert len(svc.socket.sent_messages) == 2
    assert svc.socket.sent_messages[0]['method'] == 'game_finished'
    assert svc.socket.sent_messages[1]['method'] == 'game_data'


def test_confirm_score_playing(db, socket):
    game = GameFactory(stage='playing', result='B+1.5')
    svc = GameService(db, socket, game.black_user)
    svc.user = game.black_user

    with pytest.raises(InvalidStageError):
        svc.execute('confirm_score', {'game_id': game.id, 'result': 'B+1.5'})


def test_confirm_score_finished(db, socket):
    game = GameFactory(stage='finished', result='B+1.5')
    svc = GameService(db, socket, game.black_user)
    svc.user = game.black_user

    with pytest.raises(InvalidStageError):
        svc.execute('confirm_score', {'game_id': game.id, 'result': 'B+1.5'})


def test_start_delay(db, socket):
    game = GameFactory(timing__start_at=datetime.utcnow() +
                       timedelta(seconds=10))
    svc = GameService(db, socket, game.black_user)

    with pytest.raises(GameHasNotStartedError):
        svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.board.at(30) == EMPTY


# TODO: #101 fix this test on CI
@pytest.mark.skip
def test_timing(db, socket):
    game = GameFactory(timing__timing_updated_at=datetime.utcnow()-timedelta(seconds=9),
                       timing__system='fischer',
                       timing__overtime=timedelta(seconds=15),
                       timing__black_main=timedelta(seconds=10),
                       timing__black_overtime=timedelta())
    svc = GameService(db, socket, game.black_user)

    svc.execute('move', {'game_id': game.id, 'move': 30})

    # Because of slow CI runners this test cannot be exact.
    assert 16 - game.timing.black_main.total_seconds() < 3


def test_timing_lose_on_time(db, socket, board):
    game = GameFactory(timing__timing_updated_at=datetime.utcnow()-timedelta(seconds=11),
                       timing__system='fischer',
                       timing__overtime=timedelta(seconds=15),
                       timing__black_main=timedelta(seconds=10),
                       timing__black_overtime=timedelta(),
                       board=board)

    svc = GameService(db, socket, game.black_user)

    svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.result == 'W+T'
    assert game.timing.black_main.total_seconds() == 0
    assert game.timing.black_overtime.total_seconds() < 0


def test_move_demo(db, socket):
    game = DemoGameFactory()
    socket.subscribe('game_update/'+str(game.id))

    svc = GameService(db, socket, game.demo_control)
    svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.board.at(30) == BLACK
    assert game.board.current == WHITE
    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'game_update'


def test_demo_control(db, socket):
    user = UserFactory()
    game = DemoGameFactory(demo_control=user)

    svc = GameService(db, socket, game.demo_owner)

    with pytest.raises(InvalidPlayerError):
        svc.execute('move', {'game_id': game.id, 'move': 30})

    assert game.board.at(30) == EMPTY
    assert game.board.current == BLACK


def test_demo_resign(db, socket):
    game = DemoGameFactory()
    svc = GameService(db, socket, game.demo_control)

    with pytest.raises(ServiceError):
        svc.execute('move', {'game_id': game.id, 'move': RESIGN})


def test_demo_set_current_node(db, socket):
    game = DemoGameFactory()
    game.board.play(1)
    game.board.play(2)
    game.apply_board_change()

    socket.subscribe('demo_current_node_id/'+str(game.id))
    svc = GameService(db, socket, game.demo_control)
    svc.execute('set_current_node', {'game_id': game.id, 'node_id': 1})

    assert game.board.current_node_id == 1
    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'demo_current_node_id'
    assert socket.sent_messages[0]['data']['game_id'] == game.id
    assert socket.sent_messages[0]['data']['node_id'] == 1


def test_demo_set_current_node_invalid(db, socket):
    game = DemoGameFactory()
    game.board.play(1)
    game.board.play(2)
    game.apply_board_change()

    svc = GameService(db, socket, game.demo_control)

    with pytest.raises(ServiceError):
        svc.execute('set_current_node', {'game_id': game.id, 'node_id': 2})

    assert game.board.current_node_id == 1


def test_demo_tool_triangle(db, socket):
    game = DemoGameFactory()
    svc = GameService(db, socket, game.demo_control)

    svc.execute('demo_tool_triangle', {'game_id': game.id, 'coord': 180})

    assert game.board.current_node.symbols['180'] == SYMBOL_TRIANGLE


def test_edit_info(db, socket):
    game = DemoGameFactory()
    socket.subscribe('game_info/'+str(game.id))
    svc = GameService(db, socket, game.demo_owner)
    svc.execute('edit_info', {'game_id': game.id,
                              'title': 'new title',
                              'black_display': 'new black',
                              'white_display': 'new white'})

    assert game.title == 'new title'
    assert game.black_display == 'new black'
    assert game.white_display == 'new white'

    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'game_info'
    assert socket.sent_messages[0]['data']['game_id'] == game.id


def test_edit_info_not_owner(db, socket):
    pass


def test_edit_info_not_demo(db, socket):
    pass


def test_check_due_moves(db, socket, board):
    game = GameFactory(timing__timing_updated_at=datetime.utcnow()-timedelta(seconds=11),
                       timing__system='fischer',
                       timing__overtime=timedelta(seconds=15),
                       timing__black_main=timedelta(seconds=10),
                       timing__black_overtime=timedelta(),
                       board=board)

    socket.subscribe('game_finished')

    svc = GameService(db, socket, None)
    svc.check_due_moves()

    assert game.result == 'W+T'
    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'game_finished'


def test_resume_all_games_fischer(db):
    GameFactory(stage='playing',
                timing__timing_updated_at=datetime.utcnow()-timedelta(seconds=10),
                timing__system='fischer',
                timing__overtime=timedelta(seconds=30),
                timing__overtime_count=1,
                timing__black_main=timedelta(seconds=10),
                timing__white_main=timedelta(seconds=20),
                timing__black_overtime=timedelta(),
                timing__white_overtime=timedelta())

    svc = GameService(db)
    svc.resume_all_games()

    timing = db.query(Timing).first()
    assert timing.black_main == (
        timedelta(seconds=10) + settings.RESUME_TIMING_ADD_TIME)
    assert timing.white_main == (
        timedelta(seconds=20) + settings.RESUME_TIMING_ADD_TIME)
    assert timing.black_overtime == timedelta()
    assert timing.white_overtime == timedelta()


def test_resume_all_games_cap(db):
    GameFactory(stage='playing',
                timing__system='fischer',
                timing__capped=True,
                timing__main=timedelta(minutes=1),
                timing__black_main=timedelta(minutes=2),
                timing__white_main=timedelta(minutes=3))

    svc = GameService(db)
    svc.resume_all_games()

    timing = db.query(Timing).first()
    assert timing.black_main == timing.main_cap
    assert timing.white_main == timing.main_cap
