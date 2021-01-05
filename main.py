# Test script  TODO: NEEDS TO BE UPDATED
import json
from index import Index, restore_index_from_file

if __name__ == '__main__':
    print ('Running database main.py')
    index = Index()
    index.index_file(r'C:\Users\Stefan\Github\Blog-Webcode\sample_post\post.md', 'sample-post')
    index.index_file(r'C:\Users\Stefan\Github\Blog-Webcode\sample_post\post.md', 'sample-post-2')
    index.index_file(r'C:\Users\Stefan\Github\Blog-Content\project-overview-c++-game\post.md', 'project-overview-c++-game')
    index.index_file(r'C:\Users\Stefan\Github\Blog-Content\project-overview-spaceships\post.md', 'project-overview-spaceships')

    # TODO: USE A RELATIVE PATH FROM THE DIRECTORY ROOT
    index.save_to_file('instance/index.json')
    r_index = restore_index_from_file('instance/index.json')  # TODO: DOUBLE-CHECK RESTORATION SETS CORRECT VALUES
    print ()
    print (index.num_docs, r_index.num_docs)
    print (index.num_terms, r_index.num_terms)

    queries = ['game engine']

    # with open('ql.trecrun') as output_file:
    for i in range(len(queries)):
        query = queries[i]
        results = index.search(query)
        # verifies that the results are equivalent
        print()
        print (results)
        print()
        results2 = r_index.search(query)
        print (results2)
