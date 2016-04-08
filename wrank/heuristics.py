from wrank import backend
from wrank.ladder import ladders

import time
import itertools


class Heuristic(object):

    """
    interface for heuristic
    rate returns 0->1, 1 is good.
    """

    def rate(self, team_a, team_b):
        raise NotImplementedError()

    def rate_all(self, games):
        return [(self.rate(g[0], g[1]), (g[0], g[1])) for g in games]


class DrawChanceHeuristic(Heuristic):

    """microsoft style"""

    def __init__(self, ladder):
        self.ladder = ladder

    def rate(self, team_a, team_b):
        return self.ladder.quality(team_a, team_b)


class LadderDisruptionHeuristic(Heuristic):

    """andy style"""

    def __init__(self, ladder, players, games, function):
        self.ladder = ladder
        self.players = players
        self.games = games
        self.function = function

    def _get_dist(self, ladder_data):
        # This counts a swap as '2'
        dist = 0.
        for row in ladder_data[1:]:
            dist += abs(float(row[2]))
        return dist

    def rate(self, team_a, team_b):
        result_prob = self.ladder.chances(team_a, team_b)
        match_worth = 0.
        for prob, outcome in zip(result_prob, ['beat', 'draw', 'lost']):
            game = backend.LadderGame(
                team_a + (outcome,) + team_b,
                self.players, 0)

            data = self.ladder.process(self.players,
                                       self.games + [game])
            match_worth += prob * self._get_dist(data)
        return self.function(match_worth)


class TrueskillClumpingHeuristic(Heuristic):

    """Prefer similar skills"""

    def __init__(self, data, function):
        self.mus = {l[1]: float(l[4]) for l in data[1:]}
        self.function = function

    def rate(self, team_a, team_b):
        skills = [self.mus[n] for n in team_a + team_b]
        mean = sum(skills) / len(team_a + team_b)
        return self.function(sum([abs(s - mean) for s in skills]))


class SigmaReductionHeuristic(Heuristic):

    """Try to reduce sigmas"""

    def __init__(self, ladder, players, games, function):
        self.ladder = ladder
        self.players = players
        self.games = games
        self.function = function

        self.sigmas = {}
        data = self.ladder.process(self.players, self.games)
        for row in data[1:]:
            self.sigmas[row[1]] = float(row[5])

    def _get_dist(self, ladder_data):
        dist = 0.
        for row in ladder_data[1:]:
            dist += self.sigmas[row[1]] - float(row[5])
        return dist

    def rate(self, team_a, team_b):
        result_prob = self.ladder.chances(team_a, team_b)
        match_worth = 0.
        for prob, outcome in zip(result_prob, ['beat', 'draw', 'lost']):
            game = backend.LadderGame(
                team_a + (outcome,) + team_b,
                self.players, 0)

            data = self.ladder.process(self.players,
                                       self.games + [game])
            match_worth += prob * self._get_dist(data)
        return self.function(match_worth)


class TimeSinceLastPlayedHeuristic(Heuristic):

    """Prefer not recent players"""

    def __init__(self, players, games, function):
        self.times = {p.name: p.create_time for p in players.values()}
        for g in games:
            for p in itertools.chain.from_iterable(g.teams):
                self.times[p] = g.create_time
        self.function = function

    def rate(self, team_a, team_b):
        return self.function(min(self.times[p] for p in team_a + team_b))


class UnplayedMatchupsHeuristic(Heuristic):

    """Nick style"""

    def __init__(self, players, games, function):
        self.function = function
        self.played_with = {p: {opp: 0 for opp in players} for p in players}
        self.played_vs = {p: {opp: 0 for opp in players} for p in players}
        for g in games:
            for t1, t2 in itertools.combinations(g.teams, 2):
                for p1 in t1:
                    for p2 in t2:
                        self.played_vs[p1][p2] += 1
                        self.played_vs[p2][p1] += 1
            for t in g.teams:
                for p1, p2 in itertools.combinations(t, 2):
                    self.played_with[p1][p2] += 1
                    self.played_with[p2][p1] += 1

    def rate(self, team_a, team_b):
        vs = 0.
        _with = 0.
        for p1 in team_a:
            for p2 in team_b:
                vs += self.played_vs[p1][p2]
        # double counting all these
        for p1 in team_b:
            for p2 in team_b:
                if p1 == p2:
                    continue
                _with += self.played_with[p1][p2]
        for p1 in team_a:
            for p2 in team_a:
                if p1 == p2:
                    continue
                _with += self.played_with[p1][p2]
        _with /= 2  # remove double counting
        # print vs, _with, team_a, team_b
        return self.function(vs + _with)


class DecoratorHeuristic(Heuristic):

    """Decorate another one"""

    def __init__(self, subheuristic, function):
        self.subheuristic = subheuristic
        self.function = function

    def rate(self, team_a, team_b):
        self.function(self.subheuristic.rate(team_a, team_b))


class CombinerHeuristic(Heuristic):

    """
    Combine some
    """

    def __init__(self, a, b, function):
        self.a = a
        self.b = b
        self.function = function


    def rate(self, team_a, team_b):
        return self.function(
            self.a(team_a, team_b),
            self.b(team_a, team_b)
        )


class LinearSumHeuristic(Heuristic):

    """
    Combine some linearly
    """

    def __init__(self, weight_heuristic_tuple):
        self.wh = weight_heuristic_tuple
        self.div = sum(tup[0] for tup in self.wh)

    def rate(self, team_a, team_b):
        vals = [tup[0] * tup[1].rate(team_a, team_b) for tup in self.wh]
        return sum(vals) / self.div


def linear_clamped_function(x0, y0, x1, y1):
    m = (y1 - y0) / (x1 - x0)
    c = (y0 * x1 - y1 * x0) / (x1 - x0)

    def lin(x):
        return min(1., max(0., m * x + c))
    return lin
