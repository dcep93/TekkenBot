from ..game_parser import GameSnapshot
from ..frame_data import Hook
from ..misc import Flags, Path, Windows

import configparser
import ctypes
import enum
import typing

game_string = 'Polaris-Win64-Shipping.exe'

class GameReader:
    def __init__(self) -> None:
        self.pid: typing.Optional[int] = None
        self.module_address: typing.Optional[int] = None
        self.process_handle: typing.Optional[int] = None
        self.in_match: bool = False
        self._c: configparser.ConfigParser = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        self._c.read(Path.path('config/memory_address.ini'))
        self.c: typing.Dict[str, typing.Dict[str, typing.List[int]]] = {k: {kk:list(map(lambda x: int(x, 16), vv.split())) for kk,vv in v.items()} for k,v in self._c.items()}

    def get_updated_state(self, rollback_frame: int) -> typing.Optional[GameSnapshot.GameSnapshot]:
        if not Windows.w.valid:
            raise Exception("Not windows - cannot update state")
        if not self.pid:
            self.reacquire_module()

        if self.process_handle is None:
            return None

        return self.get_game_snapshot(rollback_frame)
    
    def reacquire_module(self):
        self.pid = Windows.w.get_pid(game_string)
        if self.pid:
            print("Tekken pid acquired: %s" % self.pid)
        else:
            print("Tekken pid not acquired. Trying to acquire...")
            return
        self.module_address = Windows.w.get_module_address(self.pid, game_string)
        if self.module_address is None:
            print("%s not found. Likely wrong process id. Reacquiring pid." % game_string)
            self.pid = None
            return
        if self.module_address != self.c['MemoryAddressOffsets']['expected_module_address']:
            print("Tekken patch? enter practice mode as p1 and run $ python update_memory_address.py")
        else:
            print("Found %s" % game_string)
        self.process_handle = Windows.w.get_process_handle(self.pid)
        if not self.process_handle:
            print("Failed to acquire process_handle")

    def get_game_snapshot(self, rollback_frame: int) -> typing.Optional[GameSnapshot.GameSnapshot]:
        pointers = self.c['MemoryAddressOffsets']['player_data_pointer_offset']
        try:
            player_data_base_address = self.get_8_bytes_at_end_of_pointer_trail(pointers)
        except ReadProcessMemoryException:
            if self.in_match:
                Hook.finish_match()
            self.in_match = False
            return None

        if not self.in_match:
            Hook.start_match()
            self.in_match = True

        frame_count, player_data_frame = self.get_frame(player_data_base_address, rollback_frame)

        p1_dict = {}
        p2_dict = {}

        p2_offset = self.c['MemoryAddressOffsets']['p2_data_offset'][0]
        for name, values in self.c['PlayerDataAddress'].items():
            p1_value = self.get_4_bytes_from_data_block(player_data_frame, values[0])
            p2_value = self.get_4_bytes_from_data_block(player_data_frame, values[0] + p2_offset)
            p1_dict[name] = p1_value
            p2_dict[name] = p2_value

        p1_snapshot = GameSnapshot.PlayerSnapshot(p1_dict)
        p2_snapshot = GameSnapshot.PlayerSnapshot(p2_dict)

        is_player_player_one = self.get_8_bytes_at_end_of_pointer_trail(self.c['NonPlayerDataAddresses']["opponent_side"]) == 1

        if not is_player_player_one:
            p1_snapshot, p2_snapshot = p2_snapshot, p1_snapshot

        raw_facing = self.get_4_bytes_from_data_block(player_data_frame, self.c['GameDataAddress']['facing'][0])
        facing_bool = bool(raw_facing ^ is_player_player_one)

        return GameSnapshot.GameSnapshot(p1_snapshot, p2_snapshot, frame_count, facing_bool)

    def get_frame(self, player_data_base_address: int, rollback_frame: int) -> typing.Tuple[int, bytes]:
        rollback_frame_offset = self.c['MemoryAddressOffsets']['rollback_frame_offset'][0]
        
        frame_chunk = []

        frame_count = self.c['GameDataAddress']['frame_count'][0]
        for i in range(32):  # for rollback purposes, there are copies of the game state
            potential_second_address = player_data_base_address + (i * rollback_frame_offset)
            potential_frame_count = self.get_int_from_address(potential_second_address + frame_count, 4)
            frame_chunk.append((potential_frame_count, potential_second_address))

        best_frame_count, player_data_second_address = sorted(frame_chunk, key=lambda x: -x[0])[rollback_frame]

        player_data_frame = self.get_block_of_data(player_data_second_address, rollback_frame_offset)

        return best_frame_count, player_data_frame

    def get_block_of_data(self, address: int, size_of_block: int) -> bytes:
        data = ctypes.create_string_buffer(size_of_block)
        bytes_read = ctypes.c_ulonglong()
        successful = Windows.w.read_process_memory(
            self.process_handle,
            address,
            ctypes.byref(data),
            ctypes.sizeof(data),
            ctypes.byref(bytes_read),
        )
        if not successful:
            e = Windows.w.get_last_error()
            raise ReadProcessMemoryException("get_block_of_data Error: Code %s" % e)
        return data.raw

    def get_int_from_address(self, address: int, num_bytes: int) -> int:
        data = self.get_block_of_data(address, num_bytes)
        return int.from_bytes(data[::-1], 'little')

    def get_8_bytes_at_end_of_pointer_trail(self, trail: typing.List[int]) -> int:
        address = self.module_address
        assert(not address is None)
        for i, offset in enumerate(trail):
            address = self.get_int_from_address(address + offset, 8)
        return address

    @staticmethod
    def get_4_bytes_from_data_block(frame: bytes, offset: int) -> int:
        return int.from_bytes(frame[offset: offset + 4][::-1], 'little')

    def is_foreground_pid(self) -> bool:
        pid = Windows.w.get_foreground_pid()
        return pid == self.pid

    def get_window_rect(self) -> typing.Optional[typing.Any]:
        # see https://stackoverflow.com/questions/21175922/enumerating-windows-trough-ctypes-in-python for clues for doing this without needing focus using WindowsEnum
        if self.in_match and self.is_foreground_pid():
            return Windows.w.get_window_rect()
        else:
            return None

    def get_update_wait_ms(self, elapsed_ms: int) -> int:
        if self.in_match:
            wait_ms = max(2, 8 - int(round(elapsed_ms)))
        else:
            wait_ms = 1000
        return wait_ms

class ReadProcessMemoryException(Exception):
    pass
