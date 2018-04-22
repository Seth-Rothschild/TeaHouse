from weiqi import settings
from weiqi.models import User, Game
from weiqi.paginator import paginate
from weiqi.services import BaseService


class SearchService(BaseService):
    __service_name__ = 'search'

    @BaseService.register
    def all(self, query):
        return {
            'users': self.users(query),
            'games': self.games(query)
        }

    @BaseService.register
    def users(self, query, page=1):
        users = self.db.query(User).filter(
            User.display.ilike('%'+query+'%')).order_by(User.display)
        page_info = paginate(users, settings.SEARCH_RESULTS_PER_PAGE, page)

        results = [{
            'id': u.id,
            'created_at': u.created_at.isoformat(),
            'display': u.display,
                       'rating': u.rating,
                       'is_online': u.is_online,
                       'last_activity_at': u.last_activity_at.isoformat() if u.last_activity_at else None,
        } for u in page_info['query']]

        return {
            'page': page_info['page'],
            'total_pages': page_info['total_pages'],
            'total_results': page_info['total_results'],
            'results': results,
        }

    @BaseService.register
    def games(self, query, page=1):
        games = (self.db.query(Game)
                 .filter((Game.black_display.ilike('%'+query+'%')) |
                         (Game.white_display.ilike('%'+query+'%')) |
                         (Game.demo_owner_display.ilike('%'+query+'%')) |
                         (Game.title.ilike('%'+query+'%')))
                 .order_by(Game.created_at.desc()))

        page_info = paginate(games, settings.SEARCH_RESULTS_PER_PAGE, page)
        results = [g.to_frontend() for g in page_info['query']]

        return {
            'page': page_info['page'],
            'total_pages': page_info['total_pages'],
            'total_results': page_info['total_results'],
            'results': results,
        }
