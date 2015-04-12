import trueskill


class BasicLadder(object):

    def __init__(self):
        self.players = {}

    def add_game(self, game):
        for p in game.team_a_players:
            p.score += game.score_a - game.score_b
        for p in game.team_b_players:
            p.score -= game.score_a - game.score_b

    def process(self, players, games):
        for _, p in players.items():
            p.score = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            players.values(),
            key=lambda x: (x.score, len(x.games)),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "points", "games"))
        i = 1
        for player in ladder:
            ret.append((
                i,
                player.name,
                player.score,
                len(player.games),
            ))
            i += 1
        return ret


class BasicScaledLadder(object):

    def __init__(self):
        pass

    def add_game(self, game):
        for p in game.team_a_players:
            p.rank += game.score_a - game.score_b
        for p in game.team_b_players:
            p.rank -= game.score_a - game.score_b

    def process(self, players, games):
        for p in players.values():
            p.rank = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            players.values(),
            key=lambda x: (
                float(x.rank)
                / (1E-30 + float(len(x.games)))
                ,len(x.games)
            ),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "points/game"))
        i = 1
        for player in ladder:
            ret.append((
                i,
                player.name,
                float(player.rank)
                / (1E-30 + float(len(player.games))),
            ))
            i += 1
        return ret

class ELOLadder(object):

    def __init__(self, K=24):
        self.K = K

    def add_game(self, game):
        """
        Do an ELO rank with made up stuff for the 2 player bit.
        ref: "https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
        """

        r1 = sum([r.rank for r in game.team_a_players]) / float(len(game.team_a_players))
        r2 = sum([r.rank for r in game.team_b_players]) / float(len(game.team_b_players))
        R1 = 10. ** (r1 / 400.)
        R2 = 10. ** (r2 / 400.)
        E1 = R1 / (R1 + R2)
        E2 = R2 / (R1 + R2)
        total_score = float(game.score_a + game.score_b)
        rd1 = self.K * (float(game.score_a) / total_score - E1)
        rd2 = self.K * (float(game.score_b) / total_score - E2)

        for p in game.team_a_players:
            p.rank += rd1
        for p in game.team_b_players:
            p.rank += rd2

    def process(self, players, games):
        for p in players.values():
            p.rank = 1000

        for g in games:
            self.add_game(g)

        ladder = sorted(
            players.values(),
            key=lambda x: (x.rank, len(x.games)),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "ELO", "games"))
        for i in range(len(ladder)):
            ret.append((
                i + 1,
                ladder[i].name,
                int(ladder[i].rank),
                len(ladder[i].games)
            ))
        return ret

class TrueSkillLadder(object):

    """
    ref:
    http://trueskill.org/
    http://blogs.technet.com/b/apg/archive/2008/06/16/trueskill-in-f.aspx
    http://www.moserware.com/2010/03/computing-your-skill.html
    https://github.com/moserware/Skills
    """

    def __init__(self):
        pass

    def add_game(self, game):
        trueskill.calculate_nvn(
            game.team_a_players, game.team_b_players, game.score_a, game.score_b)

    def process(self, players, games):
        for p in players.values():
            p.mu = 25.
            p.sigma = 25./3
        for g in games[:-1]:
            self.add_game(g)

        ladder_last = sorted(
            players.values(),
            key=lambda x: (x.mu - 0 * x.sigma),
            reverse=True)

        self.add_game(games[-1])

        ladder = sorted(
            players.values(),
            key=lambda x: (x.mu - 0 * x.sigma),
            reverse=True)
        diff = []
        for p in ladder:
            diff.append(ladder_last.index(p))

        ret = []
        ret.append(("rank", "name", "change", "lvl", "mu", "sigma"))
        for i in range(len(ladder)):
            ret.append((
                str(i + 1),
                str(ladder[i].name),
                str(diff[i] - i),
                str(int(ladder[i].mu - 1 * ladder[i].sigma)),
                "{:.3}".format(ladder[i].mu),
                "{:.3}".format(ladder[i].sigma),
            ))
        return ret