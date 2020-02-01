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
            FrameDataEntry.process(self, gameState)
            self.active_frame_wait = 1
        gameState.Unrewind()
