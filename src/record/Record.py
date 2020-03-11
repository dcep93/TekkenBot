import enum

from game_parser import ScriptedGame
from game_parser.MoveInfoEnums import InputDirectionCodes, InputAttackCodes
from misc import Globals
from misc.Windows import w as Windows
from . import Shared

def record_single():
    record_start(RecordingState.SINGLE)

def record_both():
    record_start(RecordingState.BOTH)

def record_start(state):
    print("starting recording %s" % state.name)
    Recorder.state = state
    Recorder.history = []
    reader = Globals.Globals.game_reader
    if isinstance(reader, ScriptedGame.Recorder):
        reader.reset()

def record_end():
    print("ending recording")
    Recorder.state = RecordingState.OFF

    recording_string = get_recording_string()
    print(recording_string)
    Recorder.history = None
    path = Shared.get_path()
    with open(path, 'w') as fh:
        fh.write(recording_string)

    reader = Globals.Globals.game_reader
    if isinstance(reader, ScriptedGame.Recorder):
        reader.dump()

def record_if_activated():
    if Recorder.state != RecordingState.OFF:
        record_state()

moves_per_line = 10

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

def get_input_state():
    last_state = Globals.Globals.tekken_state.state_log[-1]
    if last_state.is_player_player_one:
        player = last_state.p1
        opp = last_state.p2
    else:
        player = last_state.p2
        opp = last_state.p1
    player_input_state = player.get_input_as_string()
    opp_input_state = opp.get_input_as_string()
    if Recorder.state == RecordingState.SINGLE:
        return player_input_state
    else:
        return BothInputState(player_input_state, opp_input_state)

def last_move_was(input_state):
    if len(Recorder.history) == 0:
        return False
    return Recorder.history[-1][0] == input_state

def get_move(item):
    input_state, count = item
    raw_move = get_raw_move(input_state)
    if count == 1:
        return raw_move
    else:
        return '%s(%d)' % (raw_move, count)

def get_raw_move(input_state):
    if isinstance(input_state, BothInputState):
        if input_state.input_states[1] == 'N':
            return input_state.input_states[0]
        return '/'.join(input_state.input_states)
    return input_state

def record_state():
    if Globals.Globals.game_reader.is_foreground_pid():
        input_state = get_input_state()
        if last_move_was(input_state):
            Recorder.history[-1][-1] += 1
        else:
            Recorder.history.append([input_state, 1])

def get_recording_string():
    strip_neutrals()
    moves = [get_move(i) for i in Recorder.history]
    if len(moves) == 0:
        return ''
    chunks = [moves[i:i+moves_per_line] for i in range(0, len(moves), moves_per_line)]
    lines = [' '.join(i) for i in chunks]
    moves_string = '\n'.join(lines)

    distance = get_distance()
    count = sum([i[1] for i in Recorder.history])
    quotient = distance / count
    comment = '%f / %d = %f' % (distance, count, quotient)
    return '%s\n# %s\n' % (moves_string, comment)

def strip_neutrals():
    strip_neutrals_helper(0, 1)
    strip_neutrals_helper(-1, -1)

def strip_neutrals_helper(index, step):
    while True:
        if abs(index) > len(Recorder.history):
            return
        val = Recorder.history[index]
        move_string = get_move(val)
        if move_string == 'N' or move_string.startswith('N('):
            Recorder.history.pop(index)
        else:
            return

def get_distance():
    raw_distance = Globals.Globals.tekken_state.get(True).distance
    normalized = (raw_distance - 1148262975) / 4500000
    return normalized - 2
