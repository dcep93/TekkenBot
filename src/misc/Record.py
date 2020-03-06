import enum
import os
import time

from . import Path
from game_parser.MoveInfoEnums import InputDirectionCodes, InputAttackCodes

from misc.Windows import w as Windows

seconds_per_frame = 1/60.
SIDE_SWITCH = 'SIDE_SWITCH'

direction_string_to_hexes = {
    True: {
        'u': 0x11,
        'f': 0x20,
        'b': 0x1E,
        'd': 0x1F,
    },
    False: {
        'u': 0xc8,
        'f': 0x20,
        'b': 0xCB,
        'd': 0xd0,
    }
}

attack_string_to_hex = {
    True: {
        '1': 0x16,
        '2': 0x17,
        '3': 0x24,
        '4': 0x25,
    },
    False: {
        '1': 0x47,
        '2': 0x48,
        '3': 0x4b,
        '4': 0x4c,
    }
}

@enum.unique
class RecordingState(enum.Enum):
    OFF = 0
    SINGLE = 1
    BOTH = 2

class BothInputState:
    def __init__(self, *input_states):
        self.input_states = input_states

    def __eq__(self, other):
        return isinstance(other, BothInputState) and self.input_states == other.input_states

# todo instance methods
class Recorder:
    moves_per_line = 10

    def __init__(self):
        self.history = None
        self.state = RecordingState.OFF
        self.reverse = False

    def record(self, tekken_state):
        if self.is_side_switch(tekken_state):
            self.history.append(SIDE_SWITCH)
        input_state = self.get_input_state(tekken_state)
        if self.last_move_was(input_state):
            self.history[-1][-1] += 1
        else:
            self.history.append([input_state, 1])

    @staticmethod
    def is_side_switch(self, tekken_state):
        # todo build
        return False

    def get_input_state(self, tekken_state):
        last_state = tekken_state.state_log[-1]
        if last_state.is_player_player_one:
            player = last_state.p1
            opp = last_state.p2
        else:
            player = last_state.p2
            opp = last_state.p1
        player_input_state = player.get_input_state()
        opp_input_state = opp.get_input_state()
        if self.state == RecordingState.SINGLE:
            return player_input_state
        else:
            return BothInputState(player_input_state, opp_input_state)

    def last_move_was(self, input_state):
        if len(self.history) == 0:
            return False
        return self.history[-1][0] == input_state

    def to_string(self):
        moves = [self.get_move(i) for i in self.history]
        chunks = [moves[i:i+self.moves_per_line] for i in range(0, len(moves), self.moves_per_line)]
        lines = [' '.join(i) for i in chunks]
        return '\n'.join(lines)

    def get_move(self, item):
        if item == SIDE_SWITCH:
            return item
        input_state, count = item
        raw_move = self.get_raw_move(input_state)
        if count == 1:
            return raw_move
        else:
            return '%s(%d)' % (raw_move, count)

    def get_raw_move(self, input_state):
        if isinstance(input_state, BothInputState):
            input_states = [self.get_raw_move(i) for i in input_state.input_states]
            if input_states[1] == 'N_':
                return input_states[0]
            return '/'.join(input_states)
        direction_code, attack_code, _ = input_state
        direction_string = direction_code.name
        attack_string = attack_code.name.replace('x', '').replace('N', '')
        return '%s_%s' % (direction_string, attack_string)

    @staticmethod
    def loads_moves(compacted_moves):
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

    def move_to_hexes(self, move, reverse, p1=True):
        if '/' in move:
            p1_move, p2_move = move.split('/')
            p1_codes = self.move_to_hexes(p1_move, reverse, True)
            p2_codes = self.move_to_hexes(p2_move, reverse, False)
            return p1_codes + p2_codes
        parts = move.split('_')
        direction_string, attack_string = parts
        if direction_string in ['NULL', 'N']:
            direction_hexes = []
        else:
            if reverse:
                direction_string.replace('b', 'F').replace('f', 'B').replace('F', 'f').replace('B', 'b')
            direction_hexes = [direction_string_to_hexes[p1][d] for d in direction_string]
        attack_hexes = [attack_string_to_hex[p1][a] for a in attack_string]
        hex_key_codes = direction_hexes + attack_hexes
        return hex_key_codes

class Replayer:
    def __init__(self, moves, master):
        self.moves = moves
        self.master = master
        self.pressed = []
        self.reverse = False

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

        if self.move_is_side_switch():
            self.reverse = not self.reverse
            self.i += 1
            self.handle_next_move()
        
        target = self.i * seconds_per_frame
        actual = time.time() - self.start
        diff = target - actual
        if diff > 0:
            diff_ms = int(diff * 1000)
            self.master.after(diff_ms, self.replay_next_move)
        else:
            self.replay_next_move()

    def move_is_side_switch(self):
        move = self.moves[self.i]
        return move == SIDE_SWITCH

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
        hex_key_codes = Recorder.move_to_hexes(move, self.reverse)
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
    recording_str = Recorder.to_string()
    Recorder.state = RecordingState.OFF
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
