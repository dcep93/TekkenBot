"""
This module's classes are responsible for reading and interpreting the memory of a Tekken7.exe proecess.

TekkenGameReader reads the memory of Tekken7.exe, extracts information about the state of the game, then saves a
'snapshot' of each frame.

Each GameSnapshot has 2 BotSnapshots, together encapsulating the information of both players and shared data for a single game frame.

TekkenGameState saves these snapshots and provides an api that abstracts away the difference
between questions that query one player (is player 1 currently attacking?), both players (what is the expected frame
advantage when player 2 emerges from block), or multiple game states over time (did player 1 just begin to block this
frame?, what was the last move player 2 did?).

"""

import collections
import ctypes
import enum
import math
import struct

import windows.PIDSearcher
from . import MoveInfoEnums
import misc.ConfigReader
from . import MoveDataReport
from  game_parser import MovelistParser
from . import ModuleEnumerator

import windows

game_string = 'TekkenGame-Win64-Shipping.exe'

class Player(object):
    def __init__(self):
        self.movelist = []
        self.movelist_to_use = None
        self.movelist_parser = None

class AddressType(enum.Enum):
    _float = 0
    _64bit = 1
    _string = 2

class TekkenGameReader:
    def __init__(self):
        self.ReacquireEverything()
        self.module_address = 0
        self.original_facing = None
        self.opponent_name = None
        self.is_player_player_one = None
        self.c = misc.ConfigReader.ReloadableConfig('memory_address')
        self.player_data_pointer_offset = self.c['MemoryAddressOffsets']['player_data_pointer_offset']
        self.p1 = Player()
        self.p2 = Player()

    def ReacquireEverything(self):
        self.needReacquireModule = True
        self.needReaquireGameState = True
        self.flagToReacquireNames = True
        self.pid = None

    def GetValueFromAddress(self, processHandle, address, address_type):
        if address_type is AddressType._string:
            data = ctypes.create_string_buffer(16)
            bytesRead = ctypes.c_ulonglong(16)
        elif address_type is AddressType._64bit:
            data = ctypes.c_ulonglong()
            bytesRead = ctypes.c_ulonglong()
        else:
            data = ctypes.c_ulong()
            bytesRead = ctypes.c_ulonglong(4)

        successful = windows.w.ReadProcessMemory(processHandle, address, ctypes.byref(data), ctypes.sizeof(data), ctypes.byref(bytesRead))
        if not successful:
            e = windows.w.GetLastError()
            print("ReadProcessMemory Error: Code %s" % e)
            self.ReacquireEverything()

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

    def GetBlockOfData(self, processHandle, address, size_of_block):
        data = ctypes.create_string_buffer(size_of_block)
        bytesRead = ctypes.c_ulonglong(size_of_block)
        successful = windows.w.ReadProcessMemory(processHandle, address, ctypes.byref(data), ctypes.sizeof(data), ctypes.byref(bytesRead))
        if not successful:
            e = windows.w.GetLastError()
            print("Getting Block of Data Error: Code " + str(e))
        return data

    def GetValueFromDataBlock(self, frame, offset, player_2_offset=0x0, is_float=False): # player_2_offset = 0x0
        address = offset + player_2_offset
        data_bytes = frame[address: address + 4]
        if is_float:
            return struct.unpack("<f", data_bytes)[0]
        else:
            return struct.unpack("<I", data_bytes)[0]

    def GetValueAtEndOfPointerTrail(self, processHandle, data_type, address_type):
        addresses_str = self.c['NonPlayerDataAddresses'][data_type]
        # The pointer trail is stored as a string of addresses in hex in the config. Split them up and convert
        addresses = list(map(to_hex, addresses_str.split()))
        value = self.module_address
        for i, offset in enumerate(addresses):
            if i + 1 < len(addresses):
                value = self.GetValueFromAddress(processHandle, value + offset, AddressType._64bit)
            else:
                value = self.GetValueFromAddress(processHandle, value + offset, address_type)
        return value

    def IsForegroundPID(self):
        pid = windows.PIDSearcher.GetForegroundPid()
        return pid == self.pid

    def GetWindowRect(self):
        #see https://stackoverflow.com/questions/21175922/enumerating-windows-trough-ctypes-in-python for clues for doing this without needing focus using WindowsEnum
        if self.IsForegroundPID():
            rect = ctypes.wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(ctypes.windll.user32.GetForegroundWindow(), ctypes.byref(rect))
            return rect
        else:
            return None

    def HasWorkingPID(self):
        return self.pid is not None

    def IsDataAFloat(self, data):
        return data in ('x', 'y', 'z', 'activebox_x', 'activebox_y', 'activebox_z')

    def GetUpdatedState(self, rollback_frame = 0):
        if not self.HasWorkingPID():
            self.pid = windows.PIDSearcher.GetPIDByName(game_string)
            if self.HasWorkingPID():
                print("Tekken pid acquired: %s" % self.pid)
            else:
                print("Tekken pid not acquired. Trying to acquire...")
                return None

        if self.needReacquireModule:
            self.reacquire_module()

        if self.module_address != None:
            processHandle = windows.w.OpenProcess(0x10, False, self.pid)
            try:
                return self.get_game_snapshot(rollback_frame, processHandle)
            finally:
                windows.w.CloseHandle(processHandle)

        return None

    def get_game_snapshot(self, rollback_frame, processHandle):
        player_data_base_address = self.get_player_data_base_address(processHandle)
        
        if player_data_base_address == 0:
            if not self.needReaquireGameState:
                print("No fight detected. Gamestate not updated.")
            self.needReaquireGameState = True
            self.flagToReacquireNames = True

            return None

        last_eight_frames = self.get_last_eight_frames(processHandle, player_data_base_address)

        if rollback_frame >= len(last_eight_frames):
            print("ERROR: requesting %s frame of %s long rollback frame" % (rollback_frame, len(last_eight_frames)))
            rollback_frame = len(last_eight_frames) - 1

        best_frame_count, player_data_second_address = sorted(last_eight_frames, key=lambda x: -x[0])[rollback_frame]

        player_data_frame = self.GetBlockOfData(processHandle, player_data_second_address, self.c['MemoryAddressOffsets']['rollback_frame_offset'])

        p1_bot = BotSnapshot()
        p2_bot = BotSnapshot()

        self.read_from_addresses(p1_bot, p2_bot, player_data_frame)

        bot_facing = self.GetValueFromDataBlock(player_data_frame, self.c['GameDataAddress']['facing'])
        if self.original_facing is None and best_frame_count > 0:
            self.original_facing = bot_facing > 0

        if self.needReaquireGameState:
            print("Fight detected. Updating gamestate.")
        self.needReaquireGameState = False

        p1_bot.Bake()
        p2_bot.Bake()

        if self.flagToReacquireNames and p1_bot.character_name != MoveInfoEnums.CharacterCodes.NOT_YET_LOADED.name and p2_bot.character_name != MoveInfoEnums.CharacterCodes.NOT_YET_LOADED.name:
            self.reacquire_names(processHandle, p1_bot, p2_bot)

        timer_in_frames = self.GetValueFromDataBlock(player_data_frame, self.c['GameDataAddress']['timer_in_frames'])
        return GameSnapshot(p1_bot, p2_bot, best_frame_count, timer_in_frames, bot_facing, self.opponent_name, self.is_player_player_one)

    def reacquire_module(self):
        print("Trying to acquire Tekken library in pid: %s" % self.pid)
        self.module_address = ModuleEnumerator.GetModuleAddressByPIDandName(self.pid, game_string)
        if self.module_address == None:
            print("%s not found. Likely wrong process id. Reacquiring pid." % game_string)
            self.ReacquireEverything()
        elif(self.module_address != self.c['MemoryAddressOffsets']['expected_module_address']):
            print("Unrecognized location for %s module. Tekken.exe Patch? Wrong process id?" % game_string)
        else:
            print("Found %s" % game_string)
            self.needReacquireModule = False

    def get_player_data_base_address(self, processHandle):
        addresses = list(map(to_hex, self.player_data_pointer_offset.split()))
        address = self.module_address
        for i, offset in enumerate(addresses):
            address += offset
            if i + 1 < len(addresses):
                address = self.GetValueFromAddress(processHandle, address, AddressType._64bit)
            else:
                address = self.GetValueFromAddress(processHandle, address, None)
        return address

    def get_last_eight_frames(self, processHandle, player_data_base_address):
        last_eight_frames = []

        second_address_base = self.GetValueFromAddress(processHandle, player_data_base_address, AddressType._64bit)
        offset = self.c['MemoryAddressOffsets']['rollback_frame_offset']
        frame_count = self.c['GameDataAddress']['frame_count']
        for i in range(8):  # for rollback purposes, there are 8 copies of the game state, each one updatating once every 8 frames
            potential_second_address = second_address_base + (i * offset)
            potential_frame_count = self.GetValueFromAddress(processHandle, potential_second_address + frame_count, None)
            last_eight_frames.append((potential_frame_count, potential_second_address))
        return last_eight_frames

    def read_from_addresses(self, p1_bot, p2_bot, player_data_frame):
        for data_type, value in self.c['PlayerDataAddress'].items():
            p1_value = self.GetValueFromDataBlock(player_data_frame, value, 0, self.IsDataAFloat(data_type))
            p2_value = self.GetValueFromDataBlock(player_data_frame, value, self.c['MemoryAddressOffsets']['p2_data_offset'], self.IsDataAFloat(data_type))
            address = 'PlayerDataAddress.%s' % data_type
            p1_bot.player_data_dict[address] = p1_value
            p2_bot.player_data_dict[address] = p2_value

        for data_type, value in self.c['EndBlockPlayerDataAddress'].items():
            p1_value = self.GetValueFromDataBlock(player_data_frame, value)
            p2_value = self.GetValueFromDataBlock(player_data_frame, value, self.c['MemoryAddressOffsets']['p2_end_block_offset'])
            address = 'EndBlockPlayerDataAddress.%s' % data_type
            p1_bot.player_data_dict[address] = p1_value
            p2_bot.player_data_dict[address] = p2_value

        for axis, startingAddress in ((k, v) for k,v in self.c['PlayerDataAddress'].items() if k in ('x', 'y', 'z')):
            positionOffset = 32  # our xyz coordinate is 32 bytes, a 4 byte x, y, and z value followed by five 4 byte values that don't change
            p1_coord_array = []
            p2_coord_array = []
            for i in range(23):
                address = startingAddress + (i * positionOffset)
                p1_coord_array.append(self.GetValueFromDataBlock(player_data_frame, address, 0, is_float=True))
                p2_coord_array.append(self.GetValueFromDataBlock(player_data_frame, address, self.c['MemoryAddressOffsets']['p2_data_offset'], is_float=True))
            address = 'PlayerDataAddress.%s' % axis
            p1_bot.player_data_dict[address] = p1_coord_array
            p2_bot.player_data_dict[address] = p2_coord_array

        # FIXME: This seems like it would always be true.
        # The old code seems to be doing the same, so I don't know.
        p1_bot.player_data_dict['use_opponent_movelist'] = p1_bot.player_data_dict['PlayerDataAddress.movelist_to_use'] == self.p2.movelist_to_use
        p2_bot.player_data_dict['use_opponent_movelist'] = p2_bot.player_data_dict['PlayerDataAddress.movelist_to_use'] == self.p1.movelist_to_use

        p1_bot.player_data_dict['movelist_parser'] = self.p1.movelist_parser
        p2_bot.player_data_dict['movelist_parser'] = self.p2.movelist_parser

    def reacquire_names(self, processHandle, p1_bot, p2_bot):
        self.opponent_name = self.GetValueAtEndOfPointerTrail(processHandle, "OPPONENT_NAME", True)
        self.opponent_side = self.GetValueAtEndOfPointerTrail(processHandle, "OPPONENT_SIDE", False)
        self.is_player_player_one = (self.opponent_side == 1)

        self.p1.movelist_to_use = p1_bot.player_data_dict['PlayerDataAddress.movelist_to_use']
        self.p2.movelist_to_use = p2_bot.player_data_dict['PlayerDataAddress.movelist_to_use']

        self.p1.movelist_block, p1_movelist_address = self.PopulateMovelists(processHandle, "P1_Movelist")
        self.p2.movelist_block, p2_movelist_address = self.PopulateMovelists(processHandle, "P2_Movelist")

        self.p1.movelist_parser = MovelistParser.MovelistParser(self.p1.movelist_block, p1_movelist_address)
        self.p2.movelist_parser = MovelistParser.MovelistParser(self.p2.movelist_block, p2_movelist_address)

        self.p1.movelist_names = self.p1.movelist_block[0x2E8:200000].split(b'\00') #Todo: figure out the actual size of the name movelist
        self.p2.movelist_names = self.p2.movelist_block[0x2E8:200000].split(b'\00')

        self.flagToReacquireNames = False
        print("acquired")

    def PopulateMovelists(self, processHandle, data_type):
        movelist_str = self.c["NonPlayerDataAddresses"][data_type]
        movelist_trail = list(map(to_hex, movelist_str.split()))

        movelist_address = self.GetValueFromAddress(processHandle, self.module_address + movelist_trail[0], AddressType._64bit)
        movelist_block = self.GetBlockOfData(processHandle, movelist_address, self.c["MemoryAddressOffsets"]["movelist_size"])

        return movelist_block, movelist_address

    def GetNeedReacquireState(self):
        return self.needReaquireGameState

class BotSnapshot:
    def __init__(self):
        self.player_data_dict = {}

    def Bake(self):
        d = self.player_data_dict
        self.move_id = d['PlayerDataAddress.move_id']
        self.simple_state = MoveInfoEnums.SimpleMoveStates(d['PlayerDataAddress.simple_move_state'])
        self.attack_type = MoveInfoEnums.AttackType(d['PlayerDataAddress.attack_type'])
        self.startup = d['PlayerDataAddress.attack_startup']
        self.startup_end = d['PlayerDataAddress.attack_startup_end']
        self.attack_damage = d['PlayerDataAddress.attack_damage']
        self.complex_state = MoveInfoEnums.ComplexMoveStates(d['PlayerDataAddress.complex_move_state'])
        self.damage_taken = d['PlayerDataAddress.damage_taken']
        self.move_timer = d['PlayerDataAddress.move_timer']
        self.recovery = d['PlayerDataAddress.recovery']
        self.char_id = d['PlayerDataAddress.char_id']
        self.throw_flag = d['PlayerDataAddress.throw_flag']
        self.rage_flag = d['PlayerDataAddress.rage_flag']
        self.input_counter = d['PlayerDataAddress.input_counter']
        self.input_direction = MoveInfoEnums.InputDirectionCodes(d['PlayerDataAddress.input_direction'])
        self.input_button = MoveInfoEnums.InputAttackCodes(d['PlayerDataAddress.input_attack'] % MoveInfoEnums.InputAttackCodes.xRAGE.value)
        self.rage_button_flag = d['PlayerDataAddress.input_attack'] >= MoveInfoEnums.InputAttackCodes.xRAGE.value
        self.stun_state = MoveInfoEnums.StunStates(d['PlayerDataAddress.stun_type'])
        self.power_crush_flag = d['PlayerDataAddress.power_crush'] > 0

        cancel_window_bitmask = d['PlayerDataAddress.cancel_window']
        recovery_window_bitmask = d['PlayerDataAddress.recovery']

        self.is_cancelable = (MoveInfoEnums.CancelStatesBitmask.CANCELABLE.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.CANCELABLE.value
        self.is_bufferable = (MoveInfoEnums.CancelStatesBitmask.BUFFERABLE.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.BUFFERABLE.value
        self.is_parry_1 = (MoveInfoEnums.CancelStatesBitmask.PARRYABLE_1.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.PARRYABLE_1.value
        self.is_parry_2 = (MoveInfoEnums.CancelStatesBitmask.PARRYABLE_2.value & cancel_window_bitmask) == MoveInfoEnums.CancelStatesBitmask.PARRYABLE_2.value
        
        self.is_recovering = (MoveInfoEnums.ComplexMoveStates.RECOVERING.value & recovery_window_bitmask) == MoveInfoEnums.ComplexMoveStates.RECOVERING.value
        
        if self.startup > 0:
            self.is_starting = (self.move_timer <= self.startup)
        else:
            self.is_starting = False

        self.throw_tech = MoveInfoEnums.ThrowTechs(d['PlayerDataAddress.throw_tech'])

        self.skeleton = (d['PlayerDataAddress.x'], d['PlayerDataAddress.y'], d['PlayerDataAddress.z'])

        self.active_xyz = (d['PlayerDataAddress.activebox_x'], d['PlayerDataAddress.activebox_y'], d['PlayerDataAddress.activebox_z'])

        self.is_jump = d['PlayerDataAddress.jump_flags'] & MoveInfoEnums.JumpFlagBitmask.JUMP.value == MoveInfoEnums.JumpFlagBitmask.JUMP.value
        self.hit_outcome = MoveInfoEnums.HitOutcome(d['PlayerDataAddress.hit_outcome'])
        self.mystery_state = d['PlayerDataAddress.mystery_state']

        self.wins = d['EndBlockPlayerDataAddress.round_wins']
        self.combo_counter = d['EndBlockPlayerDataAddress.display_combo_counter']
        self.combo_damage = d['EndBlockPlayerDataAddress.display_combo_damage']
        self.juggle_damage = d['EndBlockPlayerDataAddress.display_juggle_damage']

        self.use_opponents_movelist = d['use_opponent_movelist']
        self.movelist_parser = d['movelist_parser']

        try:
            self.character_name = CharacterCodes(d['PlayerDataAddress.char_id']).name
        except:
            self.character_name = "UNKNOWN"


    def PrintYInfo(self):
        print('{:.4f}, {:.4f}, {:.4f}'.format(self.highest_y, self.lowest_y, self.highest_y - self.lowest_y))

    def GetInputState(self):
        return (self.input_direction, self.input_button, self.rage_button_flag)

    def GetTrackingType(self):
        return self.complex_state

    def IsBlocking(self):
        return self.complex_state == ComplexMoveStates.BLOCK

    def IsGettingCounterHit(self):
        return self.hit_outcome in (HitOutcome.COUNTER_HIT_CROUCHING, HitOutcome.COUNTER_HIT_STANDING)

    def IsGettingGroundHit(self):
        return self.hit_outcome in (HitOutcome.GROUNDED_FACE_DOWN, HitOutcome.GROUNDED_FACE_UP)

    def IsGettingWallSplatted(self):
        return self.simple_state in (MoveInfoEnums.SimpleMoveStates.WALL_SPLAT_18, MoveInfoEnums.SimpleMoveStates.WALL_SPLAT_19)

    def IsGettingHit(self):
        return self.stun_state in (StunStates.BEING_PUNISHED, StunStates.GETTING_HIT)

    def IsHitting(self):
        return self.stun_state == StunStates.DOING_THE_HITTING

    def IsPunish(self):
        return self.stun_state == StunStates.BEING_PUNISHED

    def IsAttackMid(self):
        return self.attack_type == MoveInfoEnums.AttackType.MID

    def IsAttackUnblockable(self):
        return self.attack_type in {MoveInfoEnums.AttackType.HIGH_UNBLOCKABLE, MoveInfoEnums.AttackType.LOW_UNBLOCKABLE, MoveInfoEnums.AttackType.MID_UNBLOCKABLE}

    def IsAttackAntiair(self):
        return self.attack_type == MoveInfoEnums.AttackType.ANTIAIR_ONLY

    def IsAttackThrow(self):
        return self.throw_flag == 1

    def IsAttackLow(self):
        return self.attack_type == MoveInfoEnums.AttackType.LOW

    def IsInThrowing(self):
        return self.attack_type == MoveInfoEnums.AttackType.THROW

    def GetActiveFrames(self):
        return self.startup_end - self.startup + 1

    def IsAttackWhiffing(self):
        return self.complex_state in {ComplexMoveStates.END1, ComplexMoveStates.F_MINUS, ComplexMoveStates.RECOVERING, ComplexMoveStates.UN17, ComplexMoveStates.SS, ComplexMoveStates.WALK}

    def IsOnGround(self):
        return self.simple_state in {MoveInfoEnums.SimpleMoveStates.GROUND_FACEDOWN, MoveInfoEnums.SimpleMoveStates.GROUND_FACEUP}

    def IsBeingJuggled(self):
        return self.simple_state == MoveInfoEnums.SimpleMoveStates.JUGGLED

    def IsAirborne(self):
        return self.simple_state == MoveInfoEnums.SimpleMoveStates.AIRBORNE

    def IsHoldingUp(self):
        return self.input_direction == InputDirectionCodes.u

    def IsHoldingUpBack(self):
        return self.input_direction == InputDirectionCodes.ub

    def IsTechnicalCrouch(self):
        return self.simple_state in (MoveInfoEnums.SimpleMoveStates.CROUCH, MoveInfoEnums.SimpleMoveStates.CROUCH_BACK, MoveInfoEnums.SimpleMoveStates.CROUCH_FORWARD)

    def IsTechnicalJump(self):
        return self.is_jump

    def IsHoming1(self):
        return self.complex_state == ComplexMoveStates.S_PLUS

    def IsHoming2(self):
        return self.complex_state == ComplexMoveStates.S

    def IsPowerCrush(self):
        return self.power_crush_flag

    def IsBeingKnockedDown(self):
        return self.simple_state == MoveInfoEnums.SimpleMoveStates.KNOCKDOWN

    def IsWhileStanding(self):
        return (self.simple_state in {MoveInfoEnums.SimpleMoveStates.CROUCH, MoveInfoEnums.SimpleMoveStates.CROUCH_BACK, MoveInfoEnums.SimpleMoveStates.CROUCH_FORWARD})

    def IsWallSplat(self):
        return self.move_id == 2396 or self.move_id == 2387 or self.move_id == 2380 or self.move_id == 2382 #TODO: use the wall splat states in ComplexMoveStates #move ids may be different for 'big' characters

    def IsInRage(self):
        return self.rage_flag > 0

    def IsAbleToAct(self):
        return self.is_cancelable

    def IsParryable1(self):
        return self.is_parry_1

    def IsParryable2(self):
        return self.is_parry_2

    def IsBufferable(self):
        return self.is_bufferable

    def IsAttackStarting(self):
        if self.startup > 0:
            return self.move_timer <= self.startup
        else:
            return False


class GameSnapshot:
    def __init__(self, bot, opp, frame_count, timer_in_frames, facing_bool, opponent_name, is_player_player_one):
        self.bot = bot
        self.opp = opp
        self.frame_count = frame_count
        self.facing_bool = facing_bool
        self.timer_frames_remaining = timer_in_frames
        self.opponent_name = opponent_name
        self.is_player_player_one = is_player_player_one

    def FromMirrored(self):
        return GameSnapshot(self.opp, self.bot, self.frame_count, self.timer_frames_remaining, self.facing_bool, self.opponent_name, self.is_player_player_one)

def to_hex(x):
    return int(x, 16)
