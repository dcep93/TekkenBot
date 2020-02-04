import enum

from . import Database
from game_parser import MoveInfoEnums

def build(game_state, is_p1, active_frame_wait):
    floated = game_state.was_just_floated(not is_p1)
    game_state.unrewind()
    fa = get_fa(game_state, is_p1, floated)
    game_state.rewind(active_frame_wait)
    move_id = game_state.get(is_p1).move_id

    entry = Database.get(move_id)
    if entry is None:
        entry = build_frame_data_entry(game_state, is_p1, fa, active_frame_wait)
        Database.record(entry, floated)

    entry[DataColumns.fa] = fa

    return entry

def build_frame_data_entry(game_state, is_p1, fa, active_frame_wait):
    move_id = game_state.get(is_p1).move_id

    entry = {}

    entry[DataColumns.move_id] = move_id
    entry[DataColumns.startup] = game_state.get(is_p1).startup
    entry[DataColumns.hit_type] = MoveInfoEnums.AttackType(game_state.get(is_p1).attack_type).name + ("_THROW" if game_state.get(is_p1).is_attack_throw() else "")
    entry[DataColumns.w_rec] = game_state.get(is_p1).recovery
    entry[DataColumns.cmd] = game_state.get_current_move_string(is_p1)

    game_state.unrewind()

    if game_state.get(not is_p1).is_blocking():
        entry[DataColumns.block] = fa
    else:
        if game_state.get(not is_p1).is_getting_counter_hit():
            entry[DataColumns.counter] = fa
        else:
            entry[DataColumns.normal] = fa

    entry[DataColumns.char_name] = game_state.get(is_p1).movelist_parser.char_name
    entry[DataColumns.move_str] = game_state.get_current_move_name(is_p1)

    game_state.rewind(active_frame_wait + 1)
    entry[DataColumns.guaranteed] = not game_state.get(not is_p1).is_able_to_act()
    game_state.unrewind()
    game_state.rewind(active_frame_wait)

    return entry

def get_fa(game_state, is_p1, floated):
    receiver = game_state.get(not is_p1)
    if receiver.is_being_knocked_down():
        return 'KND'
    elif receiver.is_being_juggled():
        return 'JGL'
    elif floated:
        return 'FLT'
    else:
        time_till_recovery_p1 = game_state.get(is_p1).get_frames_til_next_move()
        time_till_recovery_p2 = game_state.get(not is_p1).get_frames_til_next_move()

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
    guaranteed = 'hit is guaranteed'
