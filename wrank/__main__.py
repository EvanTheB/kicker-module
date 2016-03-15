from wrank.front import LadderManager
import sys

if __name__ == '__main__':
    k = LadderManager(sys.argv[1])
    print "\n".join(k.ladder_command(sys.argv[2:]))

