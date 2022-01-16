# simple-search-engine

A search engine implementation written in pure Python. This project has peeled off of [Stefan's Blog](https://github.com/Stefan4472/Stefans-Blog). Calling it "stefansearch" is not an act of vanity--I wanted to call this library "simplesearch", but that name was unfortunately taken on the Python Package Index :(

For testing, this project uses the works of William Shakespeare, sourced from Project Gutenberg (https://www.gutenberg.org/ebooks/100). I've written a script to parse the Project Gutenberg text into a directory structure that can be used for testing (no easy feat!).

## Setup

```
pip install -r requirements.txt
```

## Testing

Download the Project Gutenberg ebook:
```
cd bin
python download_test_data.py ../test/shakespeare-gutenberg.txt
```

Run the parser to generate the proper directory structure:
```
# from `bin`
python parse_shakespeare.py ../test/shakespeare-gutenberg.txt ../test/TestData
```

Execute unit tests:
```
# from project root
python -m pytest --benchmark-skip
```