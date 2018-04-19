from weiqi.rating import rating_to_rank, min_rating, max_rating, rank_diff, RATING_PER_RANK, rating_range


def test_ranks():
    tests = {
        3100: "9d",
        3000: "9d",
        3001: "9d",

        2900: "9d",
        2800: "8d",
        2700: "7d",
        2600: "6d",
        2500: "5d",

        2499: "4d",
        2450: "4d",
        2401: "4d",

        2400: "4d",
        2300: "3d",
        2200: "2d",
        2100: "1d",

        2099: "1k",
        2050: "1k",
        2001: "1k",

        2000: "1k",
        1900: "2k",
        1800: "3k",
        1700: "4k",
        1600: "5k",
        1500: "6k",
        1400: "7k",
        1300: "8k",
        1200: "9k",
        1100: "10k",

        1099: "11k",
        1050: "11k",
        1001: "11k",

        1000: "11k",
        900:  "12k",
        800:  "13k",
        700:  "14k",
        600:  "15k",
        500:  "16k",
        400:  "17k",
        300:  "18k",
        200:  "19k",
        100:  "20k",

        -1:   "20k",
        -100: "20k",
        -200: "20k",
    }

    for rating, rank in tests.items():
        assert rating_to_rank(rating) == rank


def test_rank_diff():
    tests = [
        [-200, 100, 0],
        [-100, 100, 0],
        [0, 100, 0],
        [50, 100, 0],
        [90, 100, 0],
        [0, 0, 0],
        [0, 100, 0],
        [-200, 200, 1],
        [110, 200, 1],
        [150, 200, 1],
        [190, 200, 1],
        [200, 200, 0],
        [650, 350, 3],

        [min_rating("2k"), min_rating("3d"), 4],

        [2800, 3100, 1],
    ]

    for t in tests:
        assert rank_diff(t[0], t[1]) == t[2]


def test_min_rating():
    def test_in_order(start, ranks):
        for i, r in enumerate(ranks):
            assert min_rating(r) == start + i*RATING_PER_RANK

    test_in_order(100, ["20k", "19k", "18k", "17k", "16k", "15k", "14k", "13k", "12k", "11k",
                        "10k", "9k", "8k", "7k", "6k", "5k", "4k", "3k", "2k", "1k"])

    test_in_order(2100, ["1d", "2d", "3d", "4d", "5d", "6d", "7d", "8d", "9d"])

    assert min_rating("21k") == 100
    assert min_rating("22k") == 100

    assert min_rating("10d") == 2900
    assert min_rating("11d") == 2900


def test_rating_range():
    tests = [
        [min_rating('5k'), 0, min_rating('5k'), max_rating('5k')],
        [min_rating('1d'), 2, min_rating('2k'), max_rating('3d')],

        [100, 0, 100, 199],
        [200, 2, -9999, 499],
        [2900, 3, 2600, 9999]
    ]

    for t in tests:
        assert rating_range(t[0], t[1]) == (t[2], t[3])
