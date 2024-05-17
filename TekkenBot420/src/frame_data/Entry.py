import enum
import typing


@enum.unique
class DataColumns(enum.Enum):
    time = 'time (frame / diff)'
    char_name = 'character name'
    hit_type = 'attack type (high/mid/low/etc)'
    hit_outcome = 'MoveInfoEnums.HitOutcome.name'
    move_id = 'internal move id number'
    health = 'remaining health (p1 / p2)'
    combo = 'combo data (hits / damage)'
    startup = 'startup frames'
    block = 'frame advantage on block (looks in database for minimum)'
    fa = 'frame advantage right now'
    is_player = 'is this the player running TekkenBot'


Entry = typing.Dict[DataColumns, typing.Any]
