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

    def delete():
    	self.deleted = True


class KickerGame:
    def __init__(self, commandString):
        self.command = commandString
        self.deleted = False

    def delete():
    	self.deleted = True

class KickerEvent:
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

	def processEvent(self, players, games, **kwargs):
		toAdd = KickerGame(self.command)
		games.KickerGame[len(self.games)+1] = toAdd
		return 'add game: ' + toAdd)

class DelGameEvent(KickerEvent):
	def __init__(self, number):
		self.number = number

	def processEvent(self, players, games):
		games[number].delete()
		return 'del game: ' + games[number]


