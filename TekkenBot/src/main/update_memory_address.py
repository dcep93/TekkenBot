from ..game_parser import GameReader, MoveInfoEnums
from ..gui import t_tkinter, TekkenBotPrime
from ..misc import Path, Windows, w_windows
from ..record import Replay

import collections
import ctypes
# TODO
import json
import time
import typing

# TODO
DEBUG_FAST = True

# assumes PlayerDataAddress.move_id doesn't change


def main() -> None:
    if not t_tkinter.valid:
        # expected to error if invalid
        # intended to easily show a stack trace
        import tkinter
    if not Windows.w.valid:
        raise Exception("need to be on windows")
    Vars.game_reader.reacquire_module()
    if not Vars.game_reader.process_handle:
        raise Exception("need to be running tekken")

    t_tkinter.init_tk(Vars.tk)
    Vars.tk.attributes("-topmost", True)
    Vars.tk.overrideredirect(True)

    found: typing.Dict[typing.Tuple[str, str], str] = {}
    print("\n".join([
        "",
        "you should be in practice mode as p1 Jin vs Kazuya",
        "with practice options set to Opponent Actions -> Standing / Action After a Hit or Block -> Block All :",
        "if you're not on that screen already, you'll need to restart this tool",
        "do not make any inputs until phase 4",
        "",
    ]))
    for path, update_f in to_update:
        log([f"{path}"])
        Vars.active = path
        raw = update_f()
        val = hexify(raw)
        found[path] = val
        log([val, "\n"])
    config_obj = Vars.game_reader._c
    for path, val in found.items():
        # TODO experiment - run once, everything changes, run twice, everything goes back
        config_obj[path[0]][path[1]] = val
    with open(Path.path('config/memory_address.ini'), 'w') as fh:
        config_obj.write(fh)

# phases


class Vars:
    phase = 0
    max_phases = 0
    start = time.time()
    tk = t_tkinter.Tk()
    active = ("", "")
    game_reader = GameReader.GameReader()


MemoizeT = typing.TypeVar('MemoizeT', bound=typing.Callable[..., typing.Any])


def memoize(f: MemoizeT) -> MemoizeT:
    d: typing.Dict[typing.Any, typing.Any] = {}

    def g(*args: typing.Any) -> typing.Any:
        if args in d:
            return d[args]
        v = f(*args)
        d[args] = v
        return v
    return g  # type: ignore


def enter_phase(phase: int, log_before: typing.List[str], log_after_f: typing.Optional[typing.Callable[..., typing.List[str]]] = None) -> typing.Callable[..., typing.Any]:
    Vars.max_phases += 1

    def f(g: MemoizeT) -> MemoizeT:
        @memoize
        def h(*args: typing.Any) -> typing.Any:
            Vars.phase += 1
            if Vars.phase != phase:
                raise Exception(f"enter_phase {phase} {Vars.phase}")
            log([f"phase {Vars.phase} of {Vars.max_phases}"] + log_before)
            v = g(*args)
            if log_after_f is not None:
                log_after = log_after_f(v)
                log(log_after)
            return v
        return h  # type: ignore
    return f


@enter_phase(
    1,
    [
        "collecting initial memory data",
        "this usually takes around 1 minute",
    ],
    lambda memory: [
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
        Windows.w.k32.VirtualQueryEx(
            Vars.game_reader.process_handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi))

        scannable_size = mbi.RegionSize
        assert (isinstance(scannable_size, int))
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
            block = Vars.game_reader.get_block_of_data(address, scannable_size)
            memory[address] = block
        address += abs(scannable_size)
    raise Exception("get_all_memory")


@enter_phase(
    2,
    [
        "scanning memory",
        "this usually takes around 1 minute",
    ],
    lambda move_id_addresses: [f"{len(move_id_addresses)} address candidates"]
)
def get_move_id_addresses() -> typing.List[int]:
    if DEBUG_FAST:
        with open("move_id_addresses.json") as fh:
            return json.load(fh)  # type: ignore

    standing_bytes = Vars.game_reader.int_to_bytes(
        MoveInfoEnums.UniversalMoves.STANDING.value, 4)
    found_bytes = find_bytes(standing_bytes)
    move_id_addresses = [base_address +
                         index for base_address, index in found_bytes]

    with open("move_id_addresses.json", "w") as fh:
        json.dump(move_id_addresses, fh)

    return move_id_addresses


@enter_phase(
    3,
    [
        "collecting input data",
        "this usually takes around 1 minute",
    ],
)
def get_input_hexes() -> typing.Dict[str, int]:
    return {k: v for d in [
        Replay.attack_string_to_hex,
        Replay.direction_string_to_hexes,
    ] for k, v in d[True].items()}


@enter_phase(
    4,
    [
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
            return json.load(fh)  # type: ignore

    memory = get_all_memory()
    prefixes = {}
    guaranteed_prefix = 3
    to_bytes = Vars.game_reader.int_to_bytes
    for address, block_raw in memory.items():
        address_bytes, address_end_bytes = [Vars.game_reader.int_to_bytes(
            a, 8) for a in [address, address + len(block_raw)]]
        if Vars.game_reader.bytes_to_int(address_end_bytes[:guaranteed_prefix]) == 0:
            continue
        if address_bytes[:guaranteed_prefix] != address_end_bytes[:guaranteed_prefix]:
            raise Exception(f"get_pointers_map {list(address_bytes)} : {list(address_end_bytes)}")  # nopep8
        for i in range(address_bytes[guaranteed_prefix], address_end_bytes[guaranteed_prefix]+1):
            prefix = address_bytes[:guaranteed_prefix] + \
                Vars.game_reader.int_to_bytes(i, 1)
            prefixes[prefix] = [address_bytes, address_end_bytes]
    pointers_map = collections.defaultdict(list)
    num_pointers_found = 0
    for i, prefix in enumerate(prefixes):
        for base_address, index in find_bytes(prefix):
            raw_destination = memory[base_address][index -
                                                   8+len(prefix):index+len(prefix)]
            if len(raw_destination) < 8:
                continue
            destination = Vars.game_reader.bytes_to_int(raw_destination[::-1])
            source = base_address+index+len(prefix)-8
            pointers_map[hex(destination)].append(source)
            num_pointers_found += 1
        log(["get_pointers_map", f"{i+1} of {len(prefixes)}", f"{num_pointers_found} found"])  # nopep8

    with open("pointers_map.json", "w") as fh:
        json.dump(pointers_map, fh)

    return pointers_map

# helpers

# TODO


def cheat(a1: str, a2: str) -> int:
    print("cheating", a1, a2)
    return Vars.game_reader.c[a1][a2][0]


def log(arr: typing.List[str]) -> None:
    print(" / ".join([f"{(time.time()-Vars.start):0.2f} seconds"] + arr))


def update_tk() -> None:
    if Vars.game_reader.is_foreground_pid():
        tekken_rect = Windows.w.get_window_rect()
        height = 200
        geometry = f'{tekken_rect.right}x{height}+0-0'
        Vars.tk.geometry(geometry)
        Vars.tk.deiconify()
    else:
        Vars.tk.withdraw()
    Vars.tk.update()


def find_bytes(byte_array: bytes) -> typing.Iterable[typing.Tuple[int, int]]:
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

    needle = byte_array[::-1]
    for base_address, haystack in memory.items():
        update_tk()
        for index in get_indices(needle, haystack):
            yield base_address, index


def press_keys(keys: str, previous: typing.Optional[str]) -> None:
    m = get_input_hexes()
    if previous is None:
        previous = ''.join(m.keys())
        while not Vars.game_reader.is_foreground_pid():
            log(["waiting for focus"])
            sleep_frames(10)
    else:
        if not Vars.game_reader.is_foreground_pid():
            raise Exception("need to remain in focus")

    update_tk()

    for key in previous:
        if key not in keys:
            Windows.w.release_key(m[key])
    for key in keys:
        if key not in previous:
            Windows.w.press_key(m[key])


def sleep_frames(frames: float) -> None:
    seconds = frames * Replay.seconds_per_frame
    Windows.w.sleep(seconds)


@memoize
def get_point_slope() -> typing.Tuple[int, int]:
    move_id_addresses = get_move_id_addresses()

    def read_4_bytes(address: int) -> typing.Optional[int]:
        try:
            return Vars.game_reader.get_int_from_address(address, 4)
        except GameReader.ReadProcessMemoryException:
            return None

    press_keys('', None)

    def filter_move_id_addresses(move_id_addresses: typing.List[int]) -> typing.List[int]:
        press_keys('d', '')
        sleep_frames(60)
        return [a for a in move_id_addresses if read_4_bytes(a) == MoveInfoEnums.UniversalMoves.CROUCHING.value]

    try:
        move_id_addresses = filter_move_id_addresses(move_id_addresses)
    finally:
        press_keys('', 'd')

    sleep_frames(60)
    move_id_addresses = [a for a in move_id_addresses if read_4_bytes(
        a) == MoveInfoEnums.UniversalMoves.STANDING.value]

    needed_matches = 20
    for skip in range(1, 1 + len(move_id_addresses)//needed_matches):
        for i, a in enumerate(move_id_addresses):
            if i + skip >= len(move_id_addresses):
                continue
            distance = move_id_addresses[i+skip]-a
            for x in range(needed_matches)[::-1]:
                j = i + (skip * x)
                if j >= len(move_id_addresses) or move_id_addresses[j] - a != x * distance:
                    distance = -1
                    break
            if distance != -1:
                return a, distance
    raise Exception(f"get_point_slope {len(move_id_addresses)}")


def get_blocks_from_instructions(instructions: typing.List[typing.Tuple[str, int]]) -> typing.List[bytes]:
    def helper() -> typing.List[bytes]:
        move_id_offset = get_move_id_offset()
        move_id_address, rollback_frame_offset = get_point_slope()
        player_data_base_address = move_id_address - move_id_offset
        blocks = []
        press_keys('', None)
        prev_keys = ''
        prev_time = time.time()
        for keys, duration in instructions:
            press_keys(keys, prev_keys)
            prev_keys = keys
            delay = (time.time() - prev_time) / Replay.seconds_per_frame
            sleep_frames(duration - delay)
            prev_time = time.time()
            block = Vars.game_reader.get_block_of_data(
                player_data_base_address, rollback_frame_offset * 32)
            blocks.append(block)
        press_keys('', prev_keys)
        return blocks
    try:
        return helper()
    finally:
        press_keys('', None)


@memoize
def get_choreographed_blocks() -> typing.List[bytes]:
    with open("choreographed_blocks.json") as fh:
        b = [bytes(i) for i in json.load(fh)]
        return b

    b = get_blocks_from_instructions([
        ("", 10),
        ("1", 10),
        ("", 10),
        ("1", 10),
        ("", 20),
        ("", 20),
        ("", 20),
    ])
    with open("choreographed_blocks.json", "w") as fh:
        bb = [list(i) for i in b]
        json.dump(bb, fh)
    return b


@memoize
def get_throw_choreographed_blocks() -> typing.List[bytes]:
    # with open("throw_choreographed_blocks.json") as fh:
    #     b = [bytes(i) for i in json.load(fh)]
    #     return b

    b = get_blocks_from_instructions([
        ("", 10),
        ("uf12", 10),
        ("uf", 10),
        ("", 10),
    ])
    with open("throw_choreographed_blocks.json", "w") as fh:
        bb = [list(i) for i in b]
        json.dump(bb, fh)
    return b


ToValidateType = typing.Tuple[int,
                              typing.List[typing.Tuple[bytes, typing.List[typing.Tuple[int, int]]]]]


def find_offset_from_blocks(
    blocks: typing.List[bytes],
    validate_f: typing.Callable[[ToValidateType], bool],
    is_p1: bool,
) -> int:
    rollback_frame_offset = get_rollback_frame_offset()
    offset_for_p2 = 0 if is_p1 else get_p2_data_offset()
    for offset in range(0x100, 0x10000):
        if offset % 0x100 == 0:
            update_tk()
        to_validate = (offset, [
            (block, [
                (
                    base,
                    Vars.game_reader.get_4_bytes_from_data_block(
                        block, base + offset + offset_for_p2),
                )
                for base in [
                    rollback_frame_offset * i
                    for i in range(len(block)//rollback_frame_offset)
                ]
            ]) for block in blocks
        ])
        if validate_f(to_validate):
            return offset
    raise Exception("find_offset_from_block")


def find_offset_from_expected(blocks: typing.List[bytes], expected: typing.List[typing.List[int]], is_p1: bool) -> int:
    def stringify(values: typing.List[int]) -> str:
        return ",".join([""]+[hex(i) for i in values]+[""])

    expected_strs = [stringify(e) for e in expected]

    frame_count_offset = get_frame_count()

    def validate_f(to_validate: ToValidateType) -> bool:
        offset, data = to_validate

        value_by_frame: typing.Dict[int, int] = {}

        for block, block_data in data:
            for base, value in block_data:
                frame_count = Vars.game_reader.get_4_bytes_from_data_block(
                    block, base + frame_count_offset)
                value_by_frame[frame_count] = value

        values = [value_by_frame.get(
            i, -1) for i in range(min(value_by_frame), max(value_by_frame))]

        values_str = stringify(values)

        if DEBUG_FAST:
            if offset == Vars.game_reader.c[Vars.active[0]][Vars.active[1]][0]:
                if not all((e in values_str for e in expected_strs)):
                    print(values)
                    c = 0
                    p = None
                    for i in values:
                        if i == p:
                            c += 1
                        else:
                            print(p, c)
                            p = i
                            c = 1
                    print(p, c)
                    log([f"{len(values)}"])
                    import sys
                    print("bye")
                    sys.exit(1)
                return True

        return all((e in values_str for e in expected_strs))

    return find_offset_from_blocks(blocks, validate_f, is_p1)


def get_pointer_offset(sources: typing.List[int], max_offset: int) -> typing.List[int]:
    candidates: typing.Dict[int, typing.List[int]] = {
        source: [] for source in sources}

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


FoundType = typing.Union[int, typing.List[int]]


def hexify(raw: FoundType) -> str:
    if isinstance(raw, int):
        return hex(raw)
    return ' '.join([hexify(r) for r in raw])

# updaters


@memoize
def get_expected_module_address() -> int:
    assert (Vars.game_reader.module_address is not None)
    return Vars.game_reader.module_address


def get_rollback_frame_offset() -> int:
    distance: int
    return cheat("MemoryAddressOffsets", "rollback_frame_offset")
    _, distance = get_point_slope()
    return distance


@memoize
def get_move_id_offset() -> int:
    # assume that PlayerDataAddress.move_id offset doesnt change
    return Vars.game_reader.c["PlayerDataAddress"]["move_id"][0]


@memoize
def get_frame_count() -> int:
    get_all_memory()
    return cheat("GameDataAddress", "frame_count")
    blocks = get_blocks_from_instructions([("", 1)])

    def validate_f(to_validate: ToValidateType) -> bool:
        offset, data = to_validate
        for block, block_data in data:
            values = [value for base, value in block_data]
            if values[0] <= 122:
                return False
            for i in range(len(values)-1):
                diff = values[i+1]-values[i]
                if diff not in [1, -31]:
                    return False
        return True

    return find_offset_from_blocks(blocks, validate_f, True)


@memoize
def get_simple_move_state() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 20 +
            [MoveInfoEnums.SimpleMoveStates.STANDING_FORWARD.value] * 66 +
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 20,
        ],
        True,
    )


def get_p2_data_offset() -> int:
    return cheat("MemoryAddressOffsets", "p2_data_offset")
    blocks = get_choreographed_blocks()

    p2_offset_plus_simple_move_state = find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 30 +
            [MoveInfoEnums.SimpleMoveStates.STANDING_FORWARD.value] * 26 +
            [MoveInfoEnums.SimpleMoveStates.STANDING_BACK.value] * 31 +
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 10,
        ],
        True,
    )

    return p2_offset_plus_simple_move_state - get_simple_move_state()


def get_attack_type() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.AttackType.RECOVERING.value] * 30 +
            [MoveInfoEnums.AttackType.HIGH.value] * 66 +
            [MoveInfoEnums.AttackType.RECOVERING.value] * 10,
        ],
        True,
    )


def get_recovery() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [122] * 25 +
            [27] * 66 +
            [122] * 15,
        ],
        True,
    )


def get_hit_outcome() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.HitOutcome.NONE.value] * 37 +
            [MoveInfoEnums.HitOutcome.NORMAL_HIT_STANDING.value] * 27 +
            [MoveInfoEnums.HitOutcome.BLOCKED_STANDING.value] * 31 +
            [MoveInfoEnums.HitOutcome.NONE.value] * 10,
        ],
        False,
    )


def get_stun_type() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.StunStates.NONE.value] * 37 +
            [MoveInfoEnums.StunStates.GETTING_HIT.value] * 58 +
            [MoveInfoEnums.StunStates.NONE.value] * 10,
        ],
        False,
    )


def get_throw_tech() -> int:
    blocks = get_throw_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.ThrowTechs.NONE.value] * 37 +
            [MoveInfoEnums.ThrowTechs.TE1_2.value] * 158 +
            [MoveInfoEnums.ThrowTechs.NONE.value] * 10,
        ],
        False,
    )


def get_complex_move_state() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.ComplexMoveStates.F_MINUS.value] * 28 +
            [MoveInfoEnums.ComplexMoveStates.C_MINUS.value] * 9 +
            [MoveInfoEnums.ComplexMoveStates.END1.value] * 18 +
            [MoveInfoEnums.ComplexMoveStates.C_MINUS.value] * 9 +
            [MoveInfoEnums.ComplexMoveStates.END1.value] * 30 +
            [MoveInfoEnums.ComplexMoveStates.F_MINUS.value] * 17,
        ],
        True,
    )


def get_damage_taken() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [45] * 37 +
            [50] * 74,
        ],
        False,
    )


def get_input_attack() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.InputAttackCodes.N.value] * 28 +
            [MoveInfoEnums.InputAttackCodes.x1.value] * 10 +
            [MoveInfoEnums.InputAttackCodes.N.value] * 10 +
            [MoveInfoEnums.InputAttackCodes.x1.value] * 10 +
            [MoveInfoEnums.InputAttackCodes.N.value] * 54,
        ],
        True,
    )


def get_input_direction() -> int:
    blocks = get_throw_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [MoveInfoEnums.InputDirectionCodes.NULL.value] * 28 +
            [MoveInfoEnums.InputDirectionCodes.uf.value] * 110 +
            [MoveInfoEnums.InputDirectionCodes.NULL.value] * 10,
        ],
        True,
    )


def get_attack_startup() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [0] * 28 +
            [10] * 66 +
            [0] * 17,
        ],
        True,
    )


def get_char_id() -> int:
    blocks = get_choreographed_blocks()

    rollback_frame_offset = get_rollback_frame_offset()
    p2_offset = get_p2_data_offset()
    for offset in range(0x100, 0x10000):
        if offset % 0x100 == 0:
            update_tk()
        for block in blocks:
            for base in [
                rollback_frame_offset * i
                for i in range(len(block)//rollback_frame_offset)
            ]:
                p1 = Vars.game_reader.get_4_bytes_from_data_block(
                    block, base + offset)
                p2 = Vars.game_reader.get_4_bytes_from_data_block(
                    block, base + offset + p2_offset)
                if p1 != MoveInfoEnums.CharacterCodes.JIN.value or p2 != MoveInfoEnums.CharacterCodes.KAZUYA.value:
                    offset = -1
                    break
            if offset == -1:
                break
        if offset != -1:
            return offset

    raise Exception("get_char_id")


def get_move_timer() -> int:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            list(range(1, 28)) +
            list(range(1, 40)) +
            list(range(1, 17)),
        ],
        True,
    )


def get_facing() -> int:
    blocks = get_throw_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        [
            [0] * 100 +
            [1] * 100,
        ],
        True,
    )


def get_player_data_pointer_offset() -> typing.List[int]:
    pointers_map = get_pointers_map()
    move_id_address, _ = get_point_slope()

    address = move_id_address - get_move_id_offset()

    sources = pointers_map.get(hex(address), [])

    if len(sources) == 0:
        raise Exception(f"get_player_data_pointer_offset {hex(address)} {len(pointers_map)}")  # nopep8

    return get_pointer_offset(sources, 0x100)


def get_opponent_side() -> typing.List[int]:
    if DEBUG_FAST:
        return Vars.game_reader.c["NonPlayerDataAddresses"]["opponent_side"]
    # https://github.com/WAZAAAAA0/TekkenBot/issues/57#issuecomment-2087909057
    bytes_to_find_str = "01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 00 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40"
    bytes_to_find = list(map(lambda x: int(x, 16), bytes_to_find_str.split()))
    found_bytes = list(find_bytes(bytes(bytes_to_find[::-1])))
    if len(found_bytes) != 1:
        raise Exception(f"get_opponent_side {len(found_bytes)}")
    destination = found_bytes[0]
    address = destination[0] + destination[1]
    return get_pointer_offset([address], 0x10)


to_update: typing.List[typing.Tuple[typing.Tuple[str, str], typing.Callable[[], FoundType]]] = [
    # phase 1 get_all_memory
    (("MemoryAddressOffsets", "expected_module_address"), get_expected_module_address),
    (("PlayerDataAddress", "move_id"), get_move_id_offset),
    # phase 2 get_move_id_addresses
    # phase 3 get_input_hexes
    (("GameDataAddress", "frame_count"), get_frame_count),
    (("MemoryAddressOffsets", "rollback_frame_offset"), get_rollback_frame_offset),
    (("PlayerDataAddress", "simple_move_state"), get_simple_move_state),
    (("MemoryAddressOffsets", "p2_data_offset"), get_p2_data_offset),
    (("PlayerDataAddress", "attack_type"), get_attack_type),
    (("PlayerDataAddress", "recovery"), get_recovery),
    (("PlayerDataAddress", "hit_outcome"), get_hit_outcome),
    (("PlayerDataAddress", "stun_type"), get_stun_type),
    (("PlayerDataAddress", "throw_tech"), get_throw_tech),
    (("PlayerDataAddress", "complex_move_state"), get_complex_move_state),
    (("PlayerDataAddress", "damage_taken"), get_damage_taken),
    (("PlayerDataAddress", "input_attack"), get_input_attack),
    (("PlayerDataAddress", "input_direction"), get_input_direction),
    (("PlayerDataAddress", "attack_startup"), get_attack_startup),
    (("PlayerDataAddress", "char_id"), get_char_id),
    (("PlayerDataAddress", "move_timer"), get_move_timer),
    (("GameDataAddress", "facing"), get_facing),
    # phase 4 get_pointers_map
    (("MemoryAddressOffsets", "player_data_pointer_offset"),
     get_player_data_pointer_offset),
    (("NonPlayerDataAddresses", "opponent_side"), get_opponent_side),
    # TODO
    (("", ""), lambda: 1//0),
]
