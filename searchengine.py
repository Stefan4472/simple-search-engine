import json
import pathlib
import typing
import dataclasses as dc
from queue import PriorityQueue
from inverted_list import InvertedList, inverted_list_from_json
import query as q
import tokenizer as t
from scoring import score_bm25, score_ql
# TODO: PROVIDE INDEX_HTML_FILE(), WHICH STRIPS TAGS OUT?


@dc.dataclass
class Result:
    doc_id: int
    score: float


class SearchEngine:
    def __init__(
            self,
            filepath: pathlib.Path,
            stopwords_file: typing.Optional[pathlib.Path] = None,
    ):
        self.filepath = filepath
        self._index, self._doc_data = self._connect()
        self._num_docs = len(self._doc_data)
        self._num_terms = sum(inv_list.num_postings for inv_list in self._index.values())
        self._tokenizer = t.Tokenizer(stopword_filepath=stopwords_file)

    # TODO: FIGURE OUT TYPING INFO
    def _connect(self) -> (dict[str, InvertedList], typing.Any):
        if not self.filepath.suffix == '.json':
            raise ValueError('The provided file must be of type ".json"')

        # Attempt to read the provided file and deserialize the index
        try:
            with open(self.filepath, encoding='utf8') as json_file:
                json_data = json.load(json_file)
            # Read in doc_data, and make sure to convert the doc_id keys to 'int'
            doc_data = {}
            for doc_id, doc_info in json_data['doc_data'].items():
                doc_data[int(doc_id)] = doc_info
                print(doc_info)
            # Iterate through the list of serialized InvertedLists.
            # Deserialize each one and add it to the index dict under its term.
            index = {}
            for serialized_inv_list in json_data['index']:
                # print (serialized_inv_list)
                inv_list = inverted_list_from_json(serialized_inv_list)
                index[inv_list.term] = inv_list
            return index, doc_data
        # File not found: create a new file and populate with empty index and doc_data
        except FileNotFoundError:
            open(self.filepath, 'a').close()
            self.commit()
            return {}, {}

    def index_file(
            self,
            filepath: pathlib.Path,
            slug,
    ):
        doc_id = self._num_docs + 1
        position = 0
        for token in self._tokenizer.tokenize_file(filepath):
            if token not in self._index:
                self._index[token] = InvertedList(token)
            self._index[token].add_posting(doc_id, position)
            position += 1

        # update number of terms in the index and add entry to doc_data
        self._num_terms += position
        self._doc_data[doc_id] = \
            { 'slug': slug,
              'numTerms': position }

        self._num_docs += 1

    def commit(self):  # FUNNY: INDEX SIZE WENT FROM 132KB TO 51KB WHEN I WENT FROM INDENT=2 TO NO INDENT
        with open(self.filepath, 'w') as outfile:
            # print ('Dumping {}'.format(self.to_json()))
            json.dump(self.to_json(), outfile)

    def search(
            self,
            query,
            score_func='ql',
    ):
        # process the query so it can be understood
        processed_query = q.process_query(query, self._tokenizer)
        #print ('Query terms: {}'.format(processed_query.terms))
        results = self._run_query(processed_query, score_func)
        return self._format_results(results, processed_query)

    def _run_query(
            self,
            processed_query,
            score_func,
    ):
        results = PriorityQueue()
        # retrieve the InvertedLists in the same order as the query terms
        inv_lists = {word: self._index[word] if word in self._index else InvertedList(word) for word in processed_query.terms}

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
                    n = inv_list._num_docs
                    N = self._num_docs
                    dl = self._doc_data[doc_id]['numTerms']
                    avdl = self._num_terms / self._num_docs
                    # print (qf, f, n, N, dl, avdl)
                    score += score_bm25(qf, f, n, N, dl, avdl)
                elif score_func == 'ql':
                    fqd = inv_list.get_term_freq() if inv_list.curr_doc_id() == doc_id else 0
                    dl = self._doc_data[doc_id]['numTerms']
                    cq = inv_list.num_postings
                    C = self._num_terms
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
    def find_next_doc(
            self,
            inv_lists,
    ):
        in_progress = [list for list in inv_lists.values() if not list.finished()]
        if not in_progress:
            return False, -1
        next_doc_id = min([list.curr_doc_id() for list in in_progress])
        return True, next_doc_id

    # returns list of (slug, score), ordered decreasing
    def _format_results(
            self,
            results,
            processed_query,
    ):
        formatted_results = []
        while not results.empty():
            next = results.get()
            formatted_results.append((self._doc_data[next[1]]['slug'], -next[0]))
        return formatted_results

    def to_json(self):
        # Serialization currently done in JSON...
        # This will be small enough that it should be fine (despite not being highly performant)
        return {
            'doc_data': self._doc_data,
            'index': [inverted_index.to_json() for inverted_index in self._index.values()],
        }

    # DANGER
    def clear_all_data(self):
        self._index = {}
        self._doc_data = {}
        self._num_docs = 0
        self._num_terms = 0
