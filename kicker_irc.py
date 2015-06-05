import sys
import os
sys.path.append(os.path.dirname(__file__))
import ladder

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
        ladder [ranking system]
        history
    """
    text = trigger.group().split()[1:]
    print text
    ret = bot.memory['kicker_manager'].kicker_command(text)
    for l in ret:
        bot.say(l)


def setup(bot):
    bot.memory['kicker_manager'] = ladder.kicker.KickerManager()

if __name__ == '__main__':
    print 'yep'