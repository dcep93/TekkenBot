import enum
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

@enum.unique
class RecordingState(enum.Enum):
    OFF = 0
    SINGLE = 1
    BOTH = 2

class Recorder:
    history = None
    moves_per_line = 10
    state = RecordingState.OFF

    @classmethod
    def record(cls, tekken_state):
        input_state = cls.get_input_state(tekken_state)
        if cls.last_move_was(input_state):
            cls.history[-1][-1] += 1
        else:
            cls.history.append([input_state, 1])

    @classmethod
    def get_input_state(cls, tekken_state):
        last_state = self.state.state_log[-1]
        if last_state.is_player_player_one:
            player = last_state.p1
            opp = last_state.p2
        else:
            player = last_state.p2
            opp = last_state.p1
        player_input_state = player.get_input_state()
        opp_input_state = opp.get_input_state()
        if cls.state == RecordingState.SINGLE:
            return player_input_state
        else:
            return (player_input_state, opp_input_state)

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
    def get_raw_move(cls, input_state, recursive=False):
        if not recursive and cls.RecordingState == RecordingState.BOTH:
            input_states = [cls.get_raw_move(i, True) for i in input_state]
            if input_states[1] == 'N_':
                return input_states[0]
            return '/'.join(input_states)
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
    def move_to_hexes(cls, move, p1=True):
        if '/' in move:
            p1_move, p2_move = move.split('/')
            p1_codes = cls.move_to_hexes(p1_move, True)
            p2_codes = cls.move_to_hexes(p2_move, False)
            return p1_codes + p2_codes
        parts = move.split('_')
        direction_string, attack_string = parts
        direction_code = InputDirectionCodes[direction_string]
        direction_hexes = direction_code_to_hexes[direction_code]
        attack_hexes = [attack_string_to_hex[a] for a in attack_string]
        hex_key_codes = direction_hexes + attack_hexes
        return hex_key_codes

class Replayer:
    def __init__(self, moves, master):
        self.moves = moves
        self.master = master
        self.pressed = []

        self.i = None
        self.start = None

    def replay(self):
        if self.master.tekken_state.game_reader.is_foreground_pid():
            self.replay_moves()
        else:
            self.master.after(100, self.replay)

    def replay_moves(self):
        print("replaying")
        self.start = time.time()
        self.i = 0
        self.handle_next_move()

    def handle_next_move(self):
        if self.i == len(self.moves):
            self.finish()
            return
        
        target = self.i * seconds_per_frame
        actual = time.time() - self.start
        diff = target - actual
        if diff > 0:
            diff_ms = int(diff * 1000)
            self.master.after(diff_ms, self.replay_next_move)
        else:
            self.replay_next_move()

    def replay_next_move(self):
        # quit if tekken is not foreground
        if not self.master.tekken_state.game_reader.is_foreground_pid():
            print('lost focus')
            self.finish()
            return
        move = self.moves[self.i]
        self.replay_move(move)
        self.i += 1
        self.handle_next_move()

    def finish(self):
        for hex_key_code in self.pressed:
            Windows.release_key(hex_key_code)
        self.pressed = []
        print("done")

    def replay_move(self, move):
        hex_key_codes = Recorder.move_to_hexes(move)
        to_release = [i for i in self.pressed if i not in hex_key_codes]
        to_press = [i for i in hex_key_codes if i not in self.pressed]
        for hex_key_code in to_release:
            Windows.release_key(hex_key_code)
        for hex_key_code in to_press:
            Windows.press_key(hex_key_code)
        self.pressed = hex_key_codes

def record_single():
    print("starting recording single")
    Recorder.state = RecordingState.SINGLE
    Recorder.history = []

def record_both():
    print("starting recording both")
    Recorder.state = RecordingState.BOTH
    Recorder.history = []

def record_end():
    if Recorder.state == RecordingState.OFF:
        print("recording not active")
        return
    print("ending recording")
    Recorder.state = RecordingState.OFF
    recording_str = Recorder.to_string()
    path = get_path()
    with open(path, 'w') as fh:
        fh.write(recording_str)
    Recorder.history = None

def record_if_activated(tekken_state):
    if Recorder.state != RecordingState.OFF:
        Recorder.record(tekken_state)

def get_path():
    return Path.path('./record/recording.txt')

def replay(master):
    path = get_path()
    if not os.path.isfile(path):
        print("recording not found")
        return
    with open(path) as fh:
        contents = fh.read()
    raw_string = contents.replace('\n', ' ')
    compacted_moves = raw_string.split(' ')
    moves = Recorder.loads_moves(compacted_moves)
    if not Windows.valid:
        print("not windows?")
        return
    print('waiting for tekken focus')
    replayer = Replayer(moves, master)
    replayer.replay()
