from . import Database
from . import DataColumns
from game_parser import MoveInfoEnums

def build(game_state, is_p1):
    entry = {}
    entry[DataColumns.DataColumns.fa] = get_fa(game_state, is_p1)
    entry[DataColumns.DataColumns.move_id] = game_state.get(is_p1, 1).move_id
    entry[DataColumns.DataColumns.char_name] = game_state.get(is_p1).movelist_parser.char_name
    
    entry[DataColumns.DataColumns.move_name] = game_state.get_current_move_name(is_p1)
    entry[DataColumns.DataColumns.punish] = not game_state.get(not is_p1).is_able_to_act()

    loaded = Database.load(entry)
    if not loaded:
        entry = build_frame_data_entry(entry, game_state, is_p1)
        Database.record(entry)

    return entry

def build_frame_data_entry(entry, game_state, is_p1):
    entry[DataColumns.DataColumns.startup] = game_state.get(is_p1).startup
    entry[DataColumns.DataColumns.hit_type] = MoveInfoEnums.AttackType(game_state.get(is_p1).attack_type).name + ("_THROW" if game_state.get(is_p1).is_attack_throw() else "")
    entry[DataColumns.DataColumns.cmd] = game_state.get_current_move_string(is_p1)

    receiver = game_state.get(not is_p1)

    fa = entry[DataColumns.DataColumns.fa]
    if receiver.is_blocking():
        entry[DataColumns.DataColumns.block] = fa
    elif receiver.is_getting_counter_hit():
        entry[DataColumns.DataColumns.counter] = fa
    elif receiver.is_getting_hit():
        entry[DataColumns.DataColumns.normal] = fa

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
