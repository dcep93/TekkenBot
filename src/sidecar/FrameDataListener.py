"""
Collects information from GameState over time in hopes of synthesizing it and presenting it in a more useful way.

"""

from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ThrowTechs
from game_parser.MoveInfoEnums import ComplexMoveStates
from game_parser.GameState import GameState
import time
from enum import Enum

class FrameDataListener:
    def __init__(self, isPlayerOne):
        # a single class instance should be sufficient
        # sibling instances seem to make it more complicated
        self.isPlayerOne = isPlayerOne

        self.active_frame_wait = 1

    def Update(self, gameState: GameState):
        if self.isPlayerOne:
            gameState.FlipMirror()

        if self.ShouldDetermineFrameData(gameState): self.DetermineFrameData(gameState)

        if self.isPlayerOne:
            gameState.FlipMirror()

    def ShouldDetermineFrameData(self, gameState):
        if gameState.get(True).IsBlocking() or gameState.get(True).IsGettingHit() or gameState.get(False).IsInThrowing() or gameState.get(True).IsBeingKnockedDown() or gameState.get(True).IsGettingWallSplatted():
            if gameState.DidIdChangeXMovesAgo(True, self.active_frame_wait) or gameState.DidTimerInterruptXMovesAgo(True, self.active_frame_wait):
                    return True
        return False

    def DetermineFrameData(self, gameState):
        is_recovering_before_long_active_frame_move_completes = (gameState.get(True).recovery - gameState.get(True).move_timer == 0)
        gameState.Rewind(self.active_frame_wait)

        if (self.active_frame_wait < gameState.get(False).GetActiveFrames() + 1) and not is_recovering_before_long_active_frame_move_completes:
            self.active_frame_wait += 1
        else:
            self.DetermineFrameDataHelper(gameState)
            self.active_frame_wait = 1
        gameState.Unrewind()

    def DetermineFrameDataHelper(self, gameState):
        gameState.Unrewind()

        currentActiveFrame = gameState.GetLastActiveFrameHitWasOn(self.isPlayerOne, self.active_frame_wait)

        gameState.Rewind(self.active_frame_wait)

        opp_id = gameState.get(False).move_id

        frameDataEntry = FrameDataEntry(self.isPlayerOne)

        frameDataEntry.move_id = opp_id
        frameDataEntry.currentActiveFrame = currentActiveFrame
        frameDataEntry.startup = gameState.get(False).startup
        frameDataEntry.activeFrames = gameState.get(False).GetActiveFrames()
        frameDataEntry.hitType = AttackType(gameState.get(False).attack_type).name + ("_THROW" if gameState.get(False).IsAttackThrow() else "")
        frameDataEntry.recovery = gameState.get(False).recovery
        frameDataEntry.input = gameState.GetCurrentOppMoveString()

        frameDataEntry.tracking = gameState.GetOppTrackingType(frameDataEntry.startup)

        gameState.Unrewind()

        frameDataEntry.throwTech = gameState.get(True).throw_tech

        time_till_recovery_opp = gameState.get(False).GetFramesTillNextMove()
        time_till_recovery_bot = gameState.get(True).GetFramesTillNextMove()

        new_frame_advantage_calc = time_till_recovery_bot - time_till_recovery_opp

        frameDataEntry.currentFrameAdvantage = frameDataEntry.WithPlusIfNeeded(new_frame_advantage_calc)

        if gameState.get(True).IsBlocking():
            frameDataEntry.onBlock = new_frame_advantage_calc
        else:
            if gameState.get(True).IsGettingCounterHit():
                frameDataEntry.onCounterHit = new_frame_advantage_calc
            else:
                frameDataEntry.onNormalHit = new_frame_advantage_calc

        frameDataEntry.hitRecovery = time_till_recovery_opp
        frameDataEntry.blockRecovery = time_till_recovery_bot

        frameDataEntry.move_str = gameState.GetCurrentOppMoveName()

        self.printFrameData(frameDataEntry)

        gameState.Rewind(self.active_frame_wait)

    def printFrameData(self, frameDataEntry):
        print(str(frameDataEntry))

class FrameDataEntry:
    unknown = '??'
    def __init__(self, isPlayerOne):
        self.isPlayerOne = isPlayerOne

        self.move_id = self.unknown
        self.move_str = self.unknown
        self.startup = self.unknown
        self.hitType = self.unknown
        self.onBlock = self.unknown
        self.onCounterHit = self.unknown
        self.onNormalHit = self.unknown
        self.recovery = self.unknown
        self.blockFrames = self.unknown
        self.activeFrames = self.unknown
        self.currentFrameAdvantage = self.unknown
        self.currentActiveFrame = self.unknown
        self.input = self.unknown
        self.blockRecovery = self.unknown
        self.hitRecovery = self.unknown

        self.calculated_startup = -1
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

    def getPrefix(self):
        return "p1: " if self.isPlayerOne else "p2: "

    # todo revisit
    def __repr__(self):
        notes = ''

        if self.throwTech != None and self.throwTech != ThrowTechs.NONE:
            notes += self.throwTech.name + " "

        self.calculated_startup = self.startup

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
        return self.getPrefix() + non_nerd_string + notes_string + now_string
