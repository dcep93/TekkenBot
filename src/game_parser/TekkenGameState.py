
class TekkenGameState:
    def __init__(self):
        self.gameReader = TekkenGameReader()
        self.isPlayer1 = True

        self.duplicateFrameObtained = 0
        self.stateLog = []
        self.mirroredStateLog = []

        self.isMirrored = False

        self.futureStateLog = None

    def Update(self, buffer=0):
        gameData = self.gameReader.GetUpdatedState(buffer)

        if(gameData != None):
            if len(self.stateLog) == 0 or gameData.frame_count != self.stateLog[-1].frame_count: #we don't run perfectly in sync, if we get back the same frame, throw it away
                self.duplicateFrameObtained = 0

                frames_lost = 0
                if len(self.stateLog) > 0:
                    frames_lost = gameData.frame_count - self.stateLog[-1].frame_count - 1

                for i in range(min(7 - buffer, frames_lost)):
                    droppedState = self.gameReader.GetUpdatedState(min(7, frames_lost + buffer) - i)
                    self.AppendGamedata(droppedState)

                self.AppendGamedata(gameData)
                return True

            if gameData.frame_count == self.stateLog[-1].frame_count:
                self.duplicateFrameObtained += 1
        return False

    def AppendGamedata(self, gameData):
        if not self.isMirrored:
            self.stateLog.append(gameData)
            self.mirroredStateLog.append(gameData.FromMirrored())
        else:
            self.stateLog.append(gameData.FromMirrored())
            self.mirroredStateLog.append(gameData)

        if (len(self.stateLog) > 300):
            self.stateLog.pop(0)
            self.mirroredStateLog.pop(0)

    def get_recovery(self):
        opp_frames = self.stateLog[-1].opp.recovery - self.stateLog[-1].opp.move_timer
        bot_frames = self.stateLog[-1].bot.recovery - self.stateLog[-1].bot.move_timer
        return opp_frames - bot_frames
