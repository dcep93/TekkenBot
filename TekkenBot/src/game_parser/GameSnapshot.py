from ..game_parser import MoveInfoEnums

class PlayerSnapshot:
    def __init__(self, player_data_dict: typing.Dict[str, int]):
        d = player_data_dict

        self.move_id = d['move_id']
        self.simple_state = MoveInfoEnums.SimpleMoveStates(d['simple_move_state'])
        self.attack_type = MoveInfoEnums.AttackType(d['attack_type'])
        self.startup = d['attack_startup']
        self.attack_damage = d['attack_damage']
        self.complex_state = MoveInfoEnums.ComplexMoveStates(d['complex_move_state'])
        self.damage_taken = d['damage_taken']
        self.move_timer = 0 if self.startup == 0 else d['move_timer']
        self.frames_til_attack = self.startup - self.move_timer
        self.recovery = d['recovery']
        self.frames_til_next_move = self.recovery - self.move_timer
        self.char_id = d['char_id']
        throw_flag = d['throw_flag']
        self.is_attack_throw = throw_flag == 1
        self.throw_tech = MoveInfoEnums.ThrowTechs(d['throw_tech'])
        self.input_direction = MoveInfoEnums.InputDirectionCodes(d['input_direction'])
        self.input_button = MoveInfoEnums.InputAttackCodes(d['input_attack'] % MoveInfoEnums.InputAttackCodes.xRAGE.value)
        self.stun_state = MoveInfoEnums.StunStates(d['stun_type'])
        self.hit_outcome = MoveInfoEnums.HitOutcome(d['hit_outcome'])
        self.recovery_window_bitmask = d['recovery']

class GameSnapshot:
    def __init__(self, p1: PlayerSnapshot, p2: PlayerSnapshot, frame_count: int, facing_bool: bool):
        self.p1 = p1
        self.p2 = p2
        self.frame_count = frame_count
        self.facing_bool = facing_bool
