import enum

from . import Database
from game_parser import MoveInfoEnums

def build(game_state, is_p1):
    fa = get_fa(game_state, is_p1)
    move_id = game_state.get(is_p1).move_id

    entry = Database.get(move_id)
    if entry is None:
        entry = build_frame_data_entry(game_state, is_p1, fa)
        Database.record(entry)

    entry[DataColumns.fa] = fa

    return entry

def build_frame_data_entry(game_state, is_p1, fa):
    move_id = game_state.get(is_p1).move_id

    entry = {}

    entry[DataColumns.move_id] = move_id
    entry[DataColumns.startup] = game_state.get(is_p1).startup
    entry[DataColumns.hit_type] = MoveInfoEnums.AttackType(game_state.get(is_p1).attack_type).name + ("_THROW" if game_state.get(is_p1).is_attack_throw() else "")
    entry[DataColumns.cmd] = game_state.get_current_move_string(is_p1)

    receiver = game_state.get(not is_p1)

    if receiver.is_blocking():
        entry[DataColumns.block] = fa
    elif receiver.is_getting_counter_hit():
        entry[DataColumns.counter] = fa
    elif receiver.is_getting_hit():
        entry[DataColumns.normal] = fa
    elif receiver.startup == 0:
        entry[DataColumns.w_rec] = game_state.get(is_p1).get_frames_til_next_move()

    entry[DataColumns.char_name] = game_state.get(is_p1).movelist_parser.char_name
    entry[DataColumns.move_str] = game_state.get_current_move_name(is_p1)

    entry[DataColumns.punish] = not game_state.get(not is_p1).is_able_to_act()

    return entry

def get_fa(game_state, is_p1):
    receiver = game_state.get(not is_p1)
    if receiver.is_being_knocked_down():
        return 'KND'
    elif receiver.is_being_juggled():
        return 'JGL'
    elif game_state.was_just_floated(not is_p1):
        return 'FLT'
    else:
        time_till_recovery_p1 = game_state.get(is_p1).get_frames_til_next_move()
        time_till_recovery_p2 = 0 if receiver.hit_outcome is MoveInfoEnums.HitOutcome.NONE else receiver.get_frames_til_next_move()

        raw_fa = time_till_recovery_p2 - time_till_recovery_p1
        raw_fa_str = str(raw_fa)

        if raw_fa > 0:
            raw_fa_str = "+%s" % raw_fa_str
        return raw_fa_str

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
    punish = 'hit is a punish'
