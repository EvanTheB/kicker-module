# coding=utf8
"""
ebenn, modified from rss.py
"""
from __future__ import unicode_literals

from willie.module import commands, interval
from willie.config import ConfigurationError
from willie.logger import get_logger

def setup(bot):
    bot.memory['kicker_manager'] = KickerManager(bot)

@commands('kicker')
def kicker_command(bot, trigger):
    """Manage RSS feeds. For a list of commands, type: .rss help"""
    bot.memory['kicker_manager'].kicker_command(bot, trigger)

def do_ranker(players):
	ELO_ranker(players)

def basic_ranker(players):
	for p in players[0:2]:
		players.rank += 1
	for p in players[2:4]
		players.rank -= 1

def ELO_ranker(players):
	"https://metinmediamath.wordpress.com/2013/11/27/how-to-calculate-the-elo-rating-including-example/"
	K = 50

	r1 = (players[0].rank * players[1].rank) ** 0.5
	r2 = (players[2].rank * players[3].rank) ** 0.5
	R1 = 10 ** (r1/400)
	R2 = 10 ** (r2/400)
	E1 = R1 / (R1 + R2)
	E2 = R2 / (R1 + R2)
	rd1 = r1 + K * (1 - E1)
	rd2 = r2 + K * (0 - E2)

	delta1 = (rd1 ** 2 - players[0].rank * players[1].rank) / (players[0].rank + players[1].rank)
	delta2 = (rd2 ** 2 - players[2].rank * players[3].rank) / (players[2].rank + players[3].rank)

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

    def _add_event(self, event, print_reply=False):
    	self.events.append(event)
        reply = self.events[-1].processEvent(players, games)
        if print_reply:
        	self.bot.say(reply)

    def _add_player(self, name):
        self._add_event(AddPlayerEvent(name), print_reply=True)

    def _add_game(self, command):
        self._add_event(AddGameEvent(command), print_reply=True)

    def _show_ladder(self, bot):
        bot.say(str(self.players))
        bot.say(str(self.games))
        bot.say(str(self.events))
        ladder = sorted(self.players, key=lambda x: x.rank)
        count = 1
        for p in ladder:
        	bot.say("{}: {}, {}".format(count++, p.name, p.rank))

    def kicker_command(self, bot, trigger):
        text = trigger.group().split()
        print text
        if text[1] == 'add':
            self._add_player(text[2])

        elif text[1] == 'game':
            self._add_game(KickerGame(text[1:]))

        elif text[1] == 'ladder':
            self._show_ladder(bot)

        else:
            bot.say('bad command')


class KickerPlayer:
    def __init__(self, name):
        self.name = name
        self.deleted = False
        self.rank = 1000

    def delete():
    	self.deleted = True


class KickerGame:
    def __init__(self, commandString):
        self.command = commandString

        self.players = []
        self.players.append(commandString[0])
        self.players.append(commandString[1])
        self.players.append(commandString[3])
        self.players.append(commandString[4])

        self.deleted = False

    def delete():
    	self.deleted = True

class KickerEvent:
	def processEvent(self, players, games):
		pass

class AddPlayerEvent(KickerEvent):
	def __init__(self, player):
		self.player = player

	def processEvent(self, players, games):
		players[self.player] = KickerPlayer(name)
		return 'added: ' + kwargs['player']

class DelPlayerEvent(KickerEvent):
	def __init__(self, player):
		self.player = player

	def processEvent(self, players, games):
		players[self.player].delete()
		return 'deleted: ' + kwargs['player']

class AddGameEvent(KickerEvent):
	def __init__(self, command):
		self.command = command
		self.game = KickerGame(command)

	def processEvent(self, players, games):
		real_players = []
		for p in self.game.players:
			if p not in players:
				return 'fail'
			real_players.append(players[p])

		do_ranker(real_players)

		games.KickerGame[len(self.games)+1] = self.game
		return 'add game: ' + self.game)

class DelGameEvent(KickerEvent):
	def __init__(self, number):
		self.number = number

	def processEvent(self, players, games):
		games[number].delete()
		return 'del game: ' + games[number]


