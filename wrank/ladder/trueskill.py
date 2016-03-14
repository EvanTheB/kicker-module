"""
    ref:
    http://trueskill.org/
    http://blogs.technet.com/b/apg/archive/2008/06/16/trueskill-in-f.aspx
    http://www.moserware.com/2010/03/computing-your-skill.html
    https://github.com/moserware/Skills

    My python conversion of moser's true skill thing.
    Only does 2 team games because the maths of the other is what
    what is a factor graph. Why...
"""

# <summary>
# Calculate_1v1s the new ratings for only two players.
# </summary>
# <remarks>
# When you only have two players, a lot of the math simplifies.
# The main purpose of this class
# is to show the bare minimum of what a TrueSkill implementation should have.
# </remarks>

# Kicker, these should go somewhere initty.
DRAW_PROBABILITY = 0.5
# beta is the variance in real performance.
BETA = 25.0 / 6
# this keeps sigma up, to allow for real skills to change over time
DYNAMICS_FACTOR = 25.0 / 300

import math
import numpy as np


def match_quality(team_a, team_b):
    mean_a = sum([p.mu for p in team_a])
    mean_b = sum([p.mu for p in team_b])
    mean_delta = mean_a - mean_b
    denom = (2 * BETA ** 2 + sum(
        [p.sigma ** 2 for p in team_a + team_b]))

    sqrt_part = (2 * BETA ** 2) / denom
    exp_part = -0.5 * (mean_delta) ** 2 / denom
    return math.sqrt(sqrt_part) * math.exp(exp_part)


def match_quality_hard(team_a, team_b):
    # Set up multivariate gaussians
    u = np.matrix([p.mu for p in team_a + team_b]).T
    summa = np.diagflat([p.sigma ** 2 for p in team_a + team_b])
    col = np.array([1] * len(team_a) + [-1] * len(team_b))
    A = np.matrix([col]).T

    common = BETA ** 2 * A.T * A + A.T * summa * A
    exp_part = -0.5 * u.T * A * np.linalg.inv(common) * A.T * u
    sqrt_part = np.linalg.det(BETA ** 2 * A.T * A) / np.linalg.det(common)
    return math.sqrt(sqrt_part) * math.exp(exp_part)


def chances(team_a, team_b):

    draw_margin = get_draw_margin_from_draw_probability(
        DRAW_PROBABILITY, BETA, len(team_a) + len(team_b))

    c = math.sqrt(sum([p.sigma ** 2 for p in team_a]) +
                  sum([p.sigma ** 2 for p in team_b]) +
                  len(team_a + team_b) * BETA ** 2)
    mean_a = sum([p.mu for p in team_a])
    mean_b = sum([p.mu for p in team_b])
    mean_delta = mean_a - mean_b

    mean_delta /= c
    draw_margin /= c
    p_win = gaussian_cumulative_to(mean_delta - abs(draw_margin))
    p_loss = gaussian_cumulative_to(-mean_delta - abs(draw_margin))

    p_draw = (gaussian_cumulative_to(abs(mean_delta) + abs(draw_margin))
              - gaussian_cumulative_to(abs(mean_delta) - abs(draw_margin)))

    return p_win, p_draw, p_loss


def calculate_match_quality(team_a, team_b):
    # We just use equation 4.1 found on page 8 of the TrueSkill 2006 paper:
    beta_squared = BETA ** 2

    # This is the square root part of the equation:
    sqrtPart = math.sqrt((4 * beta_squared) /
                         (4 * beta_squared +
                          sum([p.sigma ** 2 for p in team_a]) +
                          sum([p.sigma ** 2 for p in team_b])))
    # This is the exponent part of the equation:
    expPart = math.exp((-
                        1 *
                        (sum([p.mu for p in team_a]) -
                         sum([p.mu for p in team_b])) ** 2) /
                       (2 *
                        (4 *
                         beta_squared +
                         sum([p.sigma ** 2 for p in team_a]) +
                            sum([p.sigma ** 2 for p in team_b]))))
    return sqrtPart * expPart


def calculate_nvn(team_a, team_b, was_win):
    """
    Calculates new trueskills for a two team game.
    Scores are translated to win/loss/draw.
    Teams are lists of players with 'mu' and 'sigma'
    If it wasnt a win it was a draw.
    """
    draw_margin = get_draw_margin_from_draw_probability(
        DRAW_PROBABILITY, BETA, len(team_a) + len(team_b))

    c = math.sqrt(sum([p.sigma ** 2 for p in team_a]) +
                  sum([p.sigma ** 2 for p in team_b]) +
                  len(team_a + team_b) * BETA ** 2)
    skill_a = sum([p.mu for p in team_a])
    skill_b = sum([p.mu for p in team_b])

    # winner - loser
    if was_win:
        skill_delta_a = skill_a - skill_b
        skill_delta_b = skill_delta_a
    else:
        skill_delta_a = skill_a - skill_b
        skill_delta_b = skill_b - skill_a

    def update_team_ratings(team, mean_delta, is_draw, is_winner):
        """
        helper for doing the maths per team.
        """
        assert not (is_draw and is_winner)
        rank_multiplier = 1.0 if is_winner or is_draw else -1.0
        if not is_draw:
            v = v_exceeds_margin(mean_delta, draw_margin, c)
            w = w_exceeds_margin(mean_delta, draw_margin, c)
        else:
            v = v_within_margin(mean_delta, draw_margin, c)
            w = w_within_margin(mean_delta, draw_margin, c)

        for player in team:
            mean_multiplier = (player.sigma ** 2 + DYNAMICS_FACTOR ** 2) / c
            variance_with_dynamics = player.sigma ** 2 + DYNAMICS_FACTOR ** 2
            std_dev_multiplier = variance_with_dynamics / (c ** 2)
            # print mean_delta, is_draw, is_winner, player.mu, rank_multiplier,
            # mean_multiplier, v
            new_mean = player.mu + (rank_multiplier * mean_multiplier * v)
            new_std_dev = math.sqrt(
                variance_with_dynamics * (1 - w * std_dev_multiplier))

            player.mu = new_mean
            player.sigma = new_std_dev
    # print "game:"
    update_team_ratings(
        team_a, skill_delta_a, not was_win, was_win)
    update_team_ratings(
        team_b, skill_delta_b, not was_win, False)


def calculate_1v1(team_a, team_b, score_a, score_b):
    """
    Calculates new trueskills for a two player game.
    Scores are translated to win/loss/draw.
    players have 'mu' and 'sigma'
    """
    draw_margin = get_draw_margin_from_draw_probability(
        DRAW_PROBABILITY, BETA, 2)
    c = math.sqrt(team_a.sigma ** 2 +
                  team_b.sigma ** 2 +
                  2 * BETA ** 2)

    mean_delta = ((team_a.mu - team_b.mu) if score_a > score_b
                  else (team_b.mu - team_a.mu))

    def update_rating(team, mean_delta, was_draw, winner):
        """
        helper for doing the maths per team.
        """
        rank_multiplier = 1.0 if winner else -1.0
        if not was_draw:
            v = v_exceeds_margin(mean_delta, draw_margin, c)
            w = w_exceeds_margin(mean_delta, draw_margin, c)

        else:
            v = v_within_margin(mean_delta, draw_margin, c)
            w = w_within_margin(mean_delta, draw_margin, c)
            rank_multiplier = 1.0

        mean_multiplier = (team.sigma ** 2 + DYNAMICS_FACTOR ** 2) / c
        variance_with_dynamics = team.sigma ** 2 + DYNAMICS_FACTOR ** 2
        std_dev_multiplier = variance_with_dynamics / (c ** 2)
        new_mean = team.mu + (rank_multiplier * mean_multiplier * v)
        new_std_dev = math.sqrt(
            variance_with_dynamics * (1 - w * std_dev_multiplier))
        team.mu = new_mean
        team.sigma = new_std_dev

    update_rating(team_a, mean_delta, score_a == score_b, score_a > score_b)
    update_rating(team_b, mean_delta, score_a == score_b, score_b > score_a)


def v_exceeds_margin(team_performance_difference, draw_margin, c=1.0):
    """
    The V function for a win
    """

    team_performance_difference /= c
    draw_margin /= c

    denominator = gaussian_cumulative_to(
        team_performance_difference - draw_margin)
    # numerical instability happens
    if denominator < 1e-10:
        return -team_performance_difference + draw_margin
    return gaussian_at(team_performance_difference - draw_margin) / denominator


def w_exceeds_margin(team_performance_difference, draw_margin, c=1.0):
    """
    The W function for a win
    """
    team_performance_difference /= c
    draw_margin /= c

    denominator = gaussian_cumulative_to(
        team_performance_difference - draw_margin)
    if denominator < 1e-10:
        if team_performance_difference < 0.0:
            return 1.0
        return 0.0
    vWin = v_exceeds_margin(team_performance_difference, draw_margin)
    return vWin * (vWin + team_performance_difference - draw_margin)


def v_within_margin(team_performance_difference, draw_margin, c=1.0):
    """
    The V function for a draw
    """
    team_performance_difference /= c
    draw_margin /= c
    # print team_performance_difference, draw_margin

    abs_tpd = abs(team_performance_difference)
    denominator = (gaussian_cumulative_to(draw_margin - abs_tpd) -
                   gaussian_cumulative_to(-draw_margin - abs_tpd))
    if denominator < 2.222758749e-162:
        assert False
        if team_performance_difference < 0.0:

            return -team_performance_difference - draw_margin

        return -team_performance_difference + draw_margin

    numerator = (gaussian_at(-draw_margin - abs_tpd) -
                 gaussian_at(draw_margin - abs_tpd))
    if team_performance_difference < 0.0:

        return -numerator / denominator

    return numerator / denominator


def w_within_margin(team_performance_difference, draw_margin, c=1.0):
    """
    The W function for a draw
    """
    team_performance_difference /= c
    draw_margin /= c

    abs_tpd = abs(team_performance_difference)
    denominator = (gaussian_cumulative_to(draw_margin - abs_tpd) -
                   gaussian_cumulative_to(-draw_margin - abs_tpd))
    if denominator < 2.222758749e-162:

        return 1.0

    vt = v_within_margin(abs_tpd, draw_margin)
    return vt * vt + ((draw_margin - abs_tpd) * gaussian_at(draw_margin - abs_tpd) -
                      (-draw_margin - abs_tpd) * gaussian_at(-draw_margin - abs_tpd)) / denominator


def gaussian_at(x, mean=0.0, standard_dev=1.0):
    """
    gaussian function at x
    """
    # // See http://mathworld.wolfram.com/NormalDistribution.html
    # // 1 -(x-mean)^2 / (2*stdDev^2)
    # // P(x) = ------------------- * e
    # // stdDev * sqrt(2*pi)
    multiplier = 1.0 / (standard_dev * math.sqrt(2 * math.pi))
    exp_part = (-1.0 * (x - mean) ** 2 / (2 * (standard_dev ** 2)))
    result = multiplier * math.exp(exp_part)
    return result


def gaussian_cumulative_to(x, mean=0.0, standard_dev=1.0):
    """
    cumulative (error function) to x.
    """
    x = (x - mean) / standard_dev
    return 0.5 + 0.5 * math.erf(x / math.sqrt(2))


# def error_function_cumulative_to(x):
#     """
#     What the heck is this
#     """
# // Derived from page 265 of Numerical Recipes 3rd Edition
#     z = abs(x)
#     t = 2.0 / (2.0 + z)
#     ty = 4 * t - 2
#     coefficients = [
#         -1.3026537197817094, 6.4196979235649026e-1,
#         1.9476473204185836e-2, -9.561514786808631e-3, -9.46595344482036e-4,
#         3.66839497852761e-4, 4.2523324806907e-5, -2.0278578112534e-5,
#         -1.624290004647e-6, 1.303655835580e-6, 1.5626441722e-8, -
#         8.5238095915e-8,
#         6.529054439e-9, 5.059343495e-9, -9.91364156e-10, -2.27365122e-10,
#         9.6467911e-11, 2.394038e-12, -6.886027e-12, 8.94487e-13, 3.13092e-13,
#         -1.12708e-13, 3.81e-16, 7.106e-15, -
#         1.523e-15, -9.4e-17, 1.21e-16, -2.8e-17
#     ]
#     ncof = len(coefficients)
#     d = 0.0
#     dd = 0.0
#     for j in reversed(coefficients):
#         tmp = d
#         d = ty * d - dd + j
#         dd = tmp
#     ans = t * math.exp(-z * z + 0.5 * (coefficients[0] + ty * d) - dd)
#     return ans if x >= 0.0 else 2.0 - ans


def get_draw_margin_from_draw_probability(draw_probability, beta, n_players):
    """
    From the % chance of draw get the magic number
    """
    denom = beta * math.sqrt(n_players)

    hi = 100.
    lo = -100.

    while abs(hi - lo) > 0.00001:
        mid = (hi + lo) / 2
        dp = 2 * gaussian_cumulative_to(mid / denom) - 1
        if dp < draw_probability:
            lo = mid
        else:
            hi = mid
    return mid


# def gaussian_inverse_cumulative_to(x, mean=0.0, standard_dev=1.0):
#     """
#     This is weird
#     """
# // From numerical recipes, page 320
# return mean - math.sqrt(2) * standard_dev *
# inverse_error_function_cumulative_to(2 * x)


# def inverse_error_function_cumulative_to(p):
# // From page 265 of numerical recipes
#     if p >= 2.0:

#         return -100

#     if p <= 0.0:

#         return 100

#     pp = p if p < 1.0 else 2 - p
# // Initial guess
#     t = math.sqrt(-2 * math.log(pp / 2.0))
#     x = -0.70711 *
#         ((2.30753 + t * 0.27061) / (1.0 + t * (0.99229 + t * 0.04481)) - t)
#     for j in range(2):

#         err = error_function_cumulative_to(x) - pp
# // Halley
#         x += err / (1.12837916709551257 * math.exp(-(x * x)) - x * err)

#     return x if p < 1.0 else -x


def tester(a, b, a_s, b_s, message):
    calculate_1v1(a, b, a_s, b_s)
    print message
    print a
    print b
    print


def tester_team(a, b, a_s, b_s, message):
    calculate_NvN(a, b, a_s, b_s)
    print message
    print repr(a)
    print b
    print

if __name__ == "__main__":
    class Player():

        def __init__(self, mu=25.0, sigma=25.0 / 3):
            self.mu = float(mu)
            self.sigma = float(sigma)

        def __str__(self):
            return "{0.mu} {0.sigma}".format(self)

        def __repr__(self):
            return self.__str__()

    a = Player()
    b = Player()


# Draw
    tester(a, b, 1, 1, "draw")
# win
    tester(a, b, 2, 0, "win")
# win
    tester(a, b, 0, 2, "loss")

# High skill
    tester(Player(mu=35), Player(mu=15), 1, 1, "high skill draw")
    tester(Player(mu=35), Player(mu=15), 2, 0, "high skill win")
# High confidence
    tester(Player(sigma=1), Player(sigma=1), 1, 1, "high confidence draw")
    tester(Player(sigma=1), Player(sigma=1), 2, 0, "high confidence win")

# Test team
    a = [Player()] * 2 + [Player(mu=35)]
    b = [Player()] * 2 + [Player(mu=35)]
    tester_team(a, b, 1, 1, "team draw")
    tester_team(a, b, 2, 0, "team win")
    tester_team(a, b, 0, 2, "team loss")
