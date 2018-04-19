from datetime import datetime, timedelta

import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyText
from weiqi.board import Board
from weiqi.glicko2 import Player
from weiqi.models import User, Room, RoomUser, RoomMessage, Automatch, Game, Timing, Challenge
from weiqi.test import session


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = session

    last_activity_at = datetime.utcnow()
    email = FuzzyText(suffix='@test.test')
    password = ''
    display = FuzzyText()
    info_text = FuzzyText()
    is_online = True
    rating = 1000
    rating_data = factory.lazy_attribute(lambda o: Player(o.rating))

    @factory.post_generation
    def factory_password(self, *args, **kwargs):
        self.set_password('pw')
        session.commit()


class RoomFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Room
        sqlalchemy_session = session
        force_flush = True

    name = FuzzyText()
    type = 'main'
    is_default = True


class RoomUserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = RoomUser
        sqlalchemy_session = session
        force_flush = True

    room = factory.SubFactory(RoomFactory)
    user = factory.SubFactory(UserFactory)


class RoomMessageFactory(SQLAlchemyModelFactory):
    class Meta:
        model = RoomMessage
        sqlalchemy_session = session
        force_flush = True

    room = factory.SubFactory(RoomFactory)
    user = factory.SubFactory(UserFactory)

    user_display = factory.lazy_attribute(lambda o: o.user.display)
    user_rating = factory.lazy_attribute(lambda o: o.user.rating)

    message = 'test'


class AutomatchFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Automatch
        sqlalchemy_session = session
        force_flush = True

    user = factory.SubFactory(UserFactory, rating=1000)
    user_rating = factory.lazy_attribute(lambda o: o.user.rating)
    min_rating = 1000
    max_rating = 1099
    preset = 'fast'


class GameFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Game
        sqlalchemy_session = session

    room = factory.SubFactory(RoomFactory)
    timing = factory.RelatedFactory(
        'weiqi.test.factories.TimingFactory', 'game')

    is_demo = False
    is_ranked = True
    is_private = False
    stage = 'playing'
    board = factory.lazy_attribute(lambda o: Board(9))
    komi = 7.5
    result = ''
    black_user = factory.SubFactory(UserFactory)
    black_display = factory.lazy_attribute(lambda o: o.black_user.display)
    black_rating = factory.lazy_attribute(lambda o: o.black_user.rating)
    white_user = factory.SubFactory(UserFactory)
    white_display = factory.lazy_attribute(lambda o: o.white_user.display)
    white_rating = factory.lazy_attribute(lambda o: o.white_user.rating)


class DemoGameFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Game
        sqlalchemy_session = session
        force_flush = True

    room = factory.SubFactory(RoomFactory)
    is_demo = True
    is_ranked = False
    stage = 'finished'
    board = factory.lazy_attribute(lambda o: Board(9))
    komi = 7.5
    result = ''
    demo_owner = factory.SubFactory(UserFactory)
    demo_owner_display = factory.lazy_attribute(lambda o: o.demo_owner.display)
    demo_owner_rating = factory.lazy_attribute(lambda o: o.demo_owner.rating)
    demo_control = factory.lazy_attribute(lambda o: o.demo_owner)
    demo_control_display = factory.lazy_attribute(
        lambda o: o.demo_control.display)


class TimingFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Timing
        sqlalchemy_session = session
        force_flush = True

    game = factory.SubFactory(GameFactory)
    system = 'fischer'
    start_at = datetime.utcnow()
    timing_updated_at = datetime.utcnow()
    next_move_at = datetime.utcnow()
    main = timedelta(minutes=1)
    overtime = timedelta(seconds=20)
    black_main = timedelta(minutes=1)
    black_overtime = timedelta(seconds=20)
    white_main = timedelta(minutes=1)
    white_overtime = timedelta(seconds=20)


class ChallengeFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Challenge
        sqlalchemy_session = session
        force_flush = True

    expire_at = datetime.utcnow() + timedelta(minutes=10)
    owner = factory.SubFactory(UserFactory)
    challengee = factory.SubFactory(UserFactory)
    board_size = 19
    handicap = 0
    komi = 7.5
    owner_is_black = True
    timing_system = 'fischer'
    maintime = timedelta(minutes=1)
    overtime = timedelta(seconds=20)
