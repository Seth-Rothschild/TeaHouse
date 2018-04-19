from datetime import datetime

from weiqi import settings
from weiqi.glicko2 import WIN, LOSS, Player, Result
from weiqi.services import RatingService
from weiqi.test.factories import GameFactory


def test_update_ratings(db):
    game = GameFactory(stage='finished', result='W+R',
                       black_user__rating=1500, white_user__rating=1500)
    svc = RatingService(db)

    svc.update_ratings(game)

    assert len(game.black_user.rating_data.results) == 1
    assert game.black_user.rating_data.results[0].result == LOSS
    assert game.black_user.rating_data.results[0].almost_equals(
        game.white_user.rating_data)
    assert game.black_user.rating_data.rating == 1500
    assert game.black_user.rating < 1500

    assert len(game.white_user.rating_data.results) == 1
    assert game.white_user.rating_data.results[0].result == WIN
    assert game.white_user.rating_data.results[0].almost_equals(
        game.black_user.rating_data)
    assert game.white_user.rating_data.rating == 1500
    assert game.white_user.rating > 1500


def test_update_ratings_aborted(db):
    game = GameFactory(stage='finished', result='aborted',
                       black_user__rating=1500, white_user__rating=1500)
    svc = RatingService(db)

    svc.update_ratings(game)

    assert len(game.black_user.rating_data.results) == 0
    assert game.black_user.rating == 1500

    assert len(game.white_user.rating_data.results) == 0
    assert game.white_user.rating == 1500


def test_handicap_black_win(db):
    game_normal = GameFactory(
        stage='finished', result='B+R', black_user__rating=1500, white_user__rating=1500)
    game_hc = GameFactory(stage='finished', result='B+R',
                          black_user__rating=1500, white_user__rating=1700)
    game_hc.board.handicap = 2
    game_hc.apply_board_change()

    svc = RatingService(db)
    svc.update_ratings(game_normal)
    svc.update_ratings(game_hc)

    assert game_normal.black_user.rating == game_hc.black_user.rating


def test_handicap_black_loss(db):
    game_normal = GameFactory(
        stage='finished', result='W+R', black_user__rating=1500, white_user__rating=1500)
    game_hc = GameFactory(stage='finished', result='W+R',
                          black_user__rating=1500, white_user__rating=1700)
    game_hc.board.handicap = 2
    game_hc.apply_board_change()

    svc = RatingService(db)
    svc.update_ratings(game_normal)
    svc.update_ratings(game_hc)

    assert game_normal.black_user.rating == game_hc.black_user.rating


def test_handicap_white_win(db):
    game_normal = GameFactory(
        stage='finished', result='W+R', black_user__rating=1700, white_user__rating=1700)
    game_hc = GameFactory(stage='finished', result='W+R',
                          black_user__rating=1500, white_user__rating=1700)
    game_hc.board.handicap = 2
    game_hc.apply_board_change()

    svc = RatingService(db)
    svc.update_ratings(game_normal)
    svc.update_ratings(game_hc)

    assert game_normal.white_user.rating == game_hc.white_user.rating


def test_handicap_white_loss(db):
    game_normal = GameFactory(
        stage='finished', result='B+R', black_user__rating=1700, white_user__rating=1700)
    game_hc = GameFactory(stage='finished', result='B+R',
                          black_user__rating=1500, white_user__rating=1700)
    game_hc.board.handicap = 2
    game_hc.apply_board_change()

    svc = RatingService(db)
    svc.update_ratings(game_normal)
    svc.update_ratings(game_hc)

    assert game_normal.white_user.rating == game_hc.white_user.rating


def test_apply_rating_periods(db):
    p1 = Player(1450, 200)
    p2 = Player(1650, 100)
    missed_p1 = 20
    missed_p2 = 100

    for _ in range(missed_p1):
        p1.update_rating()

    for _ in range(missed_p2):
        p2.update_rating()

    p1.add_result(Result(WIN, p2.rating, p2.deviation, p2.volatility))
    p2.add_result(Result(LOSS, p1.rating, p1.deviation, p1.volatility))

    p1.update_rating()
    p2.update_rating()

    game = GameFactory(stage='finished', result='B+R',
                       black_user__rating=1450, white_user__rating=1650)
    game.black_user.rating_data.deviation = 200
    game.black_user.apply_rating_data_change()
    game.black_user.last_rating_update_at = datetime.utcnow(
    ) - settings.RATING_PERIOD_DURATION*missed_p1

    game.white_user.rating_data.deviation = 100
    game.white_user.apply_rating_data_change()
    game.white_user.last_rating_update_at = datetime.utcnow(
    ) - settings.RATING_PERIOD_DURATION*missed_p2

    svc = RatingService(db)
    svc.update_ratings(game)

    assert game.black_user.rating == p1.rating
    assert game.white_user.rating == p2.rating
