"""
Generate test data from Project Gutenberg's "The Complete Works of William
Shakespeare by William Shakespeare" ebook.

https://www.gutenberg.org/ebooks/100
Plain text: https://www.gutenberg.org/files/100/100-0.txt
"""
import re
import pathlib
import click
import shutil
import urllib.request
import dataclasses as dc


@dc.dataclass
class Sonnet:
    number: int
    text: str


@click.command()
@click.argument('save_path', type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path))
@click.option('--allow_overwrite', type=bool, default=False, help='Allow the program to overwrite existing test data')
@click.option('--ebook_path', type=click.Path(exists=True, dir_okay=False, file_okay=True, path_type=pathlib.Path), help='Use a local copy of the Guthenberg Shakespeare Ebook')
def cli(
        save_path: pathlib.Path,
        allow_overwrite: bool,
        ebook_path: pathlib.Path,
):
    if save_path.exists() and not allow_overwrite:
        raise ValueError('SAVE_PATH exists, but `allow_overwrite` is not set to TRUE')

    # Download text if not specified by user
    if not ebook_path:
        ebook_path = 'shakespeare-gutenberg.txt'
        text = download_text()
        with open(ebook_path, 'wb+') as out:
            out.write(text)

    # Generate sonnets
    with open(ebook_path, encoding='utf8') as f:
        text = f.read()
    sonnets_start = text.find('THE SONNETS', text.find('THE SONNETS')+11)+11
    sonnets_end = text.find('THE END', sonnets_start)
    number_pattern = re.compile(r'(\d+)')

    sonnets_text = text[sonnets_start:sonnets_end]
    # curr_start = re.search(number_pattern, text)
    title_matches = list(re.finditer(number_pattern, sonnets_text))
    sonnets = []
    for i in range(len(title_matches) - 1):
        title_match = title_matches[i]
        next_title_match = title_matches[i+1]
        sonnet_number = int(title_match.group())
        sonnet_text = sonnets_text[title_match.end():next_title_match.start()].strip()
        sonnets.append(Sonnet(sonnet_number, sonnet_text))
    # Get the final sonnet
    title_match = title_matches[-1]
    sonnet_number = int(title_match.group())
    sonnet_text = sonnets_text[title_match.end():].strip()
    sonnets.append(Sonnet(sonnet_number, sonnet_text))

    # Clear existing save data
    if save_path.exists():
        shutil.rmtree(save_path)
    save_path.mkdir(parents=True)

    sonnets_path = save_path / 'Sonnets'
    sonnets_path.mkdir()
    for sonnet in sonnets:
        with open(sonnets_path / (str(sonnet.number) + '.txt'), 'w+', encoding='utf8') as out:
            out.write(sonnet.text)


def download_text() -> bytes:
    """
    Download the Shakespeare file from Project Guthenberg
    and return the path to it.
    """
    with urllib.request.urlopen(r'https://www.gutenberg.org/files/100/100-0.txt') as f:
        return f.read()


if __name__ == '__main__':
    cli()