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
        print trigger.nick, trigger.match.string
        text = trigger.group().split()
        bot.memory['kicker_manager'].kicker_command(bot, text)

except ImportError as e:
    print "could not import willie"

import json
import os
import shutil
import string

LOG_FILE = os.path.join(os.path.dirname(__file__), 'kicker.log')


def setup(bot):
    bot.memory['kicker_manager'] = KickerManager(bot)

def scaled_basic_ranker(players, score_a, score_b):
    for p in players:
        p.games += 1
        if p.rank is None:
            p.rank = 0
    for p in players[0:2]:
        p.rank = p.rank * (p.games - 1) + (score_a - score_b)
        p.rank /= p.games
    for p in players[2:4]:
        p.rank = p.rank * (p.games - 1) + (score_b - score_a)
        p.rank /= p.games

def basic_ranker(players, score_a, score_b):
    for p in players:
        p.games += 1
        if p.rank is None:
            p.rank = 0
    for p in players[0:2]:
        p.rank += score_a - score_b
    for p in players[2:4]:
        p.rank -= score_b - score_a

def ELO_with_K_Arith(K=50):

    def ELO_ranker(players, score_a, score_b):
        """
        Do an ELO rank with made up stuff for the 2 player bit.
        players is array of 4.
        score_a is for team of players[0:2]
        score_b is for team of players[2:4]
        ref: "https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
        """
        for p in players:
            p.games += 1
            if p.rank is None:
                p.rank = 1000

        r1 = (players[0].rank + players[1].rank) * 0.5
        r2 = (players[2].rank + players[3].rank) * 0.5
        R1 = 10 ** (r1 / 400)
        R2 = 10 ** (r2 / 400)
        E1 = R1 / (R1 + R2)
        E2 = R2 / (R1 + R2)
        rd1 = K * (score_a * 1.0 / (score_a + score_b) - E1)
        rd2 = K * (score_b * 1.0 / (score_a + score_b) - E2)

        players[0].rank += rd1
        players[1].rank += rd1
        players[2].rank += rd2
        players[3].rank += rd2

    return ELO_ranker

def ELO_with_K_Geo(K=50):

    def ELO_ranker(players, score_a, score_b):
        """
        Do an ELO rank with made up stuff for the 2 player bit.
        players is array of 4.
        score_a is for team of players[0:2]
        score_b is for team of players[2:4]
        ref: "https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
        """
        for p in players:
            p.games += 1
            if p.rank is None:
                p.rank = 1000

        r1 = (players[0].rank * players[1].rank) ** 0.5
        r2 = (players[2].rank * players[3].rank) ** 0.5
        R1 = 10 ** (r1 / 400)
        R2 = 10 ** (r2 / 400)
        E1 = R1 / (R1 + R2)
        E2 = R2 / (R1 + R2)
        rd1 = K * (score_a * 1.0 / (score_a + score_b) - E1)
        rd2 = K * (score_b * 1.0 / (score_a + score_b) - E2)

        players[0].rank += rd1
        players[1].rank += rd1
        players[2].rank += rd2
        players[3].rank += rd2

    return ELO_ranker

def ELO_with_K_Harmonic(K=50):

    def ELO_ranker(players, score_a, score_b):
        """
        Do an ELO rank with made up stuff for the 2 player bit.
        players is array of 4.
        score_a is for team of players[0:2]
        score_b is for team of players[2:4]
        ref: "https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
        """
        for p in players:
            p.games += 1
            if p.rank is None:
                p.rank = 1000

        r1 = 1/(1/players[0].rank + 1/players[0].games + 1/players[1].rank + 1/players[1].games)
        r2 = 1/(1/players[2].rank + 1/players[2].games + 1/players[3].rank + 1/players[3].games)
        R1 = 10 ** (r1 / 400)
        R2 = 10 ** (r2 / 400)
        E1 = R1 / (R1 + R2)
        E2 = R2 / (R1 + R2)
        rd1 = K * (score_a * 1.0 / (score_a + score_b) - E1)
        rd2 = K * (score_b * 1.0 / (score_a + score_b) - E2)

        players[0].rank += rd1
        players[1].rank += rd1
        players[2].rank += rd2
        players[3].rank += rd2

    return ELO_ranker

class KickerManager:

    def __init__(self, bot):
        self.players = {}
        self.games = []
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

    def _add_player(self, bot, command):
        for n in command:
            self._add_event(AddPlayerEvent(n), reply_bot=bot)
        self.save_to_log()

    def _add_game(self, bot, command):
        self._add_event(AddGameEvent(command), reply_bot=bot)
        self.save_to_log()

    def _pretty_print(self, bot, data_tuples):
    """
    This prints the tuples in nice whitespace aligned columns.
    And is hack.
    """
        # widths holds the longest strlen
        # in the list of tuples for that position
        widths = [0] * len(data_tuples[0])
        for i in range(len(widths)):
            widths[i] = 1 + len(str(max(data_tuples, key=lambda x: len(str(x[i])))[i]))
        for i in range(len(data_tuples))
            s = ""
            for word in data_tuples[i]:
                s += '{0:>{width}}'.format(w, width=widths[i])
            bot.say(s)




    def _show_ladder(self, bot, command):
        # bot.say(str(self.players))
        # bot.say(str(self.games))
        # bot.say(str(self.events))
        # elo_k = 50
        # ranker = ELO_with_K_Arith(K=elo_k)
        # if len(command) > 0:
        #     if command[0] == 'ELO':
        #         if len(command) > 1:
        #             elo_k = int(command[1])
        #         ranker = ELO_with_K_Arith(K=elo_k)
        #     elif command[0] == 'basic':
        #         ranker = basic_ranker
        #     elif command[0] == 'scaled':
        #         ranker = scaled_basic_ranker

        # for p in self.players.values():
        #     p.rank = None
        #     p.games = 0
        # for g in sorted(self.games.items()):
        #     g[1].process_game(self.players, ranker)

        # ladder = sorted(
        #     self.players.values(),
        #     key=lambda x: x.rank,
        #     reverse=True)
        # count = 1

        # bot.say("rank: name, value, games")
        # for p in ladder:
        #     bot.say(
        #         "{}: {}, {}, {}".format(
        #             count, p.name, int(
        #                 p.rank), p.games))
        #     count += 1

        ladder = BasicLadder()
        data_tuples = ladder.process(self.players, self.games)
        self._pretty_print(bot, data_tuples)

    def _show_history(self, bot, command):
        bot.say("games:")
        i = 1
        for g in games:
            bot.say("{}: {}".format(i, g))
            g += 1

    def kicker_command(self, bot, command):
        if command[1] == 'add':
            self._add_player(bot, command[2:])

        elif command[1] == 'game':
            self._add_game(bot, command[2:])

        elif command[1] == 'ladder':
            self._show_ladder(bot, command[2:])

        elif command[1] == 'history':
            self._show_history(bot, command[2:])

        else:
            bot.say('bad command')


class KickerPlayer:

    def __init__(self, name):
        self.name = name
        self.rank = 1000

    def __str__(self):
        return 'Player: {}, {}'.format(self.name, self.rank)


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
            assert False, "beat|draw|lost is bad\n{}".format(
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

    def add_game(self, team_a, team_b, score_a, score_b):
        pass

    def get_ladder(self):
        pass

class BasicLadder(KickerLadder):

    def __init__(self):
        pass

    def add_game(self, game):
        print game
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
            key=lambda x: x.rank,
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
    class Bot:
        def say(self, x):
            print x
    bot = Bot()
    k = KickerManager(bot)
    k.kicker_command(bot, ["", "ladder"])
