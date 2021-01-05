import typing
import stemmer
import pathlib


'''
Used to split text from a file into tokens that can be indexed. Initialize
with the path to a stopword file, if word stopping is desired (the stopword
file should have one stopword per line). Then call the tokenize() generator
function, which returns tokens one at a time, in order. This allows
constructions such as "for token in ___.tokenize()".
The tokenize() function relies on a helper function, _get_next_unprocessed_token,
to feed in the next parsed token from the file. This is also a generator
function, which allows the whole process to be done lazily.
So, the whole process performs tokenization->stopword filtering->Porter stemming.
'''
class Tokenizer:
    def __init__(self, stopword_filepath: typing.Optional[pathlib.Path] = None):
        self.stopword_filepath = stopword_filepath
        # set of stopwords
        self.stopwords = _generate_stopword_set(stopword_filepath)

    # lazily tokenize the given filepath using current stopword set
    def tokenize_file(self, filepath: pathlib.Path, encoding: str = 'utf8'):
        file_text = ''
        # Read file
        with open(filepath, encoding=encoding) as text_file:
            file_text = text_file.read()
        # Iterate through tokens in file
        for token in self._get_next_unprocessed_token(file_text):
            # ignore if stopword
            if self._is_stopword(token):
                continue
            # stem and return otherwise
            else:
                yield stemmer.get_porter_stem(token)

    # Lazily tokenize the given string using the current stopword set
    def tokenize_string(self, string):
        # read next token from string
        for token in self._get_next_unprocessed_token(string):
            # ignore if stopword
            if self._is_stopword(token):
                continue
            # stem and return otherwise
            else:
                yield stemmer.get_porter_stem(token)

    # returns whether the given word is a stopword, i.e. in
    # the set of self.stopwords
    def _is_stopword(self, word):
        return word in self.stopwords

    # generator for unprocessed tokens read from a string
    def _get_next_unprocessed_token(self, string):
        for line in string.splitlines():
            in_token = False
            in_abbreviation = False
            curr_token = ''
            i = 0
            while i < len(line):
                next_char = line[i]
                tokenizable = _is_tokenizable(next_char)
                # found next char in token
                if tokenizable and in_token:
                    curr_token += next_char
                # next token found
                elif tokenizable and not in_token:
                    # check for abbreviation
                    found_abbrv, abbreviation = _has_abbreviation(line, i)
                    if found_abbrv:  # consume
                        i += len(abbreviation)
                        yield abbreviation.replace('.', '').lower()
                    else:  # start next token
                        in_token = True
                        curr_token = '' + next_char
                # found end of token
                elif not tokenizable and in_token:
                    in_token = False
                    yield curr_token.lower()
                i += 1
            # Yield the token at the end of the string
            if in_token and curr_token:
                yield curr_token


# return whether a char meets the rules for being in a token
def _is_tokenizable(char):
    return (char >= 'a' and char <= 'z') or \
        (char >= 'A' and char <= 'Z') or \
        (char >= '0' and char <= '9')


# looks for pattern ([tokenizable char][period]){2,} in the string *starting
# at the given index*
# return tuple (bool found, string abbreviation)
def _has_abbreviation(string, index):
    num_letters = 0
    need_period = False
    for i in range(index, len(string)):
        if need_period and string[i] == '.':
            need_period = False
            num_letters += 1
        elif not need_period and string[i].isalpha():
            need_period = True
        else:
            break
    return (True, string[index:i]) if num_letters >= 2 else (False, '')


# takes the path to a stopword file (one stopword per line) and
# reads the words into a set
# returns the created set of stopwords, which may be empty
def _generate_stopword_set(filepath: typing.Optional[pathlib.Path]):
    stop_set = set()
    if filepath is not None:
        for line in open(filepath, 'r'):
            stop_set.add(line.strip())

    return stop_set
