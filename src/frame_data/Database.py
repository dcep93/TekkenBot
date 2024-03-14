import json

from . import DataColumns
from misc import Path

def initialize():
    return

def populate_character(character_name):
    existing = [i for i in database.keys() if i[0] == character_name]
    for i in existing:
        del database[i]
    path = Path.path('./frame_data/%s.csv' % character_name)
    with open(path, encoding='UTF-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        data = [i for i in reader if i]
        raw_moves[Characters[character_name]] = data
    header = data[0]
    for move in data[1:]:
        populate_move(character_name, header, move)

def populate_move(char_name, header, move):
    entry = {}
    entry[DataColumns.DataColumns.char_name] = char_name
    for i, db_field in enumerate(header):
        if i >= len(move): break
        if db_field in db_field_to_col:
            col = db_field_to_col[db_field]
            val = move[i]
            entry[col] = val
    move_ids_raw = entry[DataColumns.DataColumns.move_id]
    if not move_ids_raw:
        return
    move_ids = move_ids_raw.split(',')
    for move_id in move_ids:
        entry_to_save = dict(entry)
        entry_to_save[DataColumns.DataColumns.move_id] = move_id
        k = key(entry_to_save)
        if k in database:
            print('%s already in database, skipping' % (k,))
        else:
            database[k] = entry_to_save

def load(entry):
    k = key(entry)
    if k in database:
        found = database[k]
        for field, value in found.items():
            entry[field] = value
        return True
    else:
        return False

def record(entry):
    k = key(entry)
    history = histories[k]
    history.record(entry)

histories = collections.defaultdict(History)
database = {}
raw_moves = {}
