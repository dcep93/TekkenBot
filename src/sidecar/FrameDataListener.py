"""
Collects information from GameState over time in hopes of synthesizing it and presenting it in a more useful way.

"""

from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ComplexMoveStates

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
        gameState.Unrewind()

        gameState.Rewind(self.active_frame_wait)

        move_id = gameState.get(self.isP1).move_id

        frameDataEntry = FrameDataEntry(self.isP1)

        frameDataEntry.move_id = move_id
        frameDataEntry.startup = gameState.get(self.isP1).startup
        frameDataEntry.activeFrames = gameState.get(self.isP1).GetActiveFrames()
        frameDataEntry.hit_type = AttackType(gameState.get(self.isP1).attack_type).name + ("_THROW" if gameState.get(self.isP1).IsAttackThrow() else "")
        frameDataEntry.recovery = gameState.get(self.isP1).recovery
        frameDataEntry.input = gameState.GetCurrentMoveString(self.isP1)

        gameState.Unrewind()

        time_till_recovery_p1 = gameState.get(self.isP1).GetFramesTillNextMove()
        time_till_recovery_p2 = gameState.get(not self.isP1).GetFramesTillNextMove()

        new_frame_advantage_calc = time_till_recovery_p2 - time_till_recovery_p1

        frameDataEntry.currentFrameAdvantage = frameDataEntry.WithPlusIfNeeded(new_frame_advantage_calc)

        if gameState.get(not self.isP1).IsBlocking():
            frameDataEntry.on_block = frameDataEntry.currentFrameAdvantage
        else:
            if gameState.get(not self.isP1).IsGettingCounterHit():
                frameDataEntry.on_counter_hit = frameDataEntry.currentFrameAdvantage
            else:
                frameDataEntry.on_normal_hit = frameDataEntry.currentFrameAdvantage

        frameDataEntry.hit_recovery = time_till_recovery_p2
        frameDataEntry.block_recovery = time_till_recovery_p1

        frameDataEntry.move_str = gameState.GetCurrentMoveName(self.isP1)

        self.printer.print(frameDataEntry)

        gameState.Rewind(self.active_frame_wait)

class FrameDataEntry:
    unknown = '??'
    prefix_length = 4
    input_pad = 10
    columns = [
        'input',
        'move_id',
        'move_str',
        'hit_type',
        'startup',
        'on_block',
        'on_normal_hit',
        'on_counter_hit',
        'recovery',
        'hit_recovery',
        'block_recovery'
    ]

    def __init__(self, isP1):
        self.isP1 = isP1

        self.currentFrameAdvantage = self.unknown

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

    @classmethod
    def printColumns(cls):
        cols = cls.columns[:]
        before = int(cls.input_pad / 2)
        after = cls.input_pad - before
        cols[0] = (" " * before) + cols[0] + (" " * after)
        string = " ".join(cols)
        prefix = " " * cls.prefix_length
        print(prefix + string)

    @staticmethod
    def WithPlusIfNeeded(value):
        v = str(value)
        if value >= 0:
            return '+' + v
        else:
            return v

    def getRawField(self, field):
        return str(self.__getattribute__(field))

    def getField(self, field):
        v = self.getRawField(field)
        diff = len(field) - len(v)
        if field == 'input': diff += self.input_pad
        if diff <= 0: return v
        before = int(diff / 2)
        after = diff - before
        return (' ' * before) + v + (' ' * after)

    def __repr__(self):
        values = [self.getField(i) for i in self.columns]

        playerName = "p1" if self.isP1 else "p2"
        string = '|'.join(values)
        return "%s: %s / NOW:%s" % (playerName, string, self.currentFrameAdvantage)
