# ONLY ITERATES FORWARD (for now). You can call reset()
# Stores the indexes of postings for a certain doc_id.
# This is used to record the indexes at which a certain token shows up
# in the document with the given doc_id.
class PostingList:
    def __init__(self, doc_id, postings=None):  # postings is a list of integer term indexes
        self.doc_id = doc_id
        self.postings = postings if postings else []

    def append(self, term_index):
        self.postings.append(term_index)

    # Serializes to a dict which can be JSON-ified
    def to_json(self):
        return { 'doc_id': self.doc_id, 'postings': self.postings }

    def __repr__(self):
        return str(self.postings)


# Deserializes a JSON-ified PostingList
def posting_list_from_json(json_data):
    #print ('Posting List received JSON: {}'.format(json_data))
    return PostingList(json_data['doc_id'], postings=json_data['postings'])