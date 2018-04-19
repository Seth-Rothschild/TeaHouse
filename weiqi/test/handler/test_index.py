from weiqi.sgf import game_to_sgf
from weiqi.test.base import BaseAsyncHTTPTestCase
from weiqi.test.factories import GameFactory


class TestSgf(BaseAsyncHTTPTestCase):
    def test_sgf(self):
        game = GameFactory()

        res = self.fetch('/api/games/%s/sgf' % game.id)
        self.assertEqual(res.code, 200)

        assert res.body.decode() == game_to_sgf(game)
