import enum

@enum.unique
class DataColumns(enum.Enum):
    time = 'time'
    cmd = 'input command'
    char_name = 'character name'
    move_id = 'internal move id number'
    hit_type = 'attack type'
    startup = 'startup frames'
    block = 'frame advantage on block'
    normal = 'frame advantage on hit'
    counter = 'frame advantage on counter hit'
    fa = 'frame advantage right now'
    combo = 'combo data'
    health = 'remaining health'
