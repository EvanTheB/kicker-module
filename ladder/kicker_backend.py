import os
import json
import copy
import fcntl

LOG_FILE = os.path.join(os.path.dirname(__file__), 'kicker.log')


class LockFile(object):
    def __init__(self, file_obj):
        self._file_obj = file_obj
    def __enter__(self):
        fcntl.lockf(self._file_obj, fcntl.LOCK_EX)# | fcntl.LOCK_NB)
        return None
    def __exit__(self, t_type, value, traceback):
        fcntl.lockf(self._file_obj, fcntl.LOCK_UN)
        return False

class KickerData(object):

    def __init__(self):
        self.players = {}
        self.games = []
        self.events = []

    def _load_from_json(self, log_file):
        json_log = json.load(log_file)
        self.players = {}
        self.games = []
        self.events = []
        events = json_log['events']
        for e in events:
            if e['type'] == "AddPlayerEvent":
                self._add_event(AddPlayerEvent.from_json(e))
            elif e['type'] == "AddGameEvent":
                self._add_event(AddGameEvent.from_json(e))
            else:
                assert False, "failed to load event: " + str(e)

    def _save_to_log(self, log_file):
        to_save = {}
        to_save['events'] = []
        for e in self.events:
            to_save['events'].append(e.to_json())
        json.dump(
            to_save,
            log_file,
            sort_keys=True,
            indent=4,
            separators=(',', ': '))

    def _add_event(self, event):
        ret = event.process(self.players, self.games)
        self.events.append(event)
        return ret

    def get_players_games(self):
        with open(LOG_FILE, 'r+') as log:
            with LockFile(log):
                self._load_from_json(log)

        return copy.deepcopy(dict(self.players)), copy.deepcopy(list(self.games))

    def add_player(self, name):
        with open(LOG_FILE, 'r+') as log:
            with LockFile(log):
                self._load_from_json(log)
                event = AddPlayerEvent(name)
                ret = event.process(self.players, self.games)
                self.events.append(event)
                log.seek(0)
                self._save_to_log(log)

        return ret

    def add_game(self, command_words):
        with open(LOG_FILE, 'r+') as log:
            with LockFile(log):
                self._load_from_json(log)
                event = AddGameEvent(command_words)
                ret = event.process(self.players, self.games)
                self.events.append(event)
                log.seek(0)
                self._save_to_log(log)

        return ret


class KickerPlayer(object):

    def __init__(self, name):
        assert name == str(name)
        self.name = name
        self.games = []

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
            players[p].games.append(self)
        self.team_a_players = [players[p] for p in self.team_a]
        self.team_b_players = [players[p] for p in self.team_b]

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

if __name__ == '__main__':
    import random
    import time

    k = KickerData()
    # test concurrent log writes
    thread = str(random.randint(0, 100))
    print thread
    for x in range(100):
        time.sleep(0.01)
        k.add_player(thread + '_' + str(x))
