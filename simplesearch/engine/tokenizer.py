import typing
import pathlib
import simplesearch.engine.stemmer as stemmer


class Tokenizer:
    """
    Splits text into tokens that can be indexed.

    If word stopping is desired, provide a list of stopwords via the `stopwords`
    constructor argument.

    The `tokenize_file` and `tokenize_string` functions return a generator
    that will yield tokens one at a time, in order. Tokens will be stopped
    according to `stopwords` and stemmed via Porter Stemming.
    """
    def tokenize_string(
            self,
            string: str,
    ) -> typing.Generator[str, None, None]:
        """Return a generator that yields tokens from `string`."""
        for token in self._parse_tokens(string):
            yield stemmer.get_porter_stem(token)

    @staticmethod
    def _parse_tokens(string: str) -> typing.Generator[str, None, None]:
        """Parses and yields raw tokens from the given string."""
        in_token = False
        token_start = None

        for i, char in enumerate(string):
            is_tokenizable = Tokenizer._is_tokenizable(char)
            if is_tokenizable and not in_token:
                # Start of next token
                in_token = True
                token_start = i
            elif in_token and not is_tokenizable:
                # End of current token
                in_token = False
                yield string[token_start:i]
        # Get potential final token
        if in_token:
            yield string[token_start:len(string)]

    @staticmethod
    def _is_tokenizable(char: str) -> bool:
        """
        Return whether a char meets the rules for being in a token.

        `char` must have length of one!
        """
        if len(char) != 1:
            raise ValueError('`char` must have length one')
        return (
            'a' <= char <= 'z' or
            'A' <= char <= 'Z' or
            '0' <= char <= '9'
        )


# TODO: MOVE THIS SOMEWHERE ELSE
def read_stopwords_file(filepath: pathlib.Path) -> typing.Set[str]:
    """
    Takes the path to a stopwords file (one stopword per line) and
    reads the words into a set.
    """
    stop_set = set()
    for line in open(filepath, 'r'):
        stop_set.add(line.strip())
    return stop_set
