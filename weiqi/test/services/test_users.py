from weiqi.services import UserService
from weiqi.test.factories import UserFactory


def test_profile(db, socket):
    user = UserFactory(is_online=True)
    svc = UserService(db, socket)

    profile = svc.execute('profile', {'user_id': user.id})

    assert profile.get('id') == user.id
    assert profile.get('last_activity_at') == user.last_activity_at.isoformat()
    assert profile.get('is_online') == user.is_online
    assert profile.get('rating') == user.rating
    assert profile.get('display') == user.display
    assert profile.get('info_text_html') == user.info_text_html


def test_autocomplete(db, socket):
    UserFactory(display='t_one_t')
    UserFactory(display='name')
    UserFactory(display='some_one')

    svc = UserService(db, socket)

    users = svc.execute('autocomplete', {'query': 'one'})

    assert len(users) == 2
