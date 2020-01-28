from . import MoveInfoEnums


class BotSnapshot:
    def __init__(self, player_data_dict):
        d = player_data_dict

        self.movelist_to_use = d['PlayerDataAddress.movelist_to_use']
        self.move_id = d['PlayerDataAddress.move_id']
        self.simple_state = MoveInfoEnums.SimpleMoveStates(d['PlayerDataAddress.simple_move_state'])
        self.attack_type = MoveInfoEnums.AttackType(d['PlayerDataAddress.attack_type'])
        self.startup = d['PlayerDataAddress.attack_startup']
        self.startup_end = d['PlayerDataAddress.attack_startup_end']
        self.attack_damage = d['PlayerDataAddress.attack_damage']
        self.complex_state = MoveInfoEnums.ComplexMoveStates(d['PlayerDataAddress.complex_move_state'])
        self.damage_taken = d['PlayerDataAddress.damage_taken']
        self.move_timer = d['PlayerDataAddress.move_timer']
        self.recovery = d['PlayerDataAddress.recovery']
        self.char_id = d['PlayerDataAddress.char_id']
        self.throw_flag = d['PlayerDataAddress.throw_flag']
        self.rage_flag = d['PlayerDataAddress.rage_flag']
        self.input_counter = d['PlayerDataAddress.input_counter']
        self.input_direction = MoveInfoEnums.InputDirectionCodes(d['PlayerDataAddress.input_direction'])
        self.input_button = MoveInfoEnums.InputAttackCodes(d['PlayerDataAddress.input_attack'] % MoveInfoEnums.InputAttackCodes.xRAGE.value)
        self.rage_button_flag = d['PlayerDataAddress.input_attack'] >= MoveInfoEnums.InputAttackCodes.xRAGE.value
        self.stun_state = MoveInfoEnums.StunStates(d['PlayerDataAddress.stun_type'])
        self.power_crush_flag = d['PlayerDataAddress.power_crush'] > 0

        cancel_window_bitmask = d['PlayerDataAddress.cancel_window']
        recovery_window_bitmask = d['PlayerDataAddress.recovery']

        self.is_cancelable = (MoveInfoEnums.CancelStatesBitmask.CANCELABLE.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.CANCELABLE.value
        self.is_bufferable = (MoveInfoEnums.CancelStatesBitmask.BUFFERABLE.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.BUFFERABLE.value
        self.is_parry_1 = (MoveInfoEnums.CancelStatesBitmask.PARRYABLE_1.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.PARRYABLE_1.value
        self.is_parry_2 = (MoveInfoEnums.CancelStatesBitmask.PARRYABLE_2.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.PARRYABLE_2.value
        
        self.is_recovering = (MoveInfoEnums.ComplexMoveStates.RECOVERING.value & recovery_window_bitmask) == MoveInfoEnums.ComplexMoveStates.RECOVERING.value
        
        if self.startup > 0:
            self.is_starting = (self.move_timer <= self.startup)
        else:
            self.is_starting = False

        self.throw_tech = MoveInfoEnums.ThrowTechs(d['PlayerDataAddress.throw_tech'])

        self.skeleton = (d['PlayerDataAddress.x'], d['PlayerDataAddress.y'], d['PlayerDataAddress.z'])

        self.active_xyz = (d['PlayerDataAddress.activebox_x'], d['PlayerDataAddress.activebox_y'], d['PlayerDataAddress.activebox_z'])

        self.is_jump = d['PlayerDataAddress.jump_flags'] & MoveInfoEnums.JumpFlagBitmask.JUMP.value == MoveInfoEnums.JumpFlagBitmask.JUMP.value
        self.hit_outcome = MoveInfoEnums.HitOutcome(d['PlayerDataAddress.hit_outcome'])
        self.mystery_state = d['PlayerDataAddress.mystery_state']

        self.wins = d['EndBlockPlayerDataAddress.round_wins']
        self.combo_counter = d['EndBlockPlayerDataAddress.display_combo_counter']
        self.combo_damage = d['EndBlockPlayerDataAddress.display_combo_damage']
        self.juggle_damage = d['EndBlockPlayerDataAddress.display_juggle_damage']

        self.movelist_parser = d['movelist_parser']

        self.character_name = MoveInfoEnums.CharacterCodes(d['PlayerDataAddress.char_id']).name

    def GetInputState(self):
        return (self.input_direction, self.input_button, self.rage_button_flag)

    def GetTrackingType(self):
        return self.complex_state

    def IsBlocking(self):
        return self.complex_state == MoveInfoEnums.ComplexMoveStates.BLOCK

    def IsGettingCounterHit(self):
        return self.hit_outcome in (MoveInfoEnums.HitOutcome.COUNTER_HIT_CROUCHING, MoveInfoEnums.HitOutcome.COUNTER_HIT_STANDING)

    def IsGettingWallSplatted(self):
        return self.simple_state in (MoveInfoEnums.SimpleMoveStates.WALL_SPLAT_18, MoveInfoEnums.SimpleMoveStates.WALL_SPLAT_19)

    def IsGettingHit(self):
        return self.stun_state in (MoveInfoEnums.StunStates.BEING_PUNISHED, MoveInfoEnums.StunStates.GETTING_HIT)

    def IsAttackThrow(self):
        return self.throw_flag == 1

    def IsInThrowing(self):
        return self.attack_type == MoveInfoEnums.AttackType.THROW

    def GetActiveFrames(self):
        return self.startup_end - self.startup + 1

    def IsBeingKnockedDown(self):
        return self.simple_state == MoveInfoEnums.SimpleMoveStates.KNOCKDOWN

    def GetFramesTillNextMove(self):
        return self.recovery - self.move_timer

    # todo - for keeping cancelable states longer
    def IsAbleToAct(self):
        return self.is_cancelable

class GameSnapshot:
    def __init__(self, bot, opp, frame_count, timer_in_frames, facing_bool, is_player_player_one):
        self.bot = bot
        self.opp = opp
        self.frame_count = frame_count
        self.facing_bool = facing_bool
        self.timer_frames_remaining = timer_in_frames
        self.is_player_player_one = is_player_player_one

    def FromMirrored(self):
        return GameSnapshot(self.opp, self.bot, self.frame_count, self.timer_frames_remaining, self.facing_bool, self.is_player_player_one)
