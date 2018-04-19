from weiqi.models import Automatch
from weiqi.services import ConnectionService
from weiqi.test.factories import UserFactory, AutomatchFactory, RoomFactory, RoomUserFactory


def test_connect_subs(db, socket):
    user = UserFactory()

    ConnectionService(db, socket, user).connect()

    assert socket.is_subscribed('game_started')
    assert socket.is_subscribed('game_finished')
    assert socket.is_subscribed('direct_message/'+str(user.id))
    assert socket.is_subscribed('automatch_status/'+str(user.id))
    assert socket.is_subscribed('challenges/'+str(user.id))


def test_connection_data_rooms(db, socket):
    room = RoomFactory(type='main')
    ru = RoomUserFactory(room=room)
    socket.subscribe('connection_data')

    ConnectionService(db, socket, ru.user).connect()

    data = socket.sent_messages[0]['data']

    assert 'rooms' in data
    assert len(data['rooms']) == 1


def test_connection_data_automatch(db, socket):
    match = AutomatchFactory()
    socket.subscribe('connection_data')

    ConnectionService(db, socket, match.user).connect()

    data = socket.sent_messages[0]['data']
    assert data['automatch']


def test_disconnect_automatch(db, socket):
    user = UserFactory()
    AutomatchFactory(user=user, preset='fast')
    AutomatchFactory(user=user, preset='normal')
    AutomatchFactory(user=user, preset='slow')

    ConnectionService(db, socket, user).disconnect()

    assert db.query(Automatch).count() == 0


def test_disconnect_automatch_correspondence(db, socket):
    user = UserFactory()
    AutomatchFactory(user=user, preset='fast')
    AutomatchFactory(user=user, preset='correspondence')

    ConnectionService(db, socket, user).disconnect()

    assert db.query(Automatch).count() == 1
    assert db.query(Automatch).filter_by(preset='correspondence').count() == 1
