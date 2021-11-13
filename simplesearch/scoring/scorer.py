import abc
import dataclasses as dc


@dc.dataclass
class ScoreInfo:
    """
    Container for data used to calculate a score.

    TODO: IMPROVE VARIABLE NAMES
    """
    # Frequency of the term in the query
    qf: int
    # Frequency of the term in the document
    df: int
    # Frequency of the term in the corpus
    cf: int
    # Number of documents in the corpus that contain the term
    nd: int
    # Number of documents in the corpus
    nc: int
    # Number of terms in the document
    dl: int
    # Number of terms in the corpus
    dc: int
    # Average number of terms in a document
    avdl: float


class Scorer(abc.ABC):
    """
    Base class used to implement a scorer.
    Scores a single document for a single term.

    A `Scorer` implementation must implement the `calc_score()` function.
    TODO: MODIFY TO PROVIDE ALL INFOS AND RETURN THE SCORE FOR THE WHOLE DOCUMENT, NOT JUST FOR THE TERM.
    """
    @abc.abstractmethod
    def calc_score(self, info: ScoreInfo) -> float:
        pass
