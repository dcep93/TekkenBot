from . import Database, DataColumns
from game_parser import MoveInfoEnums

MAX_HEALTH = 175

def build(game_log, is_p1):
    entry = {}
    entry[DataColumns.DataColumns.fa] = get_fa(game_log, is_p1)
    entry[DataColumns.DataColumns.move_id] = game_log.get(is_p1, 1).move_id
 
    entry[DataColumns.DataColumns.char_name] = get_char_name(game_log, is_p1)
    
    entry[DataColumns.DataColumns.health] = get_remaining_health_string(game_log)

    loaded = Database.load(entry)
    if not loaded:
        entry = build_frame_data_entry(game_log, entry, is_p1)
        Database.record(entry)

    if not game_log.get(not is_p1).is_blocking():
        del entry[DataColumns.DataColumns.fa]

    return entry

def get_char_name(game_log, is_p1):
    movelist_parser = game_log.get(is_p1).movelist_parser
    return Database.Characters(movelist_parser.char_name).name if movelist_parser is not None else game_log.get(is_p1).char_id

def build_frame_data_entry(game_log, entry, is_p1):
    entry[DataColumns.DataColumns.startup] = game_log.get(is_p1).startup
    entry[DataColumns.DataColumns.hit_type] = MoveInfoEnums.AttackType(game_log.get(is_p1).attack_type).name + ("_THROW" if game_log.get(is_p1).is_attack_throw() else "")
    entry[DataColumns.DataColumns.cmd] = game_log.get_current_move_string(is_p1)

    receiver = game_log.get(not is_p1)

    fa = entry[DataColumns.DataColumns.fa]
    if receiver.is_blocking():
        entry[DataColumns.DataColumns.block] = fa
    elif receiver.is_getting_counter_hit():
        entry[DataColumns.DataColumns.counter] = fa
    elif receiver.is_getting_hit():
        entry[DataColumns.DataColumns.normal] = fa

    return entry

def get_fa(game_log, is_p1):
    receiver = game_log.get(not is_p1)
    if receiver.is_being_knocked_down():
        return 'KND'
    elif receiver.is_being_juggled():
        return 'JGL'
    elif game_log.was_just_floated(not is_p1):
        return 'FLT'
    else:
        time_till_recovery_p1 = game_log.get(is_p1).get_frames_til_next_move()
        time_till_recovery_p2 = 0 if receiver.hit_outcome is MoveInfoEnums.HitOutcome.NONE else receiver.get_frames_til_next_move()

        raw_fa = time_till_recovery_p2 - time_till_recovery_p1
        raw_fa_str = str(raw_fa)

        if raw_fa > 0:
            raw_fa_str = "+%s" % raw_fa_str
        return raw_fa_str

def get_remaining_health_string(game_log):
    remainings = [MAX_HEALTH - game_log.get(i).damage_taken for i in [True, False]]
    return '%d/%d' % tuple(remainings)