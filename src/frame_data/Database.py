import collections
import csv
import enum

from . import DataColumns
from misc import Path

@enum.unique
class Characters(enum.Enum):
    katarina = '[KATARINA]'

db_field_to_col = {
    'move_id': DataColumns.DataColumns.move_id
}

class History:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, entry):
        for field in DataColumns.DataColumns:
            self.record_field(field, entry)

    def record_field(self, field, entry):
        if field in entry:
            v = entry[field]
        else:
            v = None
        most_common = v
        if v is None:
            max_count = 0
        else:
            self.counts[field][v] += 1
            max_count = self.counts[field][v]
        for existing, count in self.counts[field].items():
            if count > max_count:
                most_common = existing
                max_count = count
        if most_common != v:
            if v is None:
                new_v = most_common
            else:
                new_v = "(%s)" % (v)
            entry[field] = new_v

def key(entry):
    return (entry[DataColumns.DataColumns.char_name], entry[DataColumns.DataColumns.move_id])

def populate_database():
    for character in Characters:
        char_name = character.value
        file_name = character.name
        path = Path.path('./database/%s.csv' % file_name)
        with open(path) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            data = [i for i in reader]
            header = data[0]
            for move in data[1:]:
                populate_move(char_name, header, move)

def populate_move(char_name, header, move):
    entry = {}
    entry[DataColumns.DataColumns.char_name] = char_name
    for i, db_field in enumerate(header):
        if db_field in db_field_to_col:
            col = db_field_to_col[db_field]
            val = move[i]
            entry[col] = val
    if not entry[DataColumns.DataColumns.move_id]:
        return
    k = key(entry)
    if k in database:
        print('%s already in database, skipping' % (k,))
    else: 
        database[k] = entry

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
populate_database()
