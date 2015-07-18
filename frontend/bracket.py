
def bracket_greedy(players, potentials):
    # O(N) (already sorted so pff)
    left = list(players)
    chosen = []
    games = []
    while len(left) >= 4 and len(potentials) > 0:
        next_potential = potentials.pop()
        if len([p for t in next_potential[1] for p in t if p in chosen]) > 0:
            continue
        for p in [p for t in next_potential[1] for p in t]:
            chosen.append(p)
            left.remove(p)
        games.append(next_potential)
    return (
        sum([g[0] for g in games]),
        games
    )


def bracket_hard(players, potentials):
    # naive : O(N choose small#) ~ N^small ~1E16 for 18 players
    # pruning works fairly well
    def rec(remaining_players, remaining_games, best_potential, cur_potential):
        if len(remaining_players) < 4:
            return (0., [])

        best_found = None
        left_to_choose = len(remaining_players) / 4
        for i, cur_game in enumerate(remaining_games):
            cur_game_p = [p for t in cur_game[1] for p in t]

            if cur_game[0] * left_to_choose + cur_potential < best_potential:
                # cannot do better, prune the rest
                # print left_to_choose, len(remaining_games)-i, best_potential,
                # cur_potential, cur_game[0] * left_to_choose + cur_potential
                break
            if len([p for p in cur_game_p if p not in remaining_players]) > 0:
                continue

            new_remaining_players = [
                p for p in remaining_players if p not in cur_game_p]
            res = rec(new_remaining_players,
                      remaining_games[i + 1:],
                      best_potential,
                      cur_potential + cur_game[0])
            if res is not None and res[0] + cur_game[0] + cur_potential > best_potential:
                best_potential = res[0] + cur_game[0] + cur_potential
                best_found = (res[0] + cur_game[0], [cur_game] + res[1])
        if best_found is not None:
            return best_found
        else:
            return None

    return rec(players, potentials, 0., 0.)


if __name__ == '__main__':
    import wrank
    from wrank.wrank import HeuristicManager
    from wrank import backend
    from wrank.ladder import ladders

    k = wrank.LadderManager()

    data = backend.LadderData()
    players, games = data.get_players_games()

    pre_ladder = ladders.TrueSkillLadder()
    pre_data = pre_ladder.process(players, games)

    draws = HeuristicManager().get_heuristic(
        pre_ladder, players, games, "slow")


    all_games = backend.all_games(players, lambda x: True)
    print bracket_hard(players, sorted(draws.rate_all(all_games), key=lambda x: x[0], reverse=True))

    all_games = backend.all_games(players, lambda x: True)
    print bracket_greedy(players, sorted(draws.rate_all(all_games), key=lambda x: x[0]))
