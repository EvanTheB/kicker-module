# kicker-module
willie module for a kicker ladder with ELO rankings n stuff.

Data is tracked in a file kicker.log, which is backed up to kicker.log_bak on read but still occasionally corrupted when I am dumb. 
Current fixing of bad data should be done by editing the log file directly. 

use with .kicker -h
A few different ladders running right now, ELO, basic(win/loss), trueskill.

To Come:
I would like to add ladder movements to the display
graphing comparisons of the various ladders and how they differ in their estimates.
Configurable for different types of games
Fix data from IRC interface
Web interface

