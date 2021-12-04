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
    'THE LIFE OF KING HENRY THE FIFTH',
    'THE FIRST PART OF HENRY THE SIXTH',
    'THE SECOND PART OF KING HENRY THE SIXTH',
    'THE THIRD PART OF KING HENRY THE SIXTH',
    'KING HENRY THE EIGHTH',
    'KING JOHN',
    'THE TRAGEDY OF JULIUS CAESAR',
    'THE TRAGEDY OF KING LEAR',
    'LOVE’S LABOUR’S LOST',
    'THE TRAGEDY OF MACBETH',
    'MEASURE FOR MEASURE',
    'THE MERCHANT OF VENICE',
    'THE MERRY WIVES OF WINDSOR',
    'A MIDSUMMER NIGHT’S DREAM',
    'MUCH ADO ABOUT NOTHING',
    'THE TRAGEDY OF OTHELLO, MOOR OF VENICE',
    'PERICLES, PRINCE OF TYRE',
    'KING RICHARD THE SECOND',
    'KING RICHARD THE THIRD',
    'THE TRAGEDY OF ROMEO AND JULIET',
    'THE TAMING OF THE SHREW',
    'THE TEMPEST',
    'THE LIFE OF TIMON OF ATHENS',
    'THE TRAGEDY OF TITUS ANDRONICUS',
    'THE HISTORY OF TROILUS AND CRESSIDA',
    'TWELFTH NIGHT; OR, WHAT YOU WILL',
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
    r = re.compile(r'ACT ([IV]+)|SCENE ([IV]+)\.\s+')

    # Skip to the second 'ACT 1', which is where the actual play text starts
    text = text[text.find('ACT I\n') + 6:]
    text = text[text.find('ACT I\n'):]
    # TODO: LOOK FOR 'CHORUS', 'PROLOGUE', 'EPILOGUE', 'INDUCTION'

    curr_act = ''
    scenes: typing.List[Scene] = []
    matches = list(re.finditer(r, text))

    # Bit of a wacky loop because we need a look-ahead
    # TODO: CONVERT TO A LOOK-AHEAD LOOP (CLEANER)
    for i in range(len(matches) + 1):
        match = matches[i] if i < len(matches) else None
        prev_match = matches[i - 1] if i >= 1 else None
        # If the previous match was a scene, we need to collect it now
        if prev_match and prev_match.group().startswith('SCENE'):
            print(f'Found scene {prev_match.group(2)}')
            scene_name = prev_match.group(2)
            scene_start = prev_match.end()
            scene_end = match.start() if match else len(text)
            scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
        # If the current match is an 'ACT', we need to update state
        if match and match.group().startswith('ACT'):
            print(f'Found act {match.group(1)}')
            curr_act = match.group(1)
    return Play(title, scenes)


if __name__ == '__main__':
    with open('../shakespeare-gutenberg.txt', encoding='utf8') as f:
        text = f.read()

    sonnets_start = text.find('THE SONNETS', text.find('THE SONNETS') + 11) + 11
    sonnets_end = text.find('THE END', sonnets_start)
    text = text[sonnets_end+8:]
    end = text.find('*** END OF THE PROJECT GUTENBERG EBOOK THE COMPLETE WORKS OF WILLIAM SHAKESPEARE ***')
    text = text[:end]

    r = re.compile(r'ACT ([IV]+)|SCENE ([IV]+)\.\s+')
    next_play = text.find(TITLES[0])
    play_end = text.find(TITLES[1])

    # text = text[next_play:play_end]
    play = extract_play(TITLES[0], text[next_play:play_end])

    import pathlib
    data_path = pathlib.Path('../test/TestData/Plays')
    data_path.mkdir(exist_ok=True)
    play_path = data_path / TITLES[0].lower().replace('’', '').replace(' ', '-')
    play_path.mkdir(exist_ok=True)
    for scene in play.scenes:
        scene_path = play_path / f'ACT-{scene.act}-SCENE-{scene.name}.txt'
        with open(scene_path, 'w+', encoding='utf-8') as out:
            out.write(scene.text)
    # import sys
    # sys.exit()
    # # Skip to the second 'ACT 1', which is where the actual play text starts
    # text = text[text.find('ACT I\n')+6:]
    # text = text[text.find('ACT I\n'):]
    # # TODO: LOOK FOR 'CHORUS', 'PROLOGUE', 'EPILOGUE', 'INDUCTION'
    #
    # curr_act = ''
    # scenes: typing.List[Scene] = []
    # matches = list(re.finditer(r, text))
    #
    # # Bit of a wacky loop because we need a look-ahead
    # # TODO: CONVERT TO A LOOK-AHEAD LOOP (CLEANER)
    # for i in range(len(matches) + 1):
    #     match = matches[i] if i < len(matches) else None
    #     prev_match = matches[i - 1] if i >= 1 else None
    #     # If the previous match was a scene, we need to collect it now
    #     if prev_match and prev_match.group().startswith('SCENE'):
    #         print(f'Found scene {prev_match.group(2)}')
    #         scene_name = prev_match.group(2)
    #         scene_start = prev_match.end()
    #         scene_end = match.start() if match else len(text)
    #         scenes.append(Scene(scene_name, curr_act, text[scene_start:scene_end]))
    #     # If the current match is an 'ACT', we need to update state
    #     if match and match.group().startswith('ACT'):
    #         print(f'Found act {match.group(1)}')
    #         curr_act = match.group(1)
    # print('\n'.join([str(s) for s in scenes]))