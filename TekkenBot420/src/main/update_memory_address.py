from ..game_parser import GameReader, MoveInfoEnums
from ..gui import t_tkinter, TekkenBot420
from ..misc import Path, Windows, w_windows
from ..record import Replay

import collections
import ctypes
import re
import time
import typing


# assumes PlayerDataAddress.move_id doesn't change


def main() -> None:
    if not t_tkinter.valid:
        # expected to error if invalid
        # intended to easily show a stack trace
        import tkinter
    if not Windows.w.valid:
        raise Exception("need to be on windows")
    get_game_reader().reacquire_module()
    if not get_game_reader().process_handle:
        raise Exception("need to be running tekken")

    t_tkinter.init_tk(Vars.tk, padx=50)
    Vars.tk.overrideredirect(True)
    Vars.tk.configure(background="white")
    Vars.tk.attributes("-topmost", True)

    found: typing.Dict[typing.Tuple[str, str], str] = {}
    print("\n".join([
        "",
        "you should be in practice mode as p1 Jin vs Kazuya",
        "with practice options set to Opponent Actions -> Standing / Action After a Hit or Block -> Block All :",
        "if you're not on that screen already, you'll need to restart this tool",
        "do not make any inputs until the end of the throw animation",
        "",
    ]))
    get_all_memory()
    get_move_id_addresses()
    get_choreographed_blocks()
    get_throw_choreographed_blocks()
    for path, update_f in to_update:
        log([f"{path}"])
        Vars.active = path
        raw = update_f()
        val = ' '.join([hex(r) for r in raw])
        found[path] = val
        log([val, "\n"])
    config_obj = get_game_reader()._c
    for path, val in found.items():
        config_obj[path[0]][path[1]] = val
    with open(Path.path('config/memory_address.ini'), 'w') as fh:
        config_obj.write(fh)
    Vars.tk.withdraw()

# phases


class Vars:
    phase = 0
    max_phases = 0
    start = time.time()
    tk = t_tkinter.Tk()
    active = ("", "")


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
            get_game_reader().process_handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi))

        scannable_size = mbi.RegionSize
        assert (isinstance(scannable_size, int))
        if mbi.Protect != 0x04 or mbi.State != 0x00001000:
            scannable_size = -scannable_size
        return scannable_size

    memory: typing.Dict[int, bytes] = {}
    address = 0
    for _ in range(1_000_000):
        scannable_size = get_memory_scannable_size(address)
        if scannable_size == 0:
            return memory
        if scannable_size > 0:
            update_tk()
            block = get_game_reader().get_block_of_data(address, scannable_size)
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
    standing_bytes = get_game_reader().int_to_bytes(
        MoveInfoEnums.UniversalMoves.STANDING.value, 4)
    found_bytes = find_bytes(standing_bytes)
    move_id_addresses = [base_address +
                         index for base_address, index in found_bytes]

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
        "building pointers_map",
        "this usually takes around 5 minutes",
    ],
    lambda pointers_map: [
        "finished get_pointers_map",
        f"{len(pointers_map)}",
    ],
)
def get_pointers_map() -> typing.Dict[str, typing.List[int]]:
    memory = get_all_memory()
    prefixes = {}
    guaranteed_prefix = 3
    to_bytes = get_game_reader().int_to_bytes
    for address, block_raw in memory.items():
        address_bytes, address_end_bytes = [get_game_reader().int_to_bytes(
            a, 8) for a in [address, address + len(block_raw)]]
        if get_game_reader().bytes_to_int(address_end_bytes[:guaranteed_prefix]) == 0:
            continue
        if address_bytes[:guaranteed_prefix] != address_end_bytes[:guaranteed_prefix]:
            raise Exception(f"get_pointers_map {list(address_bytes)} : {list(address_end_bytes)}")  # nopep8
        for i in range(address_bytes[guaranteed_prefix], address_end_bytes[guaranteed_prefix]+1):
            prefix = address_bytes[:guaranteed_prefix] + \
                get_game_reader().int_to_bytes(i, 1)
            prefixes[prefix] = [address_bytes, address_end_bytes]
    pointers_map = collections.defaultdict(list)
    num_pointers_found = 0
    for i, prefix in enumerate(prefixes):
        for base_address, index in find_bytes(prefix):
            raw_destination = memory[base_address][index -
                                                   8+len(prefix):index+len(prefix)]
            if len(raw_destination) < 8:
                continue
            destination = get_game_reader().bytes_to_int(raw_destination[::-1])
            source = base_address+index+len(prefix)-8
            pointers_map[hex(destination)].append(source)
            num_pointers_found += 1
        log(["get_pointers_map", f"{i+1} of {len(prefixes)}", f"{num_pointers_found} found"])  # nopep8

    return pointers_map

# helpers


def log(arr: typing.List[str]) -> None:
    print(" / ".join([f"{(time.time()-Vars.start):0.2f} seconds"] + arr))


@memoize
def get_game_reader() -> GameReader.GameReader:
    return GameReader.GameReader()


def update_tk() -> None:
    if get_game_reader().is_foreground_pid():
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
        while not get_game_reader().is_foreground_pid():
            log(["waiting for focus"])
            sleep_frames(10)
        update_tk()
    else:
        if not get_game_reader().is_foreground_pid():
            raise Exception("need to remain in focus")

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
            return get_game_reader().get_int_from_address(address, 4)
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


def get_current_frame() -> int:
    move_id_address, rollback_frame_offset = get_point_slope()
    player_data_base_address = move_id_address - get_move_id_offset()[0]
    base = player_data_base_address + get_frame_count()[0]
    return max([get_game_reader().get_int_from_address(base + i * rollback_frame_offset, 4) for i in range(32)])


def get_blocks_from_instructions(instructions: typing.List[typing.Tuple[str, int]]) -> typing.List[bytes]:
    def helper() -> typing.List[bytes]:
        move_id_offset = get_move_id_offset()[0]
        move_id_address, rollback_frame_offset = get_point_slope()
        player_data_base_address = move_id_address - move_id_offset
        blocks = []
        press_keys('', None)
        prev_keys = ''
        for keys, duration in instructions:
            starting_frame = get_current_frame()
            press_keys(keys, prev_keys)
            prev_keys = keys
            sleep_frames(duration-2)
            block = get_game_reader().get_block_of_data(
                player_data_base_address, rollback_frame_offset * 32)
            blocks.append(block)
            while True:
                current_frame = get_current_frame()
                frames_elapsed = current_frame - starting_frame
                if duration > frames_elapsed:
                    sleep_frames(duration - frames_elapsed - 0.9)
                else:
                    break
        press_keys('', prev_keys)
        return blocks
    try:
        return helper()
    finally:
        press_keys('', None)


@memoize
def get_choreographed_blocks() -> typing.List[bytes]:
    return get_blocks_from_instructions([
        ("", 10),
        ("1", 10),
        ("", 10),
        ("1", 10),
        ("uf", 20),
        ("db", 20),
        ("", 20),
    ])


@memoize
def get_throw_choreographed_blocks() -> typing.List[bytes]:
    return get_blocks_from_instructions([
        ("", 10),
        ("24", 10),
        ("", 32),
        ("", 32),
        ("", 32),
        ("", 32),
        ("", 32),
    ])


def stringify(values: typing.List[int]) -> str:
    return ",".join([str(i) for i in values])


def find_offset_from_f(f: typing.Callable[[int], bool]) -> typing.List[int]:
    possibilities: typing.List[int] = []

    for offset in range(0x10000):
        if offset % 0x100 == 0:
            update_tk()

        if f(offset):
            possibilities.append(offset)
    return possibilities


def find_offset_from_expected(blocks: typing.List[bytes], expected: typing.List[int], extra_offset: int = 0) -> typing.List[int]:
    expected_str = stringify(expected)

    def f(offset: int) -> bool:
        values = get_values_from_blocks(blocks, offset + extra_offset)

        values_str = stringify(values)

        return expected_str in values_str

    return find_offset_from_f(f)


def get_values_from_blocks(blocks: typing.List[bytes], offset: int) -> typing.List[int]:
    rollback_frame_offset = get_rollback_frame_offset()[0]
    frame_count_offset = get_frame_count()[0]

    value_by_frame: typing.Dict[int, int] = {}

    for block in blocks:
        for base in range(0, len(block), rollback_frame_offset):
            frame_count = get_game_reader().get_4_bytes_from_data_block(
                block, base + frame_count_offset)
            value_by_frame[frame_count] = get_game_reader().get_4_bytes_from_data_block(
                block, base + offset)

    values: typing.List[int] = []
    for i in range(min(value_by_frame), max(value_by_frame)):
        v = value_by_frame[i] if i in value_by_frame else values[-1]
        values.append(v)

    return values


def get_pointer_offset(
    sources: typing.List[int],
    max_offset: int,
    desired_depth: int,
    f: typing.Callable[[typing.List[int]], bool],
) -> typing.List[int]:
    candidates: typing.Dict[int, typing.List[int]] = {
        source: [] for source in sources}

    pointers_map = get_pointers_map()
    for depth in range(desired_depth-1):
        next_candidates = {}
        for address, prev in candidates.items():
            for offset in range(max_offset):
                sources = pointers_map.get(hex(address-offset), [])
                for source in sources:
                    next_candidates[source] = [offset] + prev
        candidates = next_candidates

    possibilities = sorted([i for i in [[source - get_expected_module_address()] +
                                        prev for source, prev in candidates.items()] if i[0] > 0])

    while len(possibilities) > 1:
        print(f"pruning {len(possibilities)} possibilities")
        popup = t_tkinter.Toplevel(Vars.tk)
        t_tkinter.Label(popup, text="\n".join([
            "too many pointer offsets were found",
            "please close the game, reopen, and reenter practice mode",
            "then click to proceed",
        ])).pack(pady=10)
        t_tkinter.Button(popup, text="proceed").pack(pady=10)
        popup.wait_window()

        get_game_reader().reacquire_module()

        if not get_game_reader().process_handle:
            log(["tekken not found"])
            continue

        possibilities = [p for p in possibilities if f(p)]

    return possibilities[0]


# updaters


@memoize
def get_expected_module_address() -> typing.List[int]:
    m = get_game_reader().module_address
    assert (m is not None)
    return [m]


def get_rollback_frame_offset() -> typing.List[int]:
    distance: int
    _, distance = get_point_slope()
    return [distance]


@memoize
def get_move_id_offset() -> typing.List[int]:
    # assume that PlayerDataAddress.move_id offset doesnt change
    return get_game_reader().c["PlayerDataAddress"]["move_id"]


@memoize
def get_frame_count() -> typing.List[int]:
    move_id_offset = get_move_id_offset()[0]
    move_id_address, rollback_frame_offset = get_point_slope()
    player_data_base_address = move_id_address - move_id_offset

    block = get_game_reader().get_block_of_data(
        player_data_base_address,
        rollback_frame_offset * 32,
    )

    def f(offset: int) -> bool:
        values = [get_game_reader().get_4_bytes_from_data_block(
            block, (rollback_frame_offset * i) + offset) for i in range(32)]

        if values[0] <= 500:
            return False
        for i in range(len(values)-1):
            diff = values[i+1]-values[i]
            if diff not in [1, -31]:
                return False
        return True

    return find_offset_from_f(f)


@memoize
def get_simple_move_state() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 20 +
            [MoveInfoEnums.SimpleMoveStates.STANDING_FORWARD.value] * 54 +
            [MoveInfoEnums.SimpleMoveStates.CROUCH_BACK.value] * 16 +
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 10
        ),
    )


@ memoize
def get_p2_data_offset() -> typing.List[int]:
    blocks = get_choreographed_blocks()

    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 30 +
            [MoveInfoEnums.SimpleMoveStates.STANDING_FORWARD.value] * 26 +
            [MoveInfoEnums.SimpleMoveStates.STANDING_BACK.value] * 31 +
            [MoveInfoEnums.SimpleMoveStates.STANDING.value] * 10
        ),
        get_simple_move_state()[0],
    )


def get_attack_type() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.AttackType.RECOVERING.value] * 30 +
            [MoveInfoEnums.AttackType.HIGH.value] * 54 +
            [MoveInfoEnums.AttackType.RECOVERING.value] * 30
        ),
    )


def get_recovery() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [122] * 24 +
            [27] * 54 +
            [10] * 10 +
            [60] * 6 +
            [10] * 10 +
            [122] * 2
        ),
    )


def get_hit_outcome() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.HitOutcome.NONE.value] * 37 +
            [MoveInfoEnums.HitOutcome.NORMAL_HIT_STANDING.value] * 27 +
            [MoveInfoEnums.HitOutcome.BLOCKED_STANDING.value] * 31 +
            [MoveInfoEnums.HitOutcome.NONE.value] * 10
        ),
        get_p2_data_offset()[0],
    )


def get_stun_type() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.StunStates.NONE.value] * 37 +
            [MoveInfoEnums.StunStates.GETTING_HIT.value] * 58 +
            [MoveInfoEnums.StunStates.NONE.value] * 10
        ),
        get_p2_data_offset()[0],
    )


def get_throw_tech() -> typing.List[int]:
    blocks = get_throw_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.ThrowTechs.BROKEN_ThrowTechs.value] * 30 +
            [MoveInfoEnums.ThrowTechs.TE2.value] * 120 +
            [MoveInfoEnums.ThrowTechs.BROKEN_ThrowTechs.value] * 29
        ),
        get_p2_data_offset()[0],
    )


def get_complex_move_state() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.ComplexMoveStates.F_MINUS.value] * 28 +
            [MoveInfoEnums.ComplexMoveStates.C_MINUS.value] * 9 +
            [MoveInfoEnums.ComplexMoveStates.END1.value] * 18 +
            [MoveInfoEnums.ComplexMoveStates.C_MINUS.value] * 9 +
            [MoveInfoEnums.ComplexMoveStates.END1.value] * 18 +
            [MoveInfoEnums.ComplexMoveStates.RECOVERING.value] * 10 +
            [MoveInfoEnums.ComplexMoveStates.F_MINUS.value] * 17
        ),
    )


def get_damage_taken() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [0] * 37 +
            [5] * 74
        ),
        get_p2_data_offset()[0],
    )


def get_input_attack() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.InputAttackCodes.N.value] * 28 +
            [MoveInfoEnums.InputAttackCodes.x1.value] * 10 +
            [MoveInfoEnums.InputAttackCodes.N.value] * 10 +
            [MoveInfoEnums.InputAttackCodes.x1.value] * 10 +
            [MoveInfoEnums.InputAttackCodes.N.value] * 40
        ),
    )


def get_input_direction() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [MoveInfoEnums.InputDirectionCodes.N.value] * 28 +
            [MoveInfoEnums.InputDirectionCodes.uf.value] * 20 +
            [MoveInfoEnums.InputDirectionCodes.db.value] * 20 +
            [MoveInfoEnums.InputDirectionCodes.N.value] * 10
        ),
    )


def get_attack_startup() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [0] * 28 +
            [10] * 54 +
            [0] * 17
        ),
    )


def get_char_id() -> typing.List[int]:
    blocks = get_choreographed_blocks()

    rollback_frame_offset = get_rollback_frame_offset()
    p2_offset = get_p2_data_offset()[0]
    for offset in range(0x100, 0x10000):
        if offset % 0x100 == 0:
            update_tk()
        p1_values = get_values_from_blocks(blocks, offset)

        if not all((i == MoveInfoEnums.CharacterCodes.JIN.value) for i in p1_values):
            continue

        p2_values = get_values_from_blocks(blocks, offset + p2_offset)

        if not all((i == MoveInfoEnums.CharacterCodes.KAZUYA.value) for i in p2_values):
            continue

        return [offset]

    raise Exception("get_char_id")


def get_move_timer() -> typing.List[int]:
    blocks = get_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            list(range(1, 28)) +
            list(range(1, 28)) +
            list(range(1, 11)) +
            list(range(1, 7)) +
            list(range(1, 11))
        ),
    )


def get_facing() -> typing.List[int]:
    blocks = get_throw_choreographed_blocks()
    return find_offset_from_expected(
        blocks,
        (
            [0] * 70 +
            [1] * 60
        ),
    )


def get_player_data_pointer_offset() -> typing.List[int]:
    pointers_map = get_pointers_map()
    move_id_address, _ = get_point_slope()

    address = move_id_address - get_move_id_offset()[0]

    sources = pointers_map.get(hex(address), [])

    if len(sources) == 0:
        raise Exception(f"get_player_data_pointer_offset {hex(address)} {len(pointers_map)}")  # nopep8

    def f(pointers: typing.List[int]) -> bool:
        address = get_game_reader().get_8_bytes_at_end_of_pointer_trail(pointers)
        value = get_game_reader().get_int_from_address(address, 4)
        return value == MoveInfoEnums.UniversalMoves.STANDING.value

    return get_pointer_offset(sources, 0x100, 5, f)


def get_opponent_side() -> typing.List[int]:
    # https://github.com/WAZAAAAA0/TekkenBot/issues/57#issuecomment-2087909057
    bytes_to_find_str = "01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 02 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 04 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 08 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 10 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 20 00 00 00 00 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40 00 00 00 40"
    bytes_to_find = list(map(lambda x: int(x, 16), bytes_to_find_str.split()))
    found_bytes = list(find_bytes(bytes(bytes_to_find[::-1])))
    if len(found_bytes) != 1:
        raise Exception(f"get_opponent_side {len(found_bytes)}")
    destination = found_bytes[0]
    address = destination[0] + destination[1]

    def f(pointers: typing.List[int]) -> bool:
        address = get_game_reader(
        ).get_8_bytes_at_end_of_pointer_trail(pointers[:-1])
        value = get_game_reader().get_block_of_data(
            address + pointers[-1], len(bytes_to_find))
        return value == bytes(bytes_to_find[::-1])

    return get_pointer_offset([address], 0x10, 2, f)


to_update: typing.List[typing.Tuple[typing.Tuple[str, str], typing.Callable[[], typing.List[int]]]] = [
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
]
