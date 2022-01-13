"""
Generate test data from Project Gutenberg's "The Complete Works of William
Shakespeare by William Shakespeare" ebook.

https://www.gutenberg.org/ebooks/100
Plain text: https://www.gutenberg.org/files/100/100-0.txt
"""
import pathlib
import click
import urllib.request


@click.command()
@click.argument('save_path', type=click.Path(dir_okay=False, file_okay=True, path_type=pathlib.Path))
def download_shakespeare(save_path: pathlib.Path):
    """
    Download "The Complete Works of William Shakespeare" from Project Gutenberg
    and save the text file to SAVE_PATH.

    This program will create a file at SAVE_PATH if none exists, or overwrite
    an existing file at SAVE_PATH.
    """
    click.echo(f'Downloading to {save_path.resolve()}...')
    with urllib.request.urlopen(r'https://www.gutenberg.org/files/100/100-0.txt') as f:
        with open(save_path, 'wb+') as out:
            out.write(f.read())
    click.echo('Done')


if __name__ == '__main__':
    download_shakespeare()
