from . import GameReader

import collections
from game_parser import MoveInfoEnums

from game_parser import ScriptedGame

from misc import Flags

class GameState:
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

    def get(self, playerSelector=None):
        state = self.stateLog[-1]
        if playerSelector is None: return state
        return state.bot if playerSelector else state.opp

    def GetLastActiveFrameHitWasOn(self, isPlayerOne, frames):
        returnNextState = False
        for state in reversed(self.stateLog[-(frames + 2):]):
            if returnNextState:
                player = state.opp if isPlayerOne else state.bot
                return (player.move_timer - player.startup) + 1

            player = state.bot if isPlayerOne else state.opp
            if player.move_timer == 1:
                returnNextState = True
        return 0

    def DidTimerInterruptXMovesAgo(self, isPlayerOne, framesAgo):
        player = self.getOldPlayer(isPlayerOne, framesAgo)
        if player is None: return False
        return player.move_timer < player.move_timer

    def DidIdChangeXMovesAgo(self, isPlayerOne, framesAgo):
        player_before = self.getOldPlayer(isPlayerOne, framesAgo + 1)
        if player_before is None: return False
        player_ago = self.getOldPlayer(isPlayerOne, framesAgo)
        return player_ago.move_id != player_before.move_id

    def getOldPlayer(self, isPlayerOne, framesAgo):
        if len(self.stateLog) <= framesAgo: return None
        state = self.stateLog[-framesAgo]
        return state.bot if isPlayerOne else state.opp

    def GetCurrentMoveName(self, isPlayerOne):
        move_id = self.get(isPlayerOne).move_id
        if move_id > 30000: return 'Universal_{}'.format(move_id)
        player = self.gameReader.p1 if isPlayerOne else self.gameReader.p2
        movelist_names = player.movelist_names
        index = (move_id * 2) + 4
        if index < len(movelist_names):
            move = movelist[index]
            try:
                return move.decode('utf-8')
            except:
                pass
        return "ERROR"

    def GetTrackingType(self, isPlayerOne, startup):
        if len(self.stateLog) > startup:
            complex_states = [MoveInfoEnums.ComplexMoveStates.UNKN]
            for state in reversed(self.stateLog[-startup:]):
                player = state.bot if isPlayerOne else state.opp
                tracking = player.GetTrackingType()
                if -1 < tracking.value < 8:
                    complex_states.append(tracking)
            return collections.Counter(complex_states).most_common(1)[0][0]
        else:
            return MoveInfoEnums.ComplexMoveStates.F_MINUS

    def GetCurrentMoveString(self, isPlayerOne):
        if self.get(isPlayerOne).movelist_parser != None:
            move_id = self.get(isPlayerOne).move_id
            previous_move_id = -1

            input_array = []

            i = 0
            done = False

            while(True):
                next_move, last_move_was_empty_cancel = self.get(isPlayerOne).movelist_parser.input_for_move(move_id, previous_move_id)
                next_move = str(next_move)

                if last_move_was_empty_cancel:
                    input_array[-1] = ''

                #if len(next_move) > 0:
                input_array.append(next_move)

                if self.get(isPlayerOne).movelist_parser.can_be_done_from_neutral(move_id):
                    break

                while(True):
                    old_player = self.getOldPlayer(isPlayerOne, i)
                    i += 1
                    if old_player is None:
                        done = True
                        break
                    if old_player.move_id != move_id:
                        previous_move_id = move_id
                        move_id = old_player.move_id
                        break
                if done: break

            clean_input_array = reversed([a for a in input_array if len(a) > 0])
            return ','.join(clean_input_array)
        else:
            return 'N/A'
