import numpy as np
import pylab
import matplotlib.pyplot as plt
import math


import kicker_ladders
import kicker_backend

COLOURS = ['b', 'g','r',  'c',  'm','y',  'k',]

def get_subset(graph_data, names):
    return [[d for d in l if d[0] in names] for l in graph_data]


def data_to_yarr(graph_data):
    names = [t[0] for t in graph_data[0]]
    ret = []
    for n in names:
        data = get_subset(graph_data, n)
        y = [float(l[0][1]) for l in data]
        ret.append(y)
    return ret


def graph_ranks(p, g, ladder):
    def get_names_ranks(data):
        ret = []
        for l in data[1:]:
            if float(l[5]) > 7.:
                ret.append((l[1], len(data)))
            else:
                ret.append((l[1], l[0]))
        return ret

    graph_data = []
    for i in range(1, len(g) + 1):
        data = ladder.process(p, g[0:i])
        graph_data.append(get_names_ranks(data))

    for y in data_to_yarr(graph_data):
        plt.plot(y)
    pylab.savefig('graph_ranks.svg')
    plt.show()


def graph_level(p, g, ladder):
    def get_names_lvl(data):
        ret = []
        for l in data[1:]:
            ret.append((l[1], l[3]))
        return ret

    graph_data = []
    for i in range(1, len(g) + 1):
        data = ladder.process(p, g[0:i])
        graph_data.append(get_names_lvl(data))

    for y in data_to_yarr(graph_data):
        plt.plot(y)
    pylab.savefig('graph_level.svg')
    plt.show()


def graph_skill(p, g, ladder):
    def get_names_skill(data):
        ret = []
        for l in data[1:]:
            if float(l[5]) > 7.:
                ret.append((l[1], 0.))
            else:
                ret.append((l[1], l[4]))
        return ret

    graph_data = []
    for i in range(1, len(g) + 1):
        data = ladder.process(p, g[0:i])
        graph_data.append(get_names_skill(data))

    for y in data_to_yarr(graph_data):
        plt.plot(y)
    pylab.savefig('graph_skill.svg')
    plt.show()


def graph_skill_error(p, g, ladder):
    def get_names_skill(data):
        ret = []
        for l in data[1:]:
            ret.append((l[1], l[4]))
        return ret

    def get_names_err(data):
        ret = []
        for l in data[1:]:
            ret.append((l[1], float(l[5])))
        return ret

    def get_top_n(data):
        tup = sorted(data, key=lambda x: x[1])
        names = [t[0] for t in tup[:6]]
        return names

    graph_data = []
    err_data = []
    for i in range(1, len(g) + 1):
        data = ladder.process(p, g[0:i])
        graph_data.append(get_names_skill(data))
        err_data.append(get_names_err(data))
    names = get_top_n(err_data[-1])
    graph_data = get_subset(graph_data, names)
    err_data = get_subset(err_data, names)

    ys = data_to_yarr(graph_data)
    errs = data_to_yarr(err_data)
    for i in range(len(ys)):
        err = np.array(errs[i])
        y = np.array(ys[i])
        plt.fill_between(range(len(y)), y+err, y-err, alpha=0.25, color=COLOURS[i])
        plt.plot(range(len(y)), y, COLOURS[i] +'-', label = names[i])
        plt.plot(y)
    plt.legend(loc=3, ncol=len(names)/2)
    pylab.savefig('graph_error.svg')
    plt.show()



if __name__ == '__main__':
    k = kicker_backend.KickerData()
    p, g = k.get_players_games()

    ladder = kicker_ladders.TrueSkillLadder()

    graph_level(p, g, ladder)
    graph_ranks(p, g, ladder)
    graph_skill(p, g, ladder)
    graph_skill_error(p, g, ladder)
