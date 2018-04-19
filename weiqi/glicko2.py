"""
Implementation of the Glicko2 rating system.
See: http://www.glicko.net/glicko/glicko2.pdf

The calculation process is broken into 8 steps.

Step 1:
Determine initial values.

Step 2:
Convert to Glicko2 Scale from the Glicko1 scale.

Step 3:
Compute (v), the estimated variance based only on game outcomes.

Step 4:
Compute the quantity Delta, the estimated improvement.

Step 5:
Determine the new value, sigma', of the volatility, in an iterative process.

Step 6:
Update the rating deviation to the new pre-rating period value, φ_z

Step 7:
Update the rating and RD to the new values, μ′ and φ′:

Step 8:
Convert back to the Glicko1 scale.
"""

import math
from json import JSONEncoder

WIN = 1.0
DRAW = 0.5
LOSS = 0.0

# Constrains the volatility. Typically set between 0.3 and 1.2.
# Often refered to as the 'system' constant.
DEFAULT_TAU = 0.3

DEFAULT_RATING = 1500.0
DEFAULT_DEVIATION = 350.0
DEFAULT_VOLATILITY = 0.06

GLICKO2_SCALE = 173.7178


class Rating:
    def __init__(self, rating, deviation, volatility):
        self.rating = rating
        self.deviation = deviation
        self.volatility = volatility

    def to_glicko2(self):
        return Rating((self.rating-DEFAULT_RATING)/GLICKO2_SCALE,
                      self.deviation/GLICKO2_SCALE,
                      self.volatility)

    def almost_equals(self, other, epsilon=0.0001):
        return (abs(self.rating-other.rating) < epsilon and
                abs(self.deviation-other.deviation) < epsilon and
                abs(self.volatility-other.volatility) < epsilon)

    def clone(self):
        return Rating(self.rating, self.deviation, self.volatility)


class RatingEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def default_rating():
    return Rating(DEFAULT_RATING, DEFAULT_DEVIATION, DEFAULT_VOLATILITY)


def rating_from_glicko2(rating, deviation, volatility):
    return Rating(rating*GLICKO2_SCALE+DEFAULT_RATING,
                  deviation*GLICKO2_SCALE,
                  volatility)


class Result(Rating):
    def __init__(self, result, rating, deviation, volatility):
        super().__init__(rating, deviation, volatility)
        self.result = result


class Player(Rating):
    def __init__(self, rating, deviation=DEFAULT_DEVIATION, volatility=DEFAULT_VOLATILITY):
        super().__init__(rating, deviation, volatility)
        self.results = []

    def add_result(self, result):
        self.results.append(result)

    def update_rating(self):
        """Recalculates the player rating and clears all results."""
        p2 = self.to_glicko2()

        if not self.results:
            # For inactive players only step 6 of the paper applies.
            new_dev = math.sqrt((p2.deviation*p2.deviation) +
                                (p2.volatility*p2.volatility))
            rating = rating_from_glicko2(p2.rating, new_dev, p2.volatility)
        else:
            gees = []
            ees = []
            res = []
            for r in self.results:
                opponent = r.to_glicko2()
                gees.append(calc_g(opponent.deviation))
                ees.append(
                    calc_e(p2.rating, opponent.rating, opponent.deviation))
                res.append(r.result)

            est_var = estimate_variance(gees, ees)
            est_imp_part = estimate_improvement_partial(gees, ees, res)
            est_imp = est_var * est_imp_part
            new_vol = new_volatility(p2.volatility, est_var, est_imp)
            new_dev = new_deviation(p2.deviation, new_vol, est_var)
            new_rat = new_rating(p2.rating, new_dev, est_imp_part)

            rating = rating_from_glicko2(new_rat, new_dev, new_vol)

        # Upper bound by the default deviation
        rating.deviation = min(rating.deviation, DEFAULT_DEVIATION)

        self.rating = rating.rating
        self.deviation = rating.deviation
        self.volatility = rating.volatility

        self.results.clear()

    def clone(self):
        player = Player(self.rating, self.deviation, self.volatility)
        player.results = list(self.results)
        return player


def player_from_dict(data):
    if not data:
        return None

    player = Player(data['rating'], data['deviation'], data['volatility'])
    player.results = [Result(
        r['result'], r['rating'], r['deviation'], r['volatility']) for r in data['results']]

    return player


def calc_e(rating, rating_opp, deviation_opp):
    """The 'E' function."""
    return 1.0 / (1.0 + math.exp(-calc_g(deviation_opp)*(rating-rating_opp)))


def calc_g(deviation):
    """The 'g' function."""
    return 1.0 / (math.sqrt(1.0 + 3.0*deviation*deviation/(math.pi*math.pi)))


def estimate_variance(gees, ees):
    """Computes the quantity v. This is the estimated variance of the player's rating
    based only on game outcomes.
    """
    variance = 0.0

    for g, e in zip(gees, ees):
        variance += g*g*e*(1.0-e)

    return 1.0 / variance


def estimate_improvement_partial(gees, ees, results):
    """Computes the quantity 'delta', the estimated improvement in rating by comparing the pre-period rating
    to the performance rating based only on game outcomes.

     Note: This function is like the 'delta' in the algorithm, but here we don't multiply by the estimated variance.
    """
    delta = 0.0

    for g, e, r in zip(gees, ees, results):
        delta += g * (r - e)

    return delta


def new_volatility(old_vol, est_var, est_imp):
    """Calcultes the new volatility."""
    def sq(x): return x*x

    epsilon = 0.000001
    a = math.log(sq(old_vol))
    delta_sq = sq(est_imp)
    phi_sq = sq(old_vol)
    tau_sq = sq(DEFAULT_TAU)
    max_iter = 100

    def f(x):
        eX = math.exp(x)
        return eX*(delta_sq - phi_sq - est_var - eX) / (2 * sq(phi_sq + est_var + eX)) - (x - a) / tau_sq

    A = a
    B = 0.0

    if delta_sq > (phi_sq + est_var):
        B = math.log(delta_sq - phi_sq - est_var)
    else:
        val = -1.0
        k = 1

        while val < 0:
            val = f(a - k*DEFAULT_TAU)
            k += 1

        B = a - k*DEFAULT_TAU

    # Now: A < ln(sigma'^2) < B

    fA = f(A)
    fB = f(B)
    iter = 0

    while abs(B-A) > epsilon and iter < max_iter:
        C = A + (A-B)*fA/(fB-fA)
        fC = f(C)

        if fC*fB < 0:
            A = B
            fA = fB
        else:
            fA = fA / 2

        B = C
        fB = fC
        iter += 1

    if iter == max_iter-1:
        pass
        # logger.debug("Too many iterations for volatility calculation")

    new_vol = math.exp(A / 2)

    return new_vol


def new_deviation(old_dev, new_vol, est_var):
    """Calculates the new deviation. This is just the L2-norm of the deviation and the volatility."""
    phip = math.sqrt(old_dev*old_dev + new_vol*new_vol)
    return 1.0 / math.sqrt(1.0/(phip*phip)+1.0/est_var)


def new_rating(old_rating, new_dev, est_impr):
    """Calculates the new rating."""
    return old_rating + new_dev*new_dev*est_impr
