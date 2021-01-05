class ProcessedQuery:
    def __init__(self, query='', terms=None, term_counts=None):
        # the string query
        self.str_query = query if query else ''
        # list of in-order terms in the query, no repeats
        self.terms = terms if terms else []
        # map query term to number of occurrences
        self.term_counts = term_counts if term_counts else {}

def process_query(str_query, tokenizer):
    terms = []
    term_counts = {}
    for word in tokenizer.tokenize_string(str_query):
        if word not in terms:
            terms.append(word)
        if word in term_counts:
            term_counts[word] += 1
        else:
            term_counts[word] = 1
    return ProcessedQuery(str_query, terms, term_counts)
