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

        self.futureStateLog = None

    def Rewind(self, frames):
        self.futureStateLog = self.stateLog[-frames:]
        self.stateLog = self.stateLog[:-frames]

    def Unrewind(self):
        self.stateLog += self.futureStateLog
        self.futureStateLog = None

    def get(self, playerSelector=None):
        state = self.stateLog[-1]
        if playerSelector is None: return state
        return state.p1 if playerSelector else state.p2

    def getOldPlayer(self, isP1, framesAgo):
        if len(self.stateLog) <= framesAgo: return None
        state = self.stateLog[-framesAgo]
        return state.p1 if isP1 else state.p2

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
        self.stateLog.append(gameData)

        if (len(self.stateLog) > 300):
            self.stateLog.pop(0)

    def DidTimerInterruptXMovesAgo(self, isP1, framesAgo):
        player = self.getOldPlayer(isP1, framesAgo)
        if player is None: return False
        return player.move_timer < player.move_timer

    def DidIdChangeXMovesAgo(self, isP1, framesAgo):
        player_before = self.getOldPlayer(isP1, framesAgo + 1)
        if player_before is None: return False
        player_ago = self.getOldPlayer(isP1, framesAgo)
        return player_ago.move_id != player_before.move_id

    def GetCurrentMoveName(self, isP1):
        move_id = self.get(isP1).move_id
        if move_id > 30000: return 'Universal_{}'.format(move_id)
        movelist_parser = self.gameReader.p1_movelist_parser if isP1 else self.gameReader.p2_movelist_parser
        if movelist_parser is not None:
            movelist_names = movelist_parser.movelist_names
            index = (move_id * 2) + 4
            if index < len(movelist_names):
                move = movelist_names[index]
                try:
                    return move.decode('utf-8')
                except:
                    pass
        return "ERROR"

    def GetCurrentMoveString(self, isP1):
        if self.get(isP1).movelist_parser != None:
            move_id = self.get(isP1).move_id
            previous_move_id = -1

            input_array = []

            i = 0
            done = False

            while(True):
                next_move, last_move_was_empty_cancel = self.get(isP1).movelist_parser.input_for_move(move_id, previous_move_id)
                next_move = str(next_move)

                if last_move_was_empty_cancel:
                    input_array[-1] = ''

                input_array.append(next_move)

                if self.get(isP1).movelist_parser.can_be_done_from_neutral(move_id):
                    break

                while(True):
                    old_player = self.getOldPlayer(isP1, i)
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
