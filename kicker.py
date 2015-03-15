# coding=utf8
"""
ebenn, modified from rss.py
"""
from __future__ import unicode_literals
try:
    from willie.module import commands, interval
    from willie.config import ConfigurationError
    from willie.logger import get_logger

    @commands('kicker')
    def kicker_command(bot, trigger):
        """
        Manage the kicker.
        Commands:
            add <player>
            game <player> <player> (beat)|(lost)|(draw) <player> <player>
            ladder [(basic)|(ELO [K])]
            history
        """
        text = trigger.group().split()[1:]
        bot.say(bot.memory['kicker_manager'].kicker_command(text))

except ImportError as e:
    print "could not import willie"

import json
import os
import shutil
import argparse
import copy

import trueskill

LOG_FILE = os.path.join(os.path.dirname(__file__), 'kicker.log')


def setup(bot):
    bot.memory['kicker_manager'] = KickerManager()


class KickerManager:

    def __init__(self):
        self.players = {}
        self.games = []
        self.events = []
        # Load and backup log file
        with open(LOG_FILE, 'r') as log:
            kicker_log = json.load(log)
        shutil.copyfile(LOG_FILE, LOG_FILE + '_backup')
        self._load_from_log(kicker_log)

    def _load_from_log(self, log):
        events = log['events']
        for e in events:
            if e['type'] == "AddPlayerEvent":
                self._add_event(AddPlayerEvent.from_json(e))
            elif e['type'] == "AddGameEvent":
                self._add_event(AddGameEvent.from_json(e))
            else:
                assert False, "failed to load event: " + str(e)

    def _add_event(self, event):
        self.events.append(event)
        reply = self.events[-1].processEvent(self.players, self.games)
        return reply

    def save_to_log(self):
        to_save = {}
        to_save['events'] = []
        for e in self.events:
            to_save['events'].append(e.to_json())
        with open(LOG_FILE, 'w') as log:
            json.dump(
                to_save,
                log,
                sort_keys=True,
                indent=4,
                separators=(',', ': '))

    def _add_player(self, command):
        ret = ""
        for name in command.name:
            ret.append(self._add_event(AddPlayerEvent(name)))
        self.save_to_log()
        return [ret]

    def _add_game(self, command):
        ret = self._add_event(
            AddGameEvent(
                command.team_a
                + [command.result]
                + command.team_b),
        )
        self.save_to_log()
        return [ret]

    def _pretty_print(self, data_tuples):
        """
        This returns the tuples in nice whitespace aligned columns.
        And is hack. (list of strangs)
        """
        # widths holds the longest strlen
        # in the list of tuples for that position
        ret = []
        widths = [0] * len(data_tuples[0])
        for i in range(len(widths)):
            widths[i] = 1 + \
                len(str(max(data_tuples, key=lambda x: len(str(x[i])))[i]))
        for i in range(len(data_tuples)):
            s = ""
            for j in range(len(data_tuples[i])):
                s += '{0:>{width}}'.format(data_tuples[i][j], width=widths[j])
            ret.append(s)
        return ret

    def _show_ladder(self, command):
        if command.type == 'ELO':
            elo_k = 24
            if command.options:
                try:
                    elo_k = int(command.options[0])
                except ValueError:
                    return "Wanted a number. got {}".format(
                        command.options[0])
            ladder = ELOLadder(K=elo_k)
        elif command.type == 'basic':
            ladder = BasicLadder()
        elif command.type == 'scaled':
            ladder = BasicScaledLadder()
        elif command.type == 'trueskill':
            ladder = TrueSkillLadder()

        data_tuples = ladder.process(self.players, self.games)
        return self._pretty_print(data_tuples)

    def _show_history(self, command):
        ret = []
        ret.append("games:")
        i = 1
        for g in self.games:
            ret.append("{}: {}".format(i, g))
            i += 1
        return ret

    def write_index_html(self):
        data_tuples = TrueSkillLadder().process(self.players, self.games)
        output = '<table border="1"">'
        for i in data_tuples:
            output += '<tr>'
            for j in i:
                output += '<td>'
                output += str(j)
                output += '</td>'
            output += '</tr>'
        with open("www/index.html", 'w') as web_page:
            web_page.write(output)

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
        add.add_argument('name', type=str, nargs='+')
        add.set_defaults(func=self._add_player)

        game = subcommands.add_parser('game')
        game.add_argument('team_a', type=str, nargs=2)
        game.add_argument('result', type=str,
                          choices=['beat', 'draw', 'lost'])
        game.add_argument('team_b', type=str, nargs=2)
        game.set_defaults(func=self._add_game)

        history = subcommands.add_parser('history')
        history.set_defaults(func=self._show_history)

        args = parser.parse_args(command)
        if args.h:

            return parser.format_help()
        else:
            return args.func(args)


class KickerPlayer:

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'Player: {}'.format(self.name)


class KickerGame:

    def __init__(self, command_words, players):
        self.command = command_words

        self.player_names = []
        self.player_names.append(command_words[0])
        self.player_names.append(command_words[1])
        self.player_names.append(command_words[3])
        self.player_names.append(command_words[4])

        if command_words[2] == u'beat':
            self.score_a = 2
        elif command_words[2] == u'draw':
            self.score_a = 1
        elif command_words[2] == u'lost':
            self.score_a = 0
        else:
            assert False, "beat|draw|lost is bad: {}".format(
                " ".join(command_words))
        self.score_b = 2 - self.score_a

        self.team_a = []
        self.team_b = []
        for p in self.player_names[0:2]:
            assert p in players, "Player not found: {}".format(p)
            self.team_a.append(players[p])
        for p in self.player_names[2:4]:
            assert p in players, "Player not found: {}".format(p)
            self.team_b.append(players[p])

    def __str__(self):
        return " ".join(self.command)


class KickerLadder:

    def process(self, players, games):
        pass


class BasicLadder(KickerLadder):

    def __init__(self):
        pass

    def add_game(self, game):
        for p in game.team_a + game.team_b:
            p.games += 1
        for p in game.team_a:
            p.rank += game.score_a - game.score_b
        for p in game.team_b:
            p.rank -= game.score_b - game.score_a

    def process(self, players, games):
        for p in players.values():
            p.rank = 0
            p.games = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            players.values(),
            key=lambda x: (x.rank, x.games),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "points", "games"))
        i = 1
        for player in ladder:
            ret.append((
                i,
                player.name,
                player.rank,
                player.games,
            ))
            i += 1
        return ret


class BasicScaledLadder(KickerLadder):

    def __init__(self):
        pass

    def add_game(self, game):
        for p in game.team_a + game.team_b:
            p.games += 1
        for p in game.team_a:
            p.rank += game.score_a - game.score_b
        for p in game.team_b:
            p.rank += game.score_b - game.score_a

    def process(self, players, games):
        for p in players.values():
            p.rank = 0
            p.games = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            players.values(),
            key=lambda x: (float(x.rank) / float(x.games), x.games),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "points/game"))
        i = 1
        for player in ladder:
            ret.append((
                i,
                player.name,
                float(player.rank) / float(player.games),
            ))
            i += 1
        return ret


class ArithmeticMean:

    def combine(self, ranks):
        return sum(ranks) * 0.5

    def uncombine(self, val):
        return val


class GeometricMean:

    def combine(self, ranks):
        return reduce(lambda a, b: a * b, ranks) ** (1.0 / len(ranks))

    def uncombine(self, val):
        return val


class HarmonicMean:

    def combine(self, ranks):
        return reduce(lambda a, b: 1.0 / (1.0 / a + 1.0 / b), ranks)

    def uncombine(self, val):
        return val


class ELOLadder(KickerLadder):

    def __init__(self, K=50, combiner=ArithmeticMean()):
        self.K = K
        self.combiner = combiner

    def add_game(self, game):
        """
        Do an ELO rank with made up stuff for the 2 player bit.
        ref: "https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
        """
        for p in game.team_a + game.team_b:
            p.games += 1

        r1 = self.combiner.combine([r.rank for r in game.team_a])
        r2 = self.combiner.combine([r.rank for r in game.team_b])
        R1 = 10 ** (r1 / 400)
        R2 = 10 ** (r2 / 400)
        E1 = R1 / (R1 + R2)
        E2 = R2 / (R1 + R2)
        total_score = game.score_a + game.score_b
        rd1 = self.K * (game.score_a * 1.0 / total_score - E1)
        rd2 = self.K * (game.score_b * 1.0 / total_score - E2)

        for p in game.team_a:
            p.rank += self.combiner.uncombine(rd1)
        for p in game.team_b:
            p.rank += self.combiner.uncombine(rd2)

    def process(self, players, games):
        for p in players.values():
            p.rank = 1000
            p.games = 0

        for g in games:
            self.add_game(g)

        ladder = sorted(
            players.values(),
            key=lambda x: (x.rank, x.games),
            reverse=True)

        ret = []
        ret.append(("rank", "name", "ELO", "games"))
        for i in range(len(ladder)):
            ret.append((
                i + 1,
                ladder[i].name,
                int(ladder[i].rank),
                ladder[i].games
            ))
        return ret


class TrueSkillLadder(KickerLadder):

    """
    ref:
    http://trueskill.org/
    http://blogs.technet.com/b/apg/archive/2008/06/16/trueskill-in-f.aspx
    http://www.moserware.com/2010/03/computing-your-skill.html
    https://github.com/moserware/Skills
    """

    def __init__(self, mu=25.0, sigma=25.0 / 3):
        self.mu = mu
        self.sigma = sigma

    def add_game(self, game):
        for p in game.team_a + game.team_b:
            p.games += 1
        trueskill.calculate_NvN(
            game.team_a, game.team_b, game.score_a, game.score_b)

    def process(self, players, games):
        for p in players.values():
            p.mu = self.mu
            p.sigma = self.sigma
            p.games = 0

        for g in games[:-1]:
            self.add_game(g)

        ladder_last = sorted(
            players.values(),
            key=lambda x: (x.mu - 1 * x.sigma),
            reverse=True)

        self.add_game(games[-1])

        ladder = sorted(
            players.values(),
            key=lambda x: (x.mu - 1 * x.sigma),
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


class KickerEvent:

    def processEvent(self, players, games):
        pass


class AddPlayerEvent(KickerEvent):

    def __init__(self, player):
        self.player = KickerPlayer(player)

    def processEvent(self, players, games):
        players[self.player.name] = self.player
        return 'added: ' + str(self.player)

    def to_json(self):
        ret = {}
        ret['type'] = 'AddPlayerEvent'
        ret['player'] = self.player.name
        return ret

    @staticmethod
    def from_json(the_json):
        assert the_json['type'] == 'AddPlayerEvent'
        return AddPlayerEvent(the_json['player'])


class AddGameEvent(KickerEvent):

    def __init__(self, command_words):
        self.command_words = command_words

    def processEvent(self, players, games):
        game = KickerGame(self.command_words, players)
        games.append(game)
        return 'added: ' + str(game)

    def to_json(self):
        ret = {}
        ret['type'] = 'AddGameEvent'
        ret['command'] = " ".join(self.command_words)
        return ret

    @staticmethod
    def from_json(the_json):
        assert the_json['type'] == 'AddGameEvent'
        return AddGameEvent(the_json['command'].split())

if __name__ == '__main__':
    k = KickerManager()
    # k.kicker_command(["-h"])
    # k.kicker_command(["ladder", "ELO", "60"])
    print "\n".join(k.kicker_command( ["ladder"]))
    # k.kicker_command( ["history"])
    # k.kicker_command(["ladder", "-h"])
    print "\n".join(k.kicker_command(["ladder", "ELO"]))
    k.write_index_html()
