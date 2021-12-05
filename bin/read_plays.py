import re
import typing
import dataclasses as dc


# List of play titles (in order), which we must find in the text
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


def extract_play(title: str, text: str) -> Play:
    # Problems: TWELFTH NIGHT,
    r = re.compile(r'ACT ([IV]+)|SCENE ([IVX1-9]+)\.\s+|INDUCTION\.|PROLOGUE\.\n|CHORUS\.\n|EPILOGUE\.\n')
    # Check for table of contents.
    # We can actually do this simple search because the only instances of
    # "Contents" are to begin a Table of Contents
    has_table_of_contents = (text.find('Contents') > -1)
    # Check for a prologue.
    has_prologue = (text.find('PROLOGUE') > -1)
    is_special = (text.find('ACT') == -1)
    # If the play has a table of contents:
    # Skip to the second 'ACT 1', which is where the actual play text starts
    if has_table_of_contents and has_prologue:
        text = text[text.find('PROLOGUE'):]
        # print('HAS PROLOGUE')
    elif has_table_of_contents and not has_prologue:
        text = text[text.find('ACT I\n') + 6:]
        text = text[text.find('ACT I'):]  # NOTE: USED TO BE 'ACT I\n', BUT THIS DIDN'T MATCH TWELFTH NIGHT
    elif is_special:
        print(f'{title} IS SPECIAL')
        # TODO: need another look: Venus and Adonis, A Lover's Complaint, The Passionate Pilgrim, The Phoenix and the Turtle, The Rape of Lucrece
        # This is good enough for A Lover's Complaint, The Phoenix and the Turtle
        return Play(title, [Scene('', '', text[text.find(title)+len(title):])])
    # print(text[:1700])
    curr_act = ''
    scenes: typing.List[Scene] = []
    matches = list(re.finditer(r, text))

    # TODO: Midsummer Night's Dream needs special handling because there is a character named "PROLOGUE"
    if 'MIDSUMMER' in title:
        print(title)
        print('YO')
        print(text[:1000])
    # Bit of a wacky loop because we need a look-ahead
    # TODO: CONVERT TO A LOOK-AHEAD LOOP (CLEANER)
    for i in range(len(matches) + 1):
        match = matches[i] if i < len(matches) else None
        prev_match = matches[i - 1] if i >= 1 else None
        # If the previous match was a scene, we need to collect it now
        if prev_match and prev_match.group().startswith('SCENE'):
            # print(f'Found scene {prev_match.group(2)}')
            scene_name = prev_match.group(2)
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('INDUCTION'):
            scene_name = 'INDUCTION'
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('PROLOGUE'):
            # print('Got prologue')
            scene_name = 'PROLOGUE'
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('CHORUS'):
            # print('Got chorus')
            scene_name = 'CHORUS'
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
        elif prev_match and prev_match.group().startswith('EPILOGUE'):
            # print('Got epilogue')
            scene_name = 'EPILOGUE'
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
        # If the current match is an 'ACT', we need to update state
        if match and match.group().startswith('ACT'):
            # print(f'Found act {match.group(1)}')
            curr_act = match.group(1)
    return Play(title, scenes)


if __name__ == '__main__':
    with open('../shakespeare-gutenberg.txt', encoding='utf8') as f:
        text = f.read()

    # Trim out the sonnets at the beginning and the license text at the end
    sonnets_start = text.find('THE SONNETS', text.find('THE SONNETS') + 11) + 11
    sonnets_end = text.find('THE END', sonnets_start)
    text = text[sonnets_end+8:text.find('***END OF THE PROJECT GUTENBERG EBOOK')]

    for play_index in range(len(TITLES)):
        # Find text indexes where the play starts and ends
        play_start = text.find(TITLES[play_index])
        play_end = text.find(TITLES[play_index + 1]) if play_index < len(TITLES) - 1 else len(text)
        # print(TITLES[play_index])
        play = extract_play(TITLES[play_index], text[play_start:play_end])

        import pathlib
        data_path = pathlib.Path('../test/TestData/Plays')
        data_path.mkdir(exist_ok=True)
        play_path = data_path / TITLES[play_index].lower().replace('’', '').replace(' ', '-').replace(':', '').replace(',', '')
        play_path.mkdir(exist_ok=True)
        for scene in play.scenes:
            scene_path = play_path / f'ACT-{scene.act}-SCENE-{scene.name}.txt'
            with open(scene_path, 'w+', encoding='utf-8') as out:
                out.write(scene.text)
