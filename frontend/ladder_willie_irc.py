"""
willie IRC frontend for wrank.
Load this file in the willie modules directory.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))
import wrank

from willie.module import commands


@commands('kicker')
def kicker_command(bot, trigger):
    """
    Manage the kicker.
    Commands:
        add <player>
        game <player> <player> (beat)|(lost)|(draw) <player> <player>
        ladder [ranking system]
        history
    """
    text = trigger.group().split()[1:]
    ret = bot.memory['kicker_manager'].ladder_command(text)
    for l in ret:
        bot.say(l)


def setup(bot):
    bot.memory['kicker_manager'] = wrank.front.LadderManager("kicker.log")
