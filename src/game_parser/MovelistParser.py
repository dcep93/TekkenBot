import collections
import struct

from . import MoveInfoEnums

class MoveNode:
    def __init__(self, forty_bytes, offset, movelist_bytes, all_names):
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

        pointer_one = struct.unpack('<Q', forty_bytes[8:16])[0] - offset
        pointer_two = struct.unpack('<Q', forty_bytes[16:24])[0] - offset
        self.number_one = struct.unpack('<I', movelist_bytes[pointer_one: pointer_one + 4])[0]
        self.number_two = struct.unpack('<I', movelist_bytes[pointer_two: pointer_two + 4])[0]

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

class MovelistParser:
    cached_movelists = {}

    def __init__(self, movelist_bytes, movelist_pointer):
        header_length = 0x2e8
        char_name_address = header_line(1, movelist_bytes, movelist_pointer)
        developer_name_address = header_line(2, movelist_bytes, movelist_pointer)

        self.char_name = movelist_bytes[char_name_address:developer_name_address].strip(b'\00').decode('utf-8')

        if self.char_name in self.cached_movelists:
            self.names, self.can_be_done_from_neutral, self.move_id_to_input, self.movelist_names = self.cached_movelists[self.char_name]
            return

        print("Parsing movelist for {}".format(self.char_name))
        unknown_regions = {}
        for i in range(42, 91, 2):
            unknown_regions[i] = header_line(i, movelist_bytes, movelist_pointer)

        names_double = movelist_bytes[header_length:unknown_regions[42]].split(b'\00')[4:]
        self.names = []
        for i in range(0, len(names_double) - 1, 2):
            self.names.append(names_double[i].decode('utf-8'))

        move_nodes_raw = movelist_bytes[unknown_regions[54]:unknown_regions[58]] #there's two regions of move nodes, first one might be blocks????
        move_nodes = []
        for i in range(0, len(move_nodes_raw), 40):
            move_nodes.append(MoveNode(move_nodes_raw[i:i+40], movelist_pointer, movelist_bytes, self.names))

        self.can_move_be_done_from_neutral = {}

        for node in move_nodes:
            move_id = node.move_id
            if not move_id in self.can_move_be_done_from_neutral:
                self.can_move_be_done_from_neutral[move_id] = False
            if node.cancel_window_1 >= 0x7FFF:
                self.can_move_be_done_from_neutral[move_id] = True

        democratically_chosen_input = {}
        for node in move_nodes:
            if not node.move_id in democratically_chosen_input:
                inputs = []
                democratically_chosen_input[node.move_id] = inputs
            else:
                inputs = democratically_chosen_input[node.move_id]
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
        for move_id, value in democratically_chosen_input.items():

            candidates = value

            if len(candidates) > 0:
                direction = sorted(candidates, key=lambda c: (sort_directions[c[0]], sort_presses[c[2]]), reverse=True)[0][0]

                button = sorted(candidates, key=lambda c: (sort_presses[c[2]], collections.Counter(candidates)[c], sort_attacks[c[1]]), reverse=True)[0][1]

                press = sorted(candidates, key=lambda c: sort_presses[c[2]], reverse=True)[0][2]

                if not (direction.isdigit() and button == 'NULL' and press == 'NULL'):
                    self.move_id_to_input[move_id] = (direction, button, press)

        self.movelist_names = movelist_bytes[0x2E8:200000].split(b'\00')

        self.cached_movelists[self.char_name] = (self.names, self.can_be_done_from_neutral, self.move_id_to_input, self.movelist_names)

    def can_be_done_from_neutral(self, move_id):
        if move_id in self.can_move_be_done_from_neutral:
            return self.can_move_be_done_from_neutral[move_id]
        else:
            return True

    def input_for_move(self, move_id, previous_move_id):
        empty_cancel_strings = ['b', '_B', '_R_D', 'y', 'Rv', '_R', '_D', 'Y']

        if move_id in self.move_id_to_input:
            string = ''
            last_move_was_empty_cancel = False

            input_tuple = self.move_id_to_input[move_id]

            if not input_tuple[0] in (MoveInfoEnums.MovelistInputCodes.NULL.name, MoveInfoEnums.MovelistInputCodes.N.name):

                if (-1 < move_id < len(self.names)) and ('66' in self.names[move_id]) and ('666' not in self.names[move_id]):
                    string += 'ff'
                else:
                    string += input_tuple[0]

            if 'Release' in input_tuple[2]:
                string += '*'

            if not input_tuple[1] in (MoveInfoEnums.MovelistButtonCodes.NULL.name,):
                string += input_tuple[1].replace("B_", "").replace("_PLUS_", "+")

            if (0 <= previous_move_id < len(self.names)) and (0 <= move_id < len(self.names)):

                if self.names[previous_move_id] in ([self.names[move_id] + s for s in empty_cancel_strings]):
                    last_move_was_empty_cancel = True

            return string, last_move_was_empty_cancel
        else:
            return "N/A", False

def header_line(line, movelist_bytes, movelist_pointer):
    header_bytes = movelist_bytes[line * 8:(line+1) * 8]
    return struct.unpack('<Q', header_bytes)[0] - movelist_pointer