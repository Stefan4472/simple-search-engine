import dataclasses as dc
# TODO: BETTER NAME/ORGANIZATION FOR THIS FILE. PROBABLY TEMPORARY


@dc.dataclass
class IntermediateResult:
    """Stores the score that a specified `doc_id` received."""
    doc_id: int
    score: float

    def __lt__(self, other):
        return self.score < other.score


@dc.dataclass
class FinalResult:
    slug: str
    score: float


@dc.dataclass
class DocInfo:
    """Store some metainformation for an indexed document."""
    slug: str
    num_terms: int
