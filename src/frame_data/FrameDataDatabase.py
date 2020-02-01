import collections

from . import FrameDataEntry

class GlobalFrameDataEntry:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, frame_data_entry, floated):
        for field in FrameDataEntry.DataColumns:
            self.record_field(field, frame_data_entry, floated)

    def record_field(self, field, frame_data_entry, floated):
        if field in frame_data_entry:
            v = frame_data_entry[field]
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
        for record, count in self.counts[field].items():
            if count > max_count:
                most_common = record
                max_count = count
        if most_common != v:
            if v is None:
                new_v = most_common
            else:
                new_v = "(%s)" % (most_common)
            frame_data_entry[field] = new_v

frame_data_entries = collections.defaultdict(GlobalFrameDataEntry)
# todo load from csv and generate csv
database = {}

def get(move_id):
    if move_id in database:
        return database[move_id]
    else:
        return None

def record(frame_data_entry, floated):
    move_id = frame_data_entry[FrameDataEntry.DataColumns.move_id]
    GlobalFrameDataEntry = frame_data_entries[move_id]
    GlobalFrameDataEntry.record(frame_data_entry, floated)
