import ctypes
import enum
import struct

from . import GameSnapshot, MoveInfoEnums
from game_parser import MovelistParser
from misc import ConfigReader, Flags
from misc.Windows import w as Windows

game_string = 'TekkenGame-Win64-Shipping.exe'

class AddressType(enum.Enum):
    _float = 0
    _64bit = 1
    _string = 2

class AcquireState(enum.Enum):
    need_pid = 0
    need_module = 1
    need_names = 2
    has_everything = 3

class GameReader:
    def __init__(self):
        self.acquire_state = AcquireState.need_pid
        self.pid = None
        self.module_address = 0
        self.original_facing = None
        self.is_player_player_one = None
        self.c = ConfigReader.ReloadableConfig('memory_address')
        self.player_data_pointer_offset = self.c['MemoryAddressOffsets']['player_data_pointer_offset']
        self.p1_movelist_parser = None
        self.p2_movelist_parser = None

    def get_value_from_address(self, process_handle, address, address_type):
        if address_type is AddressType._string:
            data = ctypes.create_string_buffer(16)
            bytes_read = ctypes.c_ulonglong(16)
        elif address_type is AddressType._64bit:
            data = ctypes.c_ulonglong()
            bytes_read = ctypes.c_ulonglong()
        else:
            data = ctypes.c_ulong()
            bytes_read = ctypes.c_ulonglong(4)

        successful = Windows.read_process_memory(process_handle, address, ctypes.byref(data), ctypes.sizeof(data), ctypes.byref(bytes_read))
        if not successful:
            e = Windows.get_last_error()
            # known problem of failing to read_process_memory
            # when not in a fight
            if not (e == 299 and self.acquire_state == AcquireState.need_names):
                print("read_process_memory Error: Code %s" % e)
            return 0

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

    @staticmethod
    def get_block_of_data(process_handle, address, size_of_block):
        data = ctypes.create_string_buffer(size_of_block)
        bytes_read = ctypes.c_ulonglong(size_of_block)
        successful = Windows.read_process_memory(process_handle, address, ctypes.byref(data), ctypes.sizeof(data), ctypes.byref(bytes_read))
        if not successful:
            e = Windows.get_last_error()
            print("Getting Block of Data Error: Code %s" % e)
        return data

    @staticmethod
    def get_value_from_data_block(frame, offset, player_2_offset=0x0, is_float=False):
        address = offset + player_2_offset
        data_bytes = frame[address: address + 4]
        if is_float:
            return struct.unpack("<f", data_bytes)[0]
        else:
            return struct.unpack("<I", data_bytes)[0]

    def get_value_at_end_of_pointer_trail(self, process_handle, data_type, address_type):
        addresses_str = self.c['NonPlayerDataAddresses'][data_type]
        addresses = split_str_to_hex(addresses_str)
        value = self.module_address
        for i, offset in enumerate(addresses):
            if i + 1 < len(addresses):
                value = self.get_value_from_address(process_handle, value + offset, AddressType._64bit)
            else:
                value = self.get_value_from_address(process_handle, value + offset, address_type)
        return value

    def is_foreground_pid(self):
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
        if not self.has_working_pid():
            if not Windows.valid:
                print("not windows?")
                return None
            self.pid = Windows.get_pid(game_string)
            if self.has_working_pid():
                print("Tekken pid acquired: %s" % self.pid)
                self.acquire_state = AcquireState.need_module
            else:
                print("Tekken pid not acquired. Trying to acquire...")
                return None

        if self.acquire_state == AcquireState.need_module:
            self.reacquire_module()

        if self.module_address is not None:
            process_handle = Windows.open_process(0x10, False, self.pid)
            try:
                return self.get_game_snapshot(rollback_frame, process_handle)
            finally:
                Windows.close_handle(process_handle)

        return None

    def get_update_wait_ms(self, elapsed_ms):
        if self.acquire_state == AcquireState.has_everything:
            elapsed_time = 1000 * elapsed_ms
            wait_ms = max(2, 8 - int(round(elapsed_time)))
        else:
            wait_ms = 1000
        return wait_ms

    def get_game_snapshot(self, rollback_frame, process_handle):
        player_data_base_address = self.get_player_data_base_address(process_handle)

        if player_data_base_address == 0:
            self.acquire_state = AcquireState.need_names
            return None

        last_eight_frames = self.get_last_eight_frames(process_handle, player_data_base_address)

        if rollback_frame >= len(last_eight_frames):
            print("ERROR: requesting %s frame of %s long rollback frame" % (rollback_frame, len(last_eight_frames)))
            return None

        best_frame_count, player_data_second_address = sorted(last_eight_frames, key=lambda x: -x[0])[rollback_frame]

        player_data_frame = self.get_block_of_data(process_handle, player_data_second_address, self.c['MemoryAddressOffsets']['rollback_frame_offset'])

        p1_dict = {}
        p2_dict = {}

        self.read_from_addresses(p1_dict, p2_dict, player_data_frame)

        p1_snapshot = GameSnapshot.PlayerSnapshot(p1_dict)
        p2_snapshot = GameSnapshot.PlayerSnapshot(p2_dict)

        facing = self.get_value_from_data_block(player_data_frame, self.c['GameDataAddress']['facing'])
        if self.original_facing is None and best_frame_count > 0:
            self.original_facing = facing > 0

        if self.acquire_state == AcquireState.need_names and p1_snapshot.character_name != MoveInfoEnums.CharacterCodes.NOT_YET_LOADED.name and p2_snapshot.character_name != MoveInfoEnums.CharacterCodes.NOT_YET_LOADED.name:
            self.reacquire_names(process_handle)

        timer_in_frames = self.get_value_from_data_block(player_data_frame, self.c['GameDataAddress']['timer_in_frames'])
        return GameSnapshot.GameSnapshot(p1_snapshot, p2_snapshot, best_frame_count, timer_in_frames, facing, self.is_player_player_one)

    def reacquire_module(self):
        print("Trying to acquire Tekken library in pid: %s" % self.pid)
        self.module_address = Windows.get_module_address(self.pid, game_string)
        if self.module_address is None:
            print("%s not found. Likely wrong process id. Reacquiring pid." % game_string)
            self.pid = None
        elif self.module_address != self.c['MemoryAddressOffsets']['expected_module_address']:
            print("Unrecognized location for %s module. Tekken.exe Patch? Wrong process id?" % game_string)
        else:
            print("Found %s" % game_string)
            self.acquire_state = AcquireState.need_names

    def get_player_data_base_address(self, process_handle):
        addresses = split_str_to_hex(self.player_data_pointer_offset)
        address = self.module_address
        for i, offset in enumerate(addresses):
            address += offset
            if i + 1 < len(addresses):
                address = self.get_value_from_address(process_handle, address, AddressType._64bit)
            else:
                address = self.get_value_from_address(process_handle, address, None)
        return address

    def get_last_eight_frames(self, process_handle, player_data_base_address):
        last_eight_frames = []

        second_address_base = self.get_value_from_address(process_handle, player_data_base_address, AddressType._64bit)
        offset = self.c['MemoryAddressOffsets']['rollback_frame_offset']
        frame_count = self.c['GameDataAddress']['frame_count']
        for i in range(8):  # for rollback purposes, there are 8 copies of the game state, each one updatating once every 8 frames
            potential_second_address = second_address_base + (i * offset)
            potential_frame_count = self.get_value_from_address(process_handle, potential_second_address + frame_count, None)
            last_eight_frames.append((potential_frame_count, potential_second_address))
        return last_eight_frames

    def read_from_addresses(self, p1_dict, p2_dict, player_data_frame):
        for data_type, value in self.c['PlayerDataAddress'].items():
            p1_value = self.get_value_from_data_block(player_data_frame, value, 0, self.is_data_a_float(data_type))
            p2_value = self.get_value_from_data_block(player_data_frame, value, self.c['MemoryAddressOffsets']['p2_data_offset'], self.is_data_a_float(data_type))
            address = 'PlayerDataAddress.%s' % data_type
            p1_dict[address] = p1_value
            p2_dict[address] = p2_value

        for data_type, value in self.c['EndBlockPlayerDataAddress'].items():
            p1_value = self.get_value_from_data_block(player_data_frame, value)
            p2_value = self.get_value_from_data_block(player_data_frame, value, self.c['MemoryAddressOffsets']['p2_end_block_offset'])
            address = 'EndBlockPlayerDataAddress.%s' % data_type
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

        p1_dict['movelist_parser'] = self.p1_movelist_parser
        p2_dict['movelist_parser'] = self.p2_movelist_parser

    def reacquire_names(self, process_handle):
        if not Flags.Flags.no_movelist:
            opponent_side = self.get_value_at_end_of_pointer_trail(process_handle, "OPPONENT_SIDE", False)
            self.is_player_player_one = (opponent_side == 1)

            p1_movelist_block, p1_movelist_address = self.populate_movelists(process_handle, "P1_Movelist")
            p2_movelist_block, p2_movelist_address = self.populate_movelists(process_handle, "P2_Movelist")

            self.p1_movelist_parser = MovelistParser.MovelistParser(p1_movelist_block, p1_movelist_address)
            self.p2_movelist_parser = MovelistParser.MovelistParser(p2_movelist_block, p2_movelist_address)

        self.acquire_state = AcquireState.has_everything
        print("acquired movelist")

    def populate_movelists(self, process_handle, data_type):
        movelist_str = self.c["NonPlayerDataAddresses"][data_type]
        movelist_trail = split_str_to_hex(movelist_str)

        movelist_address = self.get_value_from_address(process_handle, self.module_address + movelist_trail[0], AddressType._64bit)
        movelist_block = self.get_block_of_data(process_handle, movelist_address, self.c["MemoryAddressOffsets"]["movelist_size"])

        return movelist_block, movelist_address

def split_str_to_hex(string):
    return list(map(to_hex, string.split()))

def to_hex(x):
    return int(x, 16)
