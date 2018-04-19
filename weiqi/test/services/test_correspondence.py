from weiqi.services import CorrespondenceService
from weiqi.test.factories import GameFactory


def test_correspondence_settings(db, socket, mails):
    game = GameFactory(is_correspondence=True,
                       black_user__correspondence_emails=False,
                       black_user__is_online=False,
                       white_user__correspondence_emails=True,
                       white_user__is_online=False)

    svc = CorrespondenceService(db, socket)
    svc.notify_automatch_started(game)

    assert len(mails) == 1
    assert mails[0]['to'] == game.white_user.email
