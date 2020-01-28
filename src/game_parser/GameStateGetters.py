from game_parser.MoveDataReport import MoveDataReport

from . import MoveInfoEnums

import collections

class GameStateGetters:
    def IsBotBlocking(self):
        return self.stateLog[-1].bot.IsBlocking()

    def IsBotGettingCounterHit(self):
        return self.stateLog[-1].bot.IsGettingCounterHit()

    def IsBotGettingHit(self):
        return self.stateLog[-1].bot.IsGettingHit()

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

    def IsBotBeingKnockedDown(self):
        return self.stateLog[-1].bot.IsBeingKnockedDown()

    def IsBotBeingWallSplatted(self):
        return self.stateLog[-1].bot.IsGettingWallSplatted()

    def GetOppDamage(self):
        return self.stateLog[-1].opp.attack_damage

    def IsBotBeingThrown(self):
        return self.stateLog[-1].opp.IsInThrowing()

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

    def GetOppTechnicalStates(self, startup):
        #opp_id = self.stateLog[-1].opp.move_id
        tc_frames = []
        tj_frames = []
        cancel_frames = []
        buffer_frames = []
        pc_frames = []
        homing_frames1 = []
        homing_frames2 = []
        parryable_frames1 = []
        parryable_frames2 = []
        startup_frames = []
        frozen_frames = []

        previous_state = None
        skipped_frames_counter = 0
        frozen_frames_counter = 0
        for i, state in enumerate(reversed(self.stateLog[-startup:])):
            if previous_state != None:
                is_skipped = state.opp.move_timer != previous_state.opp.move_timer - 1
                if is_skipped:
                    skipped_frames_counter += 1
                is_frozen = state.bot.move_timer == previous_state.bot.move_timer
                if is_frozen:
                    frozen_frames_counter += 1
            else:
                is_skipped = False
                is_frozen = False
            if skipped_frames_counter + i <= startup:
                tc_frames.append(state.opp.IsTechnicalCrouch())
                tj_frames.append(state.opp.IsTechnicalJump())
                cancel_frames.append(state.opp.IsAbleToAct())
                buffer_frames.append(state.opp.IsBufferable())
                pc_frames.append(state.opp.IsPowerCrush())
                homing_frames1.append(state.opp.IsHoming1())
                homing_frames2.append(state.opp.IsHoming2())
                parryable_frames1.append(state.opp.IsParryable1())
                parryable_frames2.append(state.opp.IsParryable2())
                startup_frames.append(is_skipped)
                frozen_frames.append(is_frozen)

            previous_state = state

        parryable1 = MoveDataReport('PY1', parryable_frames1)
        parryable2 = MoveDataReport('PY2', parryable_frames2)
        unparryable = MoveDataReport('NO PARRY?', [not parryable1.is_present() and not parryable2.is_present()])

        return [
            MoveDataReport('TC', tc_frames),
            MoveDataReport('TJ', tj_frames),
            MoveDataReport('BUF', buffer_frames),
            MoveDataReport('xx', cancel_frames),
            MoveDataReport('PC', pc_frames),
            MoveDataReport('HOM1', homing_frames1),
            MoveDataReport('HOM2', homing_frames2),
            MoveDataReport('SKIP', startup_frames),
            MoveDataReport('FROZ', frozen_frames),
        ]

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
