from . import MoveInfoEnums

import collections

class GameStateGetters:
    def IsOppAttackThrow(self):
        return self.stateLog[-1].opp.IsAttackThrow()

    def GetOppStartup(self):
        return self.stateLog[-1].opp.startup

    def GetOppActiveFrames(self):
        return self.stateLog[-1].opp.GetActiveFrames()

    def GetLastActiveFrameHitWasOn(self, frames):
        returnNextState = False
        for state in reversed(self.stateLog[-(frames + 2):]):
            if returnNextState:
                return (state.opp.move_timer - state.opp.startup) + 1

            if state.bot.move_timer == 1:
                returnNextState = True

        return 0

    def GetOppRecovery(self):
        return self.stateLog[-1].opp.recovery

    def GetOppFramesTillNextMove(self):
        return self.GetOppRecovery() - self.GetOppMoveTimer()

    def GetBotFramesTillNextMove(self):
        return self.GetBotRecovery() - self.GetBotMoveTimer()

    def GetBotRecovery(self):
        return self.stateLog[-1].bot.recovery

    def GetOppMoveId(self):
        return self.stateLog[-1].opp.move_id

    def GetOppAttackType(self):
        return self.stateLog[-1].opp.attack_type

    def GetBotMoveTimer(self):
        return self.stateLog[-1].bot.move_timer

    def GetOppMoveTimer(self):
        return self.stateLog[-1].opp.move_timer

    def GetOppDamage(self):
        return self.stateLog[-1].opp.attack_damage

    def DidBotTimerInterruptXMovesAgo(self, framesAgo):
        if len(self.stateLog) > framesAgo:
            #if self.stateLog[0 - framesAgo].bot.move_id != 32769 or self.stateLog[0 - framesAgo -1].bot.move_id != 32769:
            return self.stateLog[0 - framesAgo].bot.move_timer < self.stateLog[0 - framesAgo - 1].bot.move_timer
            #print('{} {}'.format(self.stateLog[0 - framesAgo].bot.move_timer, self.stateLog[0 - framesAgo - 1].bot.move_timer))
            #return self.stateLog[0 - framesAgo].bot.move_timer != self.stateLog[0 - framesAgo - 1].bot.move_timer + 1

        return False

    def DidBotIdChangeXMovesAgo(self, framesAgo):
        if len(self.stateLog) > framesAgo:
            return self.stateLog[0 - framesAgo].bot.move_id != self.stateLog[0 - framesAgo - 1].bot.move_id
        else:
            return False

    def GetCurrentOppMoveString(self):
        if self.stateLog[-1].opp.movelist_parser != None:
            move_id = self.stateLog[-1].opp.move_id
            previous_move_id = -1

            input_array = []

            i = len(self.stateLog)

            while(True):
                next_move, last_move_was_empty_cancel = self.GetOppMoveString(move_id, previous_move_id)
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

    def GetOppMoveString(self, move_id, previous_move_id):
        return self.stateLog[-1].opp.movelist_parser.input_for_move(move_id, previous_move_id)

    def GetBotThrowTech(self):
        tech = self.stateLog[-1].bot.throw_tech
        if tech != MoveInfoEnums.ThrowTechs.NONE:
            return tech
        return MoveInfoEnums.ThrowTechs.NONE

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
