from datetime import datetime

from sqlalchemy.orm import undefer
from weiqi import settings
from weiqi.glicko2 import Result, WIN, LOSS
from weiqi.models import User
from weiqi.rating import RATING_PER_RANK, RATING_START
from weiqi.services import BaseService


class RatingService(BaseService):
    """Service to handle rating updates fors users.

    Game results are bundled into rating periods as recommended in the glicko2 paper.
    The results are stored for each user and kept until the end of the rating period, after which they are reset.

    Rating periods are simulated for each user individually in order to avoid having to update all users at once.
    In addition, to provide real-time rating updates, after each game the users rating will be recalculated based on
    the data of the current period.
    Note that this is done on a clone to preserve the results and only the actual rating is copied back.

    Handicap is handled by altering the opponents rating before calculation, adding or removing rating points
    relative to the handicap.
    """

    def update_ratings(self, game):
        """Updates the ratings for both players of a game."""
        if not game.is_ranked or game.stage != 'finished':
            return

        if game.black_user == game.white_user:
            return

        if game.result == 'aborted':
            return

        winner, loser = game.winner_loser

        # `winner_hc` is the handicap relative to whether the winning player was black or white.
        winner_hc = game.board.handicap
        if winner != game.black_user:
            winner_hc = -winner_hc

        winner = self._user_for_update(winner.id)
        loser = self._user_for_update(loser.id)

        self._apply_rating_periods(winner)
        self._apply_rating_periods(loser)

        winner.rating_data.add_result(
            self._rating_to_result(loser.rating_data, -winner_hc, WIN))
        winner.apply_rating_data_change()

        loser.rating_data.add_result(self._rating_to_result(
            winner.rating_data, winner_hc, LOSS))
        loser.apply_rating_data_change()

        # Recalculate rating data of this period to get the current rating, but keep all results intact as
        # the rating period has not ended yet.

        data = winner.rating_data.clone()
        data.update_rating()
        winner.rating = max(RATING_START, data.rating)

        data = loser.rating_data.clone()
        data.update_rating()
        loser.rating = max(RATING_START, data.rating)

    def _user_for_update(self, user_id):
        return self.db.query(User).options(undefer('rating_data')).with_for_update().get(user_id)

    def _apply_rating_periods(self, user):
        """Checks when the users rating was last updated and calculates rating periods if necessary."""
        if not user.last_rating_update_at:
            periods = 1
        else:
            total = (datetime.utcnow() -
                     user.last_rating_update_at).total_seconds()
            periods = int(
                total / settings.RATING_PERIOD_DURATION.total_seconds())

        if periods > 0:
            for _ in range(periods):
                user.rating_data.update_rating()

            user.apply_rating_data_change()
            user.last_rating_update_at = datetime.utcnow()

    def _rating_to_result(self, rating, increase_by_hc, result):
        return Result(result,
                      rating.rating + increase_by_hc*RATING_PER_RANK,
                      rating.deviation,
                      rating.volatility)
