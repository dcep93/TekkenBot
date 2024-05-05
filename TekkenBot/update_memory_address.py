import sys

sys.path.append('src')

import collections
import time
import threading

from game_parser import GameReader
from gui import t_tkinter, TekkenBotPrime
from misc import Windows

DEBUG_FAST = True

def main():
    if not Windows.w.valid:
        raise Exception("need to be on windows")
    Vars.game_reader = GameReader.GameReader()
    Vars.game_reader.reacquire_module()
    if not Vars.game_reader.process_handle:
        raise Exception("need to be running tekken")
    Vars.game_reader.in_match = True
    print("")
    Vars.tk = t_tkinter.Tk()
    TekkenBotPrime.init_tk(Vars.tk)
    Vars.tk.attributes("-topmost", True)
    Vars.tk.overrideredirect(True)
    print("phase 1 of 3 - collecting initial memory data - this usually takes around 1 minute - wait in practice mode and do not make any inputs")
    Vars.start = time.time()
    Vars.memory = read_all_memory()
    log([
        "finished read_all_memory",
        f"{len(Vars.memory)} pages",
        f"{sum([len(v) for v in Vars.memory.values()])/1024**3:0.2f} gb",
    ])
    print("phase 2 of 3 - collecting input data - this usually takes around 2 minutes - wait for instructions")
    Vars.move_id_addresses = get_move_id_addresses()
    log([
        "finished get_move_id_addresses",
        f"{[len(i) for i in Vars.move_id_addresses.values()]}",
    ])
    found = {}
    for path, f in to_update:
        print(path)
        if f == player_data_pointer_offset:
            print("phase 3 of 3 - building pointers_map - this usually takes around 5 minutes - feel free to make inputs")
        found[path] = f()
    print(found)

def expected_module_address():
    return hex(Vars.game_reader.module_address)

def get_p1_move_id_address_index():
    addresses = Vars.move_id_addresses[True]
    needed_copies = 4
    def helper(i):
        distance = addresses[i]-addresses[i-1]
        for j in range(1, needed_copies):
            if addresses[i+j] - addresses[i+j-1] != distance:
                return False
        return True
    for i in range(1, len(addresses)-needed_copies):
        if helper(i):
            return i
    raise Exception(f"get_p1_move_id_address")

def rollback_frame_offset():
    addresses = Vars.move_id_addresses[True]
    index = get_p1_move_id_address_index()
    return hex(addresses[index+1]-addresses[index])

def p2_data_offset():
    counts = collections.defaultdict(int)
    for p1_address in Vars.move_id_addresses[True]:
        for p2_address in Vars.move_id_addresses[False]:
            if p2_address > p1_address:
                counts[p2_address-p1_address] += 1
                break
    return hex(sorted([(v, k) for k,v in counts.items()])[-1][1])

def player_data_pointer_offset():
    address_index = get_p1_move_id_address_index()
    move_id_address = Vars.move_id_addresses[True][address_index]

    candidates = [move_id_address]
    # assume that PlayerDataAddress.move_id offset and
    # MemoryAddressOffsets.player_data_pointer_offset[1:] dont change
    # TODO see if we can avoid using known offsets
    previous_offset = Vars.game_reader.c['MemoryAddressOffsets']['player_data_pointer_offset']
    known_offsets = previous_offset[1:]
    move_id_offset = Vars.game_reader.c["PlayerDataAddress"]["move_id"]
    pointers_map = get_pointers_map()
    log([
        "finished get_pointers_map",
        f"{len(pointers_map)}",
    ])
    for offset in reversed(known_offsets+[move_id_offset]):
        next_candidates = []
        for c in candidates:
            for source in pointers_map.get(hex(c-offset), []):
                next_candidates.append(source)
        candidates = next_candidates
    candidates = [c for c in [cc - Vars.game_reader.module_address for cc in candidates] if c > 0]
    if len(candidates) != 1:
        raise Exception(f"player_data_pointer_offset {len(candidates)}")
    return " ".join([hex(i) for i in candidates+known_offsets])

to_update = [
    (("MemoryAddressOffsets", "expected_module_address"), expected_module_address),
    (("MemoryAddressOffsets", "rollback_frame_offset"), rollback_frame_offset),
    (("MemoryAddressOffsets", "p2_data_offset"), p2_data_offset),
    (("MemoryAddressOffsets", "player_data_pointer_offset"), player_data_pointer_offset),
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
        p_possibilities = wait_for_range(possibilities, crouching_bytes_map[True], 50, 200)
        print(f"waiting for {'p1' if is_p1 else 'p2'} stand")
        p_possibilities = wait_for_range(p_possibilities, crouching_bytes_map[False], 50, 200)
        move_id_addresses[is_p1] = p_possibilities
    with open("move_id_addresses.json", "w") as fh:
        json.dump(move_id_addresses, fh)
    return move_id_addresses

def wait_for_range(possibilities, expected, floor, ceiling):
    def f(p):
        try:
            return Vars.game_reader.get_int_from_address(p, 4)
        except GameReader.ReadProcessMemoryException:
            return None
    for _ in range(10_000):
        update_tk()
        p_possibilities = [p for p in possibilities if f(p) == expected]
        if len(p_possibilities) >= floor and len(p_possibilities) <= ceiling:
            return p_possibilities
        Windows.w.sleep(0.1)
    raise Exception(f"wait_for_range {len(p_possibilities)}")

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
    tk = None

if __name__ == "__main__":
    main()
