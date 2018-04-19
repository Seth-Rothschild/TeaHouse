from datetime import datetime, timedelta

import pytest
from weiqi import settings
from weiqi.models import Automatch, Game, Challenge
from weiqi.services import PlayService
from weiqi.services.play import ChallengeExpiredError, InvalidBoardSizeError, ChallengePrivateCannotBeRankedError
from weiqi.test.factories import UserFactory, AutomatchFactory, GameFactory, ChallengeFactory


def test_automatch_inserting(db, socket):
    user = UserFactory(rating=300)
    socket.subscribe('automatch_status/'+str(user.id))

    svc = PlayService(db, socket, user)
    svc.execute('automatch', {'preset': 'fast', 'max_hc': 0})

    assert db.query(Automatch).count() == 1

    item = db.query(Automatch).first()
    assert item.user == user
    assert item.user_rating == user.rating
    assert item.preset == 'fast'
    assert item.min_rating == 300
    assert item.max_rating == 399

    assert len(socket.sent_messages) == 1
    assert socket.sent_messages[0]['method'] == 'automatch_status'
    assert socket.sent_messages[0]['data']['in_queue']


def test_automatch_twice(db, socket):
    user = UserFactory()
    svc = PlayService(db, socket, user)

    svc.execute('automatch', {'preset': 'fast', 'max_hc': 0})
    svc.execute('automatch', {'preset': 'medium', 'max_hc': 0})

    assert db.query(Automatch).count() == 1
    item = db.query(Automatch).first()
    assert item.user == user
    assert item.preset == 'medium'


def test_automatch_create_game(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1600)
    AutomatchFactory(user=other, user_rating=1600,
                     user__rating=1600, min_rating=1500, max_rating=1700)

    socket.subscribe('game_started')
    socket.subscribe('automatch_status/'+str(user.id))
    socket.subscribe('automatch_status/'+str(other.id))

    svc = PlayService(db, socket, user)
    svc.execute('automatch', {'preset': 'fast', 'max_hc': 1})

    assert db.query(Automatch).count() == 0
    assert db.query(Game).count() == 1

    game = db.query(Game).first()
    assert not game.is_demo
    assert game.is_ranked
    assert game.board is not None
    assert game.board.size == settings.AUTOMATCH_SIZE
    assert game.board.handicap == 1
    assert game.komi == 0.5
    assert game.stage == 'playing'
    assert len(game.room.users.all()) == 2

    assert game.black_user in [user, other]
    assert game.white_user in [user, other]
    assert game.black_user != game.white_user

    assert game.black_display in [user.display, other.display]
    assert game.white_display in [user.display, other.display]
    assert game.black_display != game.white_display

    assert game.black_rating in [user.rating, other.rating]
    assert game.white_rating in [user.rating, other.rating]
    assert game.black_rating != game.white_rating

    assert (game.timing.start_at - (datetime.utcnow() +
                                    settings.GAME_START_DELAY)).total_seconds() < 1
    assert (game.timing.start_at -
            game.timing.timing_updated_at).total_seconds() < 1
    assert (game.timing.start_at - game.timing.next_move_at).total_seconds() < 1
    assert game.timing.system == 'fischer'
    assert game.timing.black_overtime == timedelta()
    assert game.timing.white_overtime == timedelta()

    assert len(socket.sent_messages) == 3
    assert socket.sent_messages[0]['method'] == 'game_started'
    assert socket.sent_messages[0]['data'] == game.to_frontend()
    assert socket.sent_messages[1]['method'] == 'automatch_status'
    assert not socket.sent_messages[1]['data']['in_queue']
    assert socket.sent_messages[2]['method'] == 'automatch_status'
    assert not socket.sent_messages[2]['data']['in_queue']


def test_automatch_handicap_one(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1600)
    AutomatchFactory(user=other, user_rating=1600,
                     user__rating=1600, min_rating=1400, max_rating=1700)

    svc = PlayService(db, socket, user)
    svc.execute('automatch', {'preset': 'fast', 'max_hc': 2})

    game = db.query(Game).first()
    assert game.board.handicap == 1


def test_automatch_handicap_two(db, socket):
    user = UserFactory(rating=1400)
    other = UserFactory(rating=1600)
    AutomatchFactory(user=other, user_rating=1600,
                     user__rating=1600, min_rating=1400, max_rating=1700)

    svc = PlayService(db, socket, user)
    svc.execute('automatch', {'preset': 'fast', 'max_hc': 2})

    game = db.query(Game).first()
    assert game.board.handicap == 2


def test_automatch_preset(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)
    third = UserFactory(rating=1500)
    AutomatchFactory(user=user, user_rating=1500, user__rating=1500,
                     min_rating=1500, max_rating=1500, preset='fast')

    svc = PlayService(db, socket, other)
    svc.execute('automatch', {'preset': 'slow', 'max_hc': 1})
    assert db.query(Automatch).count() == 2
    assert db.query(Game).count() == 0

    svc = PlayService(db, socket, third)
    svc.execute('automatch', {'preset': 'fast', 'max_hc': 1})
    assert db.query(Automatch).count() == 1
    assert db.query(Automatch).first().preset == 'slow'
    assert db.query(Game).count() == 1


def test_automatch_correspondence(db, socket, mails):
    user = UserFactory(rating=1500, is_online=False)
    other = UserFactory(rating=1500, is_online=False)
    AutomatchFactory(user=other, preset='correspondence',
                     user_rating=1500, user__rating=1500,
                     min_rating=1500, max_rating=1500)

    svc = PlayService(db, socket, user)
    svc.execute('automatch', {'preset': 'correspondence', 'max_hc': 0})

    assert db.query(Automatch).count() == 0
    assert db.query(Game).count() == 1

    game = db.query(Game).first()
    assert game.is_correspondence
    assert game.timing.capped

    assert len(mails) == 2
    assert mails[0]['template'] == 'correspondence/automatch_started.txt'
    assert mails[1]['template'] == 'correspondence/automatch_started.txt'
    assert {mails[0]['to'], mails[1]['to']} == {user.email, other.email}


def test_automatch_same_user_twice(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)
    GameFactory(black_user=user, white_user=other)

    AutomatchFactory(user=other, preset='correspondence',
                     user_rating=1500, user__rating=1500,
                     min_rating=1500, max_rating=1500)

    svc = PlayService(db, socket, user)
    svc.execute('automatch', {'preset': 'correspondence', 'max_hc': 0})

    assert db.query(Automatch).count() == 2
    assert db.query(Game).count() == 1


def test_game_players_handicap():
    svc = PlayService()

    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)
    assert svc.game_players_handicap(other, user)[2] == 0

    user = UserFactory(rating=1500)
    other = UserFactory(rating=1600)
    assert svc.game_players_handicap(other, user) == (user, other, 1)

    user = UserFactory(rating=1800)
    other = UserFactory(rating=1600)
    assert svc.game_players_handicap(other, user) == (other, user, 2)


def test_game_player_handicap_limit():
    svc = PlayService()

    user = UserFactory(rating=2000)
    other = UserFactory(rating=100)
    assert svc.game_players_handicap(other, user)[2] == 9


def test_game_players_random():
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)
    svc = PlayService()

    has_user_black = False
    has_user_white = False

    for i in range(20):
        if svc.game_players_handicap(other, user)[0] == user:
            has_user_black = True
        else:
            has_user_white = True

    assert has_user_black
    assert has_user_white


def test_upload_sgf(db, socket):
    user = UserFactory()
    svc = PlayService(db, socket, user)

    game_id = svc.execute('upload_sgf', {'sgf': '(;B[dd]W[qq])'})
    game = db.query(Game).get(game_id)

    assert game is not None
    assert game.room is not None
    assert game.is_demo
    assert game.demo_owner == user
    assert game.demo_owner_rating == user.rating
    assert game.demo_owner_display == user.display
    assert game.demo_control == user
    assert game.demo_control_display == user.display


def test_create_demo(db, socket):
    user = UserFactory()
    svc = PlayService(db, socket, user)

    game_id = svc.execute('create_demo', {'title': 'test', 'size': 19})
    game = db.query(Game).get(game_id)

    assert game is not None
    assert game.room is not None
    assert game.is_demo
    assert game.title == 'test'
    assert game.demo_owner == user
    assert game.demo_owner_rating == user.rating
    assert game.demo_owner_display == user.display
    assert game.demo_control == user
    assert game.demo_control_display == user.display


def test_create_demo_from_game(db, socket):
    user = UserFactory()
    game = GameFactory()
    svc = PlayService(db, socket, user)

    demo_id = svc.execute('create_demo_from_game', {'game_id': game.id})
    demo = db.query(Game).get(demo_id)

    assert demo is not None
    assert demo.room is not None
    assert demo.is_demo
    assert demo.board.to_dict() == game.board.to_dict()
    assert demo.black_display == game.black_display
    assert demo.white_display == game.white_display
    assert demo.demo_owner == user
    assert demo.demo_owner_rating == user.rating
    assert demo.demo_owner_display == user.display
    assert demo.demo_control == user
    assert demo.demo_control_display == user.display


def test_challenge_suggestion(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1550)

    svc = PlayService(db, socket, user)
    data = svc.execute('challenge_setup_suggestion', {'user_id': other.id})

    assert data['other_user_id'] == other.id
    assert data['other_display'] == other.display
    assert data['other_rating'] == other.rating
    assert data['handicap'] == 0
    assert data['owner_is_black'] is None
    assert data['komi'] == settings.DEFAULT_KOMI


def test_challenge_suggestion_handicap(db, socket):
    user = UserFactory(rating=1750)
    other = UserFactory(rating=1500)

    svc = PlayService(db, socket, user)
    data = svc.execute('challenge_setup_suggestion', {'user_id': other.id})

    assert data['other_user_id'] == other.id
    assert data['other_display'] == other.display
    assert data['other_rating'] == other.rating
    assert data['handicap'] == 2
    assert data['owner_is_black'] is False
    assert data['komi'] == settings.HANDICAP_KOMI


def test_challenge(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)

    svc = PlayService(db, socket, user)
    socket.subscribe('challenges/'+str(user.id))
    socket.subscribe('challenges/'+str(other.id))

    svc.execute('challenge', {
        'user_id': other.id,
        'size': 19,
        'handicap': 0,
        'komi': 7.5,
        'owner_is_black': True,
        'speed': 'live',
        'timing': 'fischer',
        'maintime': 10,
        'overtime': 20,
        'overtime_count': 1,
    })

    assert db.query(Challenge).count() == 1
    challenge = db.query(Challenge).first()

    assert challenge.owner == user
    assert challenge.challengee == other
    assert challenge.board_size == 19
    assert challenge.handicap == 0
    assert challenge.owner_is_black
    assert ((challenge.expire_at - datetime.utcnow()) -
            settings.CHALLENGE_EXPIRATION).total_seconds() < 60
    assert not challenge.is_correspondence
    assert challenge.timing_system == 'fischer'
    assert challenge.maintime == timedelta(minutes=10)
    assert challenge.overtime == timedelta(seconds=20)

    assert len(socket.sent_messages) == 2
    assert socket.sent_messages[0]['method'] == 'challenges'
    assert socket.sent_messages[1]['method'] == 'challenges'


def test_challenge_correspondence(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)

    svc = PlayService(db, socket, user)

    svc.execute('challenge', {
        'user_id': other.id,
        'size': 19,
        'handicap': 0,
        'komi': 7.5,
        'owner_is_black': True,
        'speed': 'correspondence',
        'timing': 'fischer',
        'maintime': 24*5,
        'overtime': 24*3,
        'overtime_count': 1,
    })

    assert db.query(Challenge).count() == 1
    challenge = db.query(Challenge).first()

    assert ((challenge.expire_at - datetime.utcnow()) -
            settings.CORRESPONDENCE_CHALLENGE_EXPIRATION).total_seconds() < 60
    assert challenge.is_correspondence
    assert challenge.timing_system == 'fischer'
    assert challenge.maintime == timedelta(hours=24*5)
    assert challenge.overtime == timedelta(hours=24*3)


def test_challenge_private(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)

    svc = PlayService(db, socket, user)

    svc.execute('challenge', {
        'user_id': other.id,
        'size': 19,
        'handicap': 0,
        'komi': 7.5,
        'owner_is_black': True,
        'speed': 'correspondence',
        'timing': 'fischer',
        'maintime': 24*5,
        'overtime': 24*3,
        'overtime_count': 1,
        'private': True
    })

    assert db.query(Challenge).count() == 1
    challenge = db.query(Challenge).first()

    assert challenge.is_private


def test_accept_private_challenge(db, socket):
    user = UserFactory(rating=1500)
    challenge = ChallengeFactory(is_private=True, owner=user)

    svc = PlayService(db, socket, challenge.challengee)
    svc.execute('accept_challenge', {'challenge_id': challenge.id})

    game = db.query(Game).first()

    assert game.is_private


def test_challenge_private_ranked(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)

    svc = PlayService(db, socket, user)

    with pytest.raises(ChallengePrivateCannotBeRankedError):
        svc.execute('challenge', {
            'user_id': other.id,
            'size': 19,
            'handicap': 0,
            'komi': 7.5,
            'owner_is_black': None,
            'speed': 'correspondence',
            'timing': 'fischer',
            'maintime': 24*5,
            'overtime': 24*3,
            'overtime_count': 1,
            'private': True,
            'ranked': True,
        })

    assert db.query(Challenge).count() == 0


def test_challenge_ranked(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)

    svc = PlayService(db, socket, user)

    svc.execute('challenge', {
        'user_id': other.id,
        'size': 19,
        'handicap': 1,
        'komi': 0.5,
        'owner_is_black': True,
        'speed': 'correspondence',
        'timing': 'fischer',
        'maintime': 24*5,
        'overtime': 24*3,
        'overtime_count': 1,
        'ranked': True,
    })

    assert db.query(Challenge).count() == 1

    challenge = db.query(Challenge).first()
    assert challenge.is_ranked
    assert challenge.board_size == 19
    assert challenge.handicap == 0
    assert challenge.komi == settings.DEFAULT_KOMI
    assert challenge.owner_is_black is not None


def test_challenge_ranked_board_size(db, socket):
    user = UserFactory(rating=1500)
    other = UserFactory(rating=1500)

    svc = PlayService(db, socket, user)

    with pytest.raises(InvalidBoardSizeError):
        svc.execute('challenge', {
            'user_id': other.id,
            'size': 13,
            'handicap': 0,
            'komi': 7.5,
            'owner_is_black': None,
            'speed': 'correspondence',
            'timing': 'fischer',
            'maintime': 24*5,
            'overtime': 24*3,
            'overtime_count': 1,
            'ranked': True,
        })

    assert db.query(Challenge).count() == 0


def test_accept_ranked_challenge(db, socket):
    user = UserFactory(rating=1500)
    challenge = ChallengeFactory(is_ranked=True, owner=user)

    svc = PlayService(db, socket, challenge.challengee)
    svc.execute('accept_challenge', {'challenge_id': challenge.id})

    game = db.query(Game).first()

    assert game.is_ranked


def test_challenge_again_replaces(db, socket):
    challenge = ChallengeFactory()
    other = ChallengeFactory(owner=challenge.owner, challengee=UserFactory())

    svc = PlayService(db, socket, challenge.owner)
    svc.execute('challenge', {
        'user_id': challenge.challengee_id,
        'size': 19,
        'handicap': 0,
        'komi': 7.5,
        'owner_is_black': True,
        'speed': 'live',
        'timing': 'fischer',
        'maintime': 10,
        'overtime': 20,
        'overtime_count': 1,
        'private': False
    })

    assert db.query(Challenge).count() == 2
    assert db.query(Challenge).first() == other


def test_decline_challenge(db, socket):
    challenge = ChallengeFactory()
    svc = PlayService(db, socket, challenge.challengee)
    socket.subscribe('challenges/'+str(challenge.owner_id))
    socket.subscribe('challenges/'+str(challenge.challengee_id))

    svc.execute('decline_challenge', {'challenge_id': challenge.id})

    assert db.query(Challenge).count() == 0
    assert len(socket.sent_messages) == 2
    assert socket.sent_messages[0]['method'] == 'challenges'
    assert socket.sent_messages[1]['method'] == 'challenges'


def test_cancel_challenge(db, socket):
    challenge = ChallengeFactory()
    svc = PlayService(db, socket, challenge.owner)
    socket.subscribe('challenges/'+str(challenge.owner_id))
    socket.subscribe('challenges/'+str(challenge.challengee_id))

    svc.execute('cancel_challenge', {'challenge_id': challenge.id})

    assert db.query(Challenge).count() == 0
    assert len(socket.sent_messages) == 2
    assert socket.sent_messages[0]['method'] == 'challenges'
    assert socket.sent_messages[1]['method'] == 'challenges'


def test_accept_challenge(db, socket):
    challenge = ChallengeFactory()
    svc = PlayService(db, socket, challenge.challengee)
    socket.subscribe('game_started')
    socket.subscribe('challenges/'+str(challenge.owner_id))
    socket.subscribe('challenges/'+str(challenge.challengee_id))

    svc.execute('accept_challenge', {'challenge_id': challenge.id})

    assert db.query(Challenge).count() == 0
    assert len(socket.sent_messages) == 3
    assert socket.sent_messages[0]['method'] == 'game_started'
    assert socket.sent_messages[1]['method'] == 'challenges'
    assert socket.sent_messages[2]['method'] == 'challenges'


def test_accept_expired_challenge(db, socket):
    challenge = ChallengeFactory(
        expire_at=datetime.utcnow() - timedelta(seconds=1))
    svc = PlayService(db, socket, challenge.challengee)

    with pytest.raises(ChallengeExpiredError):
        svc.execute('accept_challenge', {'challenge_id': challenge.id})


def test_accept_challenge_correspondence(db, socket, mails):
    challenge = ChallengeFactory(
        is_correspondence=True, owner__is_online=False, challengee__is_online=False)

    svc = PlayService(db, socket, challenge.challengee)
    svc.execute('accept_challenge', {'challenge_id': challenge.id})

    game = db.query(Game).first()
    assert game.is_correspondence
    assert game.timing.capped

    assert len(mails) == 2
    assert mails[0]['template'] == 'correspondence/challenge_started.txt'
    assert mails[1]['template'] == 'correspondence/challenge_started.txt'
    assert {mails[0]['to'], mails[1]['to']} == {
        challenge.owner.email, challenge.challengee.email}


def test_cleanup_challenges(db, socket):
    ChallengeFactory()
    ChallengeFactory(expire_at=datetime.utcnow() - timedelta(seconds=1))
    svc = PlayService(db, socket)
    svc.cleanup_challenges()

    assert db.query(Challenge).count() == 1


def test_cleanup_automatches(db, socket):
    u1 = UserFactory(is_online=True)
    AutomatchFactory(user=u1, preset='correspondence')

    u2 = UserFactory(is_online=False, last_activity_at=datetime.utcnow(
    ) - settings.AUTOMATCH_EXPIRE_CORRESPONDENCE)
    AutomatchFactory(user=u2, preset='correspondence')

    u3 = UserFactory(is_online=False, last_activity_at=datetime.utcnow() - settings.AUTOMATCH_EXPIRE_CORRESPONDENCE +
                     timedelta(minutes=1))
    AutomatchFactory(user=u3, preset='correspondence')

    svc = PlayService(db, socket)
    svc.cleanup_automatches()

    matches = db.query(Automatch).all()
    assert len(matches) == 2
    assert {matches[0].user, matches[1].user} == {u1, u3}
