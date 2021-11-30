import json
import pathlib
import typing
import dataclasses as dc
from queue import PriorityQueue
from simplesearch.engine.inverted_list import InvertedList
import simplesearch.engine.query as q
# import simplesearch.engine.tokenizer as t
from simplesearch.engine.stopper import Stopper
from simplesearch.scoring.scorer import Scorer, TermScoreInfo, DocScoreInfo
from simplesearch.scoring.ql import QlScorer
from simplesearch.engine._helper import DocInfo, IntermediateResult
from simplesearch.stemming.stemmer import Stemmer
from simplesearch.stemming.porter_stemmer import PorterStemmer
from simplesearch.tokenizing.tokenizer import Tokenizer
from simplesearch.tokenizing.alphanumeric_tokenizer import AlphaNumericTokenizer
# TODO: DISTINGUISH BETWEEN DOCID (USER PROVIDED) AND DOCNUM (SEQUENTIALLY GENERATED)


@dc.dataclass
class SearchResult:
    slug: str
    score: float


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
    # Default to `AlphaNumericTokenizer`
    _tokenizer: Tokenizer
    # Default to None
    _stopper: Stopper
    # Default to `PorterStemmer`
    _stemmer: Stemmer
    # Default to `QlSCorer`
    _scorer: Scorer

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
            tokenizer: Tokenizer = None,
            stopper: Stopper = None,
            stemmer: Stemmer = None,
            scorer: Scorer = None
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
        self._tokenizer = tokenizer if tokenizer else AlphaNumericTokenizer()
        self._stopper = stopper
        self._stemmer = stemmer if stemmer else PorterStemmer()
        self._scorer = scorer if scorer else QlScorer()

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
        Reads the file at the specified path and registers it in the
        index under the provided `file_id`.
        TODO: TEST WITH DIFFERENT ENCODINGS + ERROR HANDLING
        """
        with open(filepath, encoding=encoding) as f:
            self.index_string(f.read(), file_id)

    def index_string(
            self,
            string: str,
            file_id: str,
    ):
        """Indexes the given string, storing it under the specified `file_id`."""
        doc_id = self._num_docs + 1
        num_tokens = 0
        for token in self._process_text(string):
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
    ) -> typing.List[SearchResult]:
        results: PriorityQueue[IntermediateResult] = PriorityQueue()
        processed_query = self._process_query(query)

        # Retrieve InvertedLists corresponding to query terms
        inverted_lists = \
            [self._index[term] for term in processed_query.terms if term in self._index]
        # Reset InvertedList pointers
        for inverted_list in inverted_lists:
            inverted_list.reset_pointer()

        # Iterate over documents that contain at least one of the searched-for terms
        while True:
            remaining = [ilist for ilist in inverted_lists if not ilist.is_finished()]
            if not remaining:
                break
            # Get the next-smallest doc_id in the selected InvertedLists
            next_doc_id = min([ilist.get_curr_doc_id() for ilist in remaining])
            # Now group on `next_doc_id`
            score_infos: typing.List[TermScoreInfo] = []
            for ilist in inverted_lists:
                # Collect data required for scoring
                score_infos.append(TermScoreInfo(
                    ilist.term,
                    qf=processed_query.term_counts[ilist.term],
                    df=ilist.get_term_freq() if ilist.get_curr_doc_id() == next_doc_id else 0,
                    cf=ilist.num_postings,
                    nd=ilist.num_docs,
                    nc=self._num_docs,
                    dl=self._doc_data[next_doc_id].num_terms,
                    dc=self.num_terms,
                    avdl=self._num_terms / self._num_docs,
                ))
                ilist.move_to(next_doc_id + 1)
            # Calculate score and insert into `results`
            score = self._scorer.calc_score(DocScoreInfo(score_infos))
            results.put(IntermediateResult(next_doc_id, score, self._scorer.to_sortable(score)))
        return self._format_results(results)

    def _process_text(self, text: str) -> typing.Generator[str, None, None]:
        """A generator that tokenizes, stops, and stems the provided `text`"""
        for token in self._tokenizer.tokenize_string(text):
            if self._stopper and self._stopper.is_stopword(token):
                continue
            yield self._stemmer.get_stem(token)

    def _process_query(self, query: str) -> q.ProcessedQuery:
        term_counts = {}
        for word in self._process_text(query):
            if word in term_counts:
                term_counts[word] += 1
            else:
                term_counts[word] = 1
        return q.ProcessedQuery(query, list(term_counts.keys()), term_counts)

    def _format_results(
            self,
            results: 'PriorityQueue[IntermediateResult]',
    ) -> typing.List[SearchResult]:
        """
        Given a PriorityQueue of `IntermediateResult`, create and return
        list of `FinalResult` (which are user-processable).
        """
        formatted_results: typing.List[SearchResult] = []
        while not results.empty():
            next_result = results.get()
            formatted_results.append(SearchResult(
                self._doc_data[next_result.doc_id].slug,
                next_result.score,
            ))
        return formatted_results

    def clear_all_data(self):
        """Reset the search engine. Danger!"""
        self._index = {}
        self._doc_data = {}
        self._num_docs = 0
        self._num_terms = 0
