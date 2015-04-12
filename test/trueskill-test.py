import trueskill
import kicker_backend
import kicker_ladders

import random

def pretty_print_2d(data_2d):
    """
    This takes a list of list of stringables.
    Returns a list of strings, with whitespace to align columns.
    eg: [[a,b],[cc,ddd]] -> [' a   b', 'cc ddd']
    Is hack.
    """
    # widths[n] holds the longest strlen for column n
    ret = []
    widths = [0] * len(data_2d[0])
    for i in range(len(widths)):
        widths[i] = 1 + len(str(max(data_2d, key=lambda x: len(str(x[i])))[i]))
    for i in range(len(data_2d)):
        line = ""
        for j in range(len(data_2d[i])):
            line += '{0:>{width}}'.format(data_2d[i][j], width=widths[j])
        ret.append(line)
    return ret

players = {}
for i in range(10):
    skill = float(i*2. + 15.)
    p = kicker_backend.KickerPlayer(str(skill))
    p.trueskill = skill
    p.mu = skill
    p.sigma = 0.
    players[str(skill)] = p


games = []
for i in range(100):
    teams = random.sample(players.values(), 4)
    win, draw, loss = trueskill.chances(teams[0:2], teams[2:4])
    rand_val = random.random()
    result = None
    if rand_val < win:
        result = 'beat'
    else:
        if rand_val - win < draw:
            result = 'draw'
        else:
            assert rand_val - win - draw < loss
            result = 'lost'
    games.append(kicker_backend.KickerGame("{} {} {} {} {}".format(
        teams[0].name, teams[1].name, result, teams[2].name, teams[3].name).split(), players))
    # print games[-1]
    # print win, draw, loss

def ranking_distance(data):
    names = [float(line[1]) for line in data[1:]]
    name_corr = sorted(names, reverse=True)
    return sum([abs(name_corr.index(n) - names.index(n)) for n in name_corr])

ladder = kicker_ladders.TrueSkillLadder()
elo = kicker_ladders.ELOLadder()
kicker_backend.cross_reference(players, games)

data = ladder.process(players, games)
for l in pretty_print_2d(data):
    print l
print ranking_distance(data)

data = elo.process(players, games)
for l in pretty_print_2d(data):
    print l
print ranking_distance(data)

