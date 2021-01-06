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
    """Information stored for an indexed document."""
    slug: str
    num_terms: int


class SearchEngine:
    def __init__(
            self,
            filepath: pathlib.Path,
            encoding: str = 'utf8',
            stopwords_file: typing.Optional[pathlib.Path] = None,
    ):
        self.filepath = filepath
        self._index, self._doc_data = SearchEngine._connect(filepath, encoding)
        self._num_docs = len(self._doc_data)
        self._num_terms = sum(inv_list.num_postings for inv_list in self._index.values())
        self._tokenizer = t.Tokenizer(stopword_filepath=stopwords_file)

    @staticmethod
    def _connect(
            filepath: pathlib.Path,
            encoding: str,
    ) -> typing.Tuple[dict[str, InvertedList], dict[int, DocInfo]]:
        """Attempts to marshall data stored in `filepath`.

        Returns dict mapping token to InvertedList, and dict mapping
        doc_id to corresponding DocInfo.
        """
        if filepath.suffix != '.json':
            raise ValueError('The provided file must be of type ".json"')
        # Read the provided file and deserialize the index
        try:
            with open(filepath, encoding=encoding) as json_file:
                json_data = json.load(json_file)
            # Read in doc_data, and make sure to convert the doc_id keys to 'int'
            doc_data = {}
            for doc_id, doc_info in json_data['doc_data'].items():
                doc_data[int(doc_id)] = DocInfo(doc_info['slug'], doc_info['num_terms'])
            # Iterate through the list of serialized InvertedLists.
            # Deserialize each one and add it to the index dict under its term.
            index = {}
            for serialized_inv_list in json_data['index']:
                inv_list = inverted_list_from_json(serialized_inv_list)
                index[inv_list.term] = inv_list
            return index, doc_data
        # File not found: return empty index and doc_data
        except FileNotFoundError:
            return {}, {}

    def index_file(
            self,
            filepath: pathlib.Path,
            file_id: str,
    ):
        """Indexes the file at the specified path, and registers it in the
        index under the provided `file_id`.

        NOTE: No changes will be made to the persistent data until `commit()`
        is called.
        """
        doc_id = self._num_docs + 1
        position = 0
        # Tokenize the file
        for token in self._tokenizer.tokenize_file(filepath):
            # If token not in index, create an InvertedList for it
            if token not in self._index:
                self._index[token] = InvertedList(token)
            # Register this document as having an occurrence of the
            # token at the current word-position
            self._index[token].add_posting(doc_id, position)
            position += 1
        # Update number of terms in the index and add entry to doc_data
        self._num_terms += position
        self._doc_data[doc_id] = DocInfo(file_id, position)
        self._num_docs += 1

    def commit(self):
        """Serializes data and writes out to `self.filepath`"""
        # FUNNY: INDEX SIZE WENT FROM 132KB TO 51KB WHEN I WENT FROM INDENT=2 TO NO INDENT
        # Create empty file if it doesn't exist already
        if not self.filepath.exists():
            open(self.filepath, 'a').close()
        # Dump json
        with open(self.filepath, 'w') as outfile:
            json.dump(self.to_json(), outfile)

    def search(
            self,
            query: str,
            score_func: str = 'ql',
    ) -> list[FinalResult]:
        # TODO: MAKE SCORE_FUNC AN ENUM
        # Process the query so it can be understood
        processed_query = q.process_query(query, self._tokenizer)
        results = self._run_query(processed_query, score_func)
        return self._format_results(results)

    def _run_query(
            self,
            processed_query: q.ProcessedQuery,
            score_func: str,
    ) -> PriorityQueue[IntermediateResult]:
        results: PriorityQueue[IntermediateResult] = PriorityQueue()
        # Retrieve the InvertedLists in the same order as the query terms
        inv_lists = {
            word: self._index[word] if word in self._index else InvertedList(word)
            for word in processed_query.terms
        }

        for inv_list in inv_lists.values():
            inv_list.reset_pointer()

        # Iterate over all documents that contain at least one of the terms
        while True:
            has_next, doc_id = self._find_next_doc(inv_lists)
            if not has_next:
                break

            score = 0.0
            for term, inv_list in inv_lists.items():
                if score_func == 'bm25':
                    qf = processed_query.term_counts[term]
                    f = inv_list.get_term_freq() if inv_list.curr_doc_id() == doc_id else 0
                    n = inv_list._num_docs
                    N = self._num_docs
                    dl = self._doc_data[doc_id].num_terms
                    avdl = self._num_terms / self._num_docs
                    # print (qf, f, n, N, dl, avdl)
                    score += score_bm25(qf, f, n, N, dl, avdl)
                elif score_func == 'ql':
                    fqd = inv_list.get_term_freq() if inv_list.curr_doc_id() == doc_id else 0
                    dl = self._doc_data[doc_id].num_terms
                    cq = inv_list.num_postings
                    C = self._num_terms
                    score += score_ql(fqd, dl, cq, C)

            # put result in list using negative score as priority
            # this way, higher score is prioritized
            results.put(IntermediateResult(doc_id, -score))

            # make sure all lists are moved to the next doc_id
            for inv_list in inv_lists.values():
                inv_list.move_to(doc_id + 1)

        return results

    # inv_lists: dict mapping term->InvertedList
    # searches the lists for the next doc_id with at least one of the terms
    # returns whether a term was found, and the doc_id
    def _find_next_doc(
            self,
            inv_lists,
    ) -> (bool, int):
        in_progress = [list for list in inv_lists.values() if not list.finished()]
        if not in_progress:
            return False, -1
        next_doc_id = min([list.curr_doc_id() for list in in_progress])
        return True, next_doc_id

    # returns list of (slug, score), ordered decreasing
    def _format_results(
            self,
            results: PriorityQueue[IntermediateResult],
    ):
        formatted_results = []
        while not results.empty():
            next_result = results.get()
            formatted_results.append(FinalResult(
                self._doc_data[next_result.doc_id].slug,
                -next_result.score,
            ))
        return formatted_results

    # DANGER
    def clear_all_data(self):
        self._index = {}
        self._doc_data = {}
        self._num_docs = 0
        self._num_terms = 0

    def to_json(self):
        # Serialization currently done in JSON...
        # This will be small enough that it should be fine (despite not being highly performant)
        return {
            'doc_data': {key: {'slug': doc_data.slug, 'num_terms': doc_data.num_terms} for key, doc_data in
                         self._doc_data.items()},
            'index': [inverted_index.to_json() for inverted_index in self._index.values()],
        }
