import wrank
import sys

if __name__ == '__main__':
    k = wrank.LadderManager("kicker.log")
    print "\n".join(k.ladder_command(sys.argv[1:]))