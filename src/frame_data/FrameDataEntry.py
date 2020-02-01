import enum

from . import FrameDataDatabase

from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ComplexMoveStates

def build(gameState, isP1, active_frame_wait):
    floated = gameState.WasJustFloated(not isP1)
    gameState.Unrewind()
    fa = getFA(gameState, isP1, floated)
    gameState.Rewind(active_frame_wait)
    move_id = gameState.get(isP1).move_id

    frameDataEntry = FrameDataDatabase.get(move_id)
    if frameDataEntry is None:
        frameDataEntry = buildFrameDataEntry(gameState, isP1, fa, active_frame_wait)
        FrameDataDatabase.record(frameDataEntry, floated)

    frameDataEntry[DataColumns.fa] = fa

    return frameDataEntry

def buildFrameDataEntry(gameState, isP1, fa, active_frame_wait):
    move_id = gameState.get(isP1).move_id

    frameDataEntry = {}

    frameDataEntry[DataColumns.move_id] = move_id
    frameDataEntry[DataColumns.startup] = gameState.get(isP1).startup
    frameDataEntry[DataColumns.hit_type] = AttackType(gameState.get(isP1).attack_type).name + ("_THROW" if gameState.get(isP1).IsAttackThrow() else "")
    frameDataEntry[DataColumns.w_rec] = gameState.get(isP1).recovery
    frameDataEntry[DataColumns.cmd] = gameState.GetCurrentMoveString(isP1)

    gameState.Unrewind()

    if gameState.get(not isP1).IsBlocking():
        frameDataEntry[DataColumns.block] = fa
    else:
        if gameState.get(not isP1).IsGettingCounterHit():
            frameDataEntry[DataColumns.counter] = fa
        else:
            frameDataEntry[DataColumns.normal] = fa

    frameDataEntry[DataColumns.char_name] = gameState.get(isP1).movelist_parser.char_name
    frameDataEntry[DataColumns.move_str] = gameState.GetCurrentMoveName(isP1)

    gameState.Rewind(active_frame_wait + 1)
    frameDataEntry[DataColumns.guaranteed] = not gameState.get(not isP1).IsAbleToAct()
    gameState.Unrewind()
    gameState.Rewind(active_frame_wait)

    return frameDataEntry

def getFA(gameState, isP1, floated):
    receiver = gameState.get(not isP1)
    if receiver.IsBeingKnockedDown():
        return 'KND'
    elif receiver.IsBeingJuggled():
        return 'JGL'
    elif floated:
        return 'FLT'
    else:
        time_till_recovery_p1 = gameState.get(isP1).GetFramesTillNextMove()
        time_till_recovery_p2 = gameState.get(not isP1).GetFramesTillNextMove()

        raw_fa = time_till_recovery_p2 - time_till_recovery_p1

        return WithPlusIfNeeded(raw_fa)

def WithPlusIfNeeded(value):
    v = str(value)
    if value >= 0:
        return '+' + v
    else:
        return v

@enum.unique
class DataColumns(enum.Enum):
    cmd = 'input command'
    char_name = 'character name'
    move_id = 'internal move id number'
    move_str = 'internal move name'
    hit_type = 'attack type'
    startup = 'startup frames'
    block = 'frame advantage on block'
    normal = 'frame advantage on hit'
    counter = 'frame advantage on counter hit'
    w_rec = 'total number of frames in move'
    fa = 'frame advantage right now'
    guaranteed = 'hit is guaranteed'
