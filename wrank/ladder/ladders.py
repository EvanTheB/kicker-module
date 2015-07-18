from . import trueskill


class PlayerWrapper(object):

    """
    using this to wrap a LadderPlayer
    so I can munge in values like score
    """

    def __init__(self, player):
        self.player = player


class BasicLadder(object):

    def __init__(self):
        self.players = {}

    def add_game(self, game):
        for p in game.team_a:
            self.players[p].score += game.score_a - game.score_b
            self.players[p].games += 1
        for p in game.team_b:
            self.players[p].score -= game.score_a - game.score_b
            self.players[p].games += 1

    def process(self, players, games):
        self.players = {n: PlayerWrapper(p) for n, p in players.items()}
        for p in self.players.values():
            p.score = 0
            p.games = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            self.players.values(),
            key=lambda x: (x.score, x.games),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "points", "games"))
        i = 1
        for player in ladder:
            ret.append((
                i,
                player.player.name,
                player.score,
                player.games,
            ))
            i += 1
        return ret


class BasicScaledLadder(object):

    def __init__(self):
        self.players = {}

    def add_game(self, game):
        for p in game.team_a:
            self.players[p].score += game.score_a - game.score_b
            self.players[p].games += 1
        for p in game.team_b:
            self.players[p].score -= game.score_a - game.score_b
            self.players[p].games += 1

    def process(self, players, games):
        self.players = {n: PlayerWrapper(p) for n, p in players.items()}
        for p in self.players.values():
            p.score = 0
            p.games = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            self.players.values(),
            key=lambda x: (
                float(x.score)
                / (1E-30 + float(x.games)), x.games
            ),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "points/game"))
        i = 1
        for player in ladder:
            ret.append((
                i,
                player.player.name,
                float(player.score)
                / (1E-30 + float(player.games)),
            ))
            i += 1
        return ret


class ELOLadder(object):

    def __init__(self, K=24):
        self.players = {}
        self.K = K

    def add_game(self, game):
        """
        Do an ELO rank with made up stuff for the 2 player bit.
        ref: "https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
        """

        r1 = sum([self.players[p].rank for p in game.team_a]) / \
            float(len(game.team_a))
        r2 = sum([self.players[p].rank for p in game.team_b]) / \
            float(len(game.team_b))
        R1 = 10. ** (r1 / 400.)
        R2 = 10. ** (r2 / 400.)
        E1 = R1 / (R1 + R2)
        E2 = R2 / (R1 + R2)
        total_score = float(game.score_a + game.score_b)
        rd1 = self.K * (float(game.score_a) / total_score - E1)
        rd2 = self.K * (float(game.score_b) / total_score - E2)

        for p in game.team_a:
            self.players[p].rank += rd1
            self.players[p].games += 1
        for p in game.team_b:
            self.players[p].rank += rd2
            self.players[p].games += 1

    def process(self, players, games):
        self.players = {n: PlayerWrapper(p) for n, p in players.items()}
        for p in self.players.values():
            p.rank = 1000
            p.games = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            self.players.values(),
            key=lambda x: (x.rank, x.games),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "ELO", "games"))
        for i in range(len(ladder)):
            ret.append((
                i + 1,
                ladder[i].player.name,
                int(ladder[i].rank),
                ladder[i].games
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
        self.players = {}

    def chances(self, team_a, team_b):
        return trueskill.chances(
            [self.players[p] for p in team_a],
            [self.players[p] for p in team_b]
        )

    def quality(self, team_a, team_b):
        return trueskill.match_quality(
            [self.players[p] for p in team_a],
            [self.players[p] for p in team_b]
        )

    def add_game(self, game):
        trueskill.calculate_nvn(
            [self.players[p] for p in game.team_a],
            [self.players[p] for p in game.team_b],
            game.score_a,
            game.score_b)

    def process(self, players, games):
        self.players = {n: PlayerWrapper(p) for n, p in players.items()}
        for p in self.players.values():
            p.games = 0
            p.mu = 25.
            p.sigma = 25. / 3

        for g in games[:-1]:
            self.add_game(g)

        trueskill_sort = lambda x: (x.mu - 3 * x.sigma)

        ladder_last = sorted(
            self.players.values(),
            key=trueskill_sort,
            reverse=True)

        self.add_game(games[-1])

        ladder = sorted(
            self.players.values(),
            key=trueskill_sort,
            reverse=True)
        diff = []
        for p in ladder:
            diff.append(ladder_last.index(p))

        ret = []
        ret.append(("rank", "name", "change", "lvl", "mu", "sigma"))
        for i in range(len(ladder)):
            ret.append((
                str(i + 1),
                str(ladder[i].player.name),
                str(diff[i] - i),
                str(int(trueskill_sort(ladder[i]))),
                "{:.3}".format(ladder[i].mu),
                "{:.3}".format(ladder[i].sigma),
            ))
        return ret
