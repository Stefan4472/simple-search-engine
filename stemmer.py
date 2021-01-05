'''
Implementation of Porter Stemming, Step 1.
get_porter_stem(word) is the main, public-facing function. It delegates the
job of stemming to _porter_1a(word) and _porter_2a(word), which have yet more
private helper functions to find the longest applicable suffix to be removed.
Each of these private helper functions returns a tuple (num chars in suffix,
result of applying rule). If the rule is not applied, the tuple will be
(0, original term)
'''
# set of vowel characters, lowercase
VOWELS = { 'a', 'e', 'i', 'o', 'u' }  # TODO: ADD Y?

# takes a word and returns its Porter stem
def get_porter_stem(word):
    word = _porter_1a(word)
    word = _porter_2a(word)
    return word

# execute step 1a of Porter stemming
def _porter_1a(word):
    # if suffix is 'us' or 'ss' do nothing
    if word.endswith('us') or word.endswith('ss'):
        return word
    # attempt sses, ied/ies, and s rules in order
    for rule in [_p1a_sses, _p1a_ied_ies, _p1a_s]:
        len_suffix, stemmed_word = rule(word)
        if len_suffix > 0:
            return stemmed_word
    # no match: return original word
    return word

# replace 'sses' by 'ss'
def _p1a_sses(word):
    if word.endswith('sses'):
        return (4, word[:-2])
    return (0, word)

# delete 's' if the preceding word part contains a vowel
# not immediately before the 's'
def _p1a_s(word):
    if word.endswith('s') and _contains_vowel(word[:-1]) and not word[-2] in VOWELS:
        return (1, word[:-1])
    return (0, word)

# replace 'ied' or 'ies' by 'i' if preceded by more than one
# letter, otherwise by 'ie'
def _p1a_ied_ies(word):
    if word.endswith('ied') or word.endswith('ies'):
        if len(word) > 4:
            return (3, word[:-3] + 'i')
        else:
            return (3, word[:-3] + 'ie')
    return (0, word)

def _porter_2a(word):
    best_stem = word
    longest_suffix_rmvd = 0
    # attempt eed/eedly, ed/edly/ing/ingly rules
    # track the longest suffix removed
    for rule in [_p1b_eed_eedly, _p1b_ed_edly_ing_ingly]:
        len_suffix, stemmed_word = rule(word)
        if len_suffix > longest_suffix_rmvd:
            longest_suffix_rmvd = len_suffix
            best_stem = stemmed_word
    return best_stem

# replace 'eed', 'eedly' by 'ee' if it is in the part of the
# word after the first non-vowel following a vowel
def _p1b_eed_eedly(word):
    if word.endswith('eed'):
        test_word = word[:-3]
    elif word.endswith('eedly'):
        test_word = word[:-5]
    else:
        return (0, word)
    first_vowel_index = _find_first_vowel(test_word)
    if first_vowel_index == -1:
        return (0, word)
    else:
        for index in range(first_vowel_index + 1, len(test_word)):
            if test_word[index] not in VOWELS:
                # condition met
                return (3, word[:-1]) if word.endswith('eed') else (5, word[:-3])
        return (0, word)

# delete 'ed', 'edly', 'ing', 'ingly' if the preceeding word part
# contains a vowel, and then if the word inds in 'at', 'bl', or 'iz'
# add 'e', or if the word ends with a double letter that is not 'll',
# 'ss', or 'zz', remove the last letter, or if the word is short, add 'e'
def _p1b_ed_edly_ing_ingly(word):
    if word.endswith('ed'):
        suffix_len = 2
    elif word.endswith('edly'):
        suffix_len = 4
    elif word.endswith('ing'):
        suffix_len = 3
    elif word.endswith('ingly'):
        suffix_len = 5
    else:
        return (0, word)
    # remove suffix for further tests
    test_word = word[:-suffix_len]

    if _contains_vowel(test_word):
        if test_word.endswith('at') or test_word.endswith('bl') or \
            test_word.endswith('iz'):
            return (suffix_len, test_word + 'e')
        elif test_word[-1] == test_word[-2] and test_word[-1] != 'l' and \
            test_word[-1] != 's' and test_word[-1] != 'z':
            return (suffix_len, test_word[:-1])
        elif len(test_word) < 4:
            return (suffix_len, test_word + 'e')
        else:
            return (suffix_len, test_word)
    else:
        return (0, word)

# check if given string contains a vowel 
def _contains_vowel(word):
    return any(char in VOWELS for char in word)

# return index of first vowel found in the word,
# or -1 if no vowel is found
def _find_first_vowel(word):
    index = 0
    for char in word:
        if char in VOWELS:
            return index
        index += 1
    return -1
