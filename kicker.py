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
            ladder
            history
        """
        print trigger.nick, trigger.match.string
        text = trigger.group().split()
        bot.memory['kicker_manager'].kicker_command(bot, text)

except ImportError as e:
    print "could not import willie"

import json
import os
import shutil

LOG_FILE = os.path.join(os.path.dirname(__file__), 'kicker.log')


def setup(bot):
    bot.memory['kicker_manager'] = KickerManager(bot)


def do_ranker(players, score_a, score_b):
    ELO_ranker(players, score_a, score_b)


def basic_ranker(players, score_a, score_b):
    for p in players[0:2]:
        players.rank += score_a - score_b
    for p in players[2:4]:
        players.rank -= score_b - score_a


def ELO_ranker(players, score_a, score_b):
    "https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
    K = 50

    r1 = (players[0].rank * players[1].rank) ** 0.5
    r2 = (players[2].rank * players[3].rank) ** 0.5
    R1 = 10 ** (r1 / 400)
    R2 = 10 ** (r2 / 400)
    E1 = R1 / (R1 + R2)
    E2 = R2 / (R1 + R2)
    rd1 = r1 + K * (score_a * 1.0 / (score_a + score_b) - E1)
    rd2 = r2 + K * (score_b * 1.0 / (score_a + score_b) - E2)

    # smart bin search way of doing it?
    # sqrt((a+d)(b+d)) = c
    # d(b+a+d)=c^2
    def cloj(a, b, c):
        return lambda d: (c ** 2 - a * b) - d * a - d * b - d * d

        def bin_s(func, g_min, g_max):
            ans = func((g_min - g_min) / 2)
            while(abs(ans) > 0.1):
                if ans > 0:
                    g_max = (g_min - g_min) / 2
                else:
                    g_min = (g_min - g_min) / 2
                ans = func((g_min - g_min) / 2)
            return ans

        print "cloj:", bin_s(cloj(players[0].rank, players[1].rank, rd1), 0, 2000)

    # Not quite accurate reversal of formula. Good enough?
    delta1 = (
        (rd1 ** 2 - players[0].rank * players[1].rank)) / (players[0].rank + players[1].rank)
    delta2 = (
        (rd2 ** 2 - players[2].rank * players[3].rank)) / (players[2].rank + players[3].rank)

    players[0].rank += delta1
    players[1].rank += delta1
    players[2].rank += delta2
    players[3].rank += delta2


class KickerManager:

    def __init__(self, bot):
        self.players = {}
        self.games = {}
        self.events = []
        self.bot = bot
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

    def _add_event(self, event, reply_bot=None):
        self.events.append(event)
        reply = self.events[-1].processEvent(self.players, self.games)
        print reply
        if reply_bot is not None:
            reply_bot.say(reply)

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

    def _add_player(self, name):
        self._add_event(AddPlayerEvent(name), reply_bot=True)
        self.save_to_log()

    def _add_game(self, command):
        self._add_event(AddGameEvent(command), reply_bot=True)
        self.save_to_log()

    def _show_ladder(self, bot):
        # bot.say(str(self.players))
        # bot.say(str(self.games))
        # bot.say(str(self.events))
        ladder = sorted(
            self.players.values(),
            key=lambda x: x.rank,
            reverse=True)
        count = 1
        for p in ladder:
            bot.say("{}: {}, {}".format(count, p.name, p.rank))
            count += 1

    def _show_history(self, bot):
        bot.say("games:")
        for g in sorted(self.games.items()):
            bot.say("{}: {}".format(g[0], str(g[1])))

    def kicker_command(self, bot, command):
        if command[1] == 'add':
            self._add_player(command[2])

        elif command[1] == 'game':
            self._add_game(command[2:])

        elif command[1] == 'ladder':
            self._show_ladder(bot)

        elif command[1] == 'history':
            self._show_history(bot)

        else:
            bot.say('bad command')


class KickerPlayer:

    def __init__(self, name):
        self.name = name
        self.rank = 1000

    def __str__(self):
        return 'Player: {}, {}'.format(self.name, self.rank)


class KickerGame:

    def __init__(self, command_words):
        self.command = command_words

        self.player_names = []
        self.player_names.append(command_words[0])
        self.player_names.append(command_words[1])
        self.player_names.append(command_words[3])
        self.player_names.append(command_words[4])

        if command_words[2] == u'beat':
            self.score = 2
        elif command_words[2] == u'draw':
            self.score = 1
        elif command_words[2] == u'lost':
            self.score = 0
        else:
            assert False, "beat|draw|lost bad\n{}".format(
                " ".join(command_words))

    def __str__(self):
        return " ".join(self.command)


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
        self.game = KickerGame(command_words)

    def processEvent(self, players, games):
        real_players = []
        for p in self.game.player_names:
            assert p in players, "Player not found: {}".format(p)
            real_players.append(players[p])

        do_ranker(real_players, self.game.score, 2 - self.game.score)

        games[len(games) + 1] = self.game
        return 'add game: ' + str(self.game)

    def to_json(self):
        ret = {}
        ret['type'] = 'AddGameEvent'
        ret['command'] = " ".join(self.command_words)
        return ret

    @staticmethod
    def from_json(the_json):
        assert the_json['type'] == 'AddGameEvent'
        return AddGameEvent(the_json['command'].split())
