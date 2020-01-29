import enum
import collections
import struct

from . import MoveInfoEnums

class MoveNode:
    def __init__(self, forty_bytes, offset, all_bytes, all_names):
        unpacked = struct.unpack('<H', forty_bytes[0:2])[0]
        try:
            self.direction_bytes = MoveInfoEnums.MovelistInputCodes(unpacked).name
        except:
            self.direction_bytes = '{:x}'.format(unpacked)

        self.unknown_input_dir = struct.unpack('<H', forty_bytes[2:4])[0]

        attack_bytes = struct.unpack('<H', forty_bytes[4:6])[0]
        try:
            self.attack_bytes = MoveInfoEnums.MovelistButtonCodes(attack_bytes).name
        except:
            self.attack_bytes = str(attack_bytes)

        button_press = struct.unpack('<H', forty_bytes[6:8])[0]
        try:
            self.button_press = MoveInfoEnums.ButtonPressCodes(button_press).name
        except:
            self.button_press = str(button_press)

        self.pointer_one = struct.unpack('<Q', forty_bytes[8:16])[0] - offset
        self.pointer_two = struct.unpack('<Q', forty_bytes[16:24])[0] - offset
        self.number_one = struct.unpack('<I', all_bytes[self.pointer_one: self.pointer_one + 4])[0]
        self.number_two = struct.unpack('<I', all_bytes[self.pointer_two: self.pointer_two + 4])[0]

        self.unknown_bool = struct.unpack('<I', forty_bytes[24:28])[0]
        self.cancel_window_1 = struct.unpack('<I', forty_bytes[28:32])[0]
        self.cancel_window_2 = struct.unpack('<I', forty_bytes[32:36])[0]
        self.move_id = int(struct.unpack('<H', forty_bytes[36:38])[0])

        active = struct.unpack('<B', forty_bytes[38:39])[0]
        try:
            self.move_requires_input = MoveInfoEnums.ActiveCodes(active).name
        except:
            self.move_requires_input = str(active)

        if self.move_id < len(all_names):
            self.name = all_names[self.move_id]
        else:
            self.name = str(self.move_id)

        self.movelist_names = forty_bytes[0x2E8:200000].split(b'\00') # Todo: figure out the actual size of the name movelist

    def __repr__(self):
        return '{} | {} |{:x} | {} | {} | {:x} | {:x} | {} | {} | {} | {:x} | {}'.format(
            self.name, self.direction_bytes, self.unknown_input_dir, self.attack_bytes, self.button_press, self.number_one, self.number_two, self.unknown_bool, self.cancel_window_1, self.cancel_window_2, self.move_id, self.move_requires_input)


class MovelistParser:
    def __init__(self, movelist_bytes, movelist_pointer):
        self.bytes = movelist_bytes
        self.pointer = movelist_pointer
        self.parse_header()

    def parse_header(self):
        header_length = 0x2e8
        header_bytes = self.bytes[0:header_length]
        identifier = self.header_line(0)
        char_name_address = self.header_line(1)
        developer_name_address = self.header_line(2)
        date_address = self.header_line(3)
        timestamp_address = self.header_line(4)

        self.char_name = self.bytes[char_name_address:developer_name_address].strip(b'\00').decode('utf-8')
        print("Parsing movelist for {}".format(self.char_name))

        unknown_regions = {}
        for i in range(42, 91, 2):
            unknown_regions[i] = self.header_line(i)

        self.names_double = self.bytes[header_length:unknown_regions[42]].split(b'\00')[4:]
        self.names = []
        for i in range(0, len(self.names_double) - 1, 2):
            self.names.append(self.names_double[i].decode('utf-8'))


        self.move_nodes_raw = self.bytes[unknown_regions[54]:unknown_regions[58]] #there's two regions of move nodes, first one might be blocks????
        self.move_nodes = []
        for i in range(0, len(self.move_nodes_raw), 40):
            self.move_nodes.append(MoveNode(self.move_nodes_raw[i:i+40], self.pointer, self.bytes, self.names))

        self.can_move_be_done_from_neutral = {}

        for node in self.move_nodes:
            move_id = node.move_id
            if not move_id in self.can_move_be_done_from_neutral:
                self.can_move_be_done_from_neutral[move_id] = False
            if node.cancel_window_1 >= 0x7FFF:
                self.can_move_be_done_from_neutral[move_id] = True

        self.democratically_chosen_input = {}
        for node in self.move_nodes:
            if not node.move_id in self.democratically_chosen_input:
                inputs = []
                self.democratically_chosen_input[node.move_id] = inputs
            else:
                inputs = self.democratically_chosen_input[node.move_id]
            inputs.append((node.direction_bytes, node.attack_bytes, node.button_press))

        sort_directions = collections.defaultdict(int)

        sort_attacks = collections.defaultdict(int)

        sort_presses = collections.defaultdict(int)

        sort_directions[MoveInfoEnums.MovelistInputCodes.FC.name] = 110
        sort_directions[MoveInfoEnums.MovelistInputCodes.N.name] = 100
        sort_directions[MoveInfoEnums.MovelistInputCodes.ws.name] = 90
        sort_directions[MoveInfoEnums.MovelistInputCodes.uf.name] = 80

        sort_attacks[MoveInfoEnums.MovelistButtonCodes.B_1.name] = 100
        sort_attacks[MoveInfoEnums.MovelistButtonCodes.B_2.name] = 99
        sort_attacks[MoveInfoEnums.MovelistButtonCodes.B_3.name] = 98
        sort_attacks[MoveInfoEnums.MovelistButtonCodes.B_4.name] = 97

        sort_presses[MoveInfoEnums.ButtonPressCodes.Press.name] = 100
        sort_presses[MoveInfoEnums.ButtonPressCodes.NULL.name] = -2

        self.move_id_to_input = {}
        for move_id, value in self.democratically_chosen_input.items():

            candidates = value

            if len(candidates) > 0:
                direction = sorted(candidates, key = lambda c: (sort_directions[c[0]], sort_presses[c[2]]), reverse=True)[0][0]

                button = sorted(candidates, key=lambda c: (sort_presses[c[2]], collections.Counter(candidates)[c], sort_attacks[c[1]]), reverse=True)[0][1]

                press = sorted(candidates, key=lambda c: sort_presses[c[2]], reverse=True)[0][2]

                self.move_id_to_input[move_id] = (direction, button, press)

    def header_line(self, line):
        header_bytes = self.bytes[line * 8:(line+1) * 8]
        return struct.unpack('<Q', header_bytes)[0] - self.pointer

    def can_be_done_from_neutral(self, move_id):
        if move_id in self.can_move_be_done_from_neutral:
            return self.can_move_be_done_from_neutral[move_id]
        else:
            return True

    def input_for_move(self, move_id, previous_move_id):
        empty_cancel_strings =[ 'b', '_B', '_R_D', 'y', 'Rv', '_R', '_D', 'Y']

        if move_id in self.move_id_to_input:
            input = ''
            last_move_was_empty_cancel = False

            tuple = self.move_id_to_input[move_id]

            if not tuple[0] in (MoveInfoEnums.MovelistInputCodes.NULL.name, MoveInfoEnums.MovelistInputCodes.N.name):

                if move_id > -1 and move_id < len(self.names) and '66' in self.names[move_id] and not '666' in self.names[move_id]:# and ('66' in self.names[previous_move_id] or 'DASH' in self.names[previous_move_id]):
                    input += 'ff'
                else:
                    input += tuple[0]

            if 'Release' in tuple[2]:
                input += '*'

            if not tuple[1] in (MoveInfoEnums.MovelistButtonCodes.NULL.name,):
                input += tuple[1].replace("B_", "").replace("_PLUS_", "+")

            if previous_move_id >= 0 and previous_move_id < len(self.names) and move_id >= 0 and move_id < len(self.names):

                if self.names[previous_move_id] in ([self.names[move_id] + s for s in empty_cancel_strings]):
                    last_move_was_empty_cancel = True

            return input, last_move_was_empty_cancel
        else:
            return "N/A", False
