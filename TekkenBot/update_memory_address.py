import sys

sys.path.append('src')

import collections
import re
import time

from game_parser import GameReader

def main():
    Vars.game_reader = GameReader.GameReader()
    Vars.game_reader.reacquire_module()
    start = time.time()
    Vars.memory = read_all_memory()
    print(" / ".join([
        "finished reading memory",
        f"{len(Vars.memory)} pages",
        f"{sum([len(v) for v in Vars.memory.values()])/1024**3:0.2f} gb",
        f"{(time.time()-start):0.2f} seconds",
    ]))
    Vars.pointers_map = get_pointers_map()
    print(" / ".join([
        "finished generating pointers_map",
        f"{len(Vars.pointers_map)}",
        f"{(time.time()-start):0.2f} seconds",
    ]))
    exit()

    found = {}
    for path, f in to_update:
        print(path)
        found[path] = f()
    print(found)

def player_data_pointer_offset():
    # how do we know that the suffix remains the same?
    previous_offset = Vars.game_reader.c['MemoryAddressOffsets']['player_data_pointer_offset']
    known_suffix = GameReader.split_str_to_hex(previous_offset)[4:]
    move_id_suffix = known_suffix+[Vars.game_reader.c["PlayerDataAddress"]["move_id"]]
    # find move_id_address
    move_id_address = 0x195246A05C8 # TODO
    candidates = [move_id_address]
    for offset in reversed(move_id_suffix):
        candidates = [parent for parent in pointers_map.get(c-offset, []) for c in candidates]
    print([hex(c) for c in candidates], known_suffix)
    source = candidates[-1]
    return " ".join([f'{i:x}' for i in [source]+known_suffix])

to_update = [
    (("MemoryAddressOffsets", "player_data_pointer_offset"), player_data_pointer_offset),
]

###

def find_bytes(byte_array):
    print(byte_array)
    needle = bytes(reversed([i for i in byte_array]))
    return [address + index for address,haystack in Vars.memory.items() for index in get_indices(needle, haystack)]

def get_indices(needle, haystack):
    index = 0
    for _ in range(1000):
        index = haystack.find(needle, index)
        if index == -1:
            return
        yield index
        index += len(needle)
    raise Exception("get_indices")

def get_memory_basic_information(process_handle, address):
    class MemoryBasicInformation(GameReader.ctypes.Structure):
        """https://msdn.microsoft.com/en-us/library/aa366775"""
        _fields_ = (
            ('BaseAddress', GameReader.Windows.wintypes.LPVOID),
            ('AllocationBase',    GameReader.Windows.wintypes.LPVOID),
            ('AllocationProtect', GameReader.ctypes.c_size_t),
            ('RegionSize', GameReader.ctypes.c_size_t),
            ('State',   GameReader.Windows.wintypes.DWORD),
            ('Protect', GameReader.Windows.wintypes.DWORD),
            ('Type',    GameReader.Windows.wintypes.DWORD),
        )
    mbi = MemoryBasicInformation()
    GameReader.Windows.k32.VirtualQueryEx(process_handle, address, ctypes.byref(mbi),ctypes.sizeof(mbi))

    return {
        "scannable": mbi.Protect == 0x04 and mbi.State == 0x00001000,
        "region_size": mbi.RegionSize,
    }

def read_all_memory():
    GameReader.Windows.k32.VirtualQueryEx.argtypes = [
        GameReader.Windows.wintypes.HANDLE,
        GameReader.Windows.wintypes.LPCVOID,
        GameReader.Windows.wintypes.LPVOID,
        GameReader.ctypes.c_size_t,
    ]
    memory = {}
    address = 0
    for _ in range(100000):
        info = get_memory_basic_information(Vars.game_reader.process_handle, address)
        if info["region_size"] == 0:
            return memory
        if info["scannable"]:
            block = Vars.game_reader.get_block_of_data(address, info["region_size"])
            memory[address] = block.raw
        address += info["region_size"]
    raise Exception("read_all_memory")

def get_pointers_map():
    prefixes = set()
    for address, block_raw in Vars.memory.items():
        address_bytes, address_end_bytes = [a.to_bytes(8) for a in [address, address + len(block_raw)]]
        same_index = len(address_bytes)
        for i in range(same_index):
            if address_bytes[i] != address_end_bytes[i]:
                same_index = i
                break
        prefixes.add(address_bytes[:same_index])
    print("get_pointers_map", len(prefixes))
    exit()
    pointers_map = collections.defaultdict(list)
    for prefix in prefixes:
        for address in find_bytes(prefix):
            destination = Vars.game_reader.get_value_from_address(address, GameReader.AddressType._64bit)
            pointers_map[destination] = address
    print("get_pointers_map", len(pointers_map))
    exit()
    return pointers_map

class Vars:
    pass

if __name__ == "__main__":
    main()
