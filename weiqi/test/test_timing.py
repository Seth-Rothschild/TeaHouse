from datetime import datetime, timedelta

from weiqi.models import Timing
from weiqi.timing import update_timing, update_timing_after_move


def test_update_timing():
    tests = [
        # Player has 1min main and 30sec overtime.
        # Tests: time_passed, expected_main, expected_overtime
        [timedelta(seconds=20), timedelta(seconds=40), timedelta(seconds=30)],
        [timedelta(seconds=30), timedelta(seconds=30), timedelta(seconds=30)],
        [timedelta(seconds=60), timedelta(seconds=0), timedelta(seconds=30)],
        [timedelta(seconds=70), timedelta(seconds=0), timedelta(seconds=20)],
        [timedelta(seconds=80), timedelta(seconds=0), timedelta(seconds=10)],
        [timedelta(seconds=90), timedelta(seconds=0), timedelta(seconds=0)],
        [timedelta(seconds=100), timedelta(seconds=0), timedelta(seconds=-10)],
    ]

    for t in tests:
        timing = Timing(start_at=datetime.utcnow() - timedelta(seconds=1),
                        black_main=timedelta(minutes=1),
                        black_overtime=timedelta(seconds=30))
        timing.timing_updated_at = datetime.utcnow() - t[0]
        has_time = update_timing(timing, True)

        assert timing.timing_updated_at - datetime.utcnow() < timedelta(seconds=1)
        assert round(timing.black_main.total_seconds()
                     ) == round(t[1].total_seconds())
        assert round(timing.black_overtime.total_seconds()
                     ) == round(t[2].total_seconds())
        assert has_time == (timing.black_total.total_seconds() > 0)

        timing = Timing(start_at=datetime.utcnow() - timedelta(seconds=1),
                        white_main=timedelta(minutes=1),
                        white_overtime=timedelta(seconds=30))
        timing.timing_updated_at = datetime.utcnow() - t[0]
        has_time = update_timing(timing, False)

        assert timing.timing_updated_at - datetime.utcnow() < timedelta(seconds=1)
        assert round(timing.white_main.total_seconds()
                     ) == round(t[1].total_seconds())
        assert round(timing.white_overtime.total_seconds()
                     ) == round(t[2].total_seconds())
        assert has_time == (timing.white_total.total_seconds() > 0)


def test_start_delay():
    timing = Timing(start_at=datetime.utcnow() + timedelta(seconds=20),
                    black_main=timedelta(minutes=1),
                    black_overtime=timedelta(seconds=30))
    timing.timing_updated_at = datetime.utcnow() - timedelta(seconds=10)
    update_timing(timing, True)

    assert timing.black_main == timedelta(minutes=1)
    assert timing.black_overtime == timedelta(seconds=30)


def test_fischer():
    timing = Timing(system='fischer',
                    start_at=datetime.utcnow(),
                    timing_updated_at=datetime.utcnow(),
                    overtime=timedelta(seconds=20),
                    black_main=timedelta(minutes=2, seconds=30),
                    black_overtime=timedelta(),
                    white_main=timedelta(minutes=2),
                    white_overtime=timedelta())

    update_timing_after_move(timing, True)

    assert timing.black_main == timedelta(minutes=2, seconds=50)
    assert timing.black_overtime == timedelta()
    assert timing.white_main == timedelta(minutes=2)
    assert timing.white_overtime == timedelta()
    assert timing.next_move_at - \
        (datetime.utcnow() + timedelta(minutes=2)) < timedelta(seconds=1)

    update_timing_after_move(timing, False)

    assert timing.black_main == timedelta(minutes=2, seconds=50)
    assert timing.black_overtime == timedelta()
    assert timing.white_main == timedelta(minutes=2, seconds=20)
    assert timing.white_overtime == timedelta()
    assert timing.next_move_at - \
        (datetime.utcnow() + timedelta(minutes=2, seconds=50)) < timedelta(seconds=1)


def test_fischer_cap():
    timing = Timing(system='fischer',
                    start_at=datetime.utcnow(),
                    timing_updated_at=datetime.utcnow(),
                    capped=True,
                    main=timedelta(minutes=1, seconds=30),
                    overtime=timedelta(seconds=20),
                    black_main=timedelta(minutes=2, seconds=30),
                    black_overtime=timedelta(),
                    white_main=timedelta(minutes=2),
                    white_overtime=timedelta())

    update_timing_after_move(timing, True)
    assert timing.black_main == timedelta(minutes=2, seconds=50)

    update_timing_after_move(timing, True)
    assert timing.black_main == timedelta(minutes=3)

    update_timing_after_move(timing, True)
    assert timing.black_main == timedelta(minutes=3)
