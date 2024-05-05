import sys

sys.path.append('src')

import collections
import time

from game_parser import GameReader
from gui import t_tkinter, TekkenBotPrime
from misc import Windows

def main():
    if not Windows.w.valid:
        raise Exception("need to be on windows")
    Vars.game_reader = GameReader.GameReader()
    Vars.game_reader.reacquire_module()
    print("\n")
    tk = t_tkinter.Tk()
    TekkenBotPrime.init_tk(tk)
    tk.geometry('1600x420+0+0')
    print("collecting memory data - this usually takes around 5 minutes")
    Vars.start = time.time()
    Vars.memory = read_all_memory()
    log([
        "finished read_all_memory",
        f"{len(Vars.memory)} pages",
        f"{sum([len(v) for v in Vars.memory.values()])/1024**3:0.2f} gb",
    ])
    Vars.move_id_addresses = get_move_id_addresses()
    log([
        "finished get_move_id_addresses",
        f"{[len(i) for i in Vars.move_id_addresses]}",
    ])
    # Vars.pointers_map = get_pointers_map()
    # log([
    #     "finished get_pointers_map",
    #     f"{len(Vars.pointers_map)}",
    # ])
    found = {}
    for path, f in to_update:
        print(path)
        found[path] = f(found)
    print(found)

def expected_module_address(found):
    return hex(Vars.game_reader.module_address)

def rollback_frame_offset(found):
    addresses = Vars.move_id_addresses[True]
    distances = [addresses[i+1] - addresses[i] for i in range(len(addresses))]
    return hex(get_most_common(distances))

def p2_data_offset(found):
    offsets = [min([
        p2_address for p2_address in Vars.move_id_addresses[False] if p2_address > p1_address
    ])-p1_address for p1_address in Vars.move_id_addresses[True]]
    return hex(get_most_common(offsets))

def player_data_pointer_offset(found):
    raise Exception("player_data_pointer_offset")
    found_rollback_frame_offset = int(found[("MemoryAddressOffsets", "rollback_frame_offset")], 16)
    addresses = Vars.move_id_addresses[True]
    move_id_address = min([v for v in addresses if v + found_rollback_frame_offset in addresses])

    candidates = [move_id_address]
    # assume that PlayerDataAddress.move_id offset and
    # MemoryAddressOffsets.player_data_pointer_offset[1:] dont change
    # TODO see if we can avoid using known offsets
    previous_offset = Vars.game_reader.c['MemoryAddressOffsets']['player_data_pointer_offset']
    known_offsets = previous_offset[1:]
    move_id_offset = Vars.game_reader.c["PlayerDataAddress"]["move_id"]
    for offset in reversed(known_offsets+[move_id_offset]):
        next_candidates = []
        for c in candidates:
            for source in Vars.pointers_map.get(hex(c-offset), []):
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
    address = 0
    for _ in range(1_000_000):
        info = get_memory_basic_information(Vars.game_reader.process_handle, address)
        if info["region_size"] == 0:
            return memory
        if info["scannable"]:
            block = Vars.game_reader.get_block_of_data(address, info["region_size"])
            memory[address] = block
        address += info["region_size"]
    raise Exception("read_all_memory")

def get_pointers_map():
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
    found = 0
    for i, prefix in enumerate(prefixes):
        for base_address, index in find_bytes(prefix):
            raw_destination = Vars.memory[base_address][index-8+len(prefix):index+len(prefix)]
            if len(raw_destination) < 8:
                continue
            destination = int.from_bytes(raw_destination[::-1])
            source = base_address+index+len(prefix)-8
            pointers_map[hex(destination)].append(source)
            found += 1
        log(["get_pointers_map", f"{i+1} of {len(prefixes)}", f"{found} found"])
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
    crouching_bytes_map = {
        False: 32769,
        True: 32770,
    }
    found = find_bytes(crouching_bytes_map[False].to_bytes(4))
    possibilities = [base_address+index for base_address,index in found]
    move_id_addresses = {}
    for is_p1 in [True, False]:
        Windows.w.press_key(crouching_input_map[is_p1])
        p_possibilities = wait_for_range(possibilities, crouching_bytes_map[True], 50, 200)
        Windows.w.release_key(crouching_input_map[is_p1])
        p_possibilities = wait_for_range(p_possibilities, crouching_bytes_map[False], 50, 200)
        move_id_addresses[is_p1] = p_possibilities
    return move_id_addresses

def wait_for_range(possibilities, expected, floor, ceiling):
    for _ in range(10_000):
        p_possibilities = [p for p in possibilities if Vars.game_reader.get_int_from_address(p, 4) == expected]
        if len(p_possibilities) < 200:
            return p_possibilities
        Windows.w.sleep(0.1)
    raise Exception(f"wait_for_range {len(p_possibilities)}")

def get_most_common(arr):
    counts = collections.defaultdict(int)
    for d in arr:
        counts[d] += 1
    m = list(sorted([(v,k) for k,v in counts.items()]))[-1]
    print("get_most_common", counts)
    return m

class Vars:
    game_reader = None
    start = None
    memory = None
    move_id_addresses = None
    pointers_map = None

if __name__ == "__main__":
    main()
