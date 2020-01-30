import collections
import enum

class GlobalFrameDataEntry:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, frameDataEntry, floated):
        for field in DataColumns:
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

@enum.unique
class DataColumns(enum.Enum):
    cmd = 'input command'
    move_id = 'internal move id number'
    move_str = 'internal move name'
    hit_type = 'attack type'
    startup = 'startup frames'
    block = 'frame advantage on block'
    normal = 'frame advantage on hit'
    counter = 'frame advantage on counter hit'
    w_rec = 'total number of frames in move'
    h_rec = 'frames before attacker can act'
    b_rec = 'frames before defender can act'
    fa = 'frame advantage right now'
