"""
Collects information from TekkenGameState over time in hopes of synthesizing it and presenting it in a more useful way.

"""

from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ThrowTechs
from game_parser.MoveInfoEnums import ComplexMoveStates
from game_parser.TekkenGameState import TekkenGameState
import time
from enum import Enum

class TekkenEncyclopedia:
    def __init__(self, isPlayerOne):
        self.FrameData = {}
        self.isPlayerOne = isPlayerOne

        self.active_frame_wait = 1

    def GetPlayerString(self, reverse = False):
        if (self.isPlayerOne and not reverse) or (not self.isPlayerOne and reverse):
            return "p1: "
        else:
            return "p2: "

    def GetFrameAdvantage(self, moveId, isOnBlock = True):
        if moveId in self.FrameData:
            if isOnBlock:
                return self.FrameData[moveId].onBlock
            else:
                return self.FrameData[moveId].onNormalHit
        else:
            return None

    def Update(self, gameState: TekkenGameState):
        if self.isPlayerOne:
            gameState.FlipMirror()

        self.DetermineFrameData(gameState)

        if self.isPlayerOne:
            gameState.FlipMirror()

    def DetermineFrameData(self, gameState):
        if (gameState.IsBotBlocking() or gameState.IsBotGettingHit() or gameState.IsBotBeingThrown() or gameState.IsBotBeingKnockedDown() or gameState.IsBotBeingWallSplatted()): #or gameState.IsBotUsingOppMovelist()): #or  gameState.IsBotStartedBeingJuggled() or gameState.IsBotJustGrounded()):
            # print(gameState.stateLog[-1].bot.move_id)
            #print(gameState.stateLog[-1].bot.move_timer)
            #print(gameState.stateLog[-1].bot.recovery)
            #print(gameState.DidBotIdChangeXMovesAgo(self.active_frame_wait))

            if gameState.DidBotIdChangeXMovesAgo(self.active_frame_wait) or gameState.DidBotTimerInterruptXMovesAgo(
                    self.active_frame_wait):  # or gameState.DidOppIdChangeXMovesAgo(self.active_frame_wait):

                is_recovering_before_long_active_frame_move_completes = (gameState.GetBotRecovery() - gameState.GetBotMoveTimer() == 0)
                gameState.BackToTheFuture(self.active_frame_wait)

                #print(gameState.GetOppActiveFrames())
                if (not self.active_frame_wait >= gameState.GetOppActiveFrames() + 1) and not is_recovering_before_long_active_frame_move_completes:
                    self.active_frame_wait += 1
                else:
                    gameState.ReturnToPresent()

                    currentActiveFrame = gameState.GetLastActiveFrameHitWasOn(self.active_frame_wait)

                    gameState.BackToTheFuture(self.active_frame_wait)


                    opp_id = gameState.GetOppMoveId()

                    if opp_id in self.FrameData:
                        frameDataEntry = self.FrameData[opp_id]
                    else:
                        frameDataEntry = FrameDataEntry()
                        self.FrameData[opp_id] = frameDataEntry

                    frameDataEntry.currentActiveFrame = currentActiveFrame

                    frameDataEntry.currentFrameAdvantage = '??'
                    frameDataEntry.move_id = opp_id
                    # frameDataEntry.damage =
                    frameDataEntry.damage = gameState.GetOppDamage()
                    frameDataEntry.startup = gameState.GetOppStartup()

                    if frameDataEntry.damage == 0 and frameDataEntry.startup == 0:
                        frameDataEntry.startup, frameDataEntry.damage = gameState.GetOppLatestNonZeroStartupAndDamage()

                    frameDataEntry.activeFrames = gameState.GetOppActiveFrames()
                    frameDataEntry.hitType = AttackType(gameState.GetOppAttackType()).name
                    if gameState.IsOppAttackThrow():
                        frameDataEntry.hitType += "_THROW"

                    frameDataEntry.recovery = gameState.GetOppRecovery()

                    #frameDataEntry.input = frameDataEntry.InputTupleToInputString(gameState.GetOppLastMoveInput())

                    frameDataEntry.input = gameState.GetCurrentOppMoveString()

                    frameDataEntry.technical_state_reports = gameState.GetOppTechnicalStates(frameDataEntry.startup - 1)

                    frameDataEntry.tracking = gameState.GetOppTrackingType(frameDataEntry.startup)

                    #print(gameState.GetRangeOfMove())

                    gameState.ReturnToPresent()

                    #frameDataEntry.throwTech = gameState.GetBotThrowTech(frameDataEntry.activeFrames + frameDataEntry.startup)
                    frameDataEntry.throwTech = gameState.GetBotThrowTech(1)

                    time_till_recovery_opp = gameState.GetOppFramesTillNextMove()
                    time_till_recovery_bot = gameState.GetBotFramesTillNextMove()

                    new_frame_advantage_calc = time_till_recovery_bot - time_till_recovery_opp

                    frameDataEntry.currentFrameAdvantage = frameDataEntry.WithPlusIfNeeded(new_frame_advantage_calc)

                    if gameState.IsBotBlocking():
                        frameDataEntry.onBlock = new_frame_advantage_calc
                    else:
                        if gameState.IsBotGettingCounterHit():
                            frameDataEntry.onCounterHit = new_frame_advantage_calc
                        else:
                            frameDataEntry.onNormalHit = new_frame_advantage_calc

                    frameDataEntry.hitRecovery = time_till_recovery_opp
                    frameDataEntry.blockRecovery = time_till_recovery_bot

                    frameDataEntry.move_str = gameState.GetCurrentOppMoveName()
                    frameDataEntry.prefix = self.GetPlayerString()

                    print(str(frameDataEntry))

                    gameState.BackToTheFuture(self.active_frame_wait)

                    self.active_frame_wait = 1
                gameState.ReturnToPresent()

class FrameDataEntry:
    def __init__(self):
        self.prefix = '??'
        self.move_id = '??'
        self.move_str = '??'
        self.startup = '??'
        self.calculated_startup = -1
        self.hitType = '??'
        self.onBlock = '??'
        self.onCounterHit = '??'
        self.onNormalHit = '??'
        self.recovery = '??'
        self.damage = '??'
        self.blockFrames = '??'
        self.activeFrames = '??'
        self.currentFrameAdvantage = '??'
        self.currentActiveFrame = '??'
        self.input = '??'
        self.technical_state_reports = []
        self.blockRecovery = '??'
        self.hitRecovery = '??'
        self.throwTech = None
        self.tracking = ComplexMoveStates.F_MINUS

    def WithPlusIfNeeded(self, value):
        try:
            if value >= 0:
                return '+' + str(value)
            else:
                return str(value)
        except:
            return str(value)

    def InputTupleToInputString(self, inputTuple):
        s = ""
        for input in inputTuple:
            s += (input[0].name + input[1].name.replace('x', '+')).replace('N', '')
        if input[2]:
            s += "+R"
        return s

    def __repr__(self):
        notes = ''

        if self.throwTech != None and self.throwTech != ThrowTechs.NONE:
            notes += self.throwTech.name + " "

        self.calculated_startup = self.startup
        for report in self.technical_state_reports:
            if 'TC' in report.name and report.is_present():
                notes += str(report)
            elif 'TJ' in report.name and report.is_present():
                notes += str(report)
            elif 'PC' in report.name and report.is_present():
                notes += str(report)
            elif 'SKIP' in report.name and report.is_present():
                #print(report)
                self.calculated_startup -= report.total_present()
            elif 'FROZ' in report.name and report.is_present():
                #print(report)
                self.calculated_startup -= report.total_present()
            else:
                if report.is_present():
                    notes += str(report)

        if self.calculated_startup != self.startup:
            self.calculated_startup = str(self.calculated_startup) + "?"

        non_nerd_string = "{:^5}|{:^4}|{:^4}|{:^7}|{:^4}|{:^4}|{:^4}|{:^5}|{:^3}|{:^2}|{:^3}|{:^3}|{:^3}|".format(
            str(self.input),
            str(self.move_id),
            self.move_str,
            str(self.hitType)[:7],
            str(self.calculated_startup),
            self.WithPlusIfNeeded(self.onBlock),
            self.WithPlusIfNeeded(self.onNormalHit),
            self.WithPlusIfNeeded(self.onCounterHit),
            (str(self.currentActiveFrame) + "/" + str(self.activeFrames)),
            self.tracking.name.replace('_MINUS', '-').replace("_PLUS", '+').replace(ComplexMoveStates.UNKN.name, '?'),
            self.recovery,
            self.hitRecovery,
            self.blockRecovery
        )


        notes_string = "{}".format(notes)
        now_string = " NOW:{}".format(str(self.currentFrameAdvantage))
        return self.prefix + non_nerd_string + notes_string + now_string
