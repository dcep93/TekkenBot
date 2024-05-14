from ..frame_data import Entry
from ..game_parser import GameSnapshot, ScriptedGame
from ..gui import TekkenBotPrime
from ..misc import Path

import enum
import typing

def record_single() -> None:
    record_start(RecordingState.SINGLE)

def record_both() -> None:
    record_start(RecordingState.BOTH)

def record_start(state: RecordingState) -> None:
    print("starting recording %s" % state.name)
    TekkenBotPrime.TekkenBotPrime.t.overlay.print_f({
        Entry.DataColumns.move_id: 'RECORD',
        Entry.DataColumns.char_name: state.name
    })
    Recorder.state = state
    Recorder.history = []
    reader = TekkenBotPrime.TekkenBotPrime.t.game_reader
    if isinstance(reader, ScriptedGame.Recorder):
        reader.reset(True)

def record_end() -> None:
    print("ending recording")
    Recorder.state = RecordingState.OFF
    TekkenBotPrime.TekkenBotPrime.t.overlay.print_f({
        Entry.DataColumns.move_id: 'RECORD',
        Entry.DataColumns.char_name: Recorder.state.name
    })

    recording_string = get_recording_string()
    print(recording_string)
    Recorder.history = []
    path = get_record_path(None)
    with open(path, 'w') as fh:
        fh.write(recording_string)

    reader = TekkenBotPrime.TekkenBotPrime.t.game_reader
    if isinstance(reader, ScriptedGame.Recorder):
        reader.dump()

def record_if_activated() -> None:
    if Recorder.state != RecordingState.OFF:
        record_state()

moves_per_line = 10

@enum.unique
class RecordingState(enum.Enum):
    OFF = 0
    SINGLE = 1
    BOTH = 2

InputState = typing.Tuple[str, str]

class Recorder:
    state = RecordingState.OFF
    history: typing.List[typing.List[InputState, int]] = [] # type: ignore

def get_input_state() -> InputState:
    last_state = TekkenBotPrime.TekkenBotPrime.t.game_log.state_log[-1]
    player = last_state.p1
    opp = last_state.p2
    return (
        get_input_as_string(player),
        "" if Recorder.state == RecordingState.SINGLE else get_input_as_string(opp),
    )

def last_move_was(input_state: InputState) -> bool:
    if len(Recorder.history) == 0:
        return False
    return Recorder.history[-1][0] == input_state # type: ignore

def get_move(input_state: InputState, count: int) -> str:
    raw_move = get_raw_move(input_state)
    if count == 1:
        return raw_move
    else:
        return '%s(%d)' % (raw_move, count)

def get_raw_move(input_state: InputState) -> str:
    if isinstance(input_state, tuple):
        if input_state[1] == 'N':
            return input_state[0]
        elif input_state[0] == 'N':
            return '/%s' % input_state[1]
        else:
            return '/'.join(input_state)
    return input_state

def record_state() -> None:
    if TekkenBotPrime.TekkenBotPrime.t.game_reader.is_foreground_pid():
        input_state = get_input_state()
        if last_move_was(input_state):
            Recorder.history[-1][-1] += 1
        else:
            Recorder.history.append([input_state, 1])

def get_recording_string() -> str:
    count = sum([i[1] for i in Recorder.history])
    moves = [get_move(*i) for i in Recorder.history]
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

def get_record_path(file_name: typing.Optional[str]) -> str:
    if file_name is None:
        file_name = "recording.txt"
    return Path.path('./record/%s' % file_name)

def get_input_as_string(state: GameSnapshot.PlayerSnapshot) -> str:
    direction_string = state.input_direction.name
    attack_string = state.input_button.name.replace('x', '').replace('N', '')
    if direction_string == 'N' and attack_string != '':
        return attack_string
    return '%s%s' % (direction_string, attack_string)
