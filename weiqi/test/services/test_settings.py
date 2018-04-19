from weiqi.services import SettingsService
from weiqi.test.factories import UserFactory


def test_change_user_info(db, socket):
    user = UserFactory(correspondence_emails=False)
    svc = SettingsService(db, socket, user)

    svc.execute('save_user_info', {
        'email': 'new-test@test.test',
        'info_text': 'new text',
        'correspondence_emails': True
    })

    assert user.email == 'new-test@test.test'
    assert user.info_text == 'new text'
    assert user.correspondence_emails


def test_change_password(db, socket):
    user = UserFactory()
    svc = SettingsService(db, socket, user)

    svc.execute('change_password', {'password': 'newpw'})

    assert user.check_password('newpw')
