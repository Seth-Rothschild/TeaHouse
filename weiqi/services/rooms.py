from weiqi.models import Room, RoomMessage, RoomUser, DirectRoom, User
from weiqi.services import BaseService, ServiceError


class RoomService(BaseService):
    __service_name__ = 'rooms'

    @BaseService.authenticated
    @BaseService.register
    def message(self, room_id, message):
        ru = self.db.query(RoomUser).filter_by(
            user=self.user, room_id=room_id).first()
        if not ru:
            raise ServiceError('user not in room')

        msg = RoomMessage(
            room=ru.room,
            user=self.user,
            user_display=self.user.display,
            user_rating=self.user.rating,
            message=message)

        self.db.add(msg)
        self.db.commit()

        if ru.room.type == 'direct':
            self._message_direct(ru.room, msg)
        else:
            self.socket.publish(
                'room_message/'+str(room_id), msg.to_frontend())

    def _message_direct(self, room, msg):
        direct = self.db.query(DirectRoom).filter_by(room=room).one()

        if direct.user_one_id != self.user.id:
            direct.user_one_has_unread = True
            other = direct.user_one
        else:
            direct.user_two_has_unread = True
            other = direct.user_two

        if direct.room.users.filter_by(user=other).count() == 0:
            self.db.add(RoomUser(room=direct.room, user=other))

        self.socket.publish('direct_message/' +
                            str(direct.user_one_id), msg.to_frontend())
        self.socket.publish('direct_message/' +
                            str(direct.user_two_id), msg.to_frontend())

    @BaseService.register
    def users(self, room_id):
        room = self.db.query(Room).get(room_id)
        query = self.db.query(RoomUser).filter_by(
            room_id=room.id).join('user').filter_by(is_online=True)

        return {'users': [ru.to_frontend() for ru in query]}

    @BaseService.authenticated
    @BaseService.register
    def open_direct(self, user_id):
        if user_id == self.user.id:
            raise ServiceError('cannot open direct-chat with oneself')

        other = self.db.query(User).filter_by(id=user_id).one()
        direct = self._direct_room(self.user, other)

        if direct.room.users.filter_by(user_id=self.user.id).count() == 0:
            self.db.add(RoomUser(room=direct.room, user=self.user))

        self.db.commit()
        self._subscribe(direct.room.id)

        return {
            'other_user_id': other.id,
            'other_display': other.display,
            'is_online': other.is_online,
            'is_active': True,
            'has_unread': direct.has_unread(self.user),
            'room': direct.room.to_frontend(),
            'room_logs': [m.to_frontend() for m in direct.room.recent_messages(self.db)]
        }

    @BaseService.authenticated
    @BaseService.register
    def close_direct(self, user_id):
        other = self.db.query(User).filter_by(id=user_id).one()
        direct = DirectRoom.filter_by_users(self.db, self.user, other).one()
        direct.room.users.filter_by(user_id=self.user.id).delete()

    def _direct_room(self, user, other):
        direct = DirectRoom.filter_by_users(self.db, user, other).first()

        if not direct:
            room = Room(type='direct')
            direct = DirectRoom(room=room, user_one=user, user_two=other)

            self.db.add(room)
            self.db.add(direct)

        return direct

    @BaseService.authenticated
    @BaseService.register
    def mark_read(self, room_id):
        direct = self.db.query(DirectRoom).filter_by(room_id=room_id).first()
        if not direct:
            return

        if direct.user_one == self.user:
            direct.user_one_has_unread = False
        else:
            direct.user_two_has_unread = False

    def join_room(self, room_id, send_logs=False):
        self._subscribe(room_id)

        if self.user:
            if self.db.query(RoomUser).filter_by(room_id=room_id, user=self.user).count() == 0:
                ru = RoomUser(room_id=room_id, user=self.user)
                self.db.add(ru)

                self._update_users_max(room_id)

                self.socket.publish(
                    'room_user/'+str(ru.room_id), ru.to_frontend())

        if send_logs:
            room = self.db.query(Room).get(room_id)
            self.socket.send('room_logs', {
                'room_id': room_id,
                'logs': [m.to_frontend() for m in room.recent_messages(self.db)],
            })

    def leave_room(self, room_id):
        self._unsubscribe(room_id)

        if self.user:
            ru = self.db.query(RoomUser).filter_by(
                user=self.user, room_id=room_id).first()

            if ru:
                self.socket.publish('room_user_left/' +
                                    str(ru.room_id), ru.to_frontend())
                self.db.delete(ru)

    def _subscribe(self, room_id):
        self.socket.subscribe('room_message/'+str(room_id))
        self.socket.subscribe('room_user/'+str(room_id))
        self.socket.subscribe('room_user_left/'+str(room_id))

    def _unsubscribe(self, room_id):
        self.socket.unsubscribe('room_message/'+str(room_id))
        self.socket.unsubscribe('room_user/'+str(room_id))
        self.socket.unsubscribe('room_user_left/'+str(room_id))

    def _update_users_max(self, room_id):
        room = self.db.query(Room).filter_by(id=room_id).one()
        count = self.db.query(RoomUser).join(User).filter(
            (RoomUser.room == room) & (User.is_online.is_(True))).count()
        room.users_max = max(room.users_max, count)

    def publish_user_rooms(self):
        if not self.user:
            return

        for ru in self.user.rooms:
            if self.user.is_online:
                self.socket.publish(
                    'room_user/'+str(ru.room_id), ru.to_frontend())
            else:
                self.socket.publish('room_user_left/' +
                                    str(ru.room_id), ru.to_frontend())

    def create_default_room(self, name):
        """Creates a new default room and adds all users to that room."""
        room = Room(type='main',
                    is_default=True,
                    name=name)
        self.db.add(room)

        for user_id in self.db.query(User.id):
            ru = RoomUser(room_id=room.id, user_id=user_id[0])
            self.db.add(ru)
