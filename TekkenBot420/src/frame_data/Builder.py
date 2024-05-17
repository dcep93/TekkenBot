from ..frame_data import Entry
from ..game_parser import GameLog, GameSnapshot, MoveInfoEnums


def build(game_log: GameLog.GameLog, is_p1: bool) -> Entry.Entry:
    entry = {}
    attacker = game_log.get(is_p1, 1)
    receiver = game_log.get(not is_p1)

    try:
        char_name = MoveInfoEnums.CharacterCodes(attacker.char_id).name
    except ValueError:
        char_name = str(attacker.char_id)
    entry[Entry.DataColumns.char_name] = char_name

    entry[Entry.DataColumns.is_player] = str(is_p1)

    entry[Entry.DataColumns.move_id] = str(attacker.move_id)

    entry[Entry.DataColumns.fa] = get_fa(is_p1, attacker, receiver)

    entry[Entry.DataColumns.startup] = str(attacker.startup)

    entry[Entry.DataColumns.hit_type] = MoveInfoEnums.AttackType(
        attacker.attack_type).name

    if receiver.complex_state == MoveInfoEnums.ComplexMoveStates.BLOCK:
        entry[Entry.DataColumns.block] = entry[Entry.DataColumns.fa]
    else:
        entry[Entry.DataColumns.block] = str(None)

    entry[Entry.DataColumns.health] = get_remaining_health_string(game_log)

    entry[Entry.DataColumns.combo] = get_combo(game_log, is_p1)

    entry[Entry.DataColumns.hit_outcome] = receiver.hit_outcome.name

    return entry


def get_fa(is_p1: bool, attacker: GameSnapshot.PlayerSnapshot, receiver: GameSnapshot.PlayerSnapshot) -> str:
    if receiver.simple_state == MoveInfoEnums.SimpleMoveStates.KNOCKDOWN:
        return 'KND'
    elif receiver.hit_outcome == MoveInfoEnums.HitOutcome.JUGGLE:
        return 'JGL'
    else:
        time_till_recovery_p1 = attacker.frames_til_next_move
        time_till_recovery_p2 = 0 if receiver.hit_outcome is MoveInfoEnums.HitOutcome.NONE else receiver.frames_til_next_move

        raw_fa = time_till_recovery_p2 - time_till_recovery_p1

        raw_fa_str = str(raw_fa)

        if raw_fa > 0:
            raw_fa_str = "+%s" % raw_fa_str
        return raw_fa_str


def get_remaining_health_string(game_log: GameLog.GameLog) -> str:
    MAX_HEALTH = 180
    remainings = [MAX_HEALTH -
                  game_log.get(i).damage_taken for i in [True, False]]
    return '%d/%d' % tuple(remainings)


def get_combo(game_log: GameLog.GameLog, is_p1: bool) -> str:
    count = 0
    damage = 0
    last_damage = game_log.get(not is_p1).damage_taken
    for frame in range(1000):
        p = game_log.get(not is_p1, frame)
        if p is None:
            break
        if p.damage_taken != last_damage:
            count += 1
            damage += last_damage - p.damage_taken
            last_damage = p.damage_taken
        if p.hit_outcome in [MoveInfoEnums.HitOutcome.NONE, MoveInfoEnums.HitOutcome.BLOCKED_STANDING, MoveInfoEnums.HitOutcome.BLOCKED_CROUCHING]:
            if p.simple_state not in [
                MoveInfoEnums.SimpleMoveStates.JUGGLED,
                MoveInfoEnums.SimpleMoveStates.WALL_SPLAT_18,
                MoveInfoEnums.SimpleMoveStates.WALL_SPLAT_19,
            ]:
                break
    return f'{count}/{damage}'
