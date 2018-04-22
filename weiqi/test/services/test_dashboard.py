from datetime import datetime, timedelta

from weiqi.services import DashboardService
from weiqi.test.factories import GameFactory, DemoGameFactory


def test_popular_games_age(db):
    demo = DemoGameFactory(room__users_max=10)
    game = GameFactory(room__users_max=11)
    GameFactory(created_at=datetime.utcnow() -
                timedelta(days=30), room__users_max=12)

    svc = DashboardService(db)
    popular = svc.execute('popular_games')

    assert len(popular) == 2
    assert popular[0]['id'] == game.id
    assert popular[1]['id'] == demo.id


def test_popular_games_not_private(db):
    demo = DemoGameFactory(room__users_max=10)
    game = GameFactory(room__users_max=11)
    GameFactory(is_private=True, room__users_max=12)

    svc = DashboardService(db)
    popular = svc.execute('popular_games')

    assert len(popular) == 2
    assert popular[0]['id'] == game.id
    assert popular[1]['id'] == demo.id
