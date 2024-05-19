from ..frame_data import Entry
from ..game_parser import MoveInfoEnums
from ..misc import Path

import json
import time
import typing


class Database:
    def __init__(self) -> None:
        self.database: typing.Dict[str,
                                   typing.Dict[str, typing.Dict[str, str]]] = {}
        self.characters_to_update: typing.Dict[str, bool] = {}
        self.opp_char: typing.Optional[str] = None
        self.opp_moves: typing.Optional[typing.List[typing.Dict[str, str]]] = None

        for char in MoveInfoEnums.CharacterCodes:
            char_name = char.name.lower()
            if char_name.startswith("_"):
                continue
            filename = Path.path(f'./database/frame_data/{char_name}.json')
            try:
                with open(filename) as fh:
                    self.database[char_name] = json.load(fh)
            except FileNotFoundError:
                self.database[char_name] = {}

    def finish_match(self) -> None:
        # moves_done_by_opponent_this_match
        if self.opp_char is not None:
            filename = f'{int(time.time())}_{self.opp_char}'
            print(f"finish_match writing {filename}")
            with open(Path.path(f'./database/opponent_moves/{filename}.json'), 'w') as fh:
                json.dump(self.opp_moves, fh, indent=2)
                self.opp_char = None
                self.opp_moves = None

        for char_name in list(self.characters_to_update.keys()):
            self.characters_to_update.pop(char_name)
            print(f"finish_match updating {char_name}")
            filename = Path.path(f'./database/frame_data/{char_name}.json')
            to_write = json.dumps(
                self.database[char_name], indent=2, sort_keys=True)
            with open(filename, 'w') as fh:
                fh.write(to_write)

    def record_move(self, entry: Entry.Entry) -> None:
        raw_char_name = entry[Entry.DataColumns.char_name]
        if isinstance(raw_char_name, int):
            return
        char_name = raw_char_name.lower()

        # moves_done_by_opponent_this_match
        if not entry[Entry.DataColumns._is_player]:
            if self.opp_char == None:
                self.opp_char = char_name
                self.opp_moves = []
            assert (not self.opp_moves is None)
            self.opp_moves.append(
                {k.name: v for k, v in entry.items()}
            )

        move_id = str(entry[Entry.DataColumns.move_id])
        char_dict = self.database[char_name]
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
        self.characters_to_update[char_name] = True


d = Database()
