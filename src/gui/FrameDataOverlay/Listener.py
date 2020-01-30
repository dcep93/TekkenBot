from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ComplexMoveStates

from . import FrameDataEntry

class FrameDataListener:
    def __init__(self, printer):
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

        globalFrameDataEntry = FrameDataEntry.frameDataEntries[frameDataEntry.move_id]
        
        floated = gameState.WasJustFloated(not self.isP1)
        globalFrameDataEntry.record(frameDataEntry, floated)

        self.printer.print(self.isP1, frameDataEntry, floated, fa)

    def buildFrameDataEntry(self, gameState):
        move_id = gameState.get(self.isP1).move_id

        frameDataEntry = FrameDataEntry.FrameDataEntry()

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
