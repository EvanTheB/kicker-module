import wrank.ladder.trueskill as ts

import random

import pytest


class FakePlayer(object):
    """pretend"""

    def __init__(self, mu=None, sigma=None):
        self.mu = mu or random.random() * 50.0
        self.sigma = sigma or random.random() * 8.33

        self.mu_orig = self.mu
        self.sigma_orig = self.sigma


def test_match_quality():
    res = [
        ts.match_quality([
            [FakePlayer()],
            [FakePlayer()],
        ]),
        ts.match_quality([
            [FakePlayer(), FakePlayer()],
            [FakePlayer()],
        ]),
        ts.match_quality([
            [FakePlayer(), FakePlayer()],
            [FakePlayer()],
            [FakePlayer(),
             FakePlayer(),
             FakePlayer(), ],
        ]),
    ]
    assert all(0 <= r <= 1 for r in res)


def test_chances():
    res = [
        ts.chances(
            [FakePlayer(), FakePlayer(), ],
            [FakePlayer(), FakePlayer(), ]
        ),
        ts.chances(
            [FakePlayer(), ],
            [FakePlayer(), FakePlayer(), FakePlayer(), ]
        )
    ]
    assert all(
        0 <= a <= 1 and
        0 <= b <= 1 and
        0 <= c <= 1 and
        abs(1.0 - a - b - c) < 1E-6
        for a, b, c in res
    )


@pytest.mark.parametrize("teams",
                         [
                             [
                                 [FakePlayer(), FakePlayer()],
                                 [FakePlayer(), FakePlayer()],
                             ],
                             [
                                 [FakePlayer(), ],
                                 [FakePlayer(), FakePlayer()],
                             ],
                             [
                                 [FakePlayer(), FakePlayer(), FakePlayer()],
                                 [FakePlayer(), ],
                             ],
                         ]
                         )
@pytest.mark.parametrize("was_win", [True, False])
def test_trueskill_update(teams, was_win):
    ts.calculate_nvn(
        teams[0],
        teams[1],
        was_win
    )
    assert all(
        p.mu != p.mu_orig and
        p.sigma != p.sigma_orig
        for p in teams[0] + teams[1]
    )
