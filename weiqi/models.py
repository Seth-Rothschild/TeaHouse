# weiqi.gs
# Copyright (C) 2016 Michael Bitzi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import hmac
import json
import re
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import (Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, TypeDecorator, Text,
                        CheckConstraint, Binary, Interval, UniqueConstraint)
from sqlalchemy.orm import validates, relationship, deferred
from sqlalchemy.orm.attributes import flag_modified
from weiqi import settings
from weiqi.board import board_from_dict, BLACK
from weiqi.db import Base
from weiqi.glicko2 import player_from_dict, RatingEncoder
from weiqi.markdown import markdown_to_html


class RatingData(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return json.dumps(value, cls=RatingEncoder)

    def process_result_value(self, value, dialect):
        data = json.loads(value)
        return player_from_dict(data)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity_at = Column(DateTime)

    is_active = Column(Boolean, nullable=False, default=True)

    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    display = Column(String, nullable=False)
    info_text = deferred(Column(Text, nullable=False, default=''))

    rating = Column(Float, nullable=False, default=0)
    last_rating_update_at = Column(DateTime, default=datetime.utcnow)
    rating_data = deferred(Column(RatingData, nullable=False))

    is_online = Column(Boolean, nullable=False, default=False)

    avatar = deferred(Column(Binary))
    avatar_large = deferred(Column(Binary))

    correspondence_emails = Column(Boolean, nullable=False, default=True)

    rooms = relationship('RoomUser', back_populates='user')
    connections = relationship('Connection', back_populates='user')
    automatch = relationship('Automatch', back_populates='user')

    def set_password(self, pw):
        self.password = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, pw):
        return bcrypt.hashpw(pw.encode(), self.password.encode()) == self.password.encode()

    @validates('email')
    def validate_email(self, key, val):
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', val):
            raise ValueError('invalid email address')
        return val

    @validates('display')
    def validate_display(self, key, val):
        if not re.match(r'^[a-zA-Z0-9 _-]{2,20}$', val):
            raise ValueError('invalid display name')
        return val

    @validates('info_text')
    def validate_info_text(self, key, val):
        if len(val) > settings.MAX_USER_INFO_TEXT_LENGTH:
            raise ValueError('info text is too long')
        return val

    def auth_token(self, ts=None):
        """Generates a unique token based on the users credentials and the current timestamp."""
        if not ts:
            ts = str(datetime.timestamp(datetime.utcnow()))
        h = hmac.new(settings.SECRET)
        h.update(self.password.encode())
        h.update(ts.encode())
        return '{}-{}'.format(ts, h.hexdigest())

    def check_auth_token(self, token):
        ts, _ = token.split('-', 1)

        if datetime.utcfromtimestamp(float(ts)) < datetime.utcnow() - timedelta(days=30):
            return False

        return token == self.auth_token(ts)

    def to_frontend(self):
        return {
            'id': self.id,
            'display': self.display,
            'rating': self.rating,
        }

    def open_games(self, db):
        return (db.query(Game).join(Room).join(RoomUser)
                .filter(((Game.is_demo.isnot(True)) &
                         (Game.stage != 'finished') &
                         ((Game.black_user == self) | (Game.white_user == self))) |
                        (RoomUser.user == self))
                .order_by(Game.created_at.desc()))

    def open_demos(self, db):
        return (db.query(Game).join(Room).join(RoomUser)
                .filter((Game.is_demo.is_(True)) &
                        (Game.demo_owner == self) &
                        (RoomUser.user == self))
                .order_by(Game.created_at.desc()))

    def games(self, db):
        return (db.query(Game).filter((Game.black_user == self) |
                                      (Game.white_user == self) |
                                      (Game.demo_owner == self))
                .order_by(Game.created_at.desc()))

    def apply_rating_data_change(self):
        """Notifies sqlalchemy about a change in the `rating_data` field.

        Needs to be called after in-place changes to the field.
        """
        flag_modified(self, 'rating_data')

    @property
    def info_text_html(self):
        if not self.info_text:
            return ''
        return markdown_to_html(self.info_text)


class Connection(Base):
    __tablename__ = 'connections'

    id = Column(String, primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(ForeignKey('users.id'), nullable=True)
    user = relationship('User', back_populates='connections')

    ip = Column(String)


class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    name = Column(String, nullable=False, default='')
    type = Column(Enum('main', 'direct', 'game', name='room_type'), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)

    users_max = Column(Integer, nullable=False, default=0)

    users = relationship('RoomUser', back_populates='room', lazy='dynamic')
    game = relationship('Game', back_populates='room', uselist=False)

    def to_frontend(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
        }

    @staticmethod
    def open_rooms(db, user):
        if not user:
            return db.query(Room).filter_by(type='main')
        return db.query(Room).join('users').filter_by(user_id=user.id)

    def recent_messages(self, db, limit=None):
        if not limit:
            limit = settings.ROOM_MESSAGES_LIMIT
        return reversed(db.query(RoomMessage)
                        .filter(RoomMessage.room_id == self.id)
                        .order_by(RoomMessage.created_at.desc())[:limit])


class RoomUser(Base):
    __tablename__ = 'room_users'

    room_id = Column(ForeignKey('rooms.id'), primary_key=True)
    user_id = Column(ForeignKey('users.id'), primary_key=True)

    room = relationship('Room', back_populates='users')
    user = relationship('User', back_populates='rooms', lazy='joined')

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_frontend(self):
        return {
            'room_id': self.room_id,
            'user_id': self.user.id,
            'user_display': self.user.display,
            'user_rating': self.user.rating,
        }


class RoomMessage(Base):
    __tablename__ = 'room_messages'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    room_id = Column(ForeignKey('rooms.id'), nullable=False)
    room = relationship('Room')

    user_id = Column(ForeignKey('users.id'), nullable=False)
    user = relationship('User')

    user_display = Column(String, nullable=False)
    user_rating = Column(Float, nullable=False)

    message = Column(String, nullable=False)

    @validates('message')
    def validate_message(self, key, val):
        if not val or not val.strip():
            raise ValueError('message cannot be empty')
        return val.strip()

    def to_frontend(self):
        return {
            'id': self.id,
            'created_at': datetime_to_frontend(self.created_at),
            'room_id': self.room_id,
            'user_id': self.user_id,
            'user_display': self.user_display,
            'user_rating': self.user_rating,
            'message': self.message
        }


class DirectRoom(Base):
    __tablename__ = 'direct_rooms'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    room_id = Column(ForeignKey('rooms.id'), nullable=False)
    room = relationship('Room')

    user_one_id = Column(ForeignKey('users.id'), nullable=False)
    user_one = relationship('User', foreign_keys=[user_one_id])
    user_one_has_unread = Column(Boolean, nullable=False, default=False)

    user_two_id = Column(ForeignKey('users.id'), nullable=False)
    user_two = relationship('User', foreign_keys=[user_two_id])
    user_two_has_unread = Column(Boolean, nullable=False, default=False)

    @staticmethod
    def filter_by_users(db, user, other):
        return db.query(DirectRoom).filter(
            ((DirectRoom.user_one == user) & (DirectRoom.user_two == other)) |
            ((DirectRoom.user_one == other) & (DirectRoom.user_two == user)))

    def other(self, user):
        return self.user_one if user != self.user_one else self.user_two

    def has_unread(self, user):
        if user == self.user_one:
            return self.user_one_has_unread
        elif user == self.user_two:
            return self.user_two_has_unread
        return False


class Automatch(Base):
    __tablename__ = 'automatch'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='automatch')

    user_rating = Column(Float, nullable=False)

    preset = Column(String, nullable=False)
    min_rating = Column(Float, nullable=False)
    max_rating = Column(Float, nullable=False)

    __table_args__ = (CheckConstraint('min_rating <= max_rating', name='rating_check'),)


class BoardData(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return json.dumps(value.to_dict())

    def process_result_value(self, value, dialect):
        return board_from_dict(json.loads(value))


class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    room_id = Column(ForeignKey('rooms.id'), nullable=False)
    room = relationship('Room', back_populates='game')

    timing = relationship('Timing', back_populates='game', uselist=False)

    is_demo = Column(Boolean, nullable=False, default=False)
    is_ranked = Column(Boolean, nullable=False, default=True)
    is_correspondence = Column(Boolean, nullable=False, default=False)
    is_private = Column(Boolean, nullable=False, default=False)

    stage = Column(Enum('playing', 'counting', 'finished', name='game_stage'), nullable=False)
    title = Column(String, nullable=False, default='')

    board = deferred(Column(BoardData, nullable=False))
    komi = Column(Float, nullable=False)

    result = Column(String, nullable=False, default='')
    result_black_confirmed = Column(String, nullable=False, default='')
    result_white_confirmed = Column(String, nullable=False, default='')

    black_user_id = Column(ForeignKey('users.id'), nullable=True)
    black_user = relationship('User', foreign_keys=[black_user_id])
    black_display = Column(String, nullable=False, default='')
    black_rating = Column(Float, nullable=True)

    white_user_id = Column(ForeignKey('users.id'), nullable=True)
    white_user = relationship('User', foreign_keys=[white_user_id])
    white_display = Column(String, nullable=False, default='')
    white_rating = Column(Float, nullable=True)

    demo_owner_id = Column(ForeignKey('users.id'), nullable=True)
    demo_owner = relationship('User', foreign_keys=[demo_owner_id])
    demo_owner_display = Column(String, nullable=False, default='')
    demo_owner_rating = Column(Float, nullable=True)

    demo_control_id = Column(ForeignKey('users.id'), nullable=True)
    demo_control = relationship('User', foreign_keys=[demo_control_id])
    demo_control_display = Column(String, nullable=False, default='')

    __table_args__ = (
        CheckConstraint('NOT is_ranked OR NOT is_demo'),
        CheckConstraint('is_demo OR black_user_id IS NOT NULL'),
        CheckConstraint('is_demo OR white_user_id IS NOT NULL'),
        CheckConstraint('is_demo OR black_user_id != white_user_id'),
        CheckConstraint('NOT is_demo OR demo_owner_id IS NOT NULL'),
    )

    @validates('is_demo', 'is_correspondence')
    def validate_is_correspondence(self, key, val):
        if key == 'is_correspondence' and val and self.is_demo:
            raise ValueError('demo games cannot be correspondence games')
        return val

    @property
    def current_user(self):
        if self.is_demo:
            return self.demo_owner
        return self.black_user if self.board.current == BLACK else self.white_user

    @property
    def winner_loser(self):
        if self.result.lower().startswith('b+'):
            return self.black_user, self.white_user
        elif self.result.lower().startswith('w+'):
            return self.white_user, self.black_user
        else:
            raise ValueError('could not determine winner and loser from game result: {}'.format(self.result))

    @staticmethod
    def count_wins(db, user):
        return db.query(Game).filter(
            ((Game.is_ranked == True) & (Game.stage == 'finished')) &
            (((Game.black_user == user) & (Game.result.startswith('B+'))) |
             ((Game.white_user == user) & (Game.result.startswith('W+'))))).count()

    @staticmethod
    def active_games(db):
        return db.query(Game).distinct(Game.id).join(Room).outerjoin(RoomUser).outerjoin(Game.demo_owner).filter(
            ((Game.is_demo.is_(False)) & (Game.stage != 'finished')) |
            ((Game.is_demo.is_(True)) & (RoomUser.user_id == Game.demo_owner_id) & (User.is_online.is_(True))))

    def to_frontend(self, full=False):
        """Returns a dictionary with the game information.
        Will not return board data unless `full` is set to True.
        """
        data = {
            'id': self.id,
            'created_at': datetime_to_frontend(self.created_at),
            'room_id': self.room_id,
            'is_demo': self.is_demo,
            'is_ranked': self.is_ranked,
            'is_correspondence': self.is_correspondence,
            'is_private': self.is_private,
            'stage': self.stage,
            'title': self.title,
            'komi': self.komi,
            'result': self.result,
            'black_user_id': self.black_user_id,
            'black_display': self.black_display,
            'black_rating': self.black_rating,
            'white_user_id': self.white_user_id,
            'white_display': self.white_display,
            'white_rating': self.white_rating,
            'demo_owner_id': self.demo_owner_id,
            'demo_owner_display': self.demo_owner_display,
            'demo_owner_rating': self.demo_owner_rating
        }

        if full:
            data.update({
                'board': self.board.to_dict(),
                'timing': self.timing.to_frontend() if self.timing else None,
                'result_black_confirmed': self.result_black_confirmed,
                'result_white_confirmed': self.result_white_confirmed,
                'demo_control_id': self.demo_control_id,
                'demo_control_display': self.demo_control_display,
            })

        return data

    def apply_board_change(self):
        """Notifies sqlalchemy about a change in the `board` field.

        Needs to be called after in-place changes to the field.
        """
        flag_modified(self, 'board')


TimingSystem = Enum('fischer', 'byoyomi', name='timing_system')


class Timing(Base):
    __tablename__ = 'timings'

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    game_id = Column(ForeignKey('games.id'), nullable=False)
    game = relationship('Game', back_populates='timing')

    start_at = Column(DateTime, nullable=False)
    timing_updated_at = Column(DateTime)
    next_move_at = Column(DateTime)

    system = Column(TimingSystem, nullable=False)
    main = Column(Interval, nullable=False)
    capped = Column(Boolean, nullable=False, default=False)
    overtime = Column(Interval, nullable=False)
    overtime_count = Column(Integer, nullable=False, default=0)

    black_main = Column(Interval, nullable=False)
    black_overtime = Column(Interval, nullable=False)

    white_main = Column(Interval, nullable=False)
    white_overtime = Column(Interval, nullable=False)

    @property
    def has_started(self):
        return self.start_at < datetime.utcnow()

    @property
    def black_total(self):
        return self.black_main + self.black_overtime

    @property
    def white_total(self):
        return self.white_main + self.white_overtime

    @property
    def main_cap(self):
        return self.main * settings.TIMING_MAIN_CAP_MULTIPLIER

    def to_frontend(self):
        return {
            'start_at': self.start_at.isoformat(),
            'timing_updated_at': self.timing_updated_at.isoformat(),
            'system': self.system,
            'main': self.main.total_seconds(),
            'overtime': self.overtime.total_seconds(),
            'overtime_count': self.overtime_count,
            'black_main': self.black_main.total_seconds(),
            'black_overtime': self.black_overtime.total_seconds(),
            'white_main': self.white_main.total_seconds(),
            'white_overtime': self.white_overtime.total_seconds(),
        }


class Challenge(Base):
    __tablename__ = 'challenges'

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    expire_at = Column(DateTime, nullable=False)

    owner_id = Column(ForeignKey('users.id'), nullable=False)
    owner = relationship('User', foreign_keys=[owner_id])

    challengee_id = Column(ForeignKey('users.id'), nullable=False)
    challengee = relationship('User', foreign_keys=[challengee_id])

    board_size = Column(Integer, nullable=False, default=19)
    komi = Column(Float, nullable=False)
    handicap = Column(Integer, nullable=False)
    owner_is_black = Column(Boolean, nullable=False)

    is_correspondence = Column(Boolean, nullable=False, default=False)
    timing_system = Column(TimingSystem, nullable=False)
    maintime = Column(Interval, nullable=False)
    overtime = Column(Interval, nullable=False)
    overtime_count = Column(Integer, nullable=False, default=0)

    is_private = Column(Boolean, nullable=False, default=False)
    is_ranked = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint('owner_id != challengee_id'),
        UniqueConstraint('owner_id', 'challengee_id'),
    )

    @validates('board_size')
    def validate_board_size(self, key, val):
        if val not in [9, 13, 19]:
            raise ValueError('invalid board size')
        return val

    @validates('handicap')
    def validate_handicap(self, key, val):
        if not 0 <= val <= 9:
            raise ValueError('invalid handicap')
        return val

    @staticmethod
    def open_challenges(db, user):
        return db.query(Challenge).filter((Challenge.owner == user) | (Challenge.challengee == user))

    def to_frontend(self):
        return {
            'id': self.id,
            'created_at': datetime_to_frontend(self.created_at),
            'expire_at': datetime_to_frontend(self.expire_at),
            'owner_id': self.owner_id,
            'owner_display': self.owner.display,
            'owner_rating': self.owner.rating,
            'challengee_id': self.challengee_id,
            'challengee_display': self.challengee.display,
            'challengee_rating': self.challengee.rating,
            'board_size': self.board_size,
            'handicap': self.handicap,
            'komi': self.komi,
            'owner_is_black': self.owner_is_black,
            'is_correspondence': self.is_correspondence,
            'timing_system': self.timing_system,
            'maintime': self.maintime.total_seconds(),
            'overtime': self.overtime.total_seconds(),
            'overtime_count': self.overtime_count,
            'is_private': self.is_private,
            'is_ranked': self.is_ranked,
        }


def datetime_to_frontend(date):
    return date.isoformat()
