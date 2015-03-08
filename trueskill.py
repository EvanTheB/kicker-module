"""
    ref:
    http://trueskill.org/
    http://blogs.technet.com/b/apg/archive/2008/06/16/trueskill-in-f.aspx
    http://www.moserware.com/2010/03/computing-your-skill.html
    https://github.com/moserware/Skills

    My python conversion of moser's true skill thing.
"""

#  <summary>
# /// Calculate_1v1s the new ratings for only two players.
# /// </summary>
# /// <remarks>
# /// When you only have two players, a lot of the math simplifies. The main purpose of this class
# /// is to show the bare minimum of what a TrueSkill implementation should have.
# /// </remarks>

DRAW_PROBABILITY = 0.5
BETA = 25.0 / 6
DYNAMICS_FACTOR = 25.0 / 300
import math

def calculate_NvN(team_a, team_b, score_a, score_b):
    drawMargin = GetDrawMarginFromDrawProbability(DRAW_PROBABILITY, BETA)

    c = math.sqrt(sum([p.sigma**2 for p in team_a]) +
                  sum([p.sigma**2 for p in team_b]) +
                  len(team_a + team_b) * BETA ** 2)
    mean_a = sum([p.mu for p in team_a])
    mean_b = sum([p.mu for p in team_b])
    meanDelta = mean_a - mean_b

    def update_team_ratings(team, mean_delta, was_draw, winner):
        rankMultiplier = 1.0 if winner else -1.0
        if not was_draw:
            v = VExceedsMargin(mean_delta, drawMargin, c)
            w = WExceedsMargin(mean_delta, drawMargin, c)

        else:
            v = VWithinMargin(mean_delta, drawMargin, c)
            w = WWithinMargin(mean_delta, drawMargin, c)
            rankMultiplier = 1.0

        for p in team:
            meanMultiplier = (p.sigma ** 2 + DYNAMICS_FACTOR ** 2) / c
            varianceWithDynamics = p.sigma ** 2 + DYNAMICS_FACTOR ** 2
            stdDevMultiplier = varianceWithDynamics / (c ** 2)

            newMean = p.mu + (rankMultiplier * meanMultiplier * v)
            newStdDev = math.sqrt(
                varianceWithDynamics * (1 - w * stdDevMultiplier))

            p.mu = newMean
            p.sigma = newStdDev

    update_team_ratings(team_a,  meanDelta, score_a == score_b, score_a > score_b)
    update_team_ratings(team_b, -meanDelta, score_a == score_b, score_b > score_a)

def calculate_1v1(team_a, team_b, score_a, score_b):
    drawMargin = GetDrawMarginFromDrawProbability(DRAW_PROBABILITY, BETA)
    c = math.sqrt(team_a.sigma ** 2 +
                  team_b.sigma ** 2 +
                  2 * BETA ** 2)

    meanDelta = team_a.mu - team_b.mu

    def update_rating(team, mean_delta, was_draw, winner):
        rankMultiplier = 1.0 if winner else -1.0
        if not was_draw:
            v = VExceedsMargin(mean_delta, drawMargin, c)
            w = WExceedsMargin(mean_delta, drawMargin, c)

        else:
            v = VWithinMargin(mean_delta, drawMargin, c)
            w = WWithinMargin(mean_delta, drawMargin, c)
            rankMultiplier = 1.0

        meanMultiplier = (team.sigma ** 2 + DYNAMICS_FACTOR ** 2) / c
        varianceWithDynamics = team.sigma ** 2 + DYNAMICS_FACTOR ** 2
        stdDevMultiplier = varianceWithDynamics / (c ** 2)
        newMean = team.mu + (rankMultiplier * meanMultiplier * v)
        newStdDev = math.sqrt(
            varianceWithDynamics * (1 - w * stdDevMultiplier))
        team.mu = newMean
        team.sigma = newStdDev

    update_rating(team_a,  meanDelta, score_a == score_b, score_a > score_b)
    update_rating(team_b, -meanDelta, score_a == score_b, score_b > score_a)


def VExceedsMargin(teamPerformanceDifference, drawMargin, c=1.0):
    teamPerformanceDifference /= c
    drawMargin /= c
    denominator = GaussianCumulativeTo(teamPerformanceDifference - drawMargin)
    if (denominator < 2.222758749e-162):
        return -teamPerformanceDifference + drawMargin
    return GaussianAt(teamPerformanceDifference - drawMargin) / denominator


def WExceedsMargin(teamPerformanceDifference, drawMargin, c=1.0):
    teamPerformanceDifference /= c
    drawMargin /= c

    denominator = GaussianCumulativeTo(teamPerformanceDifference - drawMargin)
    if (denominator < 2.222758749e-162):
        if (teamPerformanceDifference < 0.0):
            return 1.0
        return 0.0
    vWin = VExceedsMargin(teamPerformanceDifference, drawMargin)
    return vWin * (vWin + teamPerformanceDifference - drawMargin)


def VWithinMargin(teamPerformanceDifference, drawMargin, c=1.0):
    teamPerformanceDifference /= c
    drawMargin /= c

    teamPerformanceDifferenceAbsoluteValue = abs(teamPerformanceDifference)
    denominator = GaussianCumulativeTo(drawMargin - teamPerformanceDifferenceAbsoluteValue) - \
        GaussianCumulativeTo(-drawMargin -
                             teamPerformanceDifferenceAbsoluteValue)
    if (denominator < 2.222758749e-162):

        if (teamPerformanceDifference < 0.0):

            return -teamPerformanceDifference - drawMargin

        return -teamPerformanceDifference + drawMargin

    numerator = GaussianAt(-drawMargin - teamPerformanceDifferenceAbsoluteValue) - \
        GaussianAt(drawMargin - teamPerformanceDifferenceAbsoluteValue)
    if (teamPerformanceDifference < 0.0):

        return -numerator / denominator

    return numerator / denominator


def WWithinMargin(teamPerformanceDifference, drawMargin, c=1.0):
    teamPerformanceDifference /= c
    drawMargin /= c

    teamPerformanceDifferenceAbsoluteValue = abs(teamPerformanceDifference)
    denominator = GaussianCumulativeTo(drawMargin - teamPerformanceDifferenceAbsoluteValue) - \
        GaussianCumulativeTo(-drawMargin -
                             teamPerformanceDifferenceAbsoluteValue)
    if (denominator < 2.222758749e-162):

        return 1.0

    vt = VWithinMargin(teamPerformanceDifferenceAbsoluteValue, drawMargin)
    return vt * vt + ((drawMargin - teamPerformanceDifferenceAbsoluteValue) * GaussianAt(drawMargin - teamPerformanceDifferenceAbsoluteValue) - (-drawMargin - teamPerformanceDifferenceAbsoluteValue) * GaussianAt(-drawMargin - teamPerformanceDifferenceAbsoluteValue)) / denominator


def GaussianAt(x, mean=0.0, standardDeviation=1.0):

    # // See http://mathworld.wolfram.com/NormalDistribution.html
    # // 1 -(x-mean)^2 / (2*stdDev^2)
    # // P(x) = ------------------- * e
    # // stdDev * sqrt(2*pi)
    multiplier = 1.0 / (standardDeviation * (2 * math.pi) ** 0.5)
    expPart = math.exp(
        (-1.0 * math.pow(x - mean, 2.0)) / (2 * (standardDeviation ** 2)))
    result = multiplier * expPart
    return result


def GaussianCumulativeTo(x, mean=0.0, standardDeviation=1.0):

    return 0.5 + 0.5 * math.erf(x / math.sqrt(2))


def ErrorFunctionCumulativeTo(x):
    # // Derived from page 265 of Numerical Recipes 3rd Edition
    z = abs(x)
    t = 2.0 / (2.0 + z)
    ty = 4 * t - 2
    coefficients = [
        -1.3026537197817094, 6.4196979235649026e-1,
        1.9476473204185836e-2, -9.561514786808631e-3, -9.46595344482036e-4,
        3.66839497852761e-4, 4.2523324806907e-5, -2.0278578112534e-5,
        -1.624290004647e-6, 1.303655835580e-6, 1.5626441722e-8, -
        8.5238095915e-8,
        6.529054439e-9, 5.059343495e-9, -9.91364156e-10, -2.27365122e-10,
        9.6467911e-11, 2.394038e-12, -6.886027e-12, 8.94487e-13, 3.13092e-13,
        -1.12708e-13, 3.81e-16, 7.106e-15, -
        1.523e-15, -9.4e-17, 1.21e-16, -2.8e-17
    ]
    ncof = len(coefficients)
    d = 0.0
    dd = 0.0
    for j in reversed(coefficients):
        tmp = d
        d = ty * d - dd + j
        dd = tmp
    ans = t * math.exp(-z * z + 0.5 * (coefficients[0] + ty * d) - dd)
    return ans if x >= 0.0 else 2.0 - ans


def GetDrawMarginFromDrawProbability(drawProbability, beta):

    # // Derived from TrueSkill technical report (MSR-TR-2006-80), page 6
    # // draw probability = 2 * CDF(margin/(sqrt(n1+n2)*beta)) -1
    # // implies
    # //
    # // margin = inversecdf((draw probability + 1)/2) * sqrt(n1+n2) * beta
    # // n1 and n2 are the number of players on each team
    margin = GaussianInverseCumulativeTo(
        .5 * (drawProbability + 1), 0, 1) * math.sqrt(1 + 1) * beta
    return margin


def GaussianInverseCumulativeTo(x, mean=0.0, standardDeviation=1.0):

    # // From numerical recipes, page 320
    return mean - math.sqrt(2) * standardDeviation * InverseErrorFunctionCumulativeTo(2 * x)


def InverseErrorFunctionCumulativeTo(p):
    # // From page 265 of numerical recipes
    if (p >= 2.0):

        return -100

    if (p <= 0.0):

        return 100

    pp = p if p < 1.0 else 2 - p
    # // Initial guess
    t = math.sqrt(-2 * math.log(pp / 2.0))
    x = -0.70711 * \
        ((2.30753 + t * 0.27061) / (1.0 + t * (0.99229 + t * 0.04481)) - t)
    for j in range(2):

        err = ErrorFunctionCumulativeTo(x) - pp
        # // Halley
        x += err / (1.12837916709551257 * math.exp(-(x * x)) - x * err)

    return x if p < 1.0 else -x

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
    class player():
        def __init__(self, mu=25.0, sigma=25.0/3):
            self.mu = float(mu)
            self.sigma = float(sigma)
        def __str__(self):
            return "{0.mu} {0.sigma}".format(self)

        def __repr__(self):
            return self.__str__()

    a = player()
    b = player()

# Draw
    tester(a, b, 1, 1, "draw")
# win
    tester(a, b, 2, 0, "win")
# win
    tester(a, b, 0, 2, "loss")

# High skill
    tester(player(mu=35), player(mu=15), 1, 1, "high skill draw")
    tester(player(mu=35), player(mu=15), 2, 0, "high skill win")
# High confidence
    tester(player(sigma=1), player(sigma=1), 1, 1, "high confidence draw")
    tester(player(sigma=1), player(sigma=1), 2, 0, "high confidence win")

# Test team
    a = [player()] * 2 + [player(mu=35)]
    b = [player()] * 2 + [player(mu=35)]
    tester_team(a, b, 1, 1, "team draw")
    tester_team(a, b, 2, 0, "team win")
    tester_team(a, b, 0, 2, "team loss")
