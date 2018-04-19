import pytest
from weiqi.models import RoomMessage, Room, RoomUser, DirectRoom
from weiqi.services import RoomService, ServiceError
from weiqi.test.factories import RoomFactory, RoomUserFactory, UserFactory


def test_room_users(db, socket):
    ru = RoomUserFactory()
    svc = RoomService(db, socket, ru.user)
    data = svc.execute('users', {'room_id': ru.room_id})

    assert data.get('users') is not None
    assert len(data.get('users')) == 1


def test_room_users_offline(db, socket):
    room = RoomFactory()
    ru = RoomUserFactory(room=room, user__is_online=True)
    RoomUserFactory(room=room, user__is_online=False)
    ru2 = RoomUserFactory(room=room, user__is_online=True)

    svc = RoomService(db, socket, ru.user)
    data = svc.execute('users', {'room_id': ru.room_id})

    users = data.get('users')
    user_ids = [u['user_id'] for u in users]

    assert users is not None
    assert len(users) == 2
    assert ru.user_id in user_ids
    assert ru2.user_id in user_ids


def test_message(db, socket):
    ru = RoomUserFactory()
    svc = RoomService(db, socket, ru.user)
    svc.execute('message', {'room_id': ru.room_id, 'message': 'test'})

    assert db.query(RoomMessage).count() == 1

    msg = db.query(RoomMessage).first()
    assert msg.message == 'test'
    assert msg.user == ru.user
    assert msg.room == ru.room


def test_message_not_in_room(db, socket):
    room = RoomFactory()
    ru = RoomUserFactory()

    svc = RoomService(db, socket, ru.user)

    with pytest.raises(ServiceError):
        svc.execute('message', {'room_id': room.id, 'message': 'test'})

    assert len(list(ru.room.recent_messages(db))) == 0
    assert len(list(room.recent_messages(db))) == 0


def test_open_direct(db, socket):
    user = UserFactory()
    other = UserFactory()

    svc = RoomService(db, socket, user)
    direct = svc.execute('open_direct', {'user_id': other.id})

    assert db.query(Room).count() == 1
    room = db.query(Room).first()
    assert room.users.count() == 1
    assert room.users.first().user == user

    svc = RoomService(db, socket, other)
    other_direct = svc.open_direct(user.id)
    assert db.query(Room).count() == 1
    other_room = db.query(Room).first()
    assert other_room == room
    assert room.users.count() == 2
    assert room.users.all()[1].user == other

    assert direct['room'] == other_direct['room']


def test_close_direct(db, socket):
    user = UserFactory()
    other = UserFactory()

    svc = RoomService(db, socket, user)
    svc.execute('open_direct', {'user_id': other.id})
    svc.execute('close_direct', {'user_id': other.id})

    room = db.query(Room).first()
    assert room.users.count() == 0


def test_message_direct(db, socket):
    user = UserFactory()
    other = UserFactory()
    svc = RoomService(db, socket, user)
    socket.subscribe('direct_message/'+str(user.id))
    socket.subscribe('direct_message/'+str(other.id))

    svc.open_direct(other.id)
    room = db.query(Room).first()

    svc.execute('message', {'room_id': room.id, 'message': 'test'})

    assert db.query(RoomMessage).count() == 1
    assert len(socket.sent_messages) == 2
    assert socket.sent_messages[0]['method'] == 'direct_message'
    assert socket.sent_messages[0]['data']['room_id'] == room.id
    assert socket.sent_messages[1]['method'] == 'direct_message'
    assert socket.sent_messages[1]['data']['room_id'] == room.id

    direct = DirectRoom.filter_by_users(db, user, other).one()
    assert not direct.user_one_has_unread
    assert direct.user_two_has_unread


def test_message_direct_joins_other(db, socket):
    user = UserFactory()
    other = UserFactory()

    svc = RoomService(db, socket, user)
    svc.open_direct(other.id)

    room = db.query(Room).first()
    svc.execute('message', {'room_id': room.id, 'message': 'test'})

    assert room.users.count() == 2


def test_join_room(db, socket):
    user = UserFactory()
    room = RoomFactory()
    svc = RoomService(db, socket, user)
    socket.subscribe('room_user/'+str(room.id))

    svc.join_room(room.id)

    assert db.query(RoomUser).count() == 1
    ru = db.query(RoomUser).first()
    assert ru.room == room
    assert ru.user == user

    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'room_user'
    assert socket.sent_messages[0]['data']['user_id'] == user.id
    assert socket.sent_messages[0]['data']['user_display'] == user.display
    assert socket.sent_messages[0]['data']['user_rating'] == user.rating


def test_leave_room(db, socket):
    user = UserFactory()
    room = RoomFactory()
    svc = RoomService(db, socket, user)

    svc.join_room(room.id)
    svc.leave_room(room.id)

    assert db.query(RoomUser).count() == 0


def test_users_max(db, socket):
    room = RoomFactory()

    svc = RoomService(db, socket, UserFactory())
    svc.join_room(room.id)
    assert room.users_max == 1

    svc = RoomService(db, socket, UserFactory())
    svc.join_room(room.id)
    assert room.users_max == 2

    svc.leave_room(room.id)
    assert room.users_max == 2

    svc = RoomService(db, socket, UserFactory(is_online=False))
    svc.join_room(room.id)
    assert room.users_max == 2


def test_create_default_room(db):
    user = UserFactory()

    svc = RoomService(db)
    svc.create_default_room('test room')

    assert db.query(Room).count() == 1

    room = db.query(Room).first()
    assert room.name == 'test room'
    assert room.is_default
    assert db.query(RoomUser).filter_by(user=user, room=room).count() == 1
