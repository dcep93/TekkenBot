import enum

class safeEnum(enum.Enum):
    @classmethod
    def _missing_(cls, value):
        print('_missing_', cls, value)
        return cls(0)

class AttackType(safeEnum):
    THROW = 6291466  #this is only the attack type *during* the throw animation
    MID_UNBLOCKABLE = 12582919
    #UNKNOWN_6 = 6 #????? may not exist
    HIGH = 10485765
    SMID = 6291460
    MID = 8388610
    LOW = 2097153
    NA = 0 #This move is not an attack

    RECOVERING = 12582912

class SimpleMoveStates(safeEnum):
    UNINITIALIZED = 0

    STANDING_FORWARD = 1
    STANDING_BACK = 2
    STANDING = 3
    STEVE = 4 #steve?

    CROUCH_FORWARD = 5
    CROUCH_BACK = 6
    CROUCH = 7

    UNKNOWN_TYPE_9 = 9 #seen on Ling

    GROUND_FACEUP = 12
    GROUND_FACEDOWN = 13

    JUGGLED = 14
    KNOCKDOWN = 15

    #THE UNDERSTANDING OF THE FOLLOWING VALUES IS NOT COMPLETE

    OFF_AXIS_GETUP = 8

    UNKNOWN_10 = 10 #Yoshimitsu
    UNKNOWN_GETUP_11 = 11

    WALL_SPLAT_18 = 18
    WALL_SPLAT_19 = 19
    TECH_ROLL_OR_FLOOR_BREAK = 20

    UNKNOWN_23 = 23 #Kuma

    AIRBORNE_24 = 24 #Yoshimitsu
    AIRBORNE = 25
    AIRBORNE_26 = 26 #Eliza. Chloe
    FLY = 27 #Devil Jin 3+4

class ComplexMoveStates(safeEnum):  #These are tracking states>
    F_MINUS = 0 # this doubles as the nothing state and an attack_starting state. #occurs on kazuya's hellsweep

    S_PLUS = 1 #homing
    S = 2 #homing, often with screw, seems to more often end up slightly off-axis?
    A = 3 #this move 'realigns' if you pause before throwing it out
    UN04 = 4 # extremely rare, eliza ff+4, 2 has this
    C_MINUS = 5 # realigns either slightly worse or slightly better than C, hard to tell
    A_PLUS = 6 #realigns very well #Alisa's b+2, 1 has this, extremely rare
    C = 7 #this realigns worse than 'A'

    END1 = 10 #after startup  ###Kazuya's ff+3 doesn't have a startup or attack ending flag, it's just 0 the whole way through ???  ###Lili's d/b+4 doesn't have it after being blocked
    BLOCK = 11
    WALK = 12 #applies to dashing and walking
    SIDEROLL_GETUP = 13 #only happens after side rolling???
    SIDEROLL_STAYDOWN = 14
    SS = 15 #sidestep left or right, also applies to juggle techs

    RECOVERING = 16 #happens after you stop walking forward or backward, jumping, getting hit, going into a stance, and some other places
    UN17 = 17  # f+4 with Ling
    UN18 = 18 #King's 1+2+3+4 ki charge

    UN20 = 20 #Dragunov's d+3+4 ground stomp

    UN22 = 22 #Eddy move
    UN23 = 23 #Steve 3+4, 1

    SW = 28 #sidewalk left or right

    UNKN = 999999 #used to indicate a non standard tracking move

class ThrowTechs(safeEnum):
    NONE = 0
    TE1 = 3489660956
    TE2 = 3758096415
    TE1_2 = 4026531870

    BROKEN_ThrowTechs = 3221225501

class StunStates(enum.Enum):
    NONE = 0
    UNKNOWN_2 = 2 #Lili BT/Jumping/Kicks?
    BLOCK = 0x01000100
    GETTING_HIT = 0x100
    DOING_THE_HITTING = 0x10000
    BEING_PUNISHED = 0x10100 #One frame at the begining of a punish #Also appears during simultaneous couterhits

    BLOCK_NO_HIT = 0x1000000 #law's UF+4, sometimes???? Proximity guard maybe?

class CancelStatesBitmask(enum.Enum):
    CANCELABLE = 0x00010000
    BUFFERABLE = 0x01000000
    PARRYABLE_1 = 0x00000001
    PARRYABLE_2 = 0x00000002

#Note that this information resides on the player BEING hit not the player doing the hitting. Also note that there's no counter hit state for side or back attacks.
class HitOutcome(enum.Enum):
    NONE = 0
    BLOCKED_STANDING = 1
    BLOCKED_CROUCHING = 2
    JUGGLE = 3
    SCREW = 4
    UNKNOWN_SCREW_5 = 5 #Xiaoyu's sample combo 3 ends with this, off-axis or right side maybe?
    UNKNOWN_6 = 6 #May not exist???
    UNKNOWN_SCREW_7 = 7 #Xiaoy's sample combo 3 includes this
    GROUNDED_FACE_DOWN = 8
    GROUNDED_FACE_UP = 9
    COUNTER_HIT_STANDING = 10
    COUNTER_HIT_CROUCHING = 11
    NORMAL_HIT_STANDING = 12
    NORMAL_HIT_CROUCHING = 13
    NORMAL_HIT_STANDING_LEFT = 14
    NORMAL_HIT_CROUCHING_LEFT = 15
    NORMAL_HIT_STANDING_BACK = 16
    NORMAL_HIT_CROUCHING_BACK = 17
    NORMAL_HIT_STANDING_RIGHT = 18
    NORMAL_HIT_CROUCHING_RIGHT = 19

class JumpFlagBitmask(enum.Enum):
    #GROUND = 0x800000
    #LANDING_OR_STANDING = 0x810000
    JUMP = 0x820000

class InputDirectionCodes(enum.Enum):
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

class InputAttackCodes(enum.Enum):
    N = 0
    x1 = 512
    x2 = 1024
    x3 = 2048
    x4 = 4096
    x1x2 = 1536
    x1x3 = 2560
    x1x4 = 4608
    x2x3 = 3072
    x2x4 = 5120
    x3x4 = 6144
    x1x2x3 = 3584
    x1x2x4 = 5632
    x1x3x4 = 6656
    x2x3x4 = 7168
    x1x2x3x4 = 7680
    xRAGE = 8192

class CharacterCodes(enum.Enum):
    DUMMY = 116
    KING_ = 128
    KAZUYA = 8
    JUN = 27
    VICTOR = 30

    PAUL = 0
    LAW = 1
    KING = 2
    YOSHIMITSU = 3
    HWOARANG = 4
    XIAOYU = 5
    JIN = 6
    BRYAN = 7
    # HEIHACHI = 8
    # KAZUYA = 9
    STEVE = 10
    JACK_7 = 11
    ASUKA = 12
    DEVIL_JIN = 13
    FENG = 14
    LILI = 15
    DRAGUNOV = 16
    LEO = 17
    LARS = 18
    ALISA = 19
    CLAUDIO = 20
    KATARINA = 21
    LUCKY_CHLOE = 22
    SHAHEEN = 23
    JOSIE = 24
    GIGAS = 25
    KAZUMI = 26
    NINA = 28
    MASTER_RAVEN = 29
    LEE = 300
    BOB = 31
    AKUMA = 32
    KUMA = 33
    PANDA = 34
    EDDY = 35
    ELIZA = 36
    MIGUEL = 37
    TEKKEN_FORCE = 38 # Not selectable
    KID_KAZUYA = 39 # Not selectable
    JACK_4 = 40 # Not selectable
    YOUNG_HEIHACHI = 41 # Not selectable
    TRAINING_DUMMY = 42 # Not selectable
    GEESE = 43 # DLC
    NOCTIS = 44 # DLC
    ANNA = 45 # DLC
    LEI = 46 # DLC
    MARDUK = 47 # DLC
    ARMOR_KING = 48 # DLC
    JULIA = 49 # DLC
    NEGAN = 50 # DLC
    ZAFINA = 51 # DLC
    GANRYU = 52 # DLC
    LEROY = 53 # DLC
    FAKHUMRAM = 54 # DLC
    KUNIMITSU = 55 # DLC

    NOT_YET_LOADED = 75 #value when a match starts for (??) frames until char_id loads

    NO_SELECTION = 255 #value if cursor is not shown

class ButtonPressCodes(enum.Enum):
    NULL = 0
    Release_4 = 4
    Release_8 = 8
    UNK_20 = 0x20
    Release = 0x2000
    Press = 0x4000

class ActiveCodes(enum.Enum):
    NULL = 0
    A = 65 #active? seem to require a button to go into cancel
    P = 80 #passive? seem to happen without further input

class MovelistButtonCodes(enum.Enum):
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

    UNK_600 = 0x600 # 1+2 only maybe? on hwoarangs b2, not HOLD


class MovelistInputCodes(enum.Enum):
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
