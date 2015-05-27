# coding=utf8
"""
ebenn, modified from rss.py
"""
from __future__ import unicode_literals


import argparse
import itertools
import os
import time
import sys

import kicker_ladders
import kicker_backend
import trueskill
import heuristics

PART_HTML = os.path.join(os.path.dirname(__file__), 'static', 'part.html')


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
                        "default"
                        ]

    def get_heuristic(self, ladder, players, games, command):

        close_game = heuristics.DrawChanceHeuristic(ladder)
        if command == "close_game":
            return close_game

        linear_10 = heuristics.linear_clamped_function(0., 0., 10., 1.)
        disrupt = heuristics.LadderDisruptionHeuristic(
            ladder, players, games, linear_10)
        if command == "disrupt":
            return disrupt

        linear_3_10 = heuristics.linear_clamped_function(
            3. * 4., 1., 10. * 4., 0.)
        class_warfare = heuristics.TrueskillClumpingHeuristic(
            ladder.process(players, games), linear_3_10)
        if command == "class_warfare":
            return class_warfare

        linear_0_1 = heuristics.linear_clamped_function(0., 0., 1.0, 1.)
        sigma = heuristics.SigmaReductionHeuristic(
            ladder, players, games, linear_0_1)
        if command == "sigma":
            return sigma

        linear_week_month = heuristics.linear_clamped_function(
            time.time() - 7. * 24. * 60. * 60., 0.,
            time.time() - 30. * 24. * 60. * 60., 1.)
        playmore = heuristics.TimeSinceLastPlayedHeuristic(
            players, games, linear_week_month)
        if command == "playmore":
            return playmore

        linear_0_30 = heuristics.linear_clamped_function(0., 1., 30., 0.)
        variety = heuristics.UnplayedMatchupsHeuristic(
            players, games, linear_0_30)
        if command == "variety":
            return variety

        lin_heur = [
            (20., close_game),
            (5., disrupt),
            (10., class_warfare),
            (2.5, sigma),
            (5., playmore),
            (5., variety),
        ]
        default = heuristics.LinearSumHeuristic(lin_heur)
        if command == "default":
            return default


class KickerManager(object):

    """
    CLI/IRC ladder interaction
    """

    def __init__(self):
        self.data = kicker_backend.KickerData()

    def kicker_command(self, command):
        class KickerArgumentParser(argparse.ArgumentParser):

            def error(self, message):
                raise KickerArgError(self.format_usage())

        class KickerArgError(Exception):
            pass

        parser = KickerArgumentParser(prog=".kicker", add_help=False)
        subcommands = parser.add_subparsers()
        parser.add_argument("-h", action="store_true")

        ladder = subcommands.add_parser('ladder')
        ladder.add_argument('type',
                            type=str,
                            choices=['ELO', 'basic', 'scaled', 'trueskill'],
                            default='trueskill',
                            nargs='?',
                            )
        ladder.add_argument('options', nargs='*')
        ladder.set_defaults(func=self._show_ladder)

        add = subcommands.add_parser('add')
        add.add_argument('name', type=str)
        add.set_defaults(func=self._add_player)

        game = subcommands.add_parser('game')
        game.add_argument('team_a', type=str, nargs=2)
        game.add_argument('result', type=str,
                          choices=['beat', 'draw', 'lost'])
        game.add_argument('team_b', type=str, nargs=2)
        game.set_defaults(func=self._add_game)

        history = subcommands.add_parser('history')
        history.set_defaults(func=self._show_history)

        next_best = subcommands.add_parser('next')
        next_best.add_argument('players', type=str, nargs='*')
        next_best.add_argument('--heuristic',
                               type=str,
                               default='default',
                               choices=HeuristicManager().command)
        next_best.set_defaults(func=self._best_matches)

        whowins = subcommands.add_parser('whowins')
        whowins.add_argument('team_a', type=str, nargs=2)
        whowins.add_argument('team_b', type=str, nargs=2)
        whowins.set_defaults(func=self._expected_outcome)

        try:
            args = parser.parse_args(command)
            return args.func(args)
        except KickerArgError as e:
            return str(e).split('\n')

    def _best_matches(self, command):
        all_players, all_games = self.data.get_players_games()
        ladder = kicker_ladders.TrueSkillLadder()
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
        pre_ladder = kicker_ladders.TrueSkillLadder()
        pre_data = pre_ladder.process(all_players, all_games)

        games = kicker_backend.all_games(players, game_filter)

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
        ladder = kicker_ladders.TrueSkillLadder()
        ladder.process(players, games)

        return [
            "w:{0[0]:.2} d:{0[1]:.2} l:{0[2]:.2}".format(
                ladder.chances(command.team_a, command.team_b)
            )
        ]

    def _add_player(self, command):
        ret = self.data.add_player(command.name)
        self.write_index_html()
        return [ret]

    def _add_game(self, command):
        ret = self.data.add_game(
            command.team_a
            + [command.result]
            + command.team_b)
        self.write_index_html()
        return [ret]

    def _show_ladder(self, command):
        players, games = self.data.get_players_games()
        if command.type == 'ELO':
            elo_k = 24
            if command.options:
                try:
                    elo_k = int(command.options[0])
                except ValueError:
                    return "Wanted a number. got {}".format(
                        command.options[0])
            ladder = kicker_ladders.ELOLadder(K=elo_k)
        elif command.type == 'basic':
            ladder = kicker_ladders.BasicLadder()
        elif command.type == 'scaled':
            ladder = kicker_ladders.BasicScaledLadder()
        elif command.type == 'trueskill':
            ladder = kicker_ladders.TrueSkillLadder()

        data = ladder.process(players, games)
        return pretty_print_2d(data)

    def _show_history(self, _):
        ret = []
        i = 1
        _, games = self.data.get_players_games()
        for g in games:
            ret.append("{}: {}".format(i, g))
            i += 1
        return ret

    def write_index_html(self):
        players, games = self.data.get_players_games()
        data_tuples = kicker_ladders.TrueSkillLadder().process(
            players, games)
        output = ""
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
        i = 1
        for g in games:
            output += "{}: {}<br>".format(i, g)
            i += 1

        full_output = """
                <!DOCTYPE html>
                <html>
                <head>
                <title>Sweet Kicker Ladder</title>
                </head>

                <body>
                <marquee>WELCOME TO LADDER</marquee>
                {body}
                </body>

                </html>
                """.format(body=output)
        with open(PART_HTML, 'w') as web_page:
            web_page.write(output)

        return output

if __name__ == '__main__':
    k = KickerManager()
    if len(sys.argv) > 1:
        "\n".join(k.kicker_command(sys.argv[1:]))
    else:
        # print "\n".join(k.kicker_command(["ladder", "basic"]))
        # print "\n".join(k.kicker_command(["ladder", "scaled"]))
        # print "\n".join(k.kicker_command(["ladder", "ELO"]))
        # print "\n".join(k.kicker_command(["ladder"]))

        # print "\n".join(k.kicker_command(["history"]))

        # print "\n".join(k.kicker_command(["whowins", "nick", "chris", "evan",
        # "andy"]))

        print "\n".join(k.kicker_command(["next", "--heuristic", "class_warfare", "celine", "evan", "chris", "william", "nick"]))
        print "\n".join(k.kicker_command(["next", "celine", "evan", "chris"]))
        print "\n".join(k.kicker_command(["next", "--heuristic", "close_game", "evan"]))
        # print "\n".join(k.kicker_command(["next"]))

        # print "\n".join(k.kicker_command(["add", "newplayer"]))
        # print "\n".join(k.kicker_command(["game", "newplayer", "newplayer",
        # "beat", "newplayer", "newplayer"]))

        print k.write_index_html()
        print "\n".join(k.kicker_command(["wrong"]))
        print "\n".join(k.kicker_command(["next", "-h"]))
