from weiqi.models import Automatch
from weiqi.prepare_startup import prepare_startup
from weiqi.test.factories import AutomatchFactory


def test_automatch_correspondence(db):
    AutomatchFactory(preset='slow')
    AutomatchFactory(preset='correspondence')

    prepare_startup()

    assert db.query(Automatch).count() == 1
    assert db.query(Automatch).filter_by(preset='correspondence').count() == 1
