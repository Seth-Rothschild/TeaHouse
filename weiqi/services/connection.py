from weiqi.models import Game, Room, RoomUser, DirectRoom, Connection, Automatch, Challenge
from weiqi.services import BaseService, UserService, GameService, RoomService


class ConnectionService(BaseService):
    __service_name__ = 'connection'

    def connect(self):
        self.socket.send('connection_data', self._connection_data())

        self.socket.subscribe('game_started')
        self.socket.subscribe('game_finished')
        self.socket.subscribe('user_status')

        if self.user:
            self.socket.subscribe('direct_message/'+str(self.user.id))
            self.socket.subscribe('automatch_status/'+str(self.user.id))
            self.socket.subscribe('challenges/'+str(self.user.id))

        self._join_open_rooms_and_games()
        self._insert_connection()
        self._check_is_online()

        UserService(self.db, self.socket, self.user).publish_status()
        RoomService(self.db, self.socket, self.user).publish_user_rooms()
        GameService(self.db, self.socket, self.user).publish_demos()

    def disconnect(self):
        self._delete_connection()
        self._check_is_online()

        if self.user:
            self.db.query(Automatch).filter((Automatch.user == self.user) &
                                            (Automatch.preset != 'correspondence')).delete()

        UserService(self.db, self.socket, self.user).publish_status()
        RoomService(self.db, self.socket, self.user).publish_user_rooms()
        GameService(self.db, self.socket, self.user).publish_demos()

    @BaseService.register
    def ping(self):
        return 'pong'

    def _connection_data(self):
        data = {}

        if self.user:
            data.update({
                'user_id': self.user.id,
                'user_display': self.user.display,
                'rating': self.user.rating,
                'wins': Game.count_wins(self.db, self.user),
                'automatch': self.db.query(Automatch).filter_by(user=self.user).count() > 0,
            })

        data.update(self._connection_data_rooms())
        data.update(self._connection_data_games())
        data.update(self._connection_data_direct_rooms())
        data.update(self._connection_data_active_games())
        data.update(self._connection_data_challenges())

        return data

    def _connection_data_rooms(self):
        rooms = []
        logs = {}

        for room in Room.open_rooms(self.db, self.user):
            rooms.append(room.to_frontend())
            logs[room.id] = [m.to_frontend()
                             for m in room.recent_messages(self.db)]

        return {'rooms': rooms, 'room_logs': logs}

    def _connection_data_games(self):
        if not self.user:
            return {}

        return {
            'open_games': [g.to_frontend(full=True) for g in self.user.open_games(self.db)]
        }

    def _connection_data_direct_rooms(self):
        if not self.user:
            return {}

        direct = []

        query = self.db.query(DirectRoom).join(Room).join(RoomUser).filter(
            ((DirectRoom.user_one == self.user) | (DirectRoom.user_two == self.user)) &
            (RoomUser.user == self.user))

        for dr in query:
            other = dr.other(self.user)

            direct.append({
                'other_user_id': other.id,
                'other_display': other.display,
                'is_online': other.is_online,
                'is_active': True,
                'has_unread': dr.has_unread(self.user),
                'room': dr.room.to_frontend(),
                'room_logs': [m.to_frontend() for m in dr.room.recent_messages(self.db)]
            })

        return {'direct_rooms': direct}

    def _connection_data_active_games(self):
        return {
            'active_games': [g.to_frontend() for g in Game.active_games(self.db)]
        }

    def _connection_data_challenges(self):
        if not self.user:
            return {}

        return {
            'challenges': [c.to_frontend() for c in Challenge.open_challenges(self.db, self.user)]
        }

    def _join_open_rooms_and_games(self):
        for room in Room.open_rooms(self.db, self.user):
            RoomService(self.db, self.socket, self.user).join_room(room.id)

            if room.type == 'game':
                GameService(self.db, self.socket,
                            self.user).subscribe(room.game.id)

    def _insert_connection(self):
        conn = Connection(id=self.socket.id,
                          user=self.user,
                          ip=self.socket.request.remote_ip)

        self.db.add(conn)

    def _delete_connection(self):
        self.db.query(Connection).filter_by(id=self.socket.id).delete()

    def _check_is_online(self):
        if self.user:
            self.user.is_online = self.db.query(Connection).filter_by(
                user_id=self.user.id).count() > 0
