import struct
from collections import Counter
from collections import defaultdict
from MoveInfoEnums import InputDirectionCodes

class MovelistParser:
    class EscapeAll(bytes):
        def __str__(self):
            return 'b\'{}\''.format(''.join('\\x{:02x}'.format(b) for b in self))

    class MoveNode:
        def __init__(self, forty_bytes, offset, all_bytes, all_names):

            #self.input_bytes = forty_bytes[0:8]

            try:
                self.direction_bytes = MovelistInputCodes(struct.unpack('<H', forty_bytes[0:2])[0]).name
            except:
                self.direction_bytes = '{:x}'.format(struct.unpack('<H', forty_bytes[0:2])[0])
                #print("Failed to find direction code for {}".format(self.direction_bytes))

            self.unknown_input_dir = struct.unpack('<H', forty_bytes[2:4])[0]

            attack_bytes = struct.unpack('<H', forty_bytes[4:6])[0]
            try:
                self.attack_bytes = MovelistButtonCodes(attack_bytes).name
            except:
                self.attack_bytes = str(attack_bytes)

            button_press = struct.unpack('<H', forty_bytes[6:8])[0]
            try:
                self.button_press = ButtonPressCodes(button_press).name
            except:
                self.button_press = str(button_press)

            self.pointer_one = struct.unpack('<Q', forty_bytes[8:16])[0] - offset
            self.pointer_two = struct.unpack('<Q', forty_bytes[16:24])[0] - offset
            self.number_one = struct.unpack('<I', all_bytes[self.pointer_one: self.pointer_one + 4])[0]
            self.number_two = struct.unpack('<I', all_bytes[self.pointer_two: self.pointer_two + 4])[0]

            self.unknown_bool = struct.unpack('<I', forty_bytes[24:28])[0]
            self.cancel_window_1 = struct.unpack('<I', forty_bytes[28:32])[0]
            self.cancel_window_2 = struct.unpack('<I', forty_bytes[32:36])[0]
            #self.unknown_bytes = forty_bytes[24:36]
            self.move_id = int(struct.unpack('<H', forty_bytes[36:38])[0])

            active = struct.unpack('<B', forty_bytes[38:39])[0]
            try:
                self.move_requires_input = ActiveCodes(active).name
            except:
                self.move_requires_input = str(active)

            if self.move_id < len(all_names):
                self.name = all_names[self.move_id]
            else:
                self.name = str(self.move_id)

        def __repr__(self):
            return '{} | {} |{:x} | {} | {} | {:x} | {:x} | {} | {} | {} | {:x} | {}'.format(
                self.name, self.direction_bytes, self.unknown_input_dir, self.attack_bytes, self.button_press, self.number_one, self.number_two, self.unknown_bool, self.cancel_window_1, self.cancel_window_2, self.move_id, self.move_requires_input)


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


        #print ('{:x}'.format(date_address - self.pointer))
        self.char_name = self.bytes[char_name_address:developer_name_address].strip(b'\00').decode('utf-8')
        print("Parsing movelist for {}".format(self.char_name))

        unknown_regions = {}
        for i in range(42, 91, 2):
            unknown_regions[i] = self.header_line(i)
            #print(unknown_regions[i])

        #self.names = self.bytes[timestamp_address:unknown_regions[42]]
        self.names_double = self.bytes[header_length:unknown_regions[42]].split(b'\00')[4:]
        self.names = []
        for i in range(0, len(self.names_double) - 1, 2):
            self.names.append(self.names_double[i].decode('utf-8'))# + '/' + self.names_double[i+1].decode('utf-8'))


        self.move_nodes_raw = self.bytes[unknown_regions[54]:unknown_regions[58]] #there's two regions of move nodes, first one might be blocks????
        self.move_nodes = []
        for i in range(0, len(self.move_nodes_raw), 40):
            self.move_nodes.append(MovelistParser.MoveNode(self.move_nodes_raw[i:i+40], self.pointer, self.bytes, self.names))


        self.linked_nodes_raw = self.bytes[unknown_regions[46]:unknown_regions[48]]
        self.linked_nodes = []
        #for i in range(0, len(self.linked_nodes_raw), 24):

        #for node in self.move_nodes:
            #if node.move_id == 324:
                #print(node.move_id)


        #self.print_nodes(0x180)

        #print('{:x}'.format(unknown_regions[54] + self.pointer))
        #print(self.bytes[date_address:timestamp_address])
        #uniques = []
        #for node in self.move_nodes:
            #uniques.append(node.button_press)
        #counter = Counter(uniques)
        #for key, value in sorted(counter.items()):
            #print('{} | {}'.format(key, value))

        #with open('movelist' + self.char_name + '.txt', 'w') as fw:
            #for node in self.move_nodes:
                #fw.write(str(node) + '\n')
            #for name in self.names:
                #fw.write(name + '\n')

        #for node in self.move_nodes:
            #if node.unknown_buton_press == 4:
                #print(node)
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



        sort_directions = {}
        sort_directions = defaultdict(lambda : 0, sort_directions)

        sort_attacks = {}
        sort_attacks = defaultdict(lambda : 0,sort_attacks)

        sort_presses = {}
        sort_presses = defaultdict(lambda: 0, sort_presses)

        #sort_directions[MovelistInputCodes.RUN_KICK.name] = 120
        #sort_directions[MovelistInputCodes.RUNx.name] = 120
        #sort_directions[MovelistInputCodes.RUN_CHOP.name] = 120

        #sort_directions[MovelistInputCodes.RUN_1.name] = 120
        #sort_directions[MovelistInputCodes.RUN_2.name] = 120
        #sort_directions[MovelistInputCodes.RUN_3.name] = 120
        #sort_directions[MovelistInputCodes.RUN_4.name] = 120
        sort_directions[MovelistInputCodes.FC.name] = 110
        #sort_directions[MovelistInputCodes.ff.name] = 110
        sort_directions[MovelistInputCodes.N.name] = 100
        sort_directions[MovelistInputCodes.ws.name] = 90
        sort_directions[MovelistInputCodes.uf.name] = 80

        #sort_directions[MovelistInputCodes.cBT.name] = -1

        sort_attacks[MovelistButtonCodes.B_1.name] = 100
        sort_attacks[MovelistButtonCodes.B_2.name] = 99
        sort_attacks[MovelistButtonCodes.B_3.name] = 98
        sort_attacks[MovelistButtonCodes.B_4.name] = 97

        sort_presses[ButtonPressCodes.Press.name] = 100
        sort_presses[ButtonPressCodes.NULL.name] = -2

        self.move_id_to_input = {}
        for move_id, value in self.democratically_chosen_input.items():

            #candidates = [a for a in value if a[2] == ButtonPressCodes.Press.name]
            candidates = value

            if len(candidates) > 0:
            #candidates = sorted(candidates, key = lambda candidate: (candidate[2], Counter(candidates)[candidate], sort_directions[candidate[0]], sort_attacks[candidate[1]]), reverse=True)

                direction = sorted(candidates, key = lambda c: (sort_directions[c[0]], sort_presses[c[2]]), reverse=True)[0][0]

                button = sorted(candidates, key=lambda c: (sort_presses[c[2]], Counter(candidates)[c], sort_attacks[c[1]]), reverse=True)[0][1]

                press = sorted(candidates, key=lambda c: sort_presses[c[2]], reverse=True)[0][2]

                self.move_id_to_input[move_id] = (direction, button, press)

    def header_line(self, line):
        bytes = self.bytes[line * 8:(line+1) * 8]
        return struct.unpack('<Q', bytes)[0] - self.pointer

    def can_be_done_from_neutral(self, move_id):
        if move_id in self.can_move_be_done_from_neutral:
            return self.can_move_be_done_from_neutral[move_id]
        else:
            return True #blocking and damage moves

    def input_for_move(self, move_id, previous_move_id):
        empty_cancel_strings =[ 'b', '_B', '_R_D', 'y', 'Rv', '_R', '_D', 'Y']

        if move_id in self.move_id_to_input:
            input = ''
            last_move_was_empty_cancel = False

            tuple = self.move_id_to_input[move_id]

            if not tuple[0] in (MovelistInputCodes.NULL.name, MovelistInputCodes.N.name):

                if move_id > -1 and move_id < len(self.names) and '66' in self.names[move_id] and not '666' in self.names[move_id]:# and ('66' in self.names[previous_move_id] or 'DASH' in self.names[previous_move_id]):
                    input += 'ff'
                else:
                    input += tuple[0]

            if 'Release' in tuple[2]:
                input += '*'
            #input += tuple[2]

            if not tuple[1] in (MovelistButtonCodes.NULL.name,):
                input += tuple[1].replace("B_", "").replace("_PLUS_", "+")

            if previous_move_id >= 0 and previous_move_id < len(self.names) and move_id >= 0 and move_id < len(self.names):

                if self.names[previous_move_id] in ([self.names[move_id] + s for s in empty_cancel_strings]):
                    #print('{} : {}'.format(self.names[previous_move_id], self.names[move_id]))
                    last_move_was_empty_cancel = True

            return input, last_move_was_empty_cancel
        else:
            return "N/A", False

    def print_nodes(self, node_id):
        for node in self.move_nodes:
            if node_id == node.move_id:
                print(node)



from enum import Enum

class ButtonPressCodes(Enum):
    NULL = 0
    Release_4 = 4
    Release_8 = 8
    UNK_20 = 0x20
    Release = 0x2000
    Press = 0x4000

class ActiveCodes(Enum):
    NULL = 0
    A = 65 #active? seem to require a button to go into cancel
    P = 80 #passive? seem to happen without further input

class MovelistButtonCodes(Enum):
    NULL = 0
    B_1 = 1
    B_2 = 2
    B_1_PLUS_2 = 3
    B_3 = 4
    B_1_PLUS_3 = 5
    B_2_PLUS_3 = 6
    B_1_PLUS_2_PLUS_3 = 7
    B_4 = 8
    B_1_PLUS_4 = 9
    B_2_PLUS_4 = 10
    B_1_PLUS_2_PLUS_4 = 11
    B_3_PLUS_4 = 12
    B_1_PLUS_3_PLUS_4 = 13
    B_2_PLUS_3_PLUS_4 = 14
    B_1_PLUS_2_PLUS_3_PLUS_4 = 15
    B_R = 16

    UNK_600= 0x600 #1+2 only maybe? on hwoarangs b2, not HOLD


class MovelistInputCodes(Enum):
    NULL = 0

    N = 0x20

    u = 0x100
    ub = 0x80
    uf = 0x200

    f = 0x40
    b = 0x10

    d = 4
    df = 8
    db = 2


    #the following codes exist only in the movelist, not in player data
    FC = 6
    d_df = 0xc #down or down forward but not down back
    _d = 0xe #sometimes d as well??
    UNK_12 = 0x12
    UNK_2e = 0x2e #guard?
    UNK_48 = 0x48 #crouch turn while holding down?
    UNK_5e = 0x5e #pitcher glove cancel, B after U+2+3 in TTT2
    UNK_60 = 0x60
    RUNx = 0x70 #actually BT??? sometimes running???
    _ub = 0x90 # item command? u/b+1 for king
    UNK_92 = 0x92 # possible alternate u/b input?
    UNK_104 = 0x104 #item command?
    FACE_DOWN = 0x120
    UNK_120 = 0x120 #leads to jump
    UNK_248 = 0x248 #???
    UNK_380 = 0x380 #Vp_sJUMPr00 roll jump?
    UNK_38a = 0x38a
    UNK_3ae = 0x3ae
    UNK_3c0 = 0x3c0 #all lead back to standing
    UNK_3de = 0x3de
    UNK_3ec = 0x3ec
    UNK_3ee = 0x3ee #Eliza's sleep cancel, so like, NOT holding b
    ws = 0x3f0 #not standing backturn?
    UNK_402 = 0x402
    UNK_404 = 0x404
    UNK_408 = 0x408
    UNK_40e = 0x40e



    _Q = 0x8000 #??? lots of these
    ff = 0x8001
    bb = 0x8002
    UNK_8003 = 0x8003 #sidesteps?
    UNK_8004 = 0x8004  # sidesteps?
    UNK_800b = 0x800b #hit standing? block standing?
    UNK_800c = 0x800c #only exists on move_id=0?

    db_f_34 = 0x8018  #guard #King's tombstone
    UNK_8019 = 0x8019  # guard
    UNK_801a = 0x801a  # guard
    UNK_801b = 0x801b  # guard

    UNK_803a = 0x803a  # standing

    RUN_CHOP = 0x80ac  # run chop
    RUN_KICK = 0x80ae  # run chop

    UNK_80af = 0x80af  # guard

    RUN_1 = 0x80b0  # run lp?
    RUN_2 = 0x80b1  # run rp?
    RUN_3 = 0x80b2  # run lk?
    RUN_4 = 0x80b3  # run rk?

    #qcf states for eliza, all the ways to make a qcf, maybe storing the input
    qcf_fb = 0x80fb #qcf+1 # this b-f for Kazumi
    qcf_fc = 0x80fc #qcf+2
    qcf_fd = 0x80fd #qcf+1
    qcf_fe = 0x80fe #qcf+2
    qcf_ff = 0x80ff  #EX only
    qcf_100 = 0x8100  # EX only
    qcf_101 = 0x8101  # No fireball?
    qcf_102 = 0x8102  # No fireball?
    qcf_103 = 0x8103  # super (double qcf)
    qcf_104 = 0x8104  # super (double qcf)

    #dp states
    dp_0b = 0x8010b #EX
    dp_0c = 0x8010c  # EX
    dp_0d = 0x8010d  # 1
    dp_0e = 0x8010e  # 2
    dp_0f = 0x8010f  # 1
    dp_10 = 0x80110  # 2

    #qcb states
    qcb_11 = 0x8011
    qcb_12 = 0x8012
    qcb_13 = 0x8013
    qcb_14 = 0x8014
    qcb_15 = 0x8015
    qcb_16 = 0x8016
    qcb_17 = 0x8017
    qcb_18 = 0x8018
    qcb_19 = 0x8019
    qcb_1a = 0x801a
    #Missing?
    qcb_1c = 0x801c
    qcb_1d = 0x801d

    f_qcf_12 = 0x8031 #gigas command throw

    EX_CANCEL_1 = 0x8122
    EX_CANCEL_2 = 0x8123

    qcf_129 = 0x8129 #1, seems to be the most common, maybe the 'normal' qcf
    qcf_12a = 0x812a #2
    qcf_12e = 0x812e







