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
for i in range(4):
    skill = float(i)
    p = kicker_backend.KickerPlayer(str(skill))
    p.trueskill = skill
    p.mu = 25.
    p.sigma = 8.333
    players[str(skill)] = p

games = []
teams = players.values()[0:4]

for i in range(50):
    games.append(kicker_backend.KickerGame("{} {} {} {} {}".format(
        teams[0].name, teams[1].name, 'lost', teams[2].name, teams[3].name).split(), players))

ladder = kicker_ladders.TrueSkillLadder()
kicker_backend.cross_reference(players, games)
data = ladder.process(players, games)
for l in pretty_print_2d(data):
    print l


