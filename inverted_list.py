from posting_list import PostingList, posting_list_from_json


class InvertedList:
    def __init__(self, term, posting_lists=None):
        self.term = term
        self.posting_lists = posting_lists if posting_lists else []  # list of PostingLists RENAME TO SOMETHING ELSE
        self.num_docs = len(self.posting_lists)
        self.num_postings = sum([len(posting_list.postings) for posting_list in self.posting_lists])
        self.curr_index = 0
        #print ('Inverted List: term is {}'.format(term))
        #print ('List is {}'.format(self.posting_lists))
        #print (self.num_docs, self.num_postings)

    def reset_pointer(self):
        self.curr_index = 0

    def add_posting(self, doc_id, term_index):
        # print ('{}: Adding posting at {} to doc {}'.format(self.term, term_index, doc_id))
        self.num_postings += 1
        if not self.posting_lists:
            self.posting_lists.append(PostingList(doc_id))
            self.posting_lists[0].append(term_index)
            self.num_docs = 1
            return
        if self.posting_lists[self.curr_index].doc_id == doc_id:
            self.posting_lists[self.curr_index].append(term_index)
        else:
            self.posting_lists.append(PostingList(doc_id))
            self.posting_lists[-1].append(term_index)
            self.curr_index += 1
            self.num_docs += 1

    def finished(self):
        return self.curr_index >= self.num_docs

    def curr_doc_id(self):
        return self.posting_lists[self.curr_index].doc_id if self.curr_index < self.num_docs else None

    # iterate forward through the list until reaching doc_id >= the given doc_id
    # returns whether the doc_id was found in the list
    def move_to(self, doc_id):
        while self.curr_index < self.num_docs and \
              self.posting_lists[self.curr_index].doc_id < doc_id:
            self.curr_index += 1
        return self.curr_index < self.num_docs and \
               self.posting_lists[self.curr_index].doc_id == doc_id

    # iterate through the list until the next doc_id
    def move_to_next(self):
        self.curr_index += 1
        return self.curr_index < self.num_docs

    def move_past(self, doc_id):
        while self.curr_index < self.num_docs and \
              self.posting_lists[self.curr_index].doc_id <= doc_id:
            self.curr_index += 1

    # get number of term occurrences in the current doc_id
    def get_term_freq(self):
        return len(self.posting_lists[self.curr_index].postings) if self.curr_index < self.num_docs else 0

    def __repr__(self):
        return '{}: curr_index {} / {}, curr_id {}' \
            .format(self.term, self.curr_index, self.num_docs - 1, self.posting_lists[self.curr_index].doc_id if self.curr_index < self.num_docs else None)

    # Serializes to a dict which can be JSON-ified
    def to_json(self):
        return { 'term': self.term,
                 'posting_list': [posting_list.to_json() for posting_list in self.posting_lists] }


def inverted_list_from_json(json_data):
    #print ('Posting list: {}'.format(json_data['posting_list']))
    return InvertedList(term=json_data['term'], \
                        posting_lists=[posting_list_from_json(p_list) for p_list in json_data['posting_list']])
