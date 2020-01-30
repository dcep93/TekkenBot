import collections
import enum

class GlobalFrameDataEntry:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, frameDataEntry, floated):
        for field in DataColumns:
            self.recordField(field.name, frameDataEntry, floated)

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
    input = 'input command'
    move_id = 'internal move id number'
    move_str = 'internal move name'
    hit_type = 'attack type'
    startup = 'startup frames'
    on_block = 'frame advantage on block'
    on_normal_hit = 'frame advantage on hit'
    on_counter_hit = 'frame advantage on counter hit'
    recovery = 'total number of frames in move'
    hit_recovery = 'frames before attacker can act'
    block_recovery = 'frames before defender can act'
    fa = 'frame advantage right now'
