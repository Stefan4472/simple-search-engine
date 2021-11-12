import pytest
import pathlib
from simplesearch.searchengine import SearchEngine
from simplesearch.test.util import create_engine
"""
Very simple test cases for the sonnets.

Note: these test cases have the problem that they are always the first line
of the sonnet. This is okay for now but should be fixed when I put a little 
more effort in!
"""


# Use scope='session' to reuse without re-generating
@pytest.fixture(scope='session')
def sonnets_engine() -> SearchEngine:
    """Creates a search engine with all of Shakespeare's sonnets indexed."""
    engine = create_engine()
    # Index all sonnets
    sonnets_dir = pathlib.Path('TestData') / 'Sonnets'
    for sonnet_path in sonnets_dir.glob('*'):
        sonnet_num = int(sonnet_path.stem)
        engine.index_file(sonnet_path, make_slug(sonnet_num))
    return engine


def make_slug(sonnet_number: int) -> str:
    return 'SONNET-{}'.format(sonnet_number)


def test_query_1(sonnets_engine):
    res = sonnets_engine.search("Weary with toil, I haste me to my bed")
    assert res[0].slug == make_slug(27)


def test_query_2(sonnets_engine):
    res = sonnets_engine.search("Let me not to the marriage of true minds")
    assert res[0].slug == make_slug(116)


def test_query_3(sonnets_engine):
    res = sonnets_engine.search("My mistress' eyes are nothing like the sun")
    assert res[0].slug == make_slug(130)


def test_query_4(sonnets_engine):
    res = sonnets_engine.search("The expense of spirit in a waste of shame")
    assert res[0].slug == make_slug(129)


def test_query_5(sonnets_engine):
    res = sonnets_engine.search("When in the chronicle of wasted time")
    assert res[0].slug == make_slug(106)


def test_query_6(sonnets_engine):
    res = sonnets_engine.search("Shall I compare thee to a summer’s day?")
    assert res[0].slug == make_slug(18)


def test_query_7(sonnets_engine):
    res = sonnets_engine.search("So now I have confessed that he is thine")
    assert res[0].slug == make_slug(134)


def test_query_8(sonnets_engine):
    res = sonnets_engine.search("To me, fair friend, you never can be old")
    assert res[0].slug == make_slug(104)


def test_query_9(sonnets_engine):
    res = sonnets_engine.search("When in disgrace with fortune and men’s eyes")
    assert res[0].slug == make_slug(29)


def test_query_10(sonnets_engine):
    res = sonnets_engine.search("From you have I been absent in the spring")
    assert res[0].slug == make_slug(98)
