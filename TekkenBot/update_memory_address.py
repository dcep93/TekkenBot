import sys

sys.path.append('src')

import collections
import time
import threading

from game_parser import GameReader, MoveInfoEnums
from gui import t_tkinter, TekkenBotPrime
from misc import Path, Windows

DEBUG_FAST = True

# config not handled:
# PlayerDataAddress.move_id
# GameDataAddress.facing

# TODO PlayerDataAddress
# recovery
# hit_outcome
# simple_move_state
# stun_type
# throw_tech
# complex_move_state
# damage_taken
# input_attack
# input_direction
# attack_startup
# char_id
# move_timer
# throw_flag
# attack_damage

def main():
    if not Windows.w.valid:
        raise Exception("need to be on windows")
    Vars.game_reader = GameReader.GameReader()
    Vars.game_reader.reacquire_module()
    if not Vars.game_reader.process_handle:
        raise Exception("need to be running tekken")
    Vars.game_reader.in_match = True
    # assume that PlayerDataAddress.move_id offset doesnt change
    Vars.move_id_offset = Vars.game_reader.c["PlayerDataAddress"]["move_id"]
    print("")
    Vars.tk = t_tkinter.Tk()
    TekkenBotPrime.init_tk(Vars.tk)
    Vars.tk.attributes("-topmost", True)
    Vars.tk.overrideredirect(True)
    Vars.start = time.time()
    log([
        "phase 1 of 3",
        "collecting initial memory data",
        "wait in practice mode and do not make any inputs",
        "this usually takes around 1 minute",
    ])
    Vars.memory = read_all_memory()
    log([
        "finished read_all_memory",
        f"{len(Vars.memory)} pages",
        f"{sum([len(v) for v in Vars.memory.values()])/1024**3:0.2f} gb",
    ])
    log([
        "phase 2 of 3",
        "collecting input data",
        "wait for instructions",
        "this usually takes around 2 minutes",
    ])
    Vars.move_id_addresses = get_move_id_addresses()
    log([
        "finished get_move_id_addresses",
        f"{[len(i) for i in Vars.move_id_addresses.values()]}",
    ])
    found = {}
    for path, f in to_update:
        print(path)
        if f == player_data_pointer_offset:
            log([
                "phase 3 of 3",
                "building pointers_map",
                "feel free to make inputs",
                "this usually takes around 5 minutes",
            ])
            Vars.pointers_map = get_pointers_map()
            log([
                "finished get_pointers_map",
                f"{len(Vars.pointers_map)}",
            ])
        found[path] = f()
    config_obj = Vars.game_reader._c
    for path, value in found.items():
        config_obj[path[0]][path[1]] = value
    with open(Path.path('config/memory_address.ini'), 'w') as fh:
        config_obj.write(fh)

def expected_module_address():
    return hex(Vars.game_reader.module_address)

def get_p1_move_id_address():
    addresses = Vars.move_id_addresses[True]
    needed_copies = 4
    def helper(i):
        distance = addresses[i]-addresses[i-1]
        for j in range(1, needed_copies):
            if addresses[i+j] - addresses[i+j-1] != distance:
                return None
        return distance
    distance = None
    for i in range(1, len(addresses)-needed_copies):
        distance = helper(i)
        if distance is not None:
            for address in addresses:
                if address + distance in addresses:
                    return address, distance
            break
    raise Exception(f"get_p1_move_id_address {distance}")

def rollback_frame_offset():
    _, distance = get_p1_move_id_address()
    return hex(distance)

def p2_data_offset():
    counts = collections.defaultdict(int)
    for p1_address in Vars.move_id_addresses[True]:
        for p2_address in Vars.move_id_addresses[False]:
            if p2_address > p1_address:
                counts[p2_address-p1_address] += 1
                break
    return hex(sorted([(v, k) for k,v in counts.items()])[-1][1])

def frame_count():
    move_id_address, distance = get_p1_move_id_address()
    player_data_base_address = move_id_address - Vars.move_id_offset
    block = Vars.game_reader.get_block_of_data(player_data_base_address, 16 * distance)
    for offset in range(0x1000, 0x10000):
        counts = [Vars.game_reader.get_4_bytes_from_data_block(block, (distance * i) + offset) for i in range(8)]
        distances = [counts[i+1] - counts[i] for i in range(len(counts)-1)]
        if all([i == 1 or i == -31 for i in distances]):
            return hex(offset)
    raise Exception(f"frame_count - (maybe try restarting the practice mode)")

def damage_taken():
    return hex(player_data_helper([
        ("waiting for 5 damage_taken", lambda e: e == MoveInfoEnums.InputAttackCodes.x1x2x3x4.value),
        ("waiting for  input", lambda e: e == MoveInfoEnums.InputAttackCodes.x3x4.value),
    ]))

def player_data_helper(instructions):
    move_id_address, distance = get_p1_move_id_address()
    player_data_base_address = move_id_address - Vars.move_id_offset
    possibilities = [player_data_base_address+i for i in range(distance)]
    for msg, f in instructions:
        print(msg)
        possibilities = wait_for_range(possibilities, f, 1, 100)
        if len(possibilities) == 0:
            break
    if len(possibilities) != 1:
        raise Exception(f"player_data_helper {len(possibilities)}")
    return possibilities[0]

def player_data_pointer_offset():
    move_id_address, _ = get_p1_move_id_address()

    candidates = {source: [] for source in Vars.pointers_map.get(hex(move_id_address-Vars.move_id_offset), [])}

    if len(candidates) == 0:
        raise Exception(f"player_data_pointer_offset {hex(move_id_address)}")

    for _ in range(10):
        next_candidates = {}
        for address, prev in candidates.items():
            for offset in range(0x100):
                sources = Vars.pointers_map.get(hex(address-offset), [])
                for source in sources:
                    diff = source - Vars.game_reader.module_address
                    if diff > 0:
                        return " ".join([hex(i) for i in [diff, offset]+prev])
                    next_candidates[source] = [offset] + prev
        candidates = next_candidates
    raise Exception(f"player_data_pointer_offset {len(candidates)}")

def opponent_side():
    bytes_to_find_str = "01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 00 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40"
    bytes_to_find = list(map(lambda x: int(x, 16), bytes_to_find_str.split()))
    found_bytes = list(find_bytes(bytes_to_find[::-1]))
    if len(found_bytes) != 1:
        raise Exception(f"opponent_side {len(found_bytes)}")
    destination = found_bytes[0]
    address = destination[0] + destination[1]
    for offset in range(0x10):
        for source in Vars.pointers_map.get(hex(address-offset), []):
            diff = source - Vars.game_reader.module_address
            if diff > 0:
                return " ".join([hex(i) for i in [diff, offset]])
    raise Exception(f"opponent_side {hex(address)}")

to_update = [
    (("MemoryAddressOffsets", "expected_module_address"), expected_module_address),
    (("MemoryAddressOffsets", "rollback_frame_offset"), rollback_frame_offset),
    (("MemoryAddressOffsets", "p2_data_offset"), p2_data_offset),
    (("GameDataAddress", "frame_count"), frame_count),
    (("GameDataAddress", "damage_taken"), damage_taken),
    (("GameDataAddress", "attack_type"), attack_type),
    (("MemoryAddressOffsets", "player_data_pointer_offset"), player_data_pointer_offset),
    (("NonPlayerDataAddresses", "opponent_side"), opponent_side),
]

###

def log(arr):
    print(" / ".join([f"{(time.time()-Vars.start):0.2f} seconds"] + arr))

def read_all_memory():
    Windows.w.k32.VirtualQueryEx.argtypes = [
        Windows.w.wintypes.HANDLE,
        Windows.w.wintypes.LPCVOID,
        Windows.w.wintypes.LPVOID,
        GameReader.ctypes.c_size_t,
    ]
    memory = {}
    if DEBUG_FAST:
        return memory
    address = 0
    for _ in range(1_000_000):
        info = get_memory_basic_information(Vars.game_reader.process_handle, address)
        if info["region_size"] == 0:
            return memory
        if info["scannable"]:
            update_tk()
            block = Vars.game_reader.get_block_of_data(address, info["region_size"])
            memory[address] = block
        address += info["region_size"]
    raise Exception("read_all_memory")

def get_pointers_map():
    import json
    if DEBUG_FAST:
        with open("pointers_map.json") as fh:
            return json.load(fh)
    prefixes = {}
    guaranteed_prefix = 3
    for address, block_raw in Vars.memory.items():
        address_bytes, address_end_bytes = [a.to_bytes(8) for a in [address, address + len(block_raw)]]
        if int.from_bytes(address_end_bytes[:guaranteed_prefix]) == 0:
            continue
        if address_bytes[:guaranteed_prefix] != address_end_bytes[:guaranteed_prefix]:
            raise Exception(f"get_pointers_map {list(address_bytes)} : {list(address_end_bytes)}")
        for i in range(address_bytes[guaranteed_prefix], address_end_bytes[guaranteed_prefix]+1):
            prefix = address_bytes[:guaranteed_prefix]+i.to_bytes(1)
            prefixes[prefix] = [address_bytes, address_end_bytes]
    pointers_map = collections.defaultdict(list)
    num_pointers_found = 0
    for i, prefix in enumerate(prefixes):
        for base_address, index in find_bytes(prefix):
            raw_destination = Vars.memory[base_address][index-8+len(prefix):index+len(prefix)]
            if len(raw_destination) < 8:
                continue
            destination = int.from_bytes(raw_destination[::-1])
            source = base_address+index+len(prefix)-8
            pointers_map[hex(destination)].append(source)
            num_pointers_found += 1
        log(["get_pointers_map", f"{i+1} of {len(prefixes)}", f"{num_pointers_found} found"])
    with open("pointers_map.json", "w") as fh:
        json.dump(pointers_map, fh)
    return pointers_map

def get_memory_basic_information(process_handle, address):
    class MemoryBasicInformation(GameReader.ctypes.Structure):
        """https://msdn.microsoft.com/en-us/library/aa366775"""
        _fields_ = (
            ('BaseAddress', Windows.w.wintypes.LPVOID),
            ('AllocationBase',    Windows.w.wintypes.LPVOID),
            ('AllocationProtect', GameReader.ctypes.c_size_t),
            ('RegionSize', GameReader.ctypes.c_size_t),
            ('State',   Windows.w.wintypes.DWORD),
            ('Protect', Windows.w.wintypes.DWORD),
            ('Type',    Windows.w.wintypes.DWORD),
        )
    mbi = MemoryBasicInformation()
    GameReader.Windows.w.k32.VirtualQueryEx(process_handle, address, GameReader.ctypes.byref(mbi), GameReader.ctypes.sizeof(mbi))

    return {
        "scannable": mbi.Protect == 0x04 and mbi.State == 0x00001000,
        "region_size": mbi.RegionSize,
    }

def find_bytes(byte_array):
    needle = bytes(byte_array[::-1])
    for base_address, haystack in Vars.memory.items():
        update_tk()
        for index in get_indices(needle, haystack):
            yield base_address, index

def get_indices(needle, haystack):
    index = 0
    for _ in range(1_000_000):
        index = haystack.find(needle, index)
        if index == -1:
            return
        yield index
        index += 1
    raise Exception(f"get_indices {index} / {len(haystack)}")

def get_move_id_addresses():
    import json
    if DEBUG_FAST:
        with open("move_id_addresses.json") as fh:
            return {k == "true":v for k, v in json.load(fh).items()}
    crouching_bytes_map = {
        False: 32769,
        True: 32770,
    }
    found_bytes = find_bytes(crouching_bytes_map[False].to_bytes(4))
    possibilities = [base_address+index for base_address,index in found_bytes]
    move_id_addresses = {}
    for is_p1 in [True, False]:
        print(f"waiting for {'p1' if is_p1 else 'p2'} crouch")
        p_possibilities = wait_for_range(possibilities, lambda e: e == crouching_bytes_map[True], 50, 200)
        print(f"waiting for {'p1' if is_p1 else 'p2'} stand")
        p_possibilities = wait_for_range(p_possibilities, lambda e: e == crouching_bytes_map[False], 50, 200)
        move_id_addresses[is_p1] = p_possibilities
    with open("move_id_addresses.json", "w") as fh:
        json.dump(move_id_addresses, fh)
    return move_id_addresses

def read_4_bytes(address):
    try:
        return Vars.game_reader.get_int_from_address(address, 4)
    except GameReader.ReadProcessMemoryException:
        return None

def wait_for_range(a_possibilities, f, floor, ceiling):
    b_possibilities = [p for p in a_possibilities if not f(read_4_bytes(p))]
    for _ in range(10_000):
        update_tk()
        c_possibilities = [p for p in b_possibilities if f(read_4_bytes(p))]
        print(len(a_possibilities), len(b_possibilities), len(c_possibilities))
        if len(c_possibilities) >= floor and len(c_possibilities) <= ceiling:
            return c_possibilities
        Windows.w.sleep(0.1)
    raise Exception(f"wait_for_range {len(b_possibilities)}")

def update_tk():
    tekken_rect = Vars.game_reader.get_window_rect()
    if tekken_rect is not None:
        height = 200
        geometry = f'{tekken_rect.right}x{height}+0-0'
        Vars.tk.geometry(geometry)
        Vars.tk.deiconify()
    else:
        Vars.tk.withdraw()
    Vars.tk.update()

class Vars:
    game_reader = None
    start = None
    memory = None
    move_id_addresses = None
    pointers_map = None
    tk = None
    move_id_offset = None

if __name__ == "__main__":
    main()
