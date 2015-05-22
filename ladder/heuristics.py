class Heuristic(object):

    """
    interface for heuristic
    rate returns 0->1, 1 is good.
    """

    def __init__(self, arg):
        pass

    def rate(self, team_a, team_b):
        pass

    def rate_all(self, games_iterator):
        return [(self.rate(g[0], g[1]), (g[0], g[1])) for g in games_iterator]


class DrawChanceHeuristic(Heuristic):

    """microsoft style"""

    def __init__(self, ladder):
        self.ladder = ladder

    def rate(self, team_a, team_b):
        pass


class LadderDisruptionHeuristic(Heuristic):

    """andy style"""

    def __init__(self, ladder):
        self.ladder = ladder

    def rate(self, team_a, team_b):
        pass


class TrueskillClumpingHeuristic(Heuristic):

    """Prefer similar skills"""

    def __init__(self, ladder):
        self.ladder = ladder

    def rate(self, team_a, team_b):
        pass


class SigmaReductionHeuristic(Heuristic):

    """Try to reduce sigmas"""

    def __init__(self, ladder):
        self.ladder = ladder

    def rate(self, team_a, team_b):
        pass


class TimeSinceLastPlayedHeuristic(Heuristic):

    """Prefer not recent players"""

    def __init__(self, ladder):
        self.ladder = ladder

    def rate(self, team_a, team_b):
        pass


class UnplayedMatchups(Heuristic):

    """Nick style"""

    def __init__(self, ladder):
        self.ladder = ladder

    def rate(self, team_a, team_b):
        pass



if __name__ == '__main__':
    import kicker_backend
    import kicker_ladders
    data = kicker_backend.KickerData()
    players, games = data.get_players_games()

    pre_ladder = kicker_ladders.TrueSkillLadder()
    pre_data = pre_ladder.process(players, games)

    all_games = kicker_backend.all_games(players)

    DrawChanceHeuristic(pre_ladder)


