import os
import time

from frame_data import DataColumns
from misc import Globals
from misc.Windows import w as Windows
from . import Record, Shared

seconds_per_frame = 1/60.
one_frame_ms = int(1000 * seconds_per_frame)
imprecise_wait_cutoff_s = 0.1
imprecise_wait_cutoff_buffer_s = 0.01

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
    moves = get_moves_from_path(Shared.RAW_PATH)
    if moves is None:
        return
    if not Windows.valid:
        print("not windows?")
        return
    print('waiting for tekken focus')
    Replayer.moves = moves
    wait_for_focus_and_replay_moves()

def get_moves_from_path(raw_path, swap=False):
    path = Shared.get_path(raw_path)
    if not os.path.isfile(path):
        print("recording not found: %s" % path)
        return None
    with open(path) as fh:
        contents = fh.read()
    all_lines = contents.split('\n')

    list_of_r_moves = []
    while all_lines and all_lines[0].startswith('@'):
        r_path = all_lines.pop(0)[1:].strip()
        if r_path.startswith('@'):
            r_path = r_path[1:]
            sub_swap = True
        else:
            sub_swap = False
        r_moves = get_moves_from_path(r_path, swap ^ sub_swap)
        if r_moves is None:
            return None
        list_of_r_moves.append(r_moves)

    lines = [line.split('#')[0].strip() for line in all_lines]
    compacted_moves = ' '.join(lines).split(' ')

    moves = loads_moves([i for i in compacted_moves if i != ''], swap)

    while list_of_r_moves:
        moves = combine(moves, list_of_r_moves.pop())

    return moves

def loads_moves(compacted_moves, swap):
    moves = []
    for compacted_move in compacted_moves:
        parts = compacted_move.split('(')
        move = parts[0]
        if swap:
            move_parts = (move + '/').split('/')
            if move_parts[0] == '':
                move = move_parts[1]
            else:
                move = '/'.join(move_parts[1::-1])
        if len(parts) == 1:
            count = 1
        else:
            count_str = parts[1].split(')')[0]
            count = int(count_str)
        if move.startswith('+'):
            r_path = move[1:]
            r_moves = get_moves_from_path(r_path, swap)
            for i in range(count):
                moves += r_moves
        else:
            moves.append((move, count))
    return moves

def combine(moves_1, moves_2):
    out = []
    moves_1 = list(moves_1)
    moves_2 = list(moves_2)
    while moves_1 and moves_2:
        m1 = moves_1.pop(0)
        m2 = moves_2.pop(0)
        m1_parts = (m1[0]+'/').split('/')
        m2_parts = (m2[0]+'/').split('/')

        out_p1 = combine_move(m1_parts[0], m2_parts[0])
        out_p2 = combine_move(m1_parts[1], m2_parts[1])

        if out_p2 == 'N':
            out_m = out_p1
        else:
            out_m = '%s/%s' % (out_p1, out_p2)
        out_c = min(m1[1], m2[1])
        out.append((out_m, out_c))

        if out_c < m1[1]:
            moves_1.insert(0, (m1[0], m1[1] - out_c))
        elif out_c < m2[1]:
            moves_2.insert(0, (m2[0], m2[1] - out_c))
    return out + moves_1 + moves_2

def combine_move(m1, m2):
    if m2 == 'N':
        return m1
    if m1 == 'N':
        return m2
    d1, a1 = move_to_strings(m1)
    d2, a2 = move_to_strings(m2)
    d = ''.join(set(d1 + d2))
    a = ''.join(set(a1 + a2))
    if d == 'N':
        return a
    return d + a

class Replayer:
    moves = None
    pressed = []

    i = None
    start = None
    count = None
    log = []

def wait_for_focus_and_replay_moves():
    if Replayer.i is not None:
        return
    Globals.Globals.master.overlay.print_f(True, {
        DataColumns.DataColumns.cmd: 'REPLAY'
    })
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

def handle_next_move():
    diff = get_diff()
    if diff > imprecise_wait_cutoff_s + imprecise_wait_cutoff_buffer_s:
        # get a bit closer because precise_wait is more expensive
        wait_s = diff - imprecise_wait_cutoff_s
        wait_ms = int(wait_s * 1000)
        Globals.Globals.master.after(wait_ms, handle_next_move)
        return
    if diff > 0:
        Windows.sleep(diff)
    else:
        Replayer.start -= diff
    replay_next_move()

def replay_next_move():
    if Replayer.i == len(Replayer.moves):
        Globals.Globals.master.after(one_frame_ms, finish)
        return

    move, count = Replayer.moves[Replayer.i]
    args = [move, count, "%0.6f" % get_diff()]
    Replayer.log.append(args)
    if count > 0:
        if replay_move(move):
            return
        Replayer.count += count
    Replayer.i += 1
    handle_next_move()

def finish():
    for hex_key_code in Replayer.pressed:
        Windows.release_key(hex_key_code)
    Replayer.pressed = []
    print("done", Replayer.count)
    while Replayer.log:
        print(*Replayer.log.pop(0))
    Replayer.i = None

def get_diff():
    target = Replayer.count * seconds_per_frame
    actual = time.time() - Replayer.start
    return target - actual

def replay_move(move):
    last_state = Globals.Globals.game_log.state_log[-1]
    reverse = bool(last_state.facing_bool) ^ (not last_state.is_player_player_one)
    hex_key_codes = move_to_hexes(move, reverse)
    to_release = [i for i in Replayer.pressed if i not in hex_key_codes]
    to_press = [i for i in hex_key_codes if i not in Replayer.pressed]
    
    # quit if tekken is not foreground
    if not Globals.Globals.game_reader.is_foreground_pid():
        print('lost focus')
        finish()
        return True

    for hex_key_code in to_release:
        Windows.release_key(hex_key_code)
    for hex_key_code in to_press:
        Windows.press_key(hex_key_code)
    Replayer.pressed = hex_key_codes
    return False

def move_to_hexes(move, reverse, p1=True):
    if '/' in move:
        p1_move, p2_move = move.split('/')
        p1_codes = move_to_hexes(p1_move, reverse, True)
        p2_codes = move_to_hexes(p2_move, reverse, False)
        return p1_codes + p2_codes
    direction_string, attack_string = move_to_strings(move)
    if direction_string in ['NULL', 'N']:
        direction_hexes = []
    else:
        if reverse ^ (not p1):
            direction_string = direction_string.replace('b', 'F').replace('f', 'B').replace('F', 'f').replace('B', 'b')
        direction_hexes = [direction_string_to_hexes[p1][d] for d in direction_string]
    attack_hexes = [attack_string_to_hex[p1][a] for a in attack_string]
    hex_key_codes = direction_hexes + attack_hexes
    return hex_key_codes

def move_to_strings(move):
    move.replace('_', '')
    direction_string = ''.join([i for i in move if i not in '1234'])
    attack_string = move[len(direction_string):]
    return direction_string, attack_string
