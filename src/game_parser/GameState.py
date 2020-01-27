from . import TekkenGameReader

from game_parser.MoveDataReport import MoveDataReport

from . import MoveInfoEnums

from game_parser import ScriptedGame

from misc import Flags

import collections

from . import GameStateGetters

class GameState(GameStateGetters.GameStateGetters):
    def __init__(self):
        if Flags.Flags.pickle_dest is not None:
            self.gameReader = ScriptedGame.Recorder(Flags.Flags.pickle_dest)
        elif Flags.Flags.pickle_src is not None:
            self.gameReader = ScriptedGame.Reader(Flags.Flags.pickle_src)
        else:
            self.gameReader = TekkenGameReader.TekkenGameReader()

        self.duplicateFrameObtained = 0
        self.stateLog = []
        self.mirroredStateLog = []

        # gah what is this
        self.isMirrored = False

        self.futureStateLog = None

    def Update(self):
        gameData = self.gameReader.GetUpdatedState(0)

        if(gameData != None):
            if len(self.stateLog) == 0 or gameData.frame_count != self.stateLog[-1].frame_count: #we don't run perfectly in sync, if we get back the same frame, throw it away
                self.duplicateFrameObtained = 0

                frames_lost = 0
                if len(self.stateLog) > 0:
                    frames_lost = gameData.frame_count - self.stateLog[-1].frame_count - 1

                missed_states = min(7, frames_lost)
                for i in range(missed_states, 0, -1):
                    droppedState = self.gameReader.GetUpdatedState(i)
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

    def getUpdateWaitMs(self, elapsed_ms):
        if self.tekken_state.gameReader.HasWorkingPID():
            elapsed_time = 1000 * elapsed_ms
            wait_ms = max(2, 8 - int(round(elapsed_time)))
        else:
            wait_ms = 1000
        return wait_ms

    def IsFightOver(self):
        return self.duplicateFrameObtained > 5

    def FlipMirror(self):
        self.mirroredStateLog, self.stateLog = self.stateLog, self.mirroredStateLog
        self.isMirrored = not self.isMirrored

    def BackToTheFuture(self, frames):
        self.futureStateLog = self.stateLog[-frames:]
        self.stateLog = self.stateLog[:-frames]

    def ReturnToPresent(self):
        self.stateLog += self.futureStateLog
        self.futureStateLog = None

    def IsGameHappening(self):
        return not self.gameReader.GetNeedReacquireState()

    def IsForegroundPID(self):
        return self.gameReader.IsForegroundPID()
