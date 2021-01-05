import json
import math
from queue import PriorityQueue
from collections import namedtuple
from flaskr.search_engine.inverted_list import InvertedList, inverted_list_from_json
import flaskr.search_engine.result as r
import flaskr.search_engine.query as q
import flaskr.search_engine.tokenizer as t

Result = namedtuple('result', 'doc_id score')

# Serialization currently done in JSON... This will be small enough that it should be fine (despite not being highly performant)

class Index:  # TODO: RENAME SEARCHENGINE?
    def __init__(self, filepath, index=None, doc_data=None):
        self.filepath = filepath
        self.index = index if index else {}
        self.doc_data = doc_data if doc_data else {}
        self.num_docs = len(doc_data) if index else 0
        self.num_terms = sum(inv_list.num_postings for inv_list in index.values()) if index else 0  # TODO: RENAME NUM_TOKENS (?)
        self.tokenizer = t.Tokenizer()  # TODO: USE STOPWORDS?

    def index_file(self, filepath, slug):  # TODO: PROVIDE INDEX_HTML_FILE()?
        # print ('Indexing {}'.format(filepath))
        file_text = ''

        doc_id = self.num_docs + 1
        position = 0
        for token in self.tokenizer.tokenize_file(filepath):
            if token not in self.index:
                self.index[token] = InvertedList(token)
            self.index[token].add_posting(doc_id, position)
            position += 1

        # update number of terms in the index and add entry to doc_data
        self.num_terms += position
        self.doc_data[doc_id] = \
            { 'slug': slug,
              'numTerms': position }

        self.num_docs += 1
        #print (self.index.keys())

    def search(self, query, score_func='ql'):
        # process the query so it can be understood
        processed_query = q.process_query(query, self.tokenizer)
        #print ('Query terms: {}'.format(processed_query.terms))
        results = self._run_query(processed_query, score_func)
        return self._format_results(results, processed_query)

    def _run_query(self, processed_query, score_func):
        results = PriorityQueue()
        # retrieve the InvertedLists in the same order as the query terms
        inv_lists = {word: self.index[word] if word in self.index else InvertedList(word) for word in processed_query.terms}

        for inv_list in inv_lists.values():
            inv_list.reset_pointer()

        # iterate over all documents that contain at least one of the terms
        while True:
            has_next, doc_id = self.find_next_doc(inv_lists)
            if not has_next:
                break

            score = 0.0
            for term, inv_list in inv_lists.items():
                if score_func == 'bm25':
                    qf = processed_query.term_counts[term]
                    f = inv_list.get_term_freq() if inv_list.curr_doc_id() == doc_id else 0
                    n = inv_list.num_docs
                    N = self.num_docs
                    dl = self.doc_data[doc_id]['numTerms']
                    avdl = self.num_terms / self.num_docs
                    # print (qf, f, n, N, dl, avdl)
                    score += score_bm25(qf, f, n, N, dl, avdl)
                elif score_func == 'ql':
                    fqd = inv_list.get_term_freq() if inv_list.curr_doc_id() == doc_id else 0
                    dl = self.doc_data[doc_id]['numTerms']
                    cq = inv_list.num_postings
                    C = self.num_terms
                    score += score_ql(fqd, dl, cq, C)

            # put result in list using negative score as priority
            # this way, higher score is prioritized
            results.put((-score, doc_id))

            # make sure all lists are moved to the next doc_id
            for list in inv_lists.values():
                list.move_to(doc_id + 1)

        return results

    # inv_lists: dict mapping term->InvertedList
    # searches the lists for the next doc_id with at least one of the terms
    # returns whether a term was found, and the doc_id
    def find_next_doc(self, inv_lists):
        in_progress = [list for list in inv_lists.values() if not list.finished()]
        if not in_progress:
            return False, -1
        next_doc_id = min([list.curr_doc_id() for list in in_progress])
        return True, next_doc_id

    # returns list of (slug, score), ordered decreasing
    def _format_results(self, results, processed_query):
        formatted_results = []
        while not results.empty():
            next = results.get()
            formatted_results.append((self.doc_data[next[1]]['slug'], -next[0]))
        return formatted_results

    def to_json(self):
        # TODO: SAVE STOPWORD FILE PATH?
        return {
            'doc_data': self.doc_data,
            'index': [inverted_index.to_json() for inverted_index in self.index.values()],
        }

    # DANGER
    def clear_all_data(self):
        self.index = {}
        self.doc_data = {}
        self.num_docs = 0
        self.num_terms = 0 

    def commit(self):  # FUNNY: INDEX SIZE WENT FROM 132KB TO 51KB WHEN I WENT FROM INDENT=2 TO NO INDENT
        with open(self.filepath, 'w') as outfile:
            # print ('Dumping {}'.format(self.to_json()))
            json.dump(self.to_json(), outfile)
    

def connect(filepath):
    if not filepath.endswith('.json'):
        raise ValueError('The provided file must be of type ".json"')
    json_data = {}
    doc_data = {}
    index = {}
    
    # Attempt to read the provided file and deserialize the index
    try:
        with open(filepath, encoding='utf8') as json_file:
            json_data = json.load(json_file)

        # Read in doc_data, and make sure to convert the doc_id keys to 'int'
        for doc_id, doc_info in json_data['doc_data'].items():
            doc_data[int(doc_id)] = doc_info

        # Iterate through the list of serialized InvertedLists.
        # Deserialize each one and add it to the index dict under its term.
        for serialized_inv_list in json_data['index']:
            #print (serialized_inv_list)
            inv_list = inverted_list_from_json(serialized_inv_list)
            index[inv_list.term] = inv_list  
    # File not found: create a new file and populate with empty index and doc_data
    except FileNotFoundError:
        open(filepath, 'a').close()
        Index(filepath).commit()
    
    return Index(filepath, index=index, doc_data=doc_data)

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
