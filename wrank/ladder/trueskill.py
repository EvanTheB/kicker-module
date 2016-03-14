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
