from datetime import datetime, timedelta


def update_timing_after_move(timing, was_blacks_turn):
    """Updates the players time after she played a move."""
    if not timing.has_started:
        return

    updater = {
        'fischer': _update_fischer,
        'byoyomi': _update_byoyomi,
    }.get(timing.system)

    if not updater:
        raise ValueError('unknown timing system: {}'.format(timing.system))

    if was_blacks_turn:
        timing.black_main, timing.black_overtime = updater(
            timing, timing.black_main, timing.black_overtime)
    else:
        timing.white_main, timing.white_overtime = updater(
            timing, timing.white_main, timing.white_overtime)

    total_other = timing.white_total if was_blacks_turn else timing.black_total
    timing.next_move_at = datetime.utcnow() + total_other


def update_timing(timing, is_blacks_turn):
    """Updates the current players time.

    Returns True if the player still has time left.
    """
    if timing.has_started:
        time_passed = datetime.utcnow() - timing.timing_updated_at

        if is_blacks_turn:
            if time_passed <= timing.black_main:
                timing.black_main -= time_passed
            else:
                timing.black_overtime -= (time_passed - timing.black_main)
                timing.black_main = timedelta()
        else:
            if time_passed <= timing.white_main:
                timing.white_main -= time_passed
            else:
                timing.white_overtime -= (time_passed - timing.white_main)
                timing.white_main = timedelta()

    total = timing.black_total if is_blacks_turn else timing.white_total

    if total.total_seconds() > 0:
        timing.next_move_at = datetime.utcnow() + total

    timing.timing_updated_at = datetime.utcnow()

    return total.total_seconds() > 0


def _update_fischer(timing, main, overtime):
    new_main = main + timing.overtime

    if timing.capped and new_main > timing.main_cap:
        new_main = timing.main_cap

    return new_main, overtime


def _update_byoyomi(timing, main, overtime):
    return main, overtime
