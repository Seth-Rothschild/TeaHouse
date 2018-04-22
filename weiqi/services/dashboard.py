from datetime import datetime

from weiqi import settings
from weiqi.models import Game, Room, User
from weiqi.services import BaseService


class DashboardService(BaseService):
    __service_name__ = 'dashboard'

    @BaseService.register
    def popular_games(self):
        games = (self.db.query(Game)
                 .join(Room)
                 .filter(Game.created_at >= datetime.utcnow() - settings.DASHBOARD_POPULAR_GAMES_MAX_AGE)
                 .filter(Game.is_private.is_(False))
                 .order_by(Room.users_max.desc())
                 .limit(settings.DASHBOARD_POPULAR_GAMES))

        return [g.to_frontend() for g in games]

    @BaseService.register
    def stats(self):
        users = self.db.query(User).count()
        online = self.db.query(User).filter_by(is_online=True).count()
        games = self.db.query(Game).count()

        return {
            'users': users,
            'online': online,
            'games': games
        }
