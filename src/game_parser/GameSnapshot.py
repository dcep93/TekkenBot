from . import MoveInfoEnums

class PlayerSnapshot:
    def __init__(self, player_data_dict):
        d = player_data_dict

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
        self.frames_til_next_move = self.recovery - self.move_timer
        self.char_id = d['PlayerDataAddress.char_id']
        raw_distance = d['PlayerDataAddress.distance']
        self.distance = (raw_distance / 3700000) - 309.76
        throw_flag = d['PlayerDataAddress.throw_flag']
        self.is_attack_throw = throw_flag == 1
        self.throw_tech = MoveInfoEnums.ThrowTechs(d['PlayerDataAddress.throw_tech'])
        self.input_direction = MoveInfoEnums.InputDirectionCodes(d['PlayerDataAddress.input_direction'])
        self.input_button = MoveInfoEnums.InputAttackCodes(d['PlayerDataAddress.input_attack'] % MoveInfoEnums.InputAttackCodes.xRAGE.value)
        self.stun_state = MoveInfoEnums.StunStates(d['PlayerDataAddress.stun_type'])
        self.hit_outcome = MoveInfoEnums.HitOutcome(d['PlayerDataAddress.hit_outcome'])
        self.recovery_window_bitmask = d['PlayerDataAddress.recovery']

class GameSnapshot:
    def __init__(self, is_player_player_one, p1, p2, frame_count, facing_bool):
        self.is_player_player_one = is_player_player_one
        self.p1 = p1
        self.p2 = p2
        self.frame_count = frame_count
        self.facing_bool = facing_bool
