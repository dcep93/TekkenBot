import os

from misc import Globals
from misc.Windows import w as Windows
from . import Record

def replay():
    path = Shared.get_path()
    if not os.path.isfile(path):
        print("recording not found")
        return
    with open(path) as fh:
        contents = fh.read()
    raw_string = contents.replace('\n', ' ')
    compacted_moves = raw_string.split(' ')
    moves = Record.loads_moves(compacted_moves)
    if not Windows.valid:
        print("not windows?")
        return
    print('waiting for tekken focus')
    Replayer.moves = moves
    wait_for_focus_and_replay_moves()


class Replayer:
    moves = None
    pressed = []
    reverse = False

    i = None
    start = None

def wait_for_focus_and_replay_moves():
    if Globals.is_foreground_pid():
        replay_moves()
    else:
        Globals.master.after(100, wait_for_focus_and_replay_moves)

def replay_moves():
    print("replaying")
    Replayer.start = time.time()
    Replayer.i = 0
    handle_next_move()

def handle_next_move():
    if Replayer.i == len(Replayer.moves):
        one_frame_ms = int(1000 * seconds_per_frame)
        Globals.master.after(one_frame_ms, finish)
        return

    if move_is_side_switch():
        Replayer.reverse = not Replayer.reverse
        Replayer.i += 1
        handle_next_move()
        return
    
    target = Replayer.i * seconds_per_frame
    actual = time.time() - Replayer.start
    diff = target - actual
    if diff > 0:
        diff_ms = int(diff * 1000)
        Globals.master.after(diff_ms, replay_next_move)
    else:
        replay_next_move()

def move_is_side_switch():
    move = Replayer.moves[Replayer.i]
    return move == SIDE_SWITCH

def replay_next_move():
    # quit if tekken is not foreground
    if not Globals.is_foreground_pid():
        print('lost focus')
        finish()
        return
    move = Replayer.moves[Replayer.i]
    replay_move(move)
    Replayer.i += 1
    handle_next_move()

def finish():
    for hex_key_code in Replayer.pressed:
        Windows.release_key(hex_key_code)
    Replayer.pressed = []
    print("done")

def replay_move(move):
    hex_key_codes = Record.move_to_hexes(move, Replayer.reverse)
    to_release = [i for i in Replayer.pressed if i not in hex_key_codes]
    to_press = [i for i in hex_key_codes if i not in Replayer.pressed]
    for hex_key_code in to_release:
        Windows.release_key(hex_key_code)
    for hex_key_code in to_press:
        Windows.press_key(hex_key_code)
    Replayer.pressed = hex_key_codes
