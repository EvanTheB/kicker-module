# coding=utf8
"""
ebenn, modified from rss.py
"""
from __future__ import unicode_literals

from willie.module import commands, interval
from willie.config import ConfigurationError
from willie.logger import get_logger

import json

def setup(bot):
    bot.memory['kicker_manager'] = KickerManager(bot)


@commands('kicker')
def kicker_command(bot, trigger):
    """Manage RSS feeds. For a list of commands, type: .rss help"""
    bot.memory['kicker_manager'].kicker_command(bot, trigger)


def do_ranker(players, score_a, score_b):
    ELO_ranker(players)


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
    rd1 = r1 + K * (score_a - E1)
    rd2 = r2 + K * (score_b - E2)

    # Not quite accurate reversal of formula. Good enough?
    delta1 = (
        rd1 ** 2 - players[0].rank * players[1].rank) / (players[0].rank + players[1].rank)
    delta2 = (
        rd2 ** 2 - players[2].rank * players[3].rank) / (players[2].rank + players[3].rank)

    players[0].rank += delta1
    players[1].rank += delta1
    players[2].rank += delta2
    players[3].rank += delta2


class KickerManager:

    def __init__(self, bot):
        self.players = {}
        self.games = {}
        self.bot = bot
        self.events = []
        with open('kicker.log', 'r') as log:
            kicker_log = json.load(log)
        self._load_from_log(kicker_log)

    def _load_from_log(log):
        pass

    def _add_event(self, event, print_reply=False):
        self.events.append(event)
        reply = self.events[-1].processEvent(self.players, self.games)
        # if print_reply:
        # self.bot.say(reply)

    def _add_player(self, name):
        self._add_event(AddPlayerEvent(name), print_reply=True)

    def _add_game(self, command):
        self._add_event(AddGameEvent(command), print_reply=True)

    def _show_ladder(self, bot):
        # bot.say(str(self.players))
        # bot.say(str(self.games))
        # bot.say(str(self.events))
        ladder = sorted(self.players.values(), key=lambda x: x.rank)
        ladder.reverse()
        count = 1
        for p in ladder:
            bot.say("{}: {}, {}".format(count, p.name, p.rank))
            count += 1

    def kicker_command(self, bot, trigger):
        text = trigger.group().split()
        print text
        if text[1] == 'add':
            self._add_player(text[2])

        elif text[1] == 'game':
            self._add_game(text[2:])

        elif text[1] == 'ladder':
            self._show_ladder(bot)

        else:
            bot.say('bad command')


class KickerPlayer:

    def __init__(self, name):
        self.name = name
        self.deleted = False
        self.rank = 1000

    def delete(self):
        self.deleted = True

    def __str__(self):
        return 'Player: {}, {}'.format(self.name, self.rank)


class KickerGame:
    def __init__(self, commandString):
        self.command = commandString

        self.players = []
        self.players.append(commandString[0])
        self.players.append(commandString[1])
        self.players.append(commandString[3])
        self.players.append(commandString[4])

        if commandString[2] == 'beat':
            self.score = 2
        elif commandString[2] == 'draw':
            self.score = 1
        elif commandString[2] == 'lost':
            self.score = 0
        else:
            print 'fail game init'

        self.deleted = False

    def delete(self):
        self.deleted = True

    def __str__(self):
        return 'Game:\n\t{}\n\t{}\n\tbeat\n\t{}\n\t{}'.format(
            str(
                self.players[0]), str(
                self.players[0]), str(
                self.players[0]), str(
                    self.players[0]))


class KickerEvent:

    def processEvent(self, players, games):
        pass


class AddPlayerEvent(KickerEvent):

    def __init__(self, player):
        self.player = KickerPlayer(player)

    def processEvent(self, players, games):
        players[self.player.name] = self.player
        return 'added: ' + str(self.player)


class DelPlayerEvent(KickerEvent):

    def __init__(self, player):
        self.player = player

    def processEvent(self, players, games):
        players[self.player].delete()
        return 'deleted: ' + str(self.player)


class AddGameEvent(KickerEvent):

    def __init__(self, command):
        self.command = command
        self.game = KickerGame(command)

    def processEvent(self, players, games):
        real_players = []
        for p in self.game.players:
            if p not in players:
                print p
                print players
                return 'fail'
            real_players.append(players[p])

        do_ranker(real_players, self.game.score, 2 - self.game.score)

        games[len(games) + 1] = self.game
        return 'add game: ' + str(self.game)


class DelGameEvent(KickerEvent):

    def __init__(self, number):
        self.number = number

    def processEvent(self, players, games):
        games[self.number].delete()
        return 'del game: ' + games[self.number]
