import typing
from simplesearch.tokenizing.tokenizer import Tokenizer


class AlphaNumericTokenizer(Tokenizer):
    """A simple tokenizer that splits on non-alphanumeric characters."""
    def tokenize_string(self, string: str) -> typing.Generator[str, None, None]:
        """Return a generator that yields tokens from `string`."""
        in_token = False
        token_start = None
        for i, char in enumerate(string):
            is_tokenizable = self._is_tokenizable(char)
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
    def _parse_tokens(string: str) -> typing.Generator[str, None, None]:
        """Parses and yields raw tokens from the given string."""

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
