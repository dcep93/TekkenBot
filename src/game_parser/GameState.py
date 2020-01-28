from . import GameReader

from game_parser import ScriptedGame

from misc import Flags

from . import GameStateGetters

class GameState(GameStateGetters.GameStateGetters):
    def __init__(self):
        if Flags.Flags.pickle_dest is not None:
            self.gameReader = ScriptedGame.Recorder(Flags.Flags.pickle_dest)
        elif Flags.Flags.pickle_src is not None:
            self.gameReader = ScriptedGame.Reader(Flags.Flags.pickle_src)
        else:
            self.gameReader = GameReader.GameReader()

        self.stateLog = []
        self.mirroredStateLog = []

        # gah what is this
        self.isMirrored = False

        self.futureStateLog = None

    def Update(self):
        gameData = self.gameReader.GetUpdatedState(0)

        if(gameData != None):
            # we don't run perfectly in sync, if we get back the same frame, throw it away
            if len(self.stateLog) == 0 or gameData.frame_count != self.stateLog[-1].frame_count:
                if len(self.stateLog) > 0:
                    frames_lost = gameData.frame_count - self.stateLog[-1].frame_count - 1
                    missed_states = min(7, frames_lost)

                    for i in range(missed_states):
                        droppedState = self.gameReader.GetUpdatedState(missed_states - i)
                        self.AppendGamedata(droppedState)

                self.AppendGamedata(gameData)
                return True
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

    def FlipMirror(self):
        self.mirroredStateLog, self.stateLog = self.stateLog, self.mirroredStateLog
        self.isMirrored = not self.isMirrored

    def Rewind(self, frames):
        self.futureStateLog = self.stateLog[-frames:]
        self.stateLog = self.stateLog[:-frames]

    def Unrewind(self):
        self.stateLog += self.futureStateLog
        self.futureStateLog = None

    def get(playerSelector=None):
        state = self.stateLog[-1]
        if playerSelector is None: return state
        return state.bot if playerSelector else state.opp
