import enum

from game_parser.MoveInfoEnums import InputDirectionCodes, InputAttackCodes
from misc import Globals
from misc.Windows import w as Windows
from . import Shared

def record_single():
    print("starting recording single")
    Recorder.state = RecordingState.SINGLE
    Recorder.history = []

def record_both():
    print("starting recording both")
    Recorder.state = RecordingState.BOTH
    Recorder.history = []

def record_end():
    print("ending recording")
    Recorder.state = RecordingState.OFF

    recording_string = get_recording_string()
    Recorder.history = None
    path = Shared.get_path()
    with open(path, 'w') as fh:
        fh.write(recording_string)

def record_if_activated():
    if Recorder.state != RecordingState.OFF:
        record_state()

SIDE_SWITCH = 'SIDE_SWITCH'
moves_per_line = 10

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

class Recorder:
    state = RecordingState.OFF
    history = None
    reverse = False

def check_for_side_switch(last_state):
    facing = bool(last_state.facing_bool) ^ (not last_state.is_player_player_one)
    if Recorder.reverse != facing:
        Recorder.reverse = facing
        Recorder.history.append(SIDE_SWITCH)

def get_input_state():
    last_state = Globals.Globals.tekken_state.state_log[-1]
    check_for_side_switch(last_state)
    if last_state.is_player_player_one:
        player = last_state.p1
        opp = last_state.p2
    else:
        player = last_state.p2
        opp = last_state.p1
    player_input_state = player.get_input_state()
    opp_input_state = opp.get_input_state()
    if Recorder.state == RecordingState.SINGLE:
        return player_input_state
    else:
        return BothInputState(player_input_state, opp_input_state)

def last_move_was(input_state):
    if len(Recorder.history) == 0:
        return False
    return Recorder.history[-1][0] == input_state

def get_move(item):
    if item == SIDE_SWITCH:
        return item
    input_state, count = item
    raw_move = get_raw_move(input_state)
    if count == 1:
        return raw_move
    else:
        return '%s(%d)' % (raw_move, count)

def get_raw_move(input_state):
    if isinstance(input_state, BothInputState):
        input_states = [get_raw_move(i) for i in input_state.input_states]
        if input_states[1] == 'N_':
            return input_states[0]
        return '/'.join(input_states)
    direction_code, attack_code, _ = input_state
    direction_string = direction_code.name
    attack_string = attack_code.name.replace('x', '').replace('N', '')
    return '%s%s' % (direction_string, attack_string)

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

def move_to_hexes(move, reverse, p1=True):
    if '/' in move:
        p1_move, p2_move = move.split('/')
        p1_codes = move_to_hexes(p1_move, reverse, True)
        p2_codes = move_to_hexes(p2_move, reverse, False)
        return p1_codes + p2_codes
    move.replace('_', '')
    direction_string = ''.join([i for i in move if i not in '1234'])
    attack_string = move[len(direction_string):]
    if direction_string in ['NULL', 'N']:
        direction_hexes = []
    else:
        if reverse ^ (not p1):
            direction_string = direction_string.replace('b', 'F').replace('f', 'B').replace('F', 'f').replace('B', 'b')
        direction_hexes = [direction_string_to_hexes[p1][d] for d in direction_string]
    attack_hexes = [attack_string_to_hex[p1][a] for a in attack_string]
    hex_key_codes = direction_hexes + attack_hexes
    return hex_key_codes

def record_state():
    if Globals.Globals.game_reader.is_foreground_pid():
        input_state = get_input_state()
        if last_move_was(input_state):
            Recorder.history[-1][-1] += 1
        else:
            Recorder.history.append([input_state, 1])

def get_recording_string():
    moves = [get_move(i) for i in Recorder.history]
    chunks = [moves[i:i+moves_per_line] for i in range(0, len(moves), moves_per_line)]
    lines = [' '.join(i) for i in chunks]
    return '\n'.join(lines)
