import sys

sys.path.append('src')

import collections
import time

from game_parser import GameReader

def main():
    Vars.game_reader = GameReader.GameReader()
    Vars.game_reader.reacquire_module()
    print("\nreading memory and generating pointers_map - this usually takes around 5 minutes")
    Vars.start = time.time()
    Vars.memory = read_all_memory()
    log([
        "finished reading memory",
        f"{len(Vars.memory)} pages",
        f"{sum([len(v) for v in Vars.memory.values()])/1024**3:0.2f} gb",
    ])
    Vars.pointers_map = get_pointers_map()
    log([
        "finished generating pointers_map",
        f"{len(Vars.pointers_map)}",
    ])

    found = {}
    for path, f in to_update:
        print(path)
        found[path] = f()
    print(found)

def player_data_pointer_offset():
    # TODO find move_id_address
    move_id_address = 0x1969F740528 # - 518 <- 0x194AA138DD8
    candidates = [move_id_address]
    # assume that PlayerDataAddress.move_id offset and
    # MemoryAddressOffsets.player_data_pointer_offset[1:] dont change
    previous_offset = Vars.game_reader.c['MemoryAddressOffsets']['player_data_pointer_offset']
    known_offsets = GameReader.split_str_to_hex(previous_offset)[1:]
    move_id_offset = Vars.game_reader.c["PlayerDataAddress"]["move_id"]
    for offset in reversed(known_offsets+[move_id_offset]):
        candidates = [source for c in candidates for source in Vars.pointers_map.get(hex(c-offset), [])]
    candidates = [c for c in [cc - Vars.game_reader.module_address for cc in candidates] if c > 0]
    if len(candidates) != 1:
        raise Exception(f"player_data_pointer_offset {len(candidates)}")
    return " ".join([hex(i) for i in candidates+known_offsets])

to_update = [
    (("MemoryAddressOffsets", "player_data_pointer_offset"), player_data_pointer_offset),
]

###

def log(arr):
    print(" / ".join([f"{(time.time()-Vars.start):0.2f} seconds"] + arr))

def read_all_memory():
    GameReader.Windows.k32.VirtualQueryEx.argtypes = [
        GameReader.Windows.wintypes.HANDLE,
        GameReader.Windows.wintypes.LPCVOID,
        GameReader.Windows.wintypes.LPVOID,
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
            memory[address] = block.raw
        address += info["region_size"]
    raise Exception("read_all_memory")

def get_pointers_map():
    prefixes = {}
    guaranteed_prefix = 3
    for address, block_raw in Vars.memory.items():
        # arbitrary cutoff
        if address < 0x10000000000:
            continue
        address_bytes, address_end_bytes = [a.to_bytes(8) for a in [address, address + len(block_raw)]]
        if address_bytes[:guaranteed_prefix] != address_end_bytes[:guaranteed_prefix]:
            raise Exception(f"get_pointers_map {list(address_bytes)} : {list(address_end_bytes)}")
        for i in range(address_bytes[guaranteed_prefix], address_end_bytes[guaranteed_prefix]+1):
            prefix = address_bytes[:guaranteed_prefix]+i.to_bytes(1)
            prefixes[prefix] = [address_bytes, address_end_bytes]
    pointers_map = collections.defaultdict(list)
    found = 0
    for i, prefix in enumerate(prefixes):
        for base_address, index in find_bytes(prefix):
            source = base_address+index+len(prefix)-8
            raw_destination = Vars.memory[base_address][index-8+len(prefix):index+len(prefix)]
            if len(raw_destination) < 8:
                continue
            destination = int.from_bytes(bytes(reversed(raw_destination)))
            pointers_map[hex(destination)].append(source)
            found += 1
        log(["get_pointers_map", f"{i+1} of {len(prefixes)}", f"{found} found"])
    return pointers_map

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
    GameReader.Windows.k32.VirtualQueryEx(process_handle, address, GameReader.ctypes.byref(mbi), GameReader.ctypes.sizeof(mbi))

    return {
        "scannable": mbi.Protect == 0x04 and mbi.State == 0x00001000,
        "region_size": mbi.RegionSize,
    }

def find_bytes(byte_array):
    needle = bytes(reversed([i for i in byte_array]))
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

class Vars:
    pass

if __name__ == "__main__":
    main()
