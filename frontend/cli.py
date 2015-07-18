"""
Command line wrapper for wrank. This should be __main__
"""

import wrank

import sys

if __name__ == '__main__':
    k = wrank.LadderManager("kicker.log")
    if len(sys.argv) > 1:
        "\n".join(k.ladder_command(sys.argv[1:]))
    else:
        print "\n".join(k.ladder_command(["ladder", "basic"]))
        # print "\n".join(k.ladder_command(["ladder", "scaled"]))
        # print "\n".join(k.ladder_command(["ladder", "ELO"]))
        print "\n".join(k.ladder_command(["ladder"]))

        print "\n".join(k.ladder_command(["history"]))

        print "\n".join(k.ladder_command(["whowins", "nick", "chris", "evan",
                                          "andy"]))

        print "\n".join(k.ladder_command(["next", "--heuristic", "class_warfare", "celine", "evan", "chris", "william", "nick"]))
        print "\n".join(k.ladder_command(["next", "celine", "evan", "chris"]))
        print "\n".join(k.ladder_command(["next", "--heuristic", "close_game", "evan"]))
        print "\n".join(k.ladder_command(["next"]))

        # print "\n".join(k.ladder_command(["add", "newplayer"]))
        # print "\n".join(k.ladder_command(["game", "newplayer", "newplayer",
        # "beat", "newplayer", "newplayer"]))

        # print k.write_index_html()
        print "\n".join(k.ladder_command(["next", "-h"]))
        print "\n".join(k.ladder_command(["wrong"]))

