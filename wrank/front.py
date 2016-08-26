# coding=utf8
"""
ebenn, modified from rss.py
"""
from __future__ import unicode_literals

import argparse
import os
import time
import itertools
from functools import reduce

from toolz import frequencies

import wrank.backend as backend
import wrank.heuristics as heuristics
from wrank.ladder import ladders

PART_HTML = os.path.join(os.path.dirname(__file__), '..', 'static', 'part.html')


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


class HeuristicManager(object):

    def __init__(self):
        self.command = ["close_game",
                        "disrupt",
                        "class_warfare",
                        "sigma",
                        "time",
                        "variety",
                        "default",
                        "slow",
                        ]

    def get_heuristic(self, ladder, players, games, command):

        close_game = heuristics.DrawChanceHeuristic(ladder)

        linear_10 = heuristics.linear_clamped_function(0., 0., 10., 1.)
        disrupt = heuristics.LadderDisruptionHeuristic(
            ladder, players, games, linear_10)

        linear_3_10 = heuristics.linear_clamped_function(
            3. * 4., 1., 10. * 4., 0.)
        close_skills = heuristics.TrueskillClumpingHeuristic(
            ladder.process(players, games), linear_3_10)

        linear_week_month = heuristics.linear_clamped_function(
            time.time() - 7. * 24. * 60. * 60., 0.,
            time.time() - 30. * 24. * 60. * 60., 1.)
        playmore = heuristics.TimeSinceLastPlayedHeuristic(
            players, games, linear_week_month)

        linear_0_30 = heuristics.linear_clamped_function(0., 1., 30., 0.)
        variety = heuristics.UnplayedMatchupsHeuristic(
            players, games, linear_0_30)

        lin_heur = [
            (1.5, close_game),
            (1., close_skills),
            (0.5, variety),
        ]
        default = heuristics.LinearSumHeuristic(lin_heur)
        if command == "fast":
            return default

        slow_lin_heur = [
            # (1., close_game),
            (0.5, close_skills),
            (2., disrupt),
            (0.5, variety),
            (0.5, playmore),
        ]
        slow = heuristics.LinearSumHeuristic(slow_lin_heur)
        if command == "slow":
            return slow


class LadderManager(object):

    """
    CLI/IRC ladder interaction
    """

    def __init__(self, log_file):
        self.data = backend.LadderData(log_file)

    def ladder_command(self, command):
        class LadderArgError(Exception):
            pass

        class LadderArgumentParser(argparse.ArgumentParser):

            def error(self, message):
                raise LadderArgError(self.format_usage())

        parser = LadderArgumentParser(prog=".wrank", add_help=False)
        subcommands = parser.add_subparsers()
        parser.add_argument("-h", action="store_true")

        ladder = subcommands.add_parser('ladder')
        ladder.add_argument('type',
                            type=str,
                            choices=['ELO', 'basic', 'scaled', 'trueskill', "trueskill_ms"],
                            default='trueskill',
                            nargs='?',
                            )
        ladder.add_argument('-v', '--verbose', action='count')
        ladder.add_argument('-b', '--history')
        ladder.add_argument('-f', '--filter', nargs='*')
        ladder.add_argument('options', nargs='*')
        ladder.set_defaults(func=self._show_ladder)

        add = subcommands.add_parser('add')
        add.add_argument('name', type=str)
        add.set_defaults(func=self._add_player)

        game = subcommands.add_parser('game')
        game.add_argument('words', type=str, nargs='*')
        game.set_defaults(func=self._add_game)

        history = subcommands.add_parser('history')
        history.add_argument('players', type=str, nargs='*')
        history.set_defaults(func=self._show_history)

        next_best = subcommands.add_parser('next')
        next_best.add_argument('players', type=str, nargs='*')
        next_best.add_argument('--heuristic', '-z',
                               type=str,
                               default='fast',
                               choices=HeuristicManager().command)
        next_best.set_defaults(func=self._best_matches)

        whowins = subcommands.add_parser('whowins')
        whowins.add_argument('team_a', type=str, nargs=2)
        whowins.add_argument('team_b', type=str, nargs=2)
        whowins.set_defaults(func=self._expected_outcome)

        try:
            args = parser.parse_args(command)
            return args.func(args)
        except LadderArgError as e:
            return str(e).split('\n')

    def _best_matches(self, command):
        all_players, all_games = self.data.get_players_games()
        ladder = ladders.TrueSkillLadder()
        ladder.process(all_players, all_games)

        # set up players and game_filter such that
        # all combinations of players if filter()
        # gives our list of potential games
        if command.players:
            if len(command.players) >= 4:
                game_filter = lambda x: True
                players = {
                    name: p for name, p in all_players.items()
                    if name in command.players
                }
            else:
                players = all_players

                def game_filter(this_game_players):
                    for name in command.players:
                        if name not in this_game_players:
                            return False
                    return True
        else:
            game_filter = lambda x: True
            players = all_players

        all_potential_games = []
        pre_ladder = ladders.TrueSkillLadder()
        pre_data = pre_ladder.process(all_players, all_games)

        games = backend.all_games(players, game_filter)

        heur = HeuristicManager().get_heuristic(ladder, all_players, all_games, command.heuristic)
        ratings = sorted(heur.rate_all(games), key=lambda x: x[0], reverse=True)

        printable = [" ".join(
            list(rating[1][0]) +
            ["vs"] +
            list(rating[1][1]) +
            ["\tv:{0:.3} w:{1[0]:.2} d:{1[1]:.2} l:{1[2]:.2}".format(
                rating[0], ladder.chances(rating[1][0], rating[1][1]))]
        ) for rating in ratings]

        return printable[0:8]

    def _expected_outcome(self, command):
        players, games = self.data.get_players_games()
        ladder = ladders.TrueSkillLadder()
        ladder.process(players, games)

        return [
            "w:{0[0]:0.2f} d:{0[1]:0.2f} l:{0[2]:0.2f}".format(
                ladder.chances(command.team_a, command.team_b)
            )
        ]

    def _add_player(self, command):
        ret = self.data.add_player(command.name)
        # self.write_index_html()
        return [ret]

    def _add_game(self, command):
        ret = self.data.add_game(
            command.words
        )
        # self.write_index_html()
        return [ret]

    def _show_ladder(self, command):
        def prepare_ladder(current, before):
            ret = []
            ret.append([
                "rank",
                "name",
                "change",
            ] + [x[0] for x in current[0].extra])
            before = {row.name: row for row in before}
            for player in current:
                ret.append([
                    str(player.rank),
                    str(player.name),
                    str(int(before[player.name].rank) - int(player.rank)),
                ] + [str(x[1]) for x in player.extra])
            return ret

        players, games = self.data.get_players_games()
        if command.filter:
            players = {k:v for k,v in players.items() if k in command.filter}
            games = [g for g in games if all(p in command.filter for p in itertools.chain.from_iterable(g.teams))]

        if command.type == 'ELO':
            elo_k = 24
            if command.options:
                try:
                    elo_k = int(command.options[0])
                except ValueError:
                    return "Wanted a number. got {}".format(
                        command.options[0])
            ladder = ladders.ELOLadder(K=elo_k)
        elif command.type == 'basic':
            ladder = ladders.BasicLadder()
        elif command.type == 'scaled':
            ladder = ladders.BasicScaledLadder()
        elif command.type == 'trueskill':
            ladder = ladders.TrueSkillLadder(dynamics_factor=25.0 / 30)
        elif command.type == 'trueskill_ms':
            ladder = ladders.TrueSkillLadder(dynamics_factor=25.0 / 300)

        if command.history:
            int(command.history)
            assert len(games) > int(command.history) > 0

        current_ladder = ladder.process(players, games)
        before_ladder = ladder.process(players, games[0:-int(command.history or 1)])

        data = prepare_ladder(current_ladder, before_ladder)

        if command.verbose is None and 'trueskill' in command.type:
            # title line is 0
            lines = [0]
            keep = set(p for p in itertools.chain.from_iterable(games[-1].teams))
            change_index = data[0].index('change')
            for i, line in enumerate(data):
                # if one of our 'keepers'
                if set(line).intersection(keep):
                    lines.append(i)
                    lines.append(i + 1)
                    lines.append(i - 1)
                # or the position changed
                if line[change_index] != '0':
                    lines.append(i)
            data = [line for i, line in enumerate(data) if i in lines]
        elif command.verbose == 1 and 'trueskill' in command.type:
            # title line is 0
            lines = [0]
            # played in last 50 games
            keep = reduce(
                lambda a, b: a.union(b), (
                    set(p for p in itertools.chain.from_iterable(g.teams))
                    for g in games[-50:]
                )
            )
            # played at least 3 games
            keep = keep.intersection(set(p for p, c in itertools.ifilter(
                lambda x: x[1] > 2,
                frequencies(
                    p for g in games for p in itertools.chain.from_iterable(g.teams)
                ).items()
            )))
            change_index = data[0].index('change')
            for i, line in enumerate(data):
                # if one of our 'keepers'
                if set(line).intersection(keep):
                    lines.append(i)
            data = [line for i, line in enumerate(data) if i in lines]
        return ["After {} games, change vs game {}".format(
            len(games), len(games) - int(command.history or 1))
            ] + pretty_print_2d(data)

    def _show_history(self, command):
        ret=[]
        i=1
        _, games=self.data.get_players_games()
        games=list(enumerate(games))
        if command.players:
            for p in command.players:
                games=[
                    (i, g) for (
                        i, g) in games if p in (
                        itertools.chain.from_iterable(
                            g.teams))]
        for i, g in games:
            ret.append("{}: {}".format(i, g))
            i += 1
        ret.reverse()
        return ret[0:5]

    def write_index_html(self):
        players, games=self.data.get_players_games()
        data_tuples=ladders.TrueSkillLadder(dynamics_factor=25.0 / 300.).process(
            players, games)
        output=""
        output += "Trueskill ladder ranked on mu - 3*sigma (P(skill>level)~0.99)<br>\n"
        output += '<table border="1">\n'
        for line in data_tuples:
            output += '<tr>'
            for col in line:
                output += '<td>'
                output += str(col)
                output += '</td>'
            output += '</tr>\n'
        output += '</table>\n'

        # output += '\n<p>Next most awesome matches (rated by how much the
        # ladder will be changed (andystyle)): <br>'
        output += '\n<p>Game history: <br>'
        i=1
        for g in games:
            output += "{}: {}<br>".format(i, g)
            i += 1

        with open(PART_HTML, 'w') as web_page:
            web_page.write(output)

        return output
