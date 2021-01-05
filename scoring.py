import math


# scores a single document for a single query term
# qf: frequency of the term in the query
# f: frequency of the term in the doc
# n: number of docs that contain the term
# N: number of docs in the collection
# dl: number of terms in the document
# avdl: average number of terms in a document
# k1, k2, b: parameters for the formula
def score_bm25(qf, f, n, N, dl, avdl, k1=1.2, k2=100, b=0.75):  # TODO: MOVE TO A DIFFERENT PLACE
    K = k1 * ((1 - b) + b * dl / avdl)
    return math.log10(1 / ((n + 0.5) / (N - n + 0.5))) * \
           (((k1 + 1) * f) / (K + f)) * \
           (((k2 + 1) * qf) / (k2 + qf))


# scores a single document for a single query term
# fqd: number of occurrences in the document
# dl: number of terms in the doc
# cq: number of times the term appears in the corpus
# C: total number of term occurrences in the corpus
def score_ql(fqd, dl, cq, C, mu=1500):
    ql_calc = (fqd + mu * (cq / C)) / (dl + mu)
    # TODO: GUARD AGAINST CQ = 0, C = 0, DL = 0, FQD = 0
    return 0.0 if ql_calc == 0 else math.log10(ql_calc)