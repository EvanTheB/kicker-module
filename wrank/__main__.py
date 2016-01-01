import wrank.control
import sys

if __name__ == '__main__':
    k = wrank.control.LadderManager("kicker.log")
    print "\n".join(k.ladder_command(sys.argv[1:]))
