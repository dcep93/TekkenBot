import os
import time

from . import Path
from game_parser.MoveInfoEnums import InputDirectionCodes, InputAttackCodes

from misc.Windows import w as Windows

seconds_per_frame = 1/60.

direction_code_to_hexes = {
    InputDirectionCodes.NULL: [],
    InputDirectionCodes.N: [],
    InputDirectionCodes.u: [0x11],
    InputDirectionCodes.ub: [0x11, 0x1E],
    InputDirectionCodes.uf: [0x11, 0x20],
    InputDirectionCodes.f: [0x20],
    InputDirectionCodes.b: [0x1E],
    InputDirectionCodes.d: [0x1F],
    InputDirectionCodes.df: [0x1F, 0x20],
    InputDirectionCodes.db: [0x1F, 0x1E],
}

attack_string_to_hex = {
    '1': 0x16,
    '2': 0x17,
    '3': 0x24,
    '4': 0x25
}

class Recording:
    history = None
    moves_per_line = 10
    pressed = []

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
        attack_string = attack_code.name.replace('x', '').replace('N', '')
        return '%s_%s' % (direction_string, attack_string)

    @classmethod
    def loads_moves(cls, compacted_moves):
        moves = []
        for compacted_move in compacted_moves:
            parts = compacted_move.split('(')
            move = parts[0]
            if len(parts) == 1:
                count = 1
            else:
                count_str = parts[1].split(')')[0]
                count = int(count_str)
            for i in range(count):
                moves.append(move)
        return moves

    @classmethod
    def replay_move(cls, move):
        parts = move.split('_')
        direction_string, attack_string = parts
        direction_code = InputDirectionCodes[direction_string]
        direction_hexes = direction_code_to_hexes[direction_code]
        attack_hexes = [attack_string_to_hex[a] for a in attack_string]
        hex_key_codes = direction_hexes + attack_hexes
        to_release = [i for i in cls.pressed if i not in hex_key_codes]
        to_press = [i for i in hex_key_codes if i not in cls.pressed]
        for hex_key_code in to_release:
            Windows.release_key(hex_key_code)
        for hex_key_code in to_press:
            Windows.press_key(hex_key_code)
        cls.pressed = hex_key_codes

class Replayer:
    def __init__(self, moves, master):
        self.moves = moves
        self.master = master

    def replay(self):
        if self.master.tekken_state.game_reader.is_foreground_pid():
            self.replay_moves()
        else:
            self.master.after(100, self.replay)

    def replay_moves(self):
        print("replaying")
        self.start = time.time()
        self.i = 0
        self.replay_next_move()

    def replay_next_move(self):
        if self.i == len(self.moves):
            self.finish()
            return
        
        target = self.i * seconds_per_frame
        actual = time.time() - self.start
        diff = target - actual
        if diff > 0:
            diff_ms = int(diff * 1000)
            self.master.after(diff_ms, self.actually_replay_next_move)
        else:
            self.actually_replay_next_move()

    def actually_replay_next_move(self):
        # quit if tekken is not foreground
        if not self.master.tekken_state.game_reader.is_foreground_pid():
            print('lost focus')
            self.finish()
            return
        move = self.moves[self.i]
        Recording.replay_move(move)
        self.i += 1
        self.replay_next_move()

    def finish(self):
        for hex_key_code in Recording.pressed:
            Windows.release_key(hex_key_code)
        Recording.pressed = []
        print("done")

def record_start():
    print("starting recording")
    Recording.history = []

def record_end():
    if Recording.history is None:
        print("recording not active")
        return
    print("ending recording")
    recording_str = Recording.to_string()
    path = Path.path('./record/recording.txt')
    with open(path, 'w') as fh:
        fh.write(recording_str)
    Recording.history = None

def record_if_activated(tekken_state):
    if Recording.history is not None:
        input_state = tekken_state.get_input_state()
        Recording.record(input_state)

def replay(master):
    path = Path.path('./record/recording.txt')
    if not os.path.isfile(path):
        print("recording not found")
        return
    with open(path) as fh:
        contents = fh.read()
    raw_string = contents.replace('\n', ' ')
    compacted_moves = raw_string.split(' ')
    moves = Recording.loads_moves(compacted_moves)
    if not Windows.valid:
        print("not windows?")
        return
    print('waiting for tekken focus')
    replayer = Replayer(moves, master)
    replayer.replay()
