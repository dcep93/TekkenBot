import collections

from . import FrameDataEntry

class GlobalFrameDataEntry:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, frameDataEntry, floated):
        for field in FrameDataEntry.DataColumns:
            self.recordField(field, frameDataEntry, floated)

    def recordField(self, field, frameDataEntry, floated):
        if field in frameDataEntry:
            v = frameDataEntry[field]
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
            frameDataEntry[field] = new_v

frameDataEntries = collections.defaultdict(GlobalFrameDataEntry)
# todo load from csv and generate csv
database = {}

def get(move_id):
    if move_id in database:
        return database[move_id]
    else:
        return None

def record(frameDataEntry, floated):
    move_id = frameDataEntry[FrameDataEntry.DataColumns.move_id]
    globalFrameDataEntry = frameDataEntries[move_id]
    globalFrameDataEntry.record(frameDataEntry, floated)
