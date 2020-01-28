from . import MoveInfoEnums

import collections

class GameStateGetters:
    def GetCurrentOppMoveString(self):
        if self.stateLog[-1].opp.movelist_parser != None:
            move_id = self.stateLog[-1].opp.move_id
            previous_move_id = -1

            input_array = []

            i = len(self.stateLog)

            while(True):
                next_move, last_move_was_empty_cancel = self.get(False).movelist_parser.input_for_move(move_id, previous_move_id)
                next_move = str(next_move)

                if last_move_was_empty_cancel:
                    input_array[-1] = ''

                #if len(next_move) > 0:
                input_array.append(next_move)

                if self.stateLog[-1].opp.movelist_parser.can_be_done_from_neutral(move_id):
                    break

                while(True):
                    i -= 1
                    if i < 0:
                        break
                    if self.stateLog[i].opp.move_id != move_id:
                        previous_move_id = move_id
                        move_id = self.stateLog[i].opp.move_id
                        break
                if i < 0:
                    break


            clean_input_array = reversed([a for a in input_array if len(a) > 0])
            return ','.join(clean_input_array)
        else:
            return 'N/A'

    def GetOppTrackingType(self, startup):
        if len(self.stateLog) > startup:
            complex_states = [MoveInfoEnums.ComplexMoveStates.UNKN]
            for state in reversed(self.stateLog[-startup:]):
                if -1 < state.opp.GetTrackingType().value < 8:
                    complex_states.append(state.opp.GetTrackingType())
            return collections.Counter(complex_states).most_common(1)[0][0]
        else:
            return MoveInfoEnums.ComplexMoveStates.F_MINUS

    def GetCurrentOppMoveName(self):
        move_id = self.stateLog[-1].opp.move_id
        return self.GetOppMoveName(move_id, is_for_bot=False)

    def GetOppMoveName(self, move_id, is_for_bot=False):
        if move_id > 30000:
            return 'Universal_{}'.format(move_id)

        try:
            if (not self.isMirrored and not is_for_bot) or (self.isMirrored and is_for_bot):
                movelist = self.gameReader.p1.movelist_names
            else:
                movelist = self.gameReader.p2.movelist_names

            return movelist[(move_id * 2) + 4].decode('utf-8')
        except:
            return "ERROR"
