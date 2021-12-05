import pathlib
import tempfile
import datetime
from stefansearch.engine.search_engine import SearchEngine


# TODO: THERE IS SOME CODE REUSE WITH THE `test` FOLDER. Move `test` into `stefansearch`?
# Path to the root "TestData" folder. Assumes it is in the same directory
# as this script file
TESTDATA_PATH = pathlib.Path('test') / 'TestData'


def create_engine() -> SearchEngine:
    """Create search engine on a temp file."""
    temp_fd, temp_path = tempfile.mkstemp(suffix='.json')
    with open(temp_path, 'w') as f:
        f.write('{"doc_data": {}, "index": []}')
    return SearchEngine(pathlib.Path(temp_path))


# TODO: RENAME TO 'RUN_BENCHMARKS', THEN USE PYTEST CONFIG FILE TO ADD `RUN_BENCHMARKS` TO TEST DISCOVERY PATH
def run_benchmark():
    print(datetime.datetime.now())
    engine = create_engine()
    plays_dir = TESTDATA_PATH / 'Plays'
    for play_path in plays_dir.rglob('*'):
        if play_path.is_file():
            # print(play_path)
            engine.index_file(play_path, str(play_path.absolute()), encoding='utf-8')
    engine.commit()


def test_benchmark(benchmark):
    benchmark.pedantic(run_benchmark, rounds=10)
