from datetime import datetime

from weiqi.test.factories import RoomFactory, RoomUserFactory, RoomMessageFactory


def test_room_recent_messages(db):
    room = RoomFactory()
    ru = RoomUserFactory(room=room)

    RoomMessageFactory(room=room,
                       user=ru.user,
                       message='new',
                       created_at=datetime(2016, 5, 23))

    RoomMessageFactory(room=room,
                       user=ru.user,
                       message='old',
                       created_at=datetime(2016, 5, 22))

    RoomMessageFactory(room=room,
                       user=ru.user,
                       message='even older',
                       created_at=datetime(2016, 5, 21))

    msg = list(room.recent_messages(db, 2))
    assert msg[0].message == 'old'
    assert msg[1].message == 'new'
