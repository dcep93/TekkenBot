import collections
import enum

# not the best organization, but it works
class FrameDataEntry:
    unknown = '??'
    prefix_length = 4
    paddings = {'input': 16, 'move_str': 11}

    def __init__(self):
        self.input = self.unknown
        self.move_id = self.unknown
        self.move_str = self.unknown
        self.hit_type = self.unknown
        self.startup = self.unknown
        self.on_block = self.unknown
        self.on_normal_hit = self.unknown
        self.on_counter_hit = self.unknown
        self.recovery = self.unknown
        self.hit_recovery = self.unknown
        self.block_recovery = self.unknown

        self.fa = self.unknown

    @classmethod
    def printColumns(cls):
        # todo
        return
        obj = cls()
        for col in cls.columns:
            obj.__setattr__(col, col)
        string = obj.getString()
        prefix = " " * cls.prefix_length
        print(prefix + string)

    @staticmethod
    def WithPlusIfNeeded(value):
        v = str(value)
        if value >= 0:
            return '+' + v
        else:
            return v

    def getValue(self, field):
        return str(self.__getattribute__(field))

    def getPaddedField(self, field):
        v = self.getValue(field)
        diff = len(field) - len(v)
        if field in self.paddings: diff += self.paddings[field]
        if diff <= 0: return v
        before = int(diff / 2)
        after = diff - before
        return (' ' * before) + v + (' ' * after)

    def getString(self, columns=None):
        if columns is None: columns = self.columns
        values = [self.getPaddedField(i) for i in columns]
        return '|'.join(values)

class GlobalFrameDataEntry:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, frameDataEntry, floated):
        for field in DataColumns:
            self.recordField(field.name, frameDataEntry, floated)

    def recordField(self, field, frameDataEntry, floated):
        v = frameDataEntry.getValue(field)
        most_common = v
        if v == frameDataEntry.unknown:
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
            if v == frameDataEntry.unknown:
                new_v = most_common
            else:
                new_v = "(%s)" % (most_common)
            frameDataEntry.__setattr__(field, new_v)

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
