import ctypes
import enum
import struct

from . import GameSnapshot, MoveInfoEnums
from frame_data import Hook
from misc import ConfigReader, Flags
from misc.Windows import w as Windows

# I have no idea how this file works

game_string = 'Polaris-Win64-Shipping.exe'

class AddressType(enum.Enum):
    _float = 0
    _64bit = 1
    _string = 2

class ReadProcessMemoryException(Exception):
    pass

class GameReader:
    def __init__(self):
        self.pid = None
        self.module_address = 0
        self.process_handle = None
        self.in_match = False
        self.c = ConfigReader.ConfigReader('memory_address')
        self.player_data_pointer_offset = self.c['MemoryAddressOffsets']['player_data_pointer_offset']

    def get_value_from_address(self, address, address_type):
        if address_type is AddressType._string:
            data = ctypes.create_string_buffer(16)
            bytes_read = ctypes.c_ulonglong(16)
        elif address_type is AddressType._64bit:
            data = ctypes.c_ulonglong()
            bytes_read = ctypes.c_ulonglong()
        else:
            data = ctypes.c_ulong()
            bytes_read = ctypes.c_ulonglong(4)

        successful = Windows.read_process_memory(self.process_handle, address, ctypes.byref(data), ctypes.sizeof(data), ctypes.byref(bytes_read))
        if not successful:
            e = Windows.get_last_error()
            # known problem of failing to read_process_memory
            # when not in a fight
            raise ReadProcessMemoryException("read_process_memory Error: Code %s" % e)

        value = data.value

        if address_type is AddressType._float:
            return struct.unpack("<f", value)[0]
        elif address_type is AddressType._string:
            try:
                return value.decode('utf-8')
            except:
                print("ERROR: Couldn't decode string from memory")
                return "ERROR"
        else:
            return int(value)

    def get_block_of_data(self, address, size_of_block):
        data = ctypes.create_string_buffer(size_of_block)
        bytes_read = ctypes.c_ulonglong(size_of_block)
        successful = Windows.read_process_memory(self.process_handle, address, ctypes.byref(data), ctypes.sizeof(data), ctypes.byref(bytes_read))
        if not successful:
            e = Windows.get_last_error()
            raise Exception("Getting Block of Data Error: Code %s" % e)
        return data

    @staticmethod
    def get_value_from_data_block(frame, offset, player_2_offset=0x0, is_float=False):
        address = offset + player_2_offset
        data_bytes = frame[address: address + 4]
        if is_float:
            return struct.unpack("<f", data_bytes)[0]
        else:
            return struct.unpack("<I", data_bytes)[0]

    def get_value_at_end_of_pointer_trail(self, data_type, address_type):
        addresses_str = self.c['NonPlayerDataAddresses'][data_type]
        addresses = split_str_to_hex(addresses_str)
        value = self.module_address
        for i, offset in enumerate(addresses):
            if i + 1 < len(addresses):
                value = self.get_value_from_address(value + offset, AddressType._64bit)
            else:
                value = self.get_value_from_address(value + offset, address_type)
        return value

    def is_foreground_pid(self):
        if not self.in_match:
            return False
        pid = Windows.get_foreground_pid()
        return pid == self.pid

    def get_window_rect(self):
        # see https://stackoverflow.com/questions/21175922/enumerating-windows-trough-ctypes-in-python for clues for doing this without needing focus using WindowsEnum
        if self.is_foreground_pid():
            rect = Windows.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(ctypes.windll.user32.GetForegroundWindow(), ctypes.byref(rect))
            return rect
        else:
            return None

    def has_working_pid(self):
        return self.pid is not None

    @staticmethod
    def is_data_a_float(data):
        return data in ('x', 'y', 'z', 'activebox_x', 'activebox_y', 'activebox_z')

    def get_updated_state(self, rollback_frame):
        if not Windows.valid:
            raise Exception("Not windows - cannot update state")
        if not self.has_working_pid():
            self.pid = Windows.get_pid(game_string)
            if self.has_working_pid():
                print("Tekken pid acquired: %s" % self.pid)
                self.reacquire_module()
            else:
                print("Tekken pid not acquired. Trying to acquire...")
                return None

        if self.process_handle is not None:
            return self.get_game_snapshot(rollback_frame)
        return None

    def get_update_wait_ms(self, elapsed_ms):
        if self.in_match:
            wait_ms = max(2, 8 - int(round(elapsed_ms)))
        else:
            wait_ms = 1000
        return wait_ms

    def get_game_snapshot(self, rollback_frame):
        try:
            player_data_base_address = self.get_player_data_base_address()
        except ReadProcessMemoryException:
            if self.in_match:
                Hook.finish_match()
            self.in_match = False
            return None

        if not self.in_match:
            Hook.start_match()
            self.in_match = True

        frame_chunk = self.get_frame_chunk(player_data_base_address)

        if rollback_frame >= len(frame_chunk):
            print("ERROR: requesting %s frame of %s long rollback frame" % (rollback_frame, len(frame_chunk)))
            return None

        best_frame_count, player_data_second_address = sorted(frame_chunk, key=lambda x: -x[0])[rollback_frame]

        player_data_frame = self.get_block_of_data(player_data_second_address, self.c['MemoryAddressOffsets']['rollback_frame_offset'])

        p1_dict = {}
        p2_dict = {}

        self.read_from_addresses(p1_dict, p2_dict, player_data_frame)

        p1_snapshot = GameSnapshot.PlayerSnapshot(p1_dict)
        p2_snapshot = GameSnapshot.PlayerSnapshot(p2_dict)

        is_player_player_one = self.get_value_at_end_of_pointer_trail("OPPONENT_SIDE", AddressType._64bit) == 1

        if not is_player_player_one:
            p1_snapshot, p2_snapshot = p2_snapshot, p1_snapshot

        facing_bool = bool(self.get_value_from_data_block(player_data_frame, self.c['GameDataAddress']['facing']) ^ is_player_player_one)

        return GameSnapshot.GameSnapshot(p1_snapshot, p2_snapshot, best_frame_count, facing_bool)

    def reacquire_module(self):
        print("Trying to acquire Tekken library in pid: %s" % self.pid)
        self.module_address = Windows.get_module_address(self.pid, game_string)
        if self.module_address is None:
            print("%s not found. Likely wrong process id. Reacquiring pid." % game_string)
            self.pid = None
            return
        if self.module_address != self.c['MemoryAddressOffsets']['expected_module_address']:
            print("Unrecognized location for %s module. Tekken.exe Patch? Wrong process id?" % game_string, hex(self.module_address))
        else:
            print("Found %s" % game_string)
        self.process_handle = Windows.open_process(0x10, False, self.pid)
        if not self.process_handle:
            print("Failed to acquire process_handle")

    def get_player_data_base_address(self):
        offsets = split_str_to_hex(self.player_data_pointer_offset)
        address = self.module_address
        for i, offset in enumerate(offsets):
            address = self.get_value_from_address(address+offset, AddressType._64bit)
        return address

    def get_frame_chunk(self, player_data_base_address):
        frame_chunk = []

        offset = self.c['MemoryAddressOffsets']['rollback_frame_offset']
        frame_count = self.c['GameDataAddress']['frame_count']
        for i in range(32):  # for rollback purposes, there are copies of the game state
            potential_second_address = player_data_base_address + (i * offset)
            potential_frame_count = self.get_value_from_address(potential_second_address + frame_count, None)
            frame_chunk.append((potential_frame_count, potential_second_address))
        return frame_chunk

    def read_from_addresses(self, p1_dict, p2_dict, player_data_frame):
        for data_type, value in self.c['PlayerDataAddress'].items():
            p1_value = self.get_value_from_data_block(player_data_frame, value, 0, self.is_data_a_float(data_type))
            p2_value = self.get_value_from_data_block(player_data_frame, value, self.c['MemoryAddressOffsets']['p2_data_offset'], self.is_data_a_float(data_type))
            address = 'PlayerDataAddress.%s' % data_type
            p1_dict[address] = p1_value
            p2_dict[address] = p2_value

        position_offset = 32  # our xyz coordinate is 32 bytes, a 4 byte x, y, and z value followed by five 4 byte values that don't change
        for axis, starting_address in ((k, v) for k, v in self.c['PlayerDataAddress'].items() if k in ('x', 'y', 'z')):
            p1_coord_array = []
            p2_coord_array = []
            for i in range(23):
                address = starting_address + (i * position_offset)
                p1_coord_array.append(self.get_value_from_data_block(player_data_frame, address, 0, is_float=True))
                p2_coord_array.append(self.get_value_from_data_block(player_data_frame, address, self.c['MemoryAddressOffsets']['p2_data_offset'], is_float=True))
            address = 'PlayerDataAddress.%s' % axis
            p1_dict[address] = p1_coord_array
            p2_dict[address] = p2_coord_array

def split_str_to_hex(string):
    return list(map(to_hex, string.split()))

def to_hex(x):
    return int(x, 16)
