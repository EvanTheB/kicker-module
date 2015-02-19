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
        self.games = []
        self.bot = bot

    def _add_player(self, name):
        self.players[name] = KickerPlayer(name)
        self.bot.say('added: ' + str(self.players[name]))

    def _add_game(self, command):
        self.games.append(KickerGame(command))
        self.bot.say('added: ' + str(self.games[-1]))

    def _show_ladder(self, bot):
        bot.say(str(self.players))
        bot.say(str(self.games))

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

class KickerGame:
    def __init__(self, commandString):
        self.command = commandString