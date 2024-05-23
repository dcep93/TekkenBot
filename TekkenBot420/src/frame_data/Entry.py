import enum
import typing


@enum.unique
class DataColumns(enum.Enum):
    age = 'number of frames since the last entry'
    char_name = 'character name'
    hit_type = 'attack type (high/mid/low/etc)'
    hit_outcome = 'MoveInfoEnums.HitOutcome.name'
    move_id = 'internal move id number'
    # this just uses the damage_taken field, which ignores grey health
    health = 'remaining health (p1 / p2)'
    combo = 'combo data (hits / damage)'
    startup = 'startup frames'
    block = 'frame advantage on block (looks in database for minimum)'
    fa = 'frame advantage right now'
    interrupt = 'reports c(frames before hit would land) or b(frames could have interrupted)'

    _is_player = 'is this the player running TekkenBot'


Entry = typing.Dict[DataColumns, typing.Any]
