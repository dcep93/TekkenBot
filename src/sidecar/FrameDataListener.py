"""
Collects information from GameState over time in hopes of synthesizing it and presenting it in a more useful way.

"""

from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ThrowTechs
from game_parser.MoveInfoEnums import ComplexMoveStates

class FrameDataListener:
    def __init__(self, printer):
        self.listeners = [PlayerListener(i, printer) for i in [True, False]]

    def update(self, gameState):
        for listener in self.listeners:
            listener.Update(gameState)

class PlayerListener:
    def __init__(self, isP1, printer):
        self.isP1 = isP1
        self.printer = printer

        self.active_frame_wait = 1

    def Update(self, gameState):
        if self.ShouldDetermineFrameData(gameState):
            self.DetermineFrameData(gameState)

    def ShouldDetermineFrameData(self, gameState):
        if gameState.get(self.isP1).IsBlocking() or gameState.get(self.isP1).IsGettingHit() or gameState.get(self.isP1).IsInThrowing() or gameState.get(self.isP1).IsBeingKnockedDown() or gameState.get(self.isP1).IsGettingWallSplatted():
            if gameState.DidIdChangeXMovesAgo(self.isP1, self.active_frame_wait) or gameState.DidTimerInterruptXMovesAgo(self.isP1, self.active_frame_wait):
                    return True
        return False

    def DetermineFrameData(self, gameState):
        is_recovering_before_long_active_frame_move_completes = (gameState.get(self.isP1).recovery - gameState.get(self.isP1).move_timer == 0)
        gameState.Rewind(self.active_frame_wait)

        if (self.active_frame_wait < gameState.get(not self.isP1).GetActiveFrames() + 1) and not is_recovering_before_long_active_frame_move_completes:
            self.active_frame_wait += 1
        else:
            self.DetermineFrameDataHelper(gameState)
            self.active_frame_wait = 1
        gameState.Unrewind()

    def DetermineFrameDataHelper(self, gameState):
        gameState.Unrewind()

        currentActiveFrame = gameState.GetLastActiveFrameHitWasOn(self.isP1, self.active_frame_wait)

        gameState.Rewind(self.active_frame_wait)

        opp_id = gameState.get(not self.isP1).move_id

        frameDataEntry = FrameDataEntry(self.isP1)

        frameDataEntry.move_id = opp_id
        frameDataEntry.currentActiveFrame = currentActiveFrame
        frameDataEntry.startup = gameState.get(not self.isP1).startup
        frameDataEntry.activeFrames = gameState.get(not self.isP1).GetActiveFrames()
        frameDataEntry.hitType = AttackType(gameState.get(not self.isP1).attack_type).name + ("_THROW" if gameState.get(not self.isP1).IsAttackThrow() else "")
        frameDataEntry.recovery = gameState.get(not self.isP1).recovery
        frameDataEntry.input = gameState.GetCurrentMoveString(not self.isP1)

        frameDataEntry.tracking = gameState.GetTrackingType(not self.isP1, frameDataEntry.startup)

        gameState.Unrewind()

        frameDataEntry.throwTech = gameState.get(self.isP1).throw_tech

        time_till_recovery_opp = gameState.get(not self.isP1).GetFramesTillNextMove()
        time_till_recovery_bot = gameState.get(self.isP1).GetFramesTillNextMove()

        new_frame_advantage_calc = time_till_recovery_bot - time_till_recovery_opp

        frameDataEntry.currentFrameAdvantage = frameDataEntry.WithPlusIfNeeded(new_frame_advantage_calc)

        if gameState.get(self.isP1).IsBlocking():
            frameDataEntry.onBlock = new_frame_advantage_calc
        else:
            if gameState.get(self.isP1).IsGettingCounterHit():
                frameDataEntry.onCounterHit = new_frame_advantage_calc
            else:
                frameDataEntry.onNormalHit = new_frame_advantage_calc

        frameDataEntry.hitRecovery = time_till_recovery_opp
        frameDataEntry.blockRecovery = time_till_recovery_bot

        frameDataEntry.move_str = gameState.GetCurrentMoveName(not self.isP1)

        self.printer.print(frameDataEntry)

        gameState.Rewind(self.active_frame_wait)

class FrameDataEntry:
    unknown = '??'
    def __init__(self, isP1):
        self.isP1 = isP1

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
        return "p1: " if self.isP1 else "p2: "

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
