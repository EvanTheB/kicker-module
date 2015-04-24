import os
import shutil
import json
import copy

LOG_FILE = os.path.join(os.path.dirname(__file__), 'kicker.log')

def cross_reference(players, games):
    for p in players:
        players[p].games = []
    for g in games:
        g.team_a_players = []
        g.team_b_players = []
        for p in g.team_a:
            players[p].games.append(g)
            g.team_a_players.append(players[p])
        for p in g.team_b:
            players[p].games.append(g)
            g.team_b_players.append(players[p])

class KickerData(object):

    def __init__(self):
        self.players = {}
        self.games = []
        self.events = []

        self._load_from_log(LOG_FILE)

    def _load_from_log(self, filename):
        with open(filename, 'r') as log:
            json_log = json.load(log)

        # we backup only if it was valid json.
        # (else we would nuke the backup...)
        shutil.copyfile(filename, filename + '_backup')
        events = json_log['events']
        for e in events:
            if e['type'] == "AddPlayerEvent":
                self._add_event(AddPlayerEvent.from_json(e))
            elif e['type'] == "AddGameEvent":
                self._add_event(AddGameEvent.from_json(e))
            else:
                assert False, "failed to load event: " + str(e)

    def save_to_log(self, filename=LOG_FILE):
        to_save = {}
        to_save['events'] = []
        for e in self.events:
            to_save['events'].append(e.to_json())
        with open(filename, 'w') as log:
            json.dump(
                to_save,
                log,
                sort_keys=True,
                indent=4,
                separators=(',', ': '))

    def _add_event(self, event):
        ret = event.process(self.players, self.games)
        self.events.append(event)
        return ret

    def get_players(self):
        return dict(self.players)

    def get_games(self):
        return list(self.games)

    def add_player(self, name):
        return self._add_event(AddPlayerEvent(name))

    def add_game(self, command_words):
        return self._add_event(AddGameEvent(command_words))



class KickerPlayer(object):

    def __init__(self, name):
        assert name == str(name)
        self.name = name

    def __str__(self):
        return 'Player: {}'.format(self.name)


class AddPlayerEvent(object):

    def __init__(self, name):
        assert name not in ['beat', 'draw', 'lost', 'cake']
        self.name = name

    def process(self, players, games):
        assert self.name not in players
        players[self.name] = KickerPlayer(self.name)
        return 'added: ' + str(players[self.name])

    def to_json(self):
        ret = {}
        ret['type'] = 'AddPlayerEvent'
        ret['player'] = self.name
        return ret

    @staticmethod
    def from_json(the_json):
        assert the_json['type'] == 'AddPlayerEvent'
        return AddPlayerEvent(the_json['player'])


class KickerGame(object):

    def __init__(self, command_words, players):
        self.command_words = command_words

        if command_words[2] == u'beat':
            self.score_a = 2
        elif command_words[2] == u'draw':
            self.score_a = 1
        elif command_words[2] == u'lost':
            self.score_a = 0
        else:
            assert False, "must be beat|draw|lost: {}".format(
                " ".join(command_words))
        self.score_b = 2 - self.score_a

        self.team_a = command_words[0:2]
        self.team_b = command_words[3:5]

        for p in self.team_a + self.team_b:
            assert p in players, "Player not found: {}".format(p)

    def __str__(self):
        return "Game: " + " ".join(self.command_words)


class AddGameEvent(object):

    def __init__(self, command_words):
        self.command_words = command_words

    def process(self, players, games):
        game = KickerGame(self.command_words, players)
        games.append(game)
        return 'added: ' + str(game)

    def to_json(self):
        ret = {}
        ret['type'] = 'AddGameEvent'
        ret['command'] = " ".join(self.command_words)
        return ret

    @staticmethod
    def from_json(the_json):
        assert the_json['type'] == 'AddGameEvent'
        return AddGameEvent(the_json['command'].split())
