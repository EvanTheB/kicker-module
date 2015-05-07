# coding=utf8
"""
ebenn, modified from rss.py
"""
from __future__ import unicode_literals


import argparse
import itertools

import kicker_ladders
import kicker_backend
import trueskill


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


class KickerManager(object):

    """
    CLI/IRC ladder interaction
    """

    def __init__(self):
        self.data = kicker_backend.KickerData()

    def kicker_command(self, command):
        parser = argparse.ArgumentParser(prog=".kicker", add_help=False)
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
        next_best.set_defaults(func=self._best_matches)

        whowins = subcommands.add_parser('whowins')
        whowins.add_argument('team_a', type=str, nargs=2)
        whowins.add_argument('team_b', type=str, nargs=2)
        whowins.set_defaults(func=self._expected_outcome)

        args = parser.parse_args(command)
        if args.h:
            return [parser.format_help()]
        else:
            return args.func(args)

    def _best_matches(self, command):
        def _get_dist(ladder_data):
            dist = 0.
            for row in ladder_data[1:]:
                dist += abs(float(row[2]))
            return dist

        def _get_game_list(players, game_filter):
            seen_games = set()
            for team_a in itertools.combinations(players, 2):
                for team_b in itertools.combinations(players, 2):
                    if team_a + team_b in seen_games \
                            or team_b + team_a in seen_games\
                            or len([True for p in team_b if p in team_a]) > 0:
                        continue
                    seen_games.add(team_a + team_b)
                    if game_filter and game_filter([p.name for p in team_a + team_b]):
                        continue
                    yield team_a, team_b


        all_players = self.data.get_players().values()
        game_filter = None
        if command.players:
            if len(command.players) >= 4:
                all_players = [p for p in all_players if p.name in command.players]
            else:
                def game_filter(players):
                    for name in command.players:
                        if name not in players:
                            return False
        all_games = []
        for team_a, team_b in _get_game_list(all_players, game_filter):
            kicker_backend.cross_reference(
                self.data.get_players(), self.data.get_games())
            ladder = kicker_ladders.TrueSkillLadder()
            data = ladder.process(self.data.get_players(),
                                  self.data.get_games())
            results = trueskill.chances(team_a, team_b)
            match_worth = 0.
            for prob, outcome in zip(results, ['beat', 'draw', 'lost']):
                game = kicker_backend.KickerGame(
                    [p.name for p in team_a] + [outcome] + [p.name for p in team_b],
                    self.data.get_players())

                # get next ladder
                kicker_backend.cross_reference(
                    self.data.get_players(),
                    self.data.get_games() +
                    [game])
                ladder = kicker_ladders.TrueSkillLadder()
                data = ladder.process(self.data.get_players(),
                                      self.data.get_games() + [game])
                match_worth += prob * _get_dist(data)
            all_games.append(
                (match_worth, " ".join([p.name for p in team_a] + ["vs"] + [p.name for p in team_b] + ["\tv:{0:.2} w:{1[0]:.2} d:{1[1]:.2} l:{1[2]:.2}".format(match_worth, results)])))


        teams = sorted(all_games, reverse=True)
        return [t[1] for t in teams][0:15]

    def _expected_outcome(self, command):
        # ensure ladder is up to date
        kicker_backend.cross_reference(
            self.data.get_players(), self.data.get_games())
        ladder = kicker_ladders.TrueSkillLadder()
        ladder.process(self.data.get_players(), self.data.get_games())

        all_players = {p.name: p for p in self.data.get_players().values()}
        team_a_players = [all_players[n] for n in command.team_a]
        team_b_players = [all_players[n] for n in command.team_b]
        return [
            "w:{0[0]:.2} d:{0[1]:.2} l:{0[2]:.2}".format(
                trueskill.chances(
                    team_a_players,
                    team_b_players))]

    def _add_player(self, command):
        ret = self.data.add_player(command.name)
        self.data.save_to_log()
        return [ret]

    def _add_game(self, command):
        ret = self.data.add_game(
            command.team_a
            + [command.result]
            + command.team_b)
        self.data.save_to_log()
        # self.write_index_html()
        return [ret]

    def _show_ladder(self, command):
        kicker_backend.cross_reference(
            self.data.get_players(), self.data.get_games())
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

        data = ladder.process(self.data.get_players(), self.data.get_games())
        return pretty_print_2d(data)

    def _show_history(self, command):
        ret = []
        i = 1
        for g in self.data.get_games():
            ret.append("{}: {}".format(i, g))
            i += 1
        return ret

    def write_index_html(self):
        kicker_backend.cross_reference(
            self.data.get_players(), self.data.get_games())
        data_tuples = kicker_ladders.TrueSkillLadder().process(
            self.data.get_players(), self.data.get_games())
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

        output += '\n<p>Next most awesome matches (by how much the ladder will change(andystyle)): <br>'
        self.players = None
        matches = self._best_matches(self)
        for l in matches:
            output += l + '<br>\n'

        output += '\n<p>Game history: <br>'
        i = 1
        for g in self.data.get_games():
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
        with open("www/index.html", 'w') as web_page:
            web_page.write(full_output)
        with open("www/part.html", 'w') as web_page:
            web_page.write(output)

        return output

if __name__ == '__main__':
    k = KickerManager()
    # k.kicker_command(["-h"])
    # k.kicker_command(["ladder", "ELO", "60"])
    # print "\n".join(k.kicker_command(["ladder"]))
    # print "\n".join(k.kicker_command(["ladder", "ELO"]))
    # print "\n".join(k.kicker_command(["ladder", "basic"]))
    # print "\n".join(k.kicker_command(["ladder", "scaled"]))
    # print "\n".join(k.kicker_command(["history"]))
    # k.kicker_command(["ladder", "-h"])
    # print "\n".join(k.kicker_command(["next", "celine", "evan", "chris", "william", "nick"]))
    # print "\n".join(k.kicker_command(["next", "celine", "evan", "chris"]))
    # print "\n".join(k.kicker_command(["next"]))

    # print "\n".join(k.kicker_command(["whowins", "nick", "chris", "evan", "andy"]))
    print k.write_index_html()