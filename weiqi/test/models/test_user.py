from datetime import datetime, timedelta

from weiqi.models import User


def test_password():
    user = User()
    user.set_password('pw')

    assert user.password != 'pw'
    assert user.check_password('pw')
    assert not user.check_password('invalid')


def test_auth_token():
    user = User()
    user.set_password('pw')

    token = user.auth_token()
    assert token
    assert user.check_auth_token(token)
    assert not user.check_auth_token('00000-'+token.split('-')[1])


def test_auth_token_expired():
    user = User()
    user.set_password('pw')

    token = user.auth_token(str(datetime.timestamp(
        datetime.utcnow() - timedelta(days=29))))
    assert user.check_auth_token(token)

    token = user.auth_token(str(datetime.timestamp(
        datetime.utcnow() - timedelta(days=31))))
    assert not user.check_auth_token(token)
