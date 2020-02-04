import collections

from . import Entry

class History:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, entry, floated):
        for field in Entry.DataColumns:
            self.record_field(field, entry, floated)

    def record_field(self, field, entry, floated):
        if field in entry:
            v = entry[field]
        else:
            v = None
        most_common = v
        if v is None:
            max_count = 0
        else:
            if floated:
                max_count = 0
            else:
                max_count = self.counts[field][v] + 1
                self.counts[field][v] = max_count
        for existing, count in self.counts[field].items():
            if count > max_count:
                most_common = existing
                max_count = count
        if most_common != v:
            if v is None:
                new_v = most_common
            else:
                new_v = "(%s)" % (most_common)
            entry[field] = new_v

histories = collections.defaultdict(History)
# todo load from csv and generate csv
database = {}

def get(move_id):
    if move_id in database:
        return database[move_id]
    else:
        return None

def record(entry, floated):
    move_id = entry[Entry.DataColumns.move_id]
    history = histories[move_id]
    history.record(entry, floated)
