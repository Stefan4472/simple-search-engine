"""Experimental test script for now"""
import pytest
import pathlib
import os
from simplesearch.searchengine import SearchEngine


# Use scope='session' to reuse without re-generating
@pytest.fixture(scope='session')
def searchengine() -> SearchEngine:
    # TODO: USE TEMP FILE
    save_path = pathlib.Path('save.json')
    engine = SearchEngine(save_path)
    sonnets_dir = pathlib.Path('TestData') / 'Sonnets'

    for sonnet_path in sonnets_dir.glob('*'):
        engine.index_file(sonnet_path, sonnet_path.name)
    return engine


def test_simple(searchengine):
    res = searchengine.search('issueless shalt hap')
    assert res[0].slug == 'SONNET-9.txt'