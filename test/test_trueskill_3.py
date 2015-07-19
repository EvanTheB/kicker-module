import wrank.ladder.trueskill as trueskill
import wrank.backend
import wrank.ladder.ladders

import random
import itertools
import math

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
for i in range(15, 30, 2):
    skill = float(i)
    p = wrank.backend.LadderPlayer(str(skill), 1)
    p.trueskill = skill
    p.mu = skill
    p.sigma = 8.333
    players[str(skill)] = p


games = []
# k*m*log2(n)/log2(k!)
# 2*2*log2(len(players)) * len(players)
for i in range(int(2*2*math.log(len(players), 2) * len(players))):

    possible = []
    # we test all permutations of a random sub-sample.
    # for some reason the match quality likes people who have played already..
    # for team in itertools.permutations(random.sample(players.values(), 6), 4):
    #     possible.append((team, trueskill.match_quality_hard(team[0:2], team[2:])))

    # teams = max(possible, key=lambda x: x[1])[0]


    teams = random.sample(players.values(), 4)
    # print max(possible, key=lambda x: x[1])[1]
    # print [p.mu for p in teams]
    for p in teams:
        p.mu = float(p.name)
        p.sigma = 0.
    # print [p.mu for p in teams]


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
    games.append(wrank.backend.LadderGame("{} {} {} {} {}".format(
        teams[0].name, teams[1].name, result, teams[2].name, teams[3].name).split(), players, 1))
    print games[-1]
    print win, draw, loss
    ladder = wrank.ladder.ladders.TrueSkillLadder()
    data = ladder.process(players, games)

def ranking_distance(data):
    names = [float(line[1]) for line in data[1:]]
    name_corr = sorted(names, reverse=True)
    return sum([abs(name_corr.index(n) - names.index(n)) for n in name_corr])

ladder = wrank.ladder.ladders.TrueSkillLadder()
elo = wrank.ladder.ladders.ELOLadder()

data = ladder.process(players, games)
for l in pretty_print_2d(data):
    print l
print ranking_distance(data)

data = elo.process(players, games)
for l in pretty_print_2d(data):
    print l
print ranking_distance(data)

