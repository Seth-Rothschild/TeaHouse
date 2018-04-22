from tornado.web import HTTPError
from weiqi import settings, metrics
from weiqi.glicko2 import Player
from weiqi.handler.base import BaseHandler
from weiqi.mailer import send_mail
from weiqi.models import User, RoomUser, Room
from weiqi.rating import min_rating
from weiqi.recaptcha import validate_recaptcha


class SignUpHandler(BaseHandler):
    def post(self):
        validate_recaptcha(self.get_body_argument('recaptcha'))

        user = User(display=self.get_body_argument('display'),
                    email=self.get_body_argument('email'),
                    is_active=False)

        user.set_password(self.get_body_argument('password'))
        self._sign_up_rating(user, self.get_body_argument('rank'))
        self._sign_up_rooms(user)

        self.db.add(user)
        self.db.commit()

        url = '%s://%s/api/auth/sign-up/confirm/%d/%s' % (self.request.protocol,
                                                          self.request.host,
                                                          user.id,
                                                          user.auth_token())

        send_mail(user.email, user.display, 'Account activation', 'sign_up.txt', {
            'url': url
        })

        metrics.REGISTRATIONS.inc()

        self.write({})

    def _sign_up_rating(self, user, rank):
        rating = min_rating(rank)

        if rating < min_rating('20k') or rating > min_rating('3d'):
            raise HTTPError(400, 'invalid rank')

        user.rating = rating
        user.rating_data = Player(rating)

    def _sign_up_rooms(self, user):
        for room in self.db.query(Room).filter_by(type='main', is_default=True):
            ru = RoomUser(user=user, room=room)
            self.db.add(ru)


class SignUpConfirmHandler(BaseHandler):
    def get(self, user_id, token):
        user = self.db.query(User).get(user_id)

        if not user or not user.check_auth_token(token):
            raise HTTPError(404)

        user.is_active = True
        self.db.commit()

        self.set_secure_cookie(settings.COOKIE_NAME, str(user.id))
        self.redirect('/')


class SignInHandler(BaseHandler):
    def post(self):
        email = self.get_body_argument('email')
        password = self.get_body_argument('password')

        user = self.db.query(User).filter_by(email=email).one()

        if not user.check_password(password):
            raise HTTPError(403, 'invalid username or password')

        if not user.is_active:
            raise HTTPError(403, 'account not activated')

        self.set_secure_cookie(settings.COOKIE_NAME, str(user.id))
        self.write({})


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies()
        self.redirect('/')


class PasswordResetHandler(BaseHandler):
    def post(self):
        email = self.get_body_argument('email')
        user = self.db.query(User).filter_by(email=email).first()

        if not user:
            return

        url = '%s://%s/api/auth/password-reset/confirm/%d/%s' % (self.request.protocol,
                                                                 self.request.host,
                                                                 user.id,
                                                                 user.auth_token())

        send_mail(user.email, user.display, 'Password reset', 'password_reset.txt', {
            'url': url
        })


class PasswordResetConfirmHandler(BaseHandler):
    def get(self, user_id, token):
        messages = []
        user = self.db.query(User).get(user_id)

        if not user or not user.check_auth_token(token):
            show_form = False
            messages.append(
                {'type': 'danger', 'message': 'Token is invalid or user was not found.'})
        else:
            show_form = True

        self.render("password_reset.html",
                    messages=messages, show_form=show_form)

    def post(self, user_id, token):
        messages = []
        show_form = True

        user = self.db.query(User).filter_by(id=user_id).one()

        password = self.get_body_argument('password')
        password_confirm = self.get_body_argument('password-confirm')

        if password != password_confirm:
            messages.append(
                {'type': 'danger', 'message': 'Passwords do not match'})
        else:
            user.set_password(password)
            messages.append({'type': 'success', 'message': 'Password reset'})
            show_form = False

        self.render("password_reset.html",
                    messages=messages, show_form=show_form)
