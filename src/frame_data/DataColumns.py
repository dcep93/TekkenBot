import enum

@enum.unique
class DataColumns(enum.Enum):
    time = 'time'
    char_name = 'character name'
    move_id = 'internal move id number'
    hit_type = 'attack type'
    startup = 'startup frames'
    block = 'frame advantage on block'
    fa = 'frame advantage right now'
    combo = 'combo data'
    health = 'remaining health'
