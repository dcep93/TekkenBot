from ..game_parser import GameReader, MoveInfoEnums
from ..gui import t_tkinter, TekkenBotPrime
from ..misc import Path, Windows, w_windows
from ..record import Replay

import collections
import ctypes
import json
import threading
import time
import typing

DEBUG_FAST = True

# assumes PlayerDataAddress.move_id doesn't change

FoundType = typing.Union[int, typing.List[int]]
def main() -> None:
    print("this project is under heavy construction, and I don't really expect it to work until 5/16/24, but you're free to try it out anyway!")
    if not t_tkinter.valid:
        import tkinter
    if not Windows.w.valid:
        raise Exception("need to be on windows")
    game_reader = GameReader.GameReader()
    game_reader.reacquire_module()
    if not game_reader.process_handle:
        raise Exception("need to be running tekken")
    game_reader.in_match = True
    Vars.v = Vars(game_reader)
    found: typing.Dict[typing.Tuple[str, str], FoundType] = {}
    print("")
    print("you should be in practice mode as p1 Jun vs Raven")
    print("with practice options set to None on primary and Block All on secondary:")
    print("if you're not on that screen already, you'll need to restart this tool")
    print("do not make any inputs until phase 3")
    print("")
    for path, update_f in to_update:
        print(path)
        Vars.v.active = path
        val = update_f()
        found[path] = val
    config_obj = Vars.v.game_reader._c
    def hexify(raw: FoundType) -> str:
        if isinstance(raw, int):
            return f'0x{raw:x}'
        return ' '.join([hexify(r) for r in raw])
    for path, raw in found.items():
        # TODO experiment - run once, everything changes, run twice, everything goes back
        value = hexify(raw)
        print(path, value)
        config_obj[path[0]][path[1]] = value
    with open(Path.path('config/memory_address.ini'), 'w') as fh:
        config_obj.write(fh)

### phases

MemoizeT = typing.TypeVar('MemoizeT', bound=typing.Callable[..., typing.Any])
def memoize(f: MemoizeT) -> MemoizeT:
    d: typing.Dict[typing.Any, typing.Any] = {}
    def g(*args: typing.Any) -> typing.Any:
        if args in d:
            return d[args]
        v = f(*args)
        d[args] = v
        return v
    return g # type: ignore

def enter_phase(phase: int, log_before: typing.List[str], log_after_f: typing.Optional[typing.Callable[..., typing.List[str]]]=None) -> typing.Callable[..., typing.Any]:
    def f(g: MemoizeT) -> MemoizeT:
        @memoize
        def h(*args: typing.Any) -> typing.Any:
            Vars.v.phase += 1
            if Vars.v.phase != phase:
                raise Exception(f"enter_phase {phase} {Vars.v.phase}")
            log(log_before)
            v = g(*args)
            if log_after_f is not None:
                log_after = log_after_f(v)
                log(log_after)
            return v
        return h # type: ignore
    return f

@enter_phase(
    1,
    [
        "phase 1 of 3",
        "collecting initial memory data",
        "this usually takes around 1 minute",
    ],
    lambda memory: [
        "finished read_all_memory",
        f"{len(memory)} pages",
        f"{sum([len(v) for v in memory.values()])/1024**3:0.2f} gb",
    ],
)
def get_all_memory() -> typing.Dict[int, bytes]:
    Windows.w.k32.VirtualQueryEx.argtypes = [
        w_windows.wintypes.HANDLE,
        w_windows.wintypes.LPCVOID,
        w_windows.wintypes.LPVOID,
        ctypes.c_size_t,
    ]
    def get_memory_scannable_size(address: int) -> int:
        class MemoryBasicInformation(ctypes.Structure):
            """https://msdn.microsoft.com/en-us/library/aa366775"""
            _fields_ = (
                ('BaseAddress', w_windows.wintypes.LPVOID),
                ('AllocationBase',    w_windows.wintypes.LPVOID),
                ('AllocationProtect', ctypes.c_size_t),
                ('RegionSize', ctypes.c_size_t),
                ('State',   w_windows.wintypes.DWORD),
                ('Protect', w_windows.wintypes.DWORD),
                ('Type',    w_windows.wintypes.DWORD),
            )
        mbi = MemoryBasicInformation()
        Windows.w.k32.VirtualQueryEx(Vars.v.game_reader.process_handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi))

        scannable_size = mbi.RegionSize
        assert(isinstance(scannable_size, int))
        if mbi.Protect != 0x04 or mbi.State != 0x00001000:
            scannable_size = -scannable_size
        return scannable_size

    memory: typing.Dict[int, bytes] = {}
    if DEBUG_FAST:
        return memory
    address = 0
    for _ in range(1_000_000):
        scannable_size = get_memory_scannable_size(address)
        if scannable_size == 0:
            return memory
        if scannable_size > 0:
            update_tk()
            block = Vars.v.game_reader.get_block_of_data(address, scannable_size)
            memory[address] = block
        address += abs(scannable_size)
    raise Exception("get_all_memory")

@enter_phase(
    2,
    [
        "phase 2 of 3",
        "collecting input data",
        "this usually takes around 1 minute",
    ],
)
def get_point_slope() -> typing.Tuple[int, int]:
    if DEBUG_FAST:
        with open("point_slope.json") as fh:
            return json.load(fh) # type: ignore
    crouching_bytes_map = {
        False: 32769,
        True: 32770,
    }
    found_bytes = find_bytes(list(crouching_bytes_map[False].to_bytes(4, 'little')))
    move_id_addresses = [base_address+index for base_address,index in found_bytes]

    def read_4_bytes(address: int) -> typing.Optional[int]:
        try:
            return Vars.v.game_reader.get_int_from_address(address, 4)
        except GameReader.ReadProcessMemoryException:
            return None

    def filter_move_id_addresses() -> typing.List[int]:
        press_keys('d', '')
        sleep_frames(32)
        move_id_addresses = [a for a in move_id_addresses if read_4_bytes(a) == crouching_bytes_map[True]]

        press_keys('', None)
        sleep_frames(32)
        move_id_addresses = [a for a in move_id_addresses if read_4_bytes(a) == crouching_bytes_map[False]]
        return move_id_addresses
    
    try:
        move_id_addresses = filter_move_id_addresses()
    finally:
        press_keys('', None)

    def helper() -> typing.Tuple[int, int]:
        needed_matches = 20
        for skip in range(1 + len(move_id_addresses)//needed_matches):
            for i, a in enumerate(move_id_addresses):
                distance = move_id_addresses[i+skip]-a
                for x in range(needed_matches)[::-1]:
                    j = i + (skip * x)
                    if j > len(move_id_addresses) or move_id_addresses[j] - a != x * distance:
                        distance = -1
                        break
                if distance != -1:
                    print(a, distance, skip)
                    raise Exception("debug get_point_slope")
                    return a, distance
        raise Exception("get_point_slope")

    point_slope = helper()
    
    with open("point_slope.json", "w") as fh:
        json.dump(point_slope, fh)
    return point_slope

@enter_phase(
    3,
    [
        "phase 3 of 3",
        "building pointers_map - feel free to make inputs",
        "this usually takes around 5 minutes",
    ],
    lambda pointers_map: [
        "finished get_pointers_map",
        f"{len(pointers_map)}",
    ],
)
def get_pointers_map() -> typing.Dict[str, typing.List[int]]:
    if DEBUG_FAST:
        with open("pointers_map.json") as fh:
            return json.load(fh) # type: ignore
    memory = get_all_memory()
    prefixes = {}
    guaranteed_prefix = 3
    for address, block_raw in memory.items():
        address_bytes, address_end_bytes = [a.to_bytes(8, 'little') for a in [address, address + len(block_raw)]]
        if int.from_bytes(address_end_bytes[:guaranteed_prefix], 'little') == 0:
            continue
        if address_bytes[:guaranteed_prefix] != address_end_bytes[:guaranteed_prefix]:
            raise Exception(f"get_pointers_map {list(address_bytes)} : {list(address_end_bytes)}")
        for i in range(address_bytes[guaranteed_prefix], address_end_bytes[guaranteed_prefix]+1):
            prefix = address_bytes[:guaranteed_prefix]+i.to_bytes(1, 'little')
            prefixes[prefix] = [address_bytes, address_end_bytes]
    pointers_map = collections.defaultdict(list)
    num_pointers_found = 0
    for i, prefix in enumerate(prefixes):
        for base_address, index in find_bytes(prefix):
            raw_destination = memory[base_address][index-8+len(prefix):index+len(prefix)]
            if len(raw_destination) < 8:
                continue
            destination = int.from_bytes(raw_destination[::-1], 'little')
            source = base_address+index+len(prefix)-8
            pointers_map[hex(destination)].append(source)
            num_pointers_found += 1
        log(["get_pointers_map", f"{i+1} of {len(prefixes)}", f"{num_pointers_found} found"])
    with open("pointers_map.json", "w") as fh:
        json.dump(pointers_map, fh)
    return pointers_map

### helpers

def log(arr: typing.List[str]) -> None:
    print(" / ".join([f"{(time.time()-Vars.v.start):0.2f} seconds"] + arr))

def update_tk() -> None:
    tekken_rect = Vars.v.game_reader.get_window_rect()
    if tekken_rect is not None:
        height = 200
        geometry = f'{tekken_rect.right}x{height}+0-0'
        Vars.v.tk.geometry(geometry)
        Vars.v.tk.deiconify()
    else:
        Vars.v.tk.withdraw()
    Vars.v.tk.update()

def find_bytes(byte_array: typing.List[int]) -> typing.Iterable[typing.Tuple[int, int]]:
    memory = get_all_memory()
    def get_indices(needle: bytes, haystack: bytes) -> typing.Iterable[int]:
        index = 0
        for _ in range(1_000_000):
            index = haystack.find(needle, index)
            if index == -1:
                return
            yield index
            index += 1
        raise Exception(f"find_bytes {index} / {len(haystack)}")

    needle = bytes(byte_array[::-1])
    for base_address, haystack in memory.items():
        update_tk()
        for index in get_indices(needle, haystack):
            yield base_address, index

def press_keys(keys: str, previous: typing.Optional[str]) -> None:
    m = {k:v for d in [
        Replay.attack_string_to_hex,
        Replay.direction_string_to_hexes,
    ] for k,v in d[True].items()}
    if previous is None:
        previous = ''.join(m.keys())
    for key in previous:
        if key not in keys:
            Windows.w.release_key(m[key])
    for key in keys:
        if key not in previous:
            Windows.w.press_key(m[key])

def sleep_frames(frames: int) -> None:
    seconds = frames * Replay.seconds_per_frame
    Windows.w.sleep(seconds)

def get_blocks_from_instructions(instructions: typing.List[typing.Tuple[str, int]]) -> typing.List[bytes]:
    def helper() -> typing.List[bytes]:
        move_id_offset = get_move_id_offset()
        move_id_address, rollback_frame_offset = get_point_slope()
        player_data_base_address = move_id_address - move_id_offset
        blocks = []
        prev = ''
        for keys, duration in instructions:
            press_keys(keys, prev)
            prev = keys
            sleep_frames(duration)
            block = Vars.v.game_reader.get_block_of_data(player_data_base_address, rollback_frame_offset * 32)
            blocks.append(block)
        press_keys('', None)
        return blocks
    try:
        return helper()
    finally:
        press_keys('', None)

@memoize
def get_choreographed_blocks() -> typing.List[bytes]:
    return get_blocks_from_instructions([
        ("1", 10),
        ("", 60),
        ("1", 10),
    ])

def find_offset_from_blocks(
    blocks: typing.List[bytes],
    validate_f: typing.Callable[[typing.List[typing.List[typing.Tuple[int, int, int]]]], bool],
) -> int:
    _, rollback_frame_offset = get_point_slope()
    for offset in range(0x100, 0x10000):
        value_blocks = [
            [
                (
                    base,
                    offset,
                    Vars.v.game_reader.get_4_bytes_from_data_block(block, base + offset),
                )
                for base in [
                    rollback_frame_offset * i
                    for i in range(len(block)//rollback_frame_offset)
                ]
            ] for block in blocks
        ]
        if validate_f(value_blocks):
            return offset
    raise Exception("find_offset_from_block")

def find_offset_from_expected(blocks: typing.List[bytes], expected: typing.List[int]) -> int:
    frame_count_offset = get_frame_count()

    def stringify(values: typing.List[int]) -> str:
        return ",".join([""]+[str(i) for i in values]+[""])
    
    def validate_f(value_blocks: typing.List[typing.List[typing.Tuple[int, int, int]]]) -> bool:
        values = [value for block in value_blocks for base, offset, value in block]

        if DEBUG_FAST:
            if value_blocks[0][0][1] == Vars.v.game_reader.c[Vars.v.active[0]][Vars.v.active[1]][0]:
                print(values)

        values_str = stringify(values)
        expected_str = stringify(expected)

        return expected_str in values_str

    return find_offset_from_blocks(blocks, validate_f)

def get_pointer_offset(sources: typing.List[int], max_offset: int) -> typing.List[int]:
    candidates: typing.Dict[int, typing.List[int]] = {source: [] for source in sources}

    pointers_map = get_pointers_map()
    for _ in range(10):
        next_candidates = {}
        for address, prev in candidates.items():
            for offset in range(max_offset):
                sources = pointers_map.get(hex(address-offset), [])
                for source in sources:
                    diff = source - get_expected_module_address()
                    if diff > 0:
                        return [diff, offset]+prev
                    next_candidates[source] = [offset] + prev
        candidates = next_candidates
    raise Exception(f"get_pointer_offset {len(candidates)}")
    
### updaters

@memoize
def get_expected_module_address() -> int:
    assert(Vars.v.game_reader.module_address is not None)
    return Vars.v.game_reader.module_address

@memoize
def get_rollback_frame_offset() -> int:
    distance: int
    _, distance = get_point_slope()
    return distance

@memoize
def get_move_id_offset() -> int:
    # assume that PlayerDataAddress.move_id offset doesnt change
    return Vars.v.game_reader.c["PlayerDataAddress"]["move_id"][0]

@memoize
def get_frame_count() -> int:
    blocks = get_blocks_from_instructions([("", 1)])

    def validate_f(value_blocks: typing.List[typing.List[typing.Tuple[int, int, int]]]) -> bool:
        for block in value_blocks:
            values = [value for base, offset, value in block]
            for i in range(len(values)-1):
                diff = values[i+1]-values[i]
                if diff not in [1, -31]:
                    return False
        return True

    return find_offset_from_blocks(blocks, validate_f)

@memoize
def get_simple_move_state() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            256,
        ],
    )

@memoize
def get_p2_data_offset() -> int:
    simple_move_state_offset = get_simple_move_state()
    blocks = get_choreographed_blocks()

    p2_offset_plus_simple_move_state = find_offset_from_expected(
        blocks,
        [
            256,
        ],
    )

    return p2_offset_plus_simple_move_state - simple_move_state_offset

@memoize
def get_damage_taken() -> int:
    blocks = get_blocks_from_instructions([("", 1)])
    return find_offset_from_expected(
        blocks,
        [
            256,
        ],
    )

@memoize
def get_attack_type() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            256,
        ],
    )

@memoize
def get_player_data_pointer_offset() -> typing.List[int]:
    pointers_map = get_pointers_map()
    move_id_address, _ = get_point_slope()
    move_id_offset = get_move_id_offset()

    sources = pointers_map.get(hex(move_id_address-move_id_offset), [])

    if len(sources) == 0:
        raise Exception(f"get_player_data_pointer_offset {hex(move_id_address)}")

    return get_pointer_offset(sources, 0x100)

@memoize
def get_opponent_side() -> typing.List[int]:
    bytes_to_find_str = "01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 00 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40"
    bytes_to_find = list(map(lambda x: int(x, 16), bytes_to_find_str.split()))
    found_bytes = list(find_bytes(bytes_to_find[::-1]))
    if len(found_bytes) != 1:
        raise Exception(f"get_opponent_side {len(found_bytes)}")
    destination = found_bytes[0]
    address = destination[0] + destination[1]
    return get_pointer_offset([address], 0x10)

to_update: typing.List[typing.Tuple[typing.Tuple[str, str], typing.Callable[[], FoundType]]] = [
    # phase 1 get_all_memory
    (("MemoryAddressOffsets", "expected_module_address"), get_expected_module_address),
    # phase 2 get_point_slope
    (("MemoryAddressOffsets", "rollback_frame_offset"), get_rollback_frame_offset),
    (("PlayerDataAddress", "move_id"), get_move_id_offset),
    (("GameDataAddress", "frame_count"), get_frame_count),
    (("PlayerDataAddress", "simple_move_state"), get_simple_move_state),
    (("MemoryAddressOffsets", "p2_data_offset"), get_p2_data_offset),
    (("PlayerDataAddress", "damage_taken"), get_damage_taken),
    (("PlayerDataAddress", "attack_type"), get_attack_type),
    # TODO rest of the offsets
    # phase 3 get_pointers_map
    (("MemoryAddressOffsets", "player_data_pointer_offset"), get_player_data_pointer_offset),
    (("NonPlayerDataAddresses", "opponent_side"), get_opponent_side),
]

###

class Vars:
    def __init__(self, game_reader: GameReader.GameReader) -> None:
        self.game_reader = game_reader
        self.phase = 0
        self.start = time.time()
        self.tk = t_tkinter.Tk()
        self.active = ("", "")


        t_tkinter.init_tk(self.tk)
        self.tk.attributes("-topmost", True)
        self.tk.overrideredirect(True)
