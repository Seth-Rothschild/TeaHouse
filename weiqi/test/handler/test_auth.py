from weiqi.models import User
from weiqi.rating import min_rating
from weiqi.test import session
from weiqi.test.base import BaseAsyncHTTPTestCase
from weiqi.test.factories import RoomFactory, UserFactory


class TestSignUp(BaseAsyncHTTPTestCase):
    def test_sign_up(self):
        RoomFactory(is_default=False)
        room = RoomFactory(is_default=True)

        res = self.post('/api/auth/sign-up', {
            'display': 'display',
            'email': 'test@test.test',
            'rank': '3k',
            'password': 'pw',
            'recaptcha': 'PASS'
        })
        self.assertEqual(res.code, 200)

        user = session.query(User).one()

        self.assertFalse(user.is_active)
        self.assertEqual(user.display, 'display')
        self.assertEqual(user.email, 'test@test.test')
        self.assertEqual(user.rating, min_rating('3k'))
        self.assertTrue(user.check_password('pw'))
        self.assertIsNotNone(user.rating_data)
        self.assertEqual(user.rating_data.rating, min_rating('3k'))

        self.assertEqual(len(user.rooms), 1)
        self.assertEqual(user.rooms[0].room_id, room.id)

    def test_sign_up_confirm(self):
        user = UserFactory(is_active=False)

        res = self.fetch('/api/auth/sign-up/confirm/%d/%s' %
                         (user.id, user.auth_token()))
        session.commit()

        self.assertEqual(res.code, 200)
        self.assertTrue(user.is_active)


class TestSignIn(BaseAsyncHTTPTestCase):
    def test_sign_in(self):
        user = UserFactory(is_active=True)

        res = self.post('/api/auth/sign-in', {
            'email': user.email,
            'password': 'pw'
        })
        session.commit()

        self.assertEqual(res.code, 200)

    def test_sign_in_not_activated(self):
        user = UserFactory(is_active=False)

        res = self.post('/api/auth/sign-in', {
            'email': user.email,
            'password': 'pw'
        })
        session.commit()

        self.assertEqual(res.code, 403)


class TestPasswordReset(BaseAsyncHTTPTestCase):
    def test_password_reset(self):
        user = UserFactory()

        res = self.post('/api/auth/password-reset', {
            'email': user.email
        })

        self.assertEqual(res.code, 200)

    def test_password_reset_confirm(self):
        user = UserFactory()

        res = self.post('/api/auth/password-reset/confirm/%d/%s' % (user.id, user.auth_token()), {
            'password': 'newpw',
            'password-confirm': 'newpw'
        })
        session.commit()

        self.assertEqual(res.code, 200)
        self.assertTrue(user.check_password('newpw'))
