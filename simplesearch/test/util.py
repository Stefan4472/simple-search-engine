import pathlib
import tempfile
from simplesearch.engine.search_engine import SearchEngine


def create_engine() -> SearchEngine:
    """Create search engine on a temp file."""
    temp_fd, temp_path = tempfile.mkstemp(suffix='.json')
    with open(temp_path, 'w') as f:
        f.write('{"doc_data": {}, "index": []}')
    return SearchEngine(pathlib.Path(temp_path))
