import os
import time

from frame_data import DataColumns
from misc import Globals
from misc.Windows import w as Windows
from . import Record, Shared

seconds_per_frame = 1/60.
one_frame_ms = int(1000 * seconds_per_frame)

direction_string_to_hexes = {
    True: {
        'u': 0x11,
        'f': 0x20,
        'b': 0x1E,
        'd': 0x1F,
    },
    False: {
        'u': 0xC8,
        'f': 0xCD,
        'b': 0xCB,
        'd': 0xD0,
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

def replay():
    path = Shared.get_path()
    if not os.path.isfile(path):
        print("recording not found")
        return
    with open(path) as fh:
        contents = fh.read()
    lines = [line.split('#')[0].strip() for line in contents.split('\n')]
    compacted_moves = ' '.join(lines).split(' ')

    moves = loads_moves([i for i in compacted_moves if i != ''])
    if not Windows.valid:
        print("not windows?")
        return
    print('waiting for tekken focus')
    Replayer.moves = moves
    wait_for_focus_and_replay_moves()

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
        moves.append((move, count))
    return moves

class Replayer:
    moves = None
    pressed = []

    i = None
    start = None
    count = None

    listening = False

def wait_for_focus_and_replay_moves():
    if Replayer.i is not None:
        return
    if Globals.Globals.game_reader.is_foreground_pid():
        replay_moves()
    else:
        Globals.Globals.master.after(100, wait_for_focus_and_replay_moves)

def replay_moves():
    if Replayer.i is not None:
        return
    print("replaying")
    time.sleep(0.01)
    Replayer.start = time.time()
    Replayer.i = 0
    Replayer.count = 0
    handle_next_move()

    listen_for_click()

def handle_next_move():
    target = Replayer.count * seconds_per_frame
    actual = time.time() - Replayer.start
    diff = target - actual
    if diff > 0:
        diff_ms = int(diff * 1000)
        Globals.Globals.master.after(diff_ms, replay_next_move)
    else:
        Replayer.start -= diff
        replay_next_move()

def replay_next_move():
    if Replayer.i == len(Replayer.moves):
        Globals.Globals.master.after(one_frame_ms, finish)
        return

    move, count = Replayer.moves[Replayer.i]
    print_diff(move, count)
    if count > 0:
        replay_move(move)
        Replayer.count += count
    Replayer.i += 1
    handle_next_move()

def finish():
    for hex_key_code in Replayer.pressed:
        Windows.release_key(hex_key_code)
    Replayer.pressed = []
    print("done", Replayer.count)
    Replayer.i = None

def print_diff(move, count):
    target = Replayer.count * seconds_per_frame
    actual = time.time() - Replayer.start
    diff = (target - actual)*60
    print(move, count, diff)

def replay_move(move):
    last_state = Globals.Globals.tekken_state.state_log[-1]
    reverse = bool(last_state.facing_bool) ^ (not last_state.is_player_player_one)
    hex_key_codes = move_to_hexes(move, reverse)
    to_release = [i for i in Replayer.pressed if i not in hex_key_codes]
    to_press = [i for i in hex_key_codes if i not in Replayer.pressed]
    
    # quit if tekken is not foreground
    if not Globals.Globals.game_reader.is_foreground_pid():
        print('lost focus')
        finish()
        return

    for hex_key_code in to_release:
        Windows.release_key(hex_key_code)
    for hex_key_code in to_press:
        Windows.press_key(hex_key_code)
    Replayer.pressed = hex_key_codes

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

def listen_for_click():
    if Replayer.listening:
        return
    Globals.Globals.master.overlay.toplevel.bind("<Button-1>", handle_click)
    Replayer.listening = True

def handle_click(e):
    Globals.Globals.master.after(5*one_frame_ms, replay)
    Globals.Globals.master.overlay.print_f(True, {
        DataColumns.DataColumns.cmd: 'REPLAY'
    })
