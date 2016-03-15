import pytest

import wrank.heuristics


@pytest.mark.parametrize("heuristic",
                         [
                             wrank.heuristics.DrawChanceHeuristic,
                             wrank.heuristics.LadderDisruptionHeuristic,
                             wrank.heuristics.TrueskillClumpingHeuristic,
                             wrank.heuristics.SigmaReductionHeuristic,
                             wrank.heuristics.TimeSinceLastPlayedHeuristic,
                             wrank.heuristics.UnplayedMatchupsHeuristic,
                             wrank.heuristics.DecoratorHeuristic,
                             wrank.heuristics.CombinerHeuristic,
                             wrank.heuristics.LinearSumHeuristic,
                         ]
                         )
def test_heuristics(heuristic):
    h = heuristic()
