from game_parser.MoveInfoEnums import InputDirectionCodes, InputAttackCodes

class Recording:
    history = None
    moves_per_line = 30

    @classmethod
    def record(cls, input_state):
        if cls.last_move_was(input_state):
            cls.history[-1][-1] += 1
        else:
            cls.history.append([input_state, 1])

    @classmethod
    def last_move_was(cls, input_state):
        if len(cls.history) == 0:
            return False
        return cls.history[-1][0] == input_state

    @classmethod
    def to_string(cls):
        moves = [cls.get_move(i) for i in cls.history]
        chunks = [moves[i:i+cls.moves_per_line] for i in range(0, len(moves), cls.moves_per_line)]
        lines = [' '.join(i) for i in chunks]
        return '\n'.join(lines)

    @classmethod
    def get_move(cls, item):
        input_state, count = item
        raw_move = cls.get_raw_move(input_state)
        if count == 1:
            return raw_move
        else:
            return '%s(%d)' % (raw_move, count)

    @classmethod
    def get_raw_move(cls, input_state):
        direction_code, attack_code, _ = input_state
        direction_string = direction_code.name
        if attack_code == InputAttackCodes.N:
            return direction_string
        attack_string = attack_code.name.replace('x', '').replace('N', '')
        if direction_code == InputDirectionCodes.N:
            return attack_string
        return '%s%s' % (direction_string, attack_string)


def record_start():
    Recording.history = []

def record_end():
    print(Recording.to_string())
    Recording.history = None

def record_if_activated(tekken_state):
    if Recording.history is not None:
        input_state = tekken_state.get_input_state()
        Recording.record(input_state)

def replay():
    print('replay')