# wrank
A ranking system for games.
python setup.py develop

Originally a ladder for kicker controlled by IRC, now cli and web frontends also.
Currently only supports 2v2 games, goal is to make it more general.

Data is tracked in a file kicker.log, this should be provided on command line in future. Fixing of bad data should be done by editing the log file directly, it should be straightforward.

# Sick Features
* ladder! 
** ELO or trueskill
* graphs!
* predict outcome of any game!
* suggest good future games!
** based on heuristics!
* history of games for any set of players!

# Frontends
IRC via sopel
web via web.py
cli
svg graphs
hipchat???

You will likely need to edit the frontends to make them work, they assume you are me.

# Ladders
A few different ladders created, ELO, basic(win/loss), win/loss scaled by number of games, trueskill. Trueskill is the most interesting and default. Trueskill code was adapted from Jeff Mosers article and c# code https://github.com/moserware/Skills.

To Come:
Configurable for different types of games
Proper setup.py and frontends that work off the shelf.
