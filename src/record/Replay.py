import os
import time

from frame_data import DataColumns
from misc import Globals
from misc.Windows import w as Windows
from . import Record, Shared

seconds_per_frame = 1/60.
one_frame_ms = int(1000 * seconds_per_frame)

def replay():
    path = Shared.get_path()
    if not os.path.isfile(path):
        print("recording not found")
        return
    with open(path) as fh:
        contents = fh.read()
    lines = [line.split('#')[0].strip() for line in contents.split('\n')]
    compacted_moves = ' '.join(lines).split(' ')

    moves = Record.loads_moves([i for i in compacted_moves if i != ''])
    if not Windows.valid:
        print("not windows?")
        return
    print('waiting for tekken focus')
    Replayer.moves = moves
    Replayer.reverse = False
    wait_for_focus_and_replay_moves()


class Replayer:
    moves = None
    reverse = None
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

def move_is_side_switch():
    move = Replayer.moves[Replayer.i]
    return move == Record.SIDE_SWITCH

def replay_next_move():
    if Replayer.i == len(Replayer.moves):
        Globals.Globals.master.after(one_frame_ms, finish)
        return

    if move_is_side_switch():
        Replayer.reverse = not Replayer.reverse
        Replayer.i += 1
        handle_next_move()
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
    hex_key_codes = Record.move_to_hexes(move, Replayer.reverse)
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
