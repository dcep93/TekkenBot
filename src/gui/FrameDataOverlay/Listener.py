import collections
import enum

from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ComplexMoveStates

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

class FrameDataListener:
    def __init__(self, printer):
        FrameDataEntry.printColumns()
        self.listeners = [PlayerListener(i, printer) for i in [True, False]]

    def update(self, gameState):
        for listener in self.listeners:
            listener.Update(gameState)

class PlayerListener:
    def __init__(self, isP1, printer):
        self.isP1 = isP1
        self.printer = printer

        self.active_frame_wait = 1

    def Update(self, gameState):
        if self.ShouldDetermineFrameData(gameState):
            self.DetermineFrameData(gameState)

    def ShouldDetermineFrameData(self, gameState):
        if gameState.get(not self.isP1).IsBlocking() or gameState.get(not self.isP1).IsGettingHit() or gameState.get(not self.isP1).IsInThrowing() or gameState.get(not self.isP1).IsBeingKnockedDown() or gameState.get(not self.isP1).IsGettingWallSplatted():
            if gameState.DidIdChangeXMovesAgo(not self.isP1, self.active_frame_wait) or gameState.DidTimerInterruptXMovesAgo(not self.isP1, self.active_frame_wait):
                    return True
        return False

    def DetermineFrameData(self, gameState):
        is_recovering_before_long_active_frame_move_completes = (gameState.get(not self.isP1).recovery - gameState.get(not self.isP1).move_timer == 0)
        gameState.Rewind(self.active_frame_wait)

        if (self.active_frame_wait < gameState.get(self.isP1).GetActiveFrames() + 1) and not is_recovering_before_long_active_frame_move_completes:
            self.active_frame_wait += 1
        else:
            self.DetermineFrameDataHelper(gameState)
            self.active_frame_wait = 1
        gameState.Unrewind()

    def DetermineFrameDataHelper(self, gameState):
        frameDataEntry = self.buildFrameDataEntry(gameState)
        fa = frameDataEntry.fa

        globalFrameDataEntry = frameDataEntries[frameDataEntry.move_id]
        
        floated = gameState.WasJustFloated(not self.isP1)
        globalFrameDataEntry.record(frameDataEntry, floated)

        self.printer.print(self.isP1, frameDataEntry, floated, fa)

    def buildFrameDataEntry(self, gameState):
        move_id = gameState.get(self.isP1).move_id

        frameDataEntry = FrameDataEntry()

        frameDataEntry.move_id = move_id
        frameDataEntry.startup = gameState.get(self.isP1).startup
        frameDataEntry.activeFrames = gameState.get(self.isP1).GetActiveFrames()
        frameDataEntry.hit_type = AttackType(gameState.get(self.isP1).attack_type).name + ("_THROW" if gameState.get(self.isP1).IsAttackThrow() else "")
        frameDataEntry.recovery = gameState.get(self.isP1).recovery
        frameDataEntry.input = gameState.GetCurrentMoveString(self.isP1)

        gameState.Unrewind()

        time_till_recovery_p1 = gameState.get(self.isP1).GetFramesTillNextMove()
        time_till_recovery_p2 = gameState.get(not self.isP1).GetFramesTillNextMove()

        raw_fa = time_till_recovery_p2 - time_till_recovery_p1

        frameDataEntry.fa = frameDataEntry.WithPlusIfNeeded(raw_fa)

        if gameState.get(not self.isP1).IsBlocking():
            frameDataEntry.on_block = frameDataEntry.fa
        else:
            if gameState.get(not self.isP1).IsGettingCounterHit():
                frameDataEntry.on_counter_hit = frameDataEntry.fa
            else:
                frameDataEntry.on_normal_hit = frameDataEntry.fa

        frameDataEntry.hit_recovery = time_till_recovery_p1
        frameDataEntry.block_recovery = time_till_recovery_p2

        frameDataEntry.move_str = gameState.GetCurrentMoveName(self.isP1)

        gameState.Rewind(self.active_frame_wait)

        return frameDataEntry

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
