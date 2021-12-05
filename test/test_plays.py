import pytest
from stefansearch.engine.search_engine import SearchEngine
from stefansearch.scoring.ql import QlScorer
from stefansearch.tokenizing.alphanumeric_tokenizer import AlphanumericTokenizer
from util import create_engine, TESTDATA_PATH
"""Very simple test cases for the plays."""


@pytest.fixture(scope='session')
def plays_engine() -> SearchEngine:
    """Creates a search engine with all of Shakespeare's plays indexed."""
    engine = create_engine()
    plays_dir = TESTDATA_PATH / 'Plays'
    for play_path in plays_dir.rglob('*'):
        if play_path.is_file():
            engine.index_file(play_path, str(play_path.absolute()), encoding='utf-8')
    return engine


def test_query_1(plays_engine):
    plays_engine._tokenizer = AlphanumericTokenizer()
    plays_engine._scorer = QlScorer()
    res = plays_engine.search("O Romeo, Romeo, wherefore art thou Romeo?")
    assert 'the-tragedy-of-romeo-and-juliet' in res[0].slug and 'ACT-II-SCENE-II' in res[0].slug
