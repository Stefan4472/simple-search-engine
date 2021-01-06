import dataclasses as dc
from tokenizer import Tokenizer


@dc.dataclass
class ProcessedQuery:
    query: str
    terms: list[str]
    term_counts: dict[str, int]


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
