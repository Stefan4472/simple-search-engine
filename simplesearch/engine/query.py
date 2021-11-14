import dataclasses as dc
import typing
from simplesearch.engine.tokenizer import Tokenizer


@dc.dataclass
class ProcessedQuery:
    query: str
    terms: typing.List[str]
    term_counts: typing.Dict[str, int]


def process_query(
        query: str,
        tokenizer: Tokenizer,
) -> ProcessedQuery:
    term_counts = {}
    for word in tokenizer.tokenize_string(query):
        if word in term_counts:
            term_counts[word] += 1
        else:
            term_counts[word] = 1
    return ProcessedQuery(query, list(term_counts.keys()), term_counts)
