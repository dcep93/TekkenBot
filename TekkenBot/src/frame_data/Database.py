import json
import time

from . import Entry
from src.game_parser import MoveInfoEnums
from src.misc import Path

def initialize():
    for char in MoveInfoEnums.CharacterCodes:
        char_name = char.name.lower()
        if char_name.startswith("_"):
            continue
        filename = Path.path(f'./database/frame_data/{char_name}.json')
        try:
            with open(filename) as fh:
                database[char_name] = json.load(fh)
        except FileNotFoundError:
            database[char_name] = {}


def finish_match():
    # moves_done_by_opponent_this_match
    if moves_done_by_opponent_this_match["char_name"] is not None:
        filename = f'{int(time.time())}_{moves_done_by_opponent_this_match["char_name"]}'
        print(f"finish_match writing {filename}")
        with open(Path.path(f'./database/opponent_moves/{filename}.json'), 'w') as fh:
            json.dump(moves_done_by_opponent_this_match.pop("moves"), fh, indent=2)
        moves_done_by_opponent_this_match["char_name"] = None

    for char_name in list(characters_to_update.keys()):
        characters_to_update.pop(char_name)
        print(f"finish_match updating {char_name}")
        filename = Path.path(f'./database/frame_data/{char_name}.json')
        to_write = json.dumps(database[char_name], indent=2, sort_keys=True)
        with open(filename, 'w') as fh:
            fh.write(to_write)

def record_move(entry):
    raw_char_name = entry[Entry.DataColumns.char_name]
    if isinstance(raw_char_name, int):
        return
    char_name = raw_char_name.lower()

    # moves_done_by_opponent_this_match
    if not entry[Entry.DataColumns.is_player]:
        if moves_done_by_opponent_this_match["char_name"] == None:
            moves_done_by_opponent_this_match["char_name"] = char_name
            moves_done_by_opponent_this_match["moves"] = []
        moves_done_by_opponent_this_match["moves"].append(
            {k.name:v for k,v in entry.items()}
        )

    move_id = str(entry[Entry.DataColumns.move_id])
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
