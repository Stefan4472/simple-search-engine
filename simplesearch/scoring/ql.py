import math
from simplesearch.scoring.scorer import Scorer, ScoreInfo


class QlScorer(Scorer):
    def __init__(self, mu: float = 1500):
        """
        QL (Query Likelihood) scoring.

        mu: tuning parameter
        """
        self.mu = mu

    def calc_score(self, info: ScoreInfo) -> float:
        ql_calc = (info.df + self.mu * (info.cf / info.dc)) / (info.dl + self.mu)
        # TODO: GUARD AGAINST CQ = 0, C = 0, DL = 0, FQD = 0
        return 0.0 if ql_calc == 0 else math.log10(ql_calc)
