import json
import time

from . import Entry
from game_parser import MoveInfoEnums
from misc import Path

def initialize():
    for char in MoveInfoEnums.CharacterCodes:
        char_name = char.name.lower()
        if char_name.startswith("_"):
            continue
        filename = Path.path(f'./database/frame_data/{char_name}.json')
        try:
            with open(filename) as fh:
                database[char_name] = json.load(fh)
        except ValueError:
            database[char_name] = {}


def finish_match():
    # moves_done_by_opponent_this_match
    filename = f'{int(time.time())}_{moves_done_by_opponent_this_match["char_name"]}'
    print(f"finish_match writing {filename}")
    with open(Path.path(f'./database/opponent_moves/{filename}.json'), 'w') as fh:
        json.dump(moves_done_by_opponent_this_match.pop("moves"), fh, indent=2)
    moves_done_by_opponent_this_match["char_name"] = None

    for char_name in list(characters_to_update.keys()):
        characters_to_update.pop(char_name)
        print("finish_match updating {char_name}")
        filename = Path.path(f'./database/frame_data/{char_name}.json')
        with open(filename, 'w') as fh:
            json.dump(database[char_name], fh, indent=2)

def record_move(entry):
    char_name = entry[Entry.DataColumns.char_name]

    # moves_done_by_opponent_this_match
    if not entry[Entry.DataColumns.is_player]:
        if moves_done_by_opponent_this_match["char_name"] == None:
            moves_done_by_opponent_this_match["char_name"] = char_name
            moves_done_by_opponent_this_match["moves"] = []
        Database.moves_done_by_opponent_this_match["moves"].append(
            {k.name:v for k,v in entry.items()}
        )

    move_id = entry[Entry.DataColumns.move_id]
    char_dict = database[char_name]
    if move_id in char_dict:
        val = char_dict[move_id]
        already_correct = True
        if entry[Entry.DataColumns.block] is None:
            entry[Entry.DataColumns.block] = val[Entry.DataColumns.block.name]
        elif \
            val[Entry.DataColumns.block.name] is None or \
            val[Entry.DataColumns.block.name] > entry[Entry.DataColumns.block]:
            val[Entry.DataColumns.block.name] = entry[Entry.DataColumns.block]
            already_correct = False
        if val[Entry.DataColumns.startup.name] > entry[Entry.DataColumns.startup]:
            val[Entry.DataColumns.startup.name] = entry[Entry.DataColumns.startup]
            already_correct = False
        if already_correct:
            return
    char_dict[move_id] = {k.name: entry[k] for k in [
        Entry.DataColumns.startup,
        Entry.DataColumns.block,
    ]}
    characters_to_update[char_name] = True


database = {}
characters_to_update = {}
moves_done_by_opponent_this_match = {"char_name": None}
