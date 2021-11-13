import json
import pathlib
import typing
from queue import PriorityQueue
from simplesearch.inverted_list import InvertedList
import simplesearch.query as q
import simplesearch.tokenizer as t
from simplesearch.scoring import score_bm25, score_ql
from simplesearch.helper import DocInfo, IntermediateResult, FinalResult
# TODO: DISTINGUISH BETWEEN DOCID (USER PROVIDED) AND DOCNUM (SEQUENTIALLY GENERATED)


class SearchEngine:
    """
    SearchEngine implementation.

    Note: You must call `commit()` to persist changes!
    """
    _filepath: pathlib.Path
    _stopwords: typing.List[str]
    _index: typing.Dict[str, InvertedList]
    _doc_data: typing.Dict[int, DocInfo]
    _num_docs: int
    _num_terms: int
    _tokenizer: t.Tokenizer

    @property
    def filepath(self) -> pathlib.Path:
        return self._filepath

    @property
    def num_docs(self) -> int:
        return self.num_docs

    @property
    def num_terms(self) -> int:
        return self._num_terms

    def __init__(
            self,
            filepath: pathlib.Path,
            stopwords: typing.List[str] = None,
    ):
        if isinstance(filepath, str):
            filepath = pathlib.Path(filepath)
        if filepath.suffix != '.json':
            raise ValueError('The provided filepath must be of type ".json"')
        self._filepath = filepath
        self._index = self._marshall_index()
        self._doc_data = self._marshall_doc_data()
        self._num_docs = len(self._doc_data)
        self._num_terms = sum(inv_list.num_postings for inv_list in self._index.values())
        self._tokenizer = t.Tokenizer(stopwords=stopwords)

    def _marshall_index(self) -> typing.Dict[str, InvertedList]:
        """Marshals inverted index from `filepath`."""
        try:
            with open(self._filepath, encoding='utf8') as f:
                json_data = json.load(f)
            # Iterate through the list of serialized InvertedLists.
            # Deserialize each one and add it to the index dict under its term.
            index = {}
            for serialized_inv_list in json_data['index']:
                inv_list = InvertedList.from_json(serialized_inv_list)
                index[inv_list.term] = inv_list
            return index
        except FileNotFoundError:
            # File not found: return empty
            return {}

    def _marshall_doc_data(self) -> typing.Dict[int, DocInfo]:
        """Marshals doc_data from `filepath`."""
        try:
            with open(self._filepath, encoding='utf8') as f:
                json_data = json.load(f)
            # Read in doc_data, and make sure to convert the doc_id keys to 'int'
            doc_data = {}
            for doc_id, doc_info in json_data['doc_data'].items():
                doc_data[int(doc_id)] = DocInfo(doc_info['slug'], doc_info['num_terms'])
            return doc_data
        except FileNotFoundError:
            # File not found: return empty
            return {}

    def commit(self):
        """
        Persist current state to `self.filepath`.

        Serialization is currently done in JSON. This is obviously not very
        performant, but is good enough for now.
        """
        # TODO: THIS COULD BE CLEANER
        doc_data = {
            key: {
                'slug': doc_data.slug,
                'num_terms': doc_data.num_terms,
            } for key, doc_data in self._doc_data.items()
        }
        index = [inverted_index.to_json() for inverted_index in self._index.values()]
        serialized = {'doc_data': doc_data, 'index': index}
        # Dump json
        with open(self.filepath, 'w+', encoding='utf8') as outfile:
            json.dump(serialized, outfile)

    def index_file(
            self,
            filepath: pathlib.Path,
            file_id: str,
            encoding: str = None,
    ):
        """
        Indexes the file at the specified path, and registers it in the
        index under the provided `file_id`.
        TODO: TEST WITH DIFFERENT ENCODINGS
        """
        doc_id = self._num_docs + 1
        num_tokens = 0
        for token in self._tokenizer.tokenize_file(filepath, encoding=encoding):
            # If token not in index, create an InvertedList for it
            if token not in self._index:
                self._index[token] = InvertedList(token)
            # Register this document as having an occurrence of the
            # token at the current word-position
            self._index[token].add_posting(doc_id, num_tokens)
            num_tokens += 1
        # Update number of terms in the index and add entry to doc_data
        self._num_terms += num_tokens
        self._doc_data[doc_id] = DocInfo(file_id, num_tokens)
        self._num_docs += 1

    def search(
            self,
            query: str,
            score_func: str = 'ql',
    ) -> typing.List[FinalResult]:
        # TODO: MAKE SCORE_FUNC AN ENUM
        processed_query = q.process_query(query, self._tokenizer)
        results = self._run_query(processed_query, score_func)
        return self._format_results(results)

    def _run_query(
            self,
            processed_query: q.ProcessedQuery,
            score_func: str,
    ) -> 'PriorityQueue[IntermediateResult]':
        results: PriorityQueue[IntermediateResult] = PriorityQueue()
        # Create dict mapping term to InvertedList for that term.
        inv_lists = {
            word: self._index[word] if word in self._index else InvertedList(word)
            for word in processed_query.terms
        }

        for inv_list in inv_lists.values():
            inv_list.reset_pointer()

        # Iterate over all documents that contain at least one of the terms
        has_next, doc_id = self._find_next_doc(inv_lists)
        while has_next:
            score = 0.0
            for term, inv_list in inv_lists.items():
                if score_func == 'bm25':
                    qf = processed_query.term_counts[term]
                    f = inv_list.get_term_freq() if inv_list.get_curr_doc_id() == doc_id else 0
                    n = inv_list._num_docs
                    N = self._num_docs
                    dl = self._doc_data[doc_id].num_terms
                    avdl = self._num_terms / self._num_docs
                    # print (qf, f, n, N, dl, avdl)
                    score += score_bm25(qf, f, n, N, dl, avdl)
                elif score_func == 'ql':
                    fqd = inv_list.get_term_freq() if inv_list.get_curr_doc_id() == doc_id else 0
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

            has_next, doc_id = self._find_next_doc(inv_lists)
        return results

    # inv_lists: dict mapping term->InvertedList
    # searches the lists for the next doc_id with at least one of the terms
    # returns whether a term was found, and the doc_id
    def _find_next_doc(
            self,
            inv_lists,
    ) -> (bool, int):
        in_progress = [list for list in inv_lists.values() if not list.is_finished()]
        if not in_progress:
            return False, -1
        next_doc_id = min([list.get_curr_doc_id() for list in in_progress])
        return True, next_doc_id

    # returns list of (slug, score), ordered decreasing
    def _format_results(
            self,
            results: 'PriorityQueue[IntermediateResult]',
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
