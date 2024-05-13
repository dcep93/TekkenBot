from ..misc import Flags

import enum

class safeEnum(enum.Enum):
    @classmethod
    def _missing_(cls, value):
        if Flags.Flags.debug:
            e = Exception(f'_missing_ {cls}, {value}')
            if Flags.Flags.debug:
                print(e)
                # raise e
        return cls(0)

class AttackType(safeEnum):
    NA = 0 #This move is not an attack

    THROW = 6291466  #this is only the attack type *during* the throw animation
    MID_UNBLOCKABLE = 12582919
    #UNKNOWN_6 = 6 #????? may not exist
    HIGH = 10485765
    SMID = 6291460
    MID = 8388610
    LOW = 2097153

    RECOVERING = 12582912
    UNKNOWN = 1048579

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

    BROKEN_54 = 54

    UNKN = 999999 #used to indicate a non standard tracking move

class ThrowTechs(safeEnum):
    NONE = 0
    TE1 = 3489660956
    TE2 = 3758096415
    TE1_2 = 4026531870

    BROKEN_ThrowTechs = 3221225501

class StunStates(safeEnum):
    NONE = 0
    UNKNOWN_2 = 2 #Lili BT/Jumping/Kicks?
    BLOCK = 0x01000100
    GETTING_HIT = 0x100
    DOING_THE_HITTING = 0x10000
    BEING_PUNISHED = 0x10100 #One frame at the begining of a punish #Also appears during simultaneous couterhits

    BLOCK_NO_HIT = 0x1000000 #law's UF+4, sometimes???? Proximity guard maybe?

#Note that this information resides on the player BEING hit not the player doing the hitting. Also note that there's no counter hit state for side or back attacks.
class HitOutcome(safeEnum):
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

class InputDirectionCodes(safeEnum):
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

class InputAttackCodes(safeEnum):
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
    PAUL = 0
    LAW = 1
    KING = 2
    YOSHIMITSU = 3
    HWOARANG = 4
    XIAOYU = 5
    JIN = 6
    BRYAN = 7
    KAZUYA = 8
    STEVE = 9
    JACK = 10
    ASUKA = 11
    DEVIL_JIN = 12
    FENG = 13
    LILI = 14
    DRAGUNOV = 15
    LEO = 16
    LARS = 17
    ALISA = 18
    CLAUDIO = 19
    SHAHEEN = 20
    NINA = 21
    LEE = 22
    KUMA = 23
    PANDA = 24
    ZAFINA = 25
    LEROY = 26
    JUN = 27
    REINA = 28
    AZUCENA = 29
    VICTOR = 30
    RAVEN = 31
    _DUMMY = 116
