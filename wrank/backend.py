import os
import json
import copy
import fcntl
import itertools
import time

# without filter there are (N choose 4) * 3 ~ N!


def all_games(players, game_filter):
    seen_games = set()
    for team_a in itertools.combinations(players.keys(), 2):
        for team_b in itertools.combinations(players.keys(), 2):
            if team_a + team_b in seen_games \
                    or team_b + team_a in seen_games \
                    or len([True for p in team_b if p in team_a]) > 0:
                continue
            seen_games.add(team_a + team_b)
            if game_filter(team_a + team_b):
                yield team_a, team_b


class LockFile(object):

    def __init__(self, file_obj):
        self._file_obj = file_obj

    def __enter__(self):
        fcntl.lockf(self._file_obj, fcntl.LOCK_EX)  # | fcntl.LOCK_NB)
        return None

    def __exit__(self, t_type, value, traceback):
        fcntl.lockf(self._file_obj, fcntl.LOCK_UN)
        return False


def init_data_file(filename):
    to_save = {}
    to_save['events'] = []
    with open(filename, 'w') as fd:
        json.dump(
            to_save,
            fd,
            sort_keys=True,
            indent=4,
            separators=(',', ': '))


class LadderData(object):

    def __init__(self, log_file):
        if not os.path.exists(log_file):
            raise ValueError("log file not found:{}".format(log_file))

        self.players = {}
        self.games = []
        self.events = []
        self.log_file = log_file

    def _load_from_json(self, log_fp):
        json_log = json.load(log_fp)
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

    def _save_to_log(self, log_fp):
        to_save = {}
        to_save['events'] = []
        for e in self.events:
            to_save['events'].append(e.to_json())
        json.dump(
            to_save,
            log_fp,
            sort_keys=True,
            indent=4,
            separators=(',', ': '))

    def _add_event(self, event):
        ret = event.process(self.players, self.games)
        self.events.append(event)
        return ret

    def get_players_games(self):
        with open(self.log_file, 'r+') as log:
            with LockFile(log):
                self._load_from_json(log)

        return copy.deepcopy(dict(self.players)), copy.deepcopy(list(self.games))

    def add_player(self, name):
        with open(self.log_file, 'r+') as log:
            with LockFile(log):
                self._load_from_json(log)
                event = AddPlayerEvent(name, time.time())
                ret = event.process(self.players, self.games)
                self.events.append(event)
                log.seek(0)
                self._save_to_log(log)

        return ret

    def add_game(self, command_words):
        with open(self.log_file, 'r+') as log:
            with LockFile(log):
                self._load_from_json(log)
                event = AddGameEvent(command_words, time.time())
                ret = event.process(self.players, self.games)
                self.events.append(event)
                log.seek(0)
                self._save_to_log(log)

        return ret


class LadderPlayer(object):

    def __init__(self, name, create_time):
        assert name == str(name)
        self.name = name
        self.games = []
        self.create_time = create_time

    def __str__(self):
        return 'Player: {}'.format(self.name)


class AddPlayerEvent(object):

    def __init__(self, name, create_time):
        assert name not in ['beat', 'draw', 'lost', 'cake']
        self.name = name
        self.create_time = create_time

    def process(self, players, games):
        assert self.name not in players
        players[self.name] = LadderPlayer(self.name, self.create_time)
        return 'added: ' + str(players[self.name])

    def to_json(self):
        ret = {}
        ret['type'] = 'AddPlayerEvent'
        ret['player'] = self.name
        ret['time'] = self.create_time
        return ret

    @staticmethod
    def from_json(the_json):
        assert the_json['type'] == 'AddPlayerEvent'
        return AddPlayerEvent(the_json['player'], the_json['time'])


class LadderGame(object):

    def __init__(self, command_words, players, create_time):
        self.command_words = command_words
        self.create_time = create_time

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

    def __init__(self, command_words, create_time):
        self.command_words = command_words
        self.create_time = create_time

    def process(self, players, games):
        game = LadderGame(self.command_words, players, self.create_time)
        games.append(game)
        return 'added: ' + str(game)

    def to_json(self):
        ret = {}
        ret['type'] = 'AddGameEvent'
        ret['command'] = " ".join(self.command_words)
        ret['time'] = self.create_time
        return ret

    @staticmethod
    def from_json(the_json):
        assert the_json['type'] == 'AddGameEvent'
        return AddGameEvent(the_json['command'].split(), the_json['time'])

if __name__ == '__main__':
    import random
    import time

    k = LadderData(os.path.join(os.path.dirname(__file__), "..", "kicker.log"))
    # test concurrent log writes
    # thread = str(random.randint(0, 100))
    # print thread
    # for x in range(100):
    #     time.sleep(0.01)
    #     k.add_player(thread + '_' + str(x))
    p, g = k.get_players_games()
    print len(p)
    print len(list(all_games(p, lambda x: True)))
