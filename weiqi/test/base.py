import urllib.parse
from unittest import TestCase

from tornado.testing import AsyncHTTPTestCase
from weiqi.application import create_app
from weiqi.models import User, RoomMessage, RoomUser, Room, DirectRoom, Connection, Automatch, Game, Timing, Challenge
from weiqi.test import session


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

        session.rollback()
        session.query(RoomUser).delete()
        session.query(RoomMessage).delete()
        session.query(Connection).delete()
        session.query(DirectRoom).delete()
        session.query(Automatch).delete()
        session.query(Timing).delete()
        session.query(Game).delete()
        session.query(Room).delete()
        session.query(Challenge).delete()
        session.query(User).delete()


class BaseAsyncHTTPTestCase(BaseTestCase, AsyncHTTPTestCase):
    def get_app(self):
        return create_app()

    def post(self, url, data):
        return self.fetch(url, method='POST', body=urllib.parse.urlencode(data))
