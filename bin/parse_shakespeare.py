"""
Parses Project Gutenberg's "The Complete Works of William Shakespeare"
text, which should have been downloaded via `download_test_data.py`.
Saves data into a directory structure that can be used when running tests.
"""
import pathlib
import click
import dataclasses as dc
import re
import typing


# List of play titles (in order), which we must find in the text.
# These must be spelled exactly as they appear in the text.
TITLES = [
    'ALL’S WELL THAT ENDS WELL',
    'ANTONY AND CLEOPATRA',
    'AS YOU LIKE IT',
    'THE COMEDY OF ERRORS',
    'THE TRAGEDY OF CORIOLANUS',
    'CYMBELINE',
    'THE TRAGEDY OF HAMLET, PRINCE OF DENMARK',
    'THE FIRST PART OF KING HENRY THE FOURTH',
    'THE SECOND PART OF KING HENRY THE FOURTH',
    'THE LIFE OF KING HENRY V',
    'THE FIRST PART OF HENRY THE SIXTH',
    'THE SECOND PART OF KING HENRY THE SIXTH',
    'THE THIRD PART OF KING HENRY THE SIXTH',
    'KING HENRY THE EIGHTH',
    'KING JOHN',
    'THE TRAGEDY OF JULIUS CAESAR',
    'THE TRAGEDY OF KING LEAR',
    'LOVE’S LABOUR’S LOST',
    'MACBETH',
    'MEASURE FOR MEASURE',
    'THE MERCHANT OF VENICE',
    'THE MERRY WIVES OF WINDSOR',
    'A MIDSUMMER NIGHT’S DREAM',
    'MUCH ADO ABOUT NOTHING',
    'OTHELLO, THE MOOR OF VENICE',
    'PERICLES, PRINCE OF TYRE',
    'THE LIFE AND DEATH OF KING RICHARD THE SECOND',
    'KING RICHARD THE THIRD',
    'THE TRAGEDY OF ROMEO AND JULIET',
    'THE TAMING OF THE SHREW',
    'THE TEMPEST',
    'THE LIFE OF TIMON OF ATHENS',
    'THE TRAGEDY OF TITUS ANDRONICUS',
    'THE HISTORY OF TROILUS AND CRESSIDA',
    'TWELFTH NIGHT: OR, WHAT YOU WILL',
    'THE TWO GENTLEMEN OF VERONA',
    'THE TWO NOBLE KINSMEN',
    'THE WINTER’S TALE',
    'A LOVER’S COMPLAINT',
    'THE PASSIONATE PILGRIM',
    'THE PHOENIX AND THE TURTLE',
    'THE RAPE OF LUCRECE',
    'VENUS AND ADONIS',
]


@dc.dataclass
class Scene:
    name: str
    act: str
    text: str


@dc.dataclass
class Play:
    title: str
    scenes: typing.List[Scene]


@dc.dataclass
class Sonnet:
    number: int
    text: str


def parse_plays(text: str) -> typing.List[Play]:
    plays: typing.List[Play] = []
    for play_index in range(len(TITLES)):
        # Find text indexes where the play starts and ends
        play_start = text.find(TITLES[play_index])
        play_end = text.find(TITLES[play_index + 1]) if play_index < len(TITLES) - 1 else len(text)
        plays.append(parse_play(TITLES[play_index], text[play_start:play_end]))
    return plays


def parse_play(title: str, text: str) -> Play:
    """
    Parse the given `text` into a `Play` instance.

    This is pretty tricky because the Project Gutenberg text does not use
    any consistent conventions.
    """
    # Regex that matches "sections" found in the text.
    # We add the negative lookahead to "CHORUS" to avoid matching the persona,
    # "CHORUS", who shows up in A Midsummer Night's Dream. The CHORUS *persona*
    # always has four spaces on the next line, while the CHORUS *scenes* don't.
    # We match an optional period after "SCENE" because two scenes in
    # King Richard are missing a trailing period.
    r = re.compile(r'ACT ([IV]+)|SCENE ([IVX1-9]+)\.?\s+|INDUCTION\.|PROLOGUE\.\n|CHORUS\.\n^(?!    )|EPILOGUE\.\n')
    # Check for table of contents.
    # We can actually do this simple search because the only instances of
    # "Contents" are to begin a Table of Contents
    has_table_of_contents = (text.find('Contents') > -1)
    # Check for a prologue.
    # Note: we have to distinguish a *scene* prologue from the character named
    # "PROLOGUE" in A Midsummer Night's Dream.
    # We do this by checking for the period afterwards (the character name
    # isn't followed by a period).
    has_prologue = (text.find('PROLOGUE.') > -1)
    # A play is "special" if there are no Acts or Scenes defined.
    is_special = (text.find('ACT') == -1)

    # Play has a table of contents and a prologue: skip to after the prologue
    if has_table_of_contents and has_prologue:
        text = text[text.find('PROLOGUE.'):]
    # Play has a table of contents, and no prologue:
    # skip to the second 'ACT 1', which is where the actual play text starts
    elif has_table_of_contents and not has_prologue:
        text = text[text.find('ACT I\n') + 6:]
        # NOTE: used to find 'ACT I\n', but this didn't work for Twelfth Night
        text = text[text.find('ACT I'):]
    # Handle special case (no Acts or Scenes). We just take these as-is.
    # The "special" works are: A Lover's Complaint, The Passionate Pilgrim,
    # The Phoenix and the Turtle, The Rape of Lucrece, and Venus and Adonis
    elif is_special:
        return Play(title, [Scene('', '', text[text.find(title)+len(title):].strip())])

    curr_act = ''
    scenes: typing.List[Scene] = []
    matches = list(re.finditer(r, text))

    # Split play into "sections". Also track current Act number.
    # This is a bit of a wacky loop because we need to look ahead.
    # TODO: CONVERT TO A LOOK-AHEAD LOOP (CLEANER)
    for i in range(len(matches) + 1):
        match = matches[i] if i < len(matches) else None
        prev_match = matches[i - 1] if i >= 1 else None
        # If the previous match was a scene, we need to collect it now
        if prev_match and prev_match.group().startswith('SCENE'):
            scene_name = prev_match.group(2)
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('INDUCTION'):
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene('INDUCTION', curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('PROLOGUE'):
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene('PROLOGUE', curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('CHORUS'):
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene('CHORUS', curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('EPILOGUE'):
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene('EPILOGUE', curr_act, text[scene_start:scene_end]))
        # If the current match is an 'ACT', we need to update state
        if match and match.group().startswith('ACT'):
            curr_act = match.group(1)
    return Play(title, scenes)


def parse_sonnets(text: str) -> typing.List[Sonnet]:
    sonnets: typing.List[Sonnet] = []
    number_pattern = re.compile(r'(\d+)')
    title_matches = list(re.finditer(number_pattern, text))
    for i in range(len(title_matches) - 1):
        title_match = title_matches[i]
        next_title_match = title_matches[i + 1]
        sonnet_number = int(title_match.group())
        sonnet_text = text[title_match.end():next_title_match.start()].strip()
        sonnets.append(Sonnet(sonnet_number, sonnet_text))
    # Get the final sonnet
    title_match = title_matches[-1]
    sonnet_number = int(title_match.group())
    sonnet_text = text[title_match.end():].strip()
    sonnets.append(Sonnet(sonnet_number, sonnet_text))
    return sonnets


def parse_shakespeare(text: str) -> typing.Tuple[typing.List[Sonnet], typing.List[Play]]:
    """
    Given the whole Project Gutenberg text, parses and returns a
    list of parsed `Sonnet` and a list of `Play` instances.
    """
    sonnets_start = text.find('THE SONNETS', text.find('THE SONNETS') + 11) + 11
    sonnets_end = text.find('THE END', sonnets_start)
    sonnets = parse_sonnets(text[sonnets_start:sonnets_end])

    plays_start = sonnets_end + 8
    plays_end = text.find('*** END OF THE PROJECT GUTENBERG EBOOK')
    plays = parse_plays(text[plays_start:plays_end])
    return sonnets, plays


@click.command()
@click.argument('file_path', type=click.Path(dir_okay=False, file_okay=True, exists=True, path_type=pathlib.Path))
@click.argument('save_path', type=click.Path(dir_okay=True, file_okay=False, path_type=pathlib.Path))
def parse_shakespeare_cmd(
        file_path: pathlib.Path,
        save_path: pathlib.Path,
):
    """
    Read the Project Gutenberg "The Complete Works of William Shakespeare"
    text and save it into the desired directory structure for testing.
    This program will not overwrite existing data in SAVE_PATH--generally,
    you should delete the contents before running this program.

    FILE_PATH: path to the "The Complete Works of William Shakespeare" text file
    SAVE_PATH: path to where the directory structure should be created.
    """
    with open(file_path, encoding='utf8') as f:
        sonnets, plays = parse_shakespeare(f.read())

    save_path.mkdir(exist_ok=True)
    sonnets_path = save_path / 'Sonnets'
    sonnets_path.mkdir()
    for sonnet in sonnets:
        with open(sonnets_path / (str(sonnet.number) + '.txt'), 'w+', encoding='utf8') as out:
            out.write(sonnet.text)

    plays_path = save_path / 'Plays'
    plays_path.mkdir(exist_ok=True)
    for play in plays:
        # "Regularize" the play name for creating a path
        regularized_name = play.title.lower().replace('’', '')\
            .replace(' ', '-').replace(':', '').replace(',', '')
        play_path = plays_path / regularized_name
        play_path.mkdir(exist_ok=True)
        for scene in play.scenes:
            if scene.act and scene.name:
                scene_path = play_path / f'ACT-{scene.act}-SCENE-{scene.name}.txt'
            elif scene.name:
                scene_path = play_path / f'{scene.name}.txt'
            else:
                scene_path = play_path / f'{regularized_name}.txt'
            with open(scene_path, 'w+', encoding='utf-8') as out:
                out.write(scene.text)


if __name__ == '__main__':
    parse_shakespeare_cmd()
