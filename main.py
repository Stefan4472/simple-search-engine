import pathlib
from searchengine import SearchEngine


if __name__ == '__main__':
    # TODO: USE STOPWORDS?
    index = SearchEngine(pathlib.Path('index.json'))
    # index.index_file(r'C:\Users\Stefan\Github\Blog-Webcode\sample_post\post.md', 'sample-post')
    # index.index_file(r'C:\Users\Stefan\Github\Blog-Webcode\sample_post\post.md', 'sample-post-2')
    # index.index_file(r'C:\Users\Stefan\Github\Blog-Content\project-overview-c++-game\post.md', 'project-overview-c++-game')
    # index.index_file(r'C:\Users\Stefan\Github\Blog-Content\project-overview-spaceships\post.md', 'project-overview-spaceships')
    #
    # index.commit()
    print(index.search('game engine'))
