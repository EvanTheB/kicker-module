import wrank.ladder.trueskill as ts


class FakePlayer(object):
    """pretend"""

    def __init__(self, mu, sigma):
        self.mu = mu
        self.sigma = sigma


def test_match_quality():
    res = [
        ts.match_quality([
            [FakePlayer(25.0, 8.33)],
            [FakePlayer(25.0, 8.33)],
        ]),
        ts.match_quality([
            [FakePlayer(25.0, 8.33), FakePlayer(25.0, 8.33)],
            [FakePlayer(25.0, 8.33)],
        ]),
        ts.match_quality([
            [FakePlayer(25.0, 8.33), FakePlayer(25.0, 8.33)],
            [FakePlayer(25.0, 8.33)],
            [FakePlayer(25.0, 8.33),
             FakePlayer(25.0, 8.33),
             FakePlayer(25.0, 8.33), ],
        ]),
    ]
    assert all(0 <= r <= 1 for r in res)
