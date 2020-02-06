import collections

from . import Entry

class History:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, entry):
        for field in Entry.DataColumns:
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

histories = collections.defaultdict(History)
# todo load from csv and generate csv
database = {}

def get(move_id):
    if move_id in database:
        return database[move_id]
    else:
        return None

def record(entry):
    move_id = entry[Entry.DataColumns.move_id]
    history = histories[move_id]
    history.record(entry)
