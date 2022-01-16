import pathlib
import tempfile
from stefansearch.engine.search_engine import SearchEngine


# Path to the root "TestData" folder. Assumes it is in the same directory
# as this script file
TESTDATA_PATH = pathlib.Path(__file__).parent / 'TestData'


def create_engine() -> SearchEngine:
    """Create search engine on a temp file."""
    temp_fd, temp_path = tempfile.mkstemp(suffix='.json')
    with open(temp_path, 'w') as f:
        f.write('{"doc_data": {}, "index": []}')
    return SearchEngine(pathlib.Path(temp_path))
