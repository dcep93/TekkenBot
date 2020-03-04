import os
import time

from . import Path
from game_parser.MoveInfoEnums import InputDirectionCodes, InputAttackCodes

seconds_per_frame = 1/60.

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

def replay(game_reader):
    path = Path.path('./record/recording.txt')
    if not os.path.isfile(path):
        print("recording not found")
        return
    with open(path) as fh:
        contents = fh.read()
    raw_string = contents.replace('\n', ' ')
    compacted_moves = raw_string.split(' ')
    moves = Recording.loads_moves(compacted_moves)
    print('waiting for tekken focus')
    while True:
        if game_reader.is_foreground_pid():
            break
        time.sleep(1)
    print("replaying")
    start = time.time()
    for i, move in enumerate(moves):
        # quit if tekken is not foreground
        if not game_reader.is_foreground_pid():
            return
        target = i * seconds_per_frame
        actual = time.time() - start
        diff = target - actual
        if diff > 0:
            time.sleep(diff)

        Recording.replay_move(move)
