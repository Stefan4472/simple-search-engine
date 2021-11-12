from simplesearch.searchengine import SearchEngine
from simplesearch.test.test_sonnets import sonnets_engine
# TODO: WHAT'S A BETTER WAY TO TEST THIS?


def test_serialize(sonnets_engine):
    sonnets_engine.commit()
    marshalled_engine = SearchEngine(sonnets_engine.filepath)

    res_orig = sonnets_engine.search("Weary with toil, I haste me to my bed")
    res_marshalled = marshalled_engine.search("Weary with toil, I haste me to my bed")
    assert res_orig == res_marshalled