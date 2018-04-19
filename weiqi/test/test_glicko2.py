"""Glicko2 tests based on the example calculation in the paper:
http://www.glicko.net/glicko/glicko2.pdf
"""

import json
import math

import pytest
from weiqi.glicko2 import (Player, Rating, Result, rating_from_glicko2, DEFAULT_VOLATILITY, WIN, LOSS, calc_g, calc_e,
                           estimate_variance, estimate_improvement_partial, new_volatility, new_deviation,
                           new_rating, player_from_dict, RatingEncoder)


@pytest.fixture
def player():
    return Player(1500, 200, DEFAULT_VOLATILITY)


@pytest.fixture
def opponents():
    return [
        Player(1400, 30, DEFAULT_VOLATILITY),
        Player(1550, 100, DEFAULT_VOLATILITY),
        Player(1700, 300, DEFAULT_VOLATILITY),
    ]


@pytest.fixture
def results():
    return [WIN, LOSS, LOSS]


def test_rescale(opponents):
    for opp in opponents:
        glicko2 = opp.to_glicko2()
        rescaled = rating_from_glicko2(
            glicko2.rating, glicko2.deviation, glicko2.volatility)

        assert opp.almost_equals(rescaled)


def test_player_to_glicko2(player):
    glicko2 = player.to_glicko2()
    expected = Rating(0, 1.1513, DEFAULT_VOLATILITY)

    assert glicko2.almost_equals(expected)


def test_opponent_to_glicko2(opponents):
    expected = [
        Rating(-0.5756, 0.1727, DEFAULT_VOLATILITY),
        Rating(0.2878, 0.5756, DEFAULT_VOLATILITY),
        Rating(1.1513, 1.7269, DEFAULT_VOLATILITY),
    ]

    for opp, exp in zip(opponents, expected):
        glicko2 = opp.to_glicko2()
        assert glicko2.almost_equals(exp)


def test_gees_ees(player, opponents):
    exp_gee = [0.9955, 0.9531, 0.7242]
    exp_ee = [0.639, 0.432, 0.303]
    p2 = player.to_glicko2()

    for g, e, opp in zip(exp_gee, exp_ee, opponents):
        o2 = opp.to_glicko2()
        gee = calc_g(o2.deviation)
        ee = calc_e(p2.rating, o2.rating, o2.deviation)

        assert math.isclose(gee, g, abs_tol=0.0001)
        assert math.isclose(ee, e, abs_tol=0.001)


def test_algo(player, opponents, results):
    p2 = player.to_glicko2()
    opps = [o.to_glicko2() for o in opponents]
    gees = [calc_g(o.deviation) for o in opps]
    ees = [calc_e(p2.rating, o.rating, o.deviation) for o in opps]

    est_var = estimate_variance(gees, ees)
    assert math.isclose(est_var, 1.7785, abs_tol=0.001)

    est_imp_part = estimate_improvement_partial(gees, ees, results)
    est_imp = est_var * est_imp_part
    assert math.isclose(est_imp, -0.4834, abs_tol=0.001)

    new_vol = new_volatility(p2.volatility, est_var, est_imp)
    assert math.isclose(new_vol, 0.05999, abs_tol=0.00001)

    new_dev = new_deviation(p2.deviation, new_vol, est_var)
    assert math.isclose(new_dev, 0.8722, abs_tol=0.0001)

    new_rat = new_rating(p2.rating, new_dev, est_imp_part)
    assert math.isclose(new_rat, -0.2069, abs_tol=0.0001)

    new_player = rating_from_glicko2(new_rat, new_dev, new_vol)
    assert math.isclose(new_player.rating, 1464.06, abs_tol=0.01)
    assert math.isclose(new_player.deviation, 151.52, abs_tol=0.01)


def test_update_rating(player, opponents, results):
    for res, opp in zip(results, opponents):
        player.add_result(
            Result(res, opp.rating, opp.deviation, opp.volatility))

    player.update_rating()

    assert player.results == []
    assert math.isclose(player.rating, 1464.06, abs_tol=0.01)
    assert math.isclose(player.deviation, 151.52, abs_tol=0.01)
    assert math.isclose(player.volatility, 0.05999, abs_tol=0.00001)


def test_update_rating_inactive(player):
    rating = player.rating
    deviation = player.deviation
    volatility = player.volatility

    player.update_rating()

    assert math.isclose(player.rating, rating)
    assert player.deviation > deviation
    assert math.isclose(player.volatility, volatility)


def test_player_from_dict(player):
    data = json.loads(json.dumps(player, cls=RatingEncoder))
    loaded = player_from_dict(data)
    assert player.almost_equals(loaded)
