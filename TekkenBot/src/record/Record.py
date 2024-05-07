import enum

from src.frame_data import Entry
from src.game_parser import ScriptedGame
from src.misc import Shared

def record_single():
    record_start(RecordingState.SINGLE)

def record_both():
    record_start(RecordingState.BOTH)

def record_start(state):
    print("starting recording %s" % state.name)
    Shared.Shared.frame_data_overlay.print_f({
        Entry.DataColumns.move_id: 'RECORD',
        Entry.DataColumns.char_name: state.name
    })
    Recorder.state = state
    Recorder.history = []
    reader = Shared.Shared.game_reader
    if isinstance(reader, ScriptedGame.Recorder):
        reader.reset(True)

def record_end():
    print("ending recording")
    Recorder.state = RecordingState.OFF
    Shared.Shared.frame_data_overlay.print_f({
        Entry.DataColumns.move_id: 'RECORD',
        Entry.DataColumns.char_name: Recorder.state.name
    })

    recording_string = get_recording_string()
    print(recording_string)
    Recorder.history = None
    path = get_record_path()
    with open(path, 'w') as fh:
        fh.write(recording_string)

    reader = Shared.Shared.game_reader
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

class Recorder:
    state = RecordingState.OFF
    history = None

def get_input_state():
    last_state = Shared.Shared.game_log.state_log[-1]
    player = last_state.p1
    opp = last_state.p2
    player_input_state = get_input_as_string(player)
    if Recorder.state == RecordingState.SINGLE:
        return player_input_state
    else:
        opp_input_state = get_input_as_string(opp)
        return (player_input_state, opp_input_state)

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
    if isinstance(input_state, tuple):
        if input_state[1] == 'N':
            return input_state[0]
        elif input_state[0] == 'N':
            return '/%s' % input_state[1]
        else:
            return '/'.join(input_state)
    return input_state

def record_state():
    if Shared.Shared.game_reader.is_foreground_pid():
        input_state = get_input_state()
        if last_move_was(input_state):
            Recorder.history[-1][-1] += 1
        else:
            Recorder.history.append([input_state, 1])

def get_recording_string():
    count = sum([i[1] for i in Recorder.history])
    moves = [get_move(i) for i in Recorder.history]
    if moves and moves[0].startswith('N'):
        moves = moves[1:]
        count -= Recorder.history[0][1]
    if moves and moves[-1].startswith('N'):
        moves = moves[:-1]
        count -= Recorder.history[-1][1]
    if len(moves) == 0:
        return ''
    chunks = [moves[i:i+moves_per_line] for i in range(0, len(moves), moves_per_line)]
    lines = [' '.join(i) for i in chunks]
    moves_string = '\n'.join(lines)

    return '%s\n# %d\n' % (moves_string, count)

def get_record_path(file_name):
    return Path.path('./record/recording.txt' % file_name)

def get_input_as_string(state):
    direction_string = state.input_direction.name
    attack_string = state.input_button.name.replace('x', '').replace('N', '')
    if direction_string == 'N' and attack_string != '':
        return attack_string
    return '%s%s' % (direction_string, attack_string)
