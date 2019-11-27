"""
A layer of abstraction over ArtificialKeyboard, GameInputter.py takes basic Tekken commands (forward, tap light punch,
hold back) and turns them into the actual keypresses.

"""

from enum import Enum
from ArtificialKeyboard import ArtificalKeyboard

#directinput scan codes
#https://gist.github.com/tracend/912308
class Keys_P2:
    UP = 0xc8
    DOWN = 0xd0
    LEFT = 0xCB
    RIGHT = 0xCD
    A = 0x4b
    B = 0x4c
    X = 0x47
    Y = 0x48
    START =  0xc7
    SELECT = 0xd2
    LB = 0x49
    RB = 0x4d
    LT = 0x4a
    RT = 0x4e

class Keys_P1:
    UP = 0x11
    DOWN = 0x1F
    LEFT = 0x1E
    RIGHT = 0x20
    A = 0x24
    B = 0x25
    X = 0x16
    Y = 0x17
    START =  0x30
    SELECT = 0x2F
    LB = 0x19
    RB = 0x18
    LT = 0x27
    RT = 0x26


class Buttons(Enum):
    BUTTON_1 = 1
    BUTTON_2 = 2
    BUTTON_3 = 3
    BUTTON_4 = 4
    BUTTON_LEFT = 5
    BUTTON_RIGHT = 6
    BUTTON_UP = 7
    BUTTON_DOWN = 8
    BUTTON_RB = 9
    BUTTON_ACCEPT = 10
    BUTTON_SELECT = 11





class GameControllerInputter:

    p2_controls = {
        Buttons.BUTTON_1 : Keys_P2.X,
        Buttons.BUTTON_2 : Keys_P2.Y,
        Buttons.BUTTON_3 : Keys_P2.A,
        Buttons.BUTTON_4 : Keys_P2.B,
        Buttons.BUTTON_LEFT : Keys_P2.LEFT,
        Buttons.BUTTON_RIGHT : Keys_P2.RIGHT,
        Buttons.BUTTON_UP : Keys_P2.UP,
        Buttons.BUTTON_DOWN : Keys_P2.DOWN,
        Buttons.BUTTON_RB : Keys_P2.RB,
        Buttons.BUTTON_ACCEPT : Keys_P2.A,
        Buttons.BUTTON_SELECT : Keys_P2.SELECT
    }

    p1_controls = {
        Buttons.BUTTON_1: Keys_P1.X,
        Buttons.BUTTON_2: Keys_P1.Y,
        Buttons.BUTTON_3: Keys_P1.A,
        Buttons.BUTTON_4: Keys_P1.B,
        Buttons.BUTTON_LEFT: Keys_P1.LEFT,
        Buttons.BUTTON_RIGHT: Keys_P1.RIGHT,
        Buttons.BUTTON_UP: Keys_P1.UP,
        Buttons.BUTTON_DOWN: Keys_P1.DOWN,
        Buttons.BUTTON_RB: Keys_P1.RB,
        Buttons.BUTTON_ACCEPT: Keys_P1.A,
        Buttons.BUTTON_SELECT: Keys_P1.SELECT
    }




    def __init__(self, usePlayer2Controls = True):
        if usePlayer2Controls:
            self.controls = GameControllerInputter.p2_controls
        else:
            self.controls = GameControllerInputter.p1_controls

        self.heldKeys = []
        self.tappedKeys = []
        self.releasedKeys = []
        self.heldKeys = []
        self.performedInitialKeyRelease = False
        self.wasOnLeft = True
        self.isOnLeft = True
        self.releasedKeyJailTime = 0
        self.isTekkenActiveWindow = False
        self.SetControlsOnLeft()


    def checkFacing(self):
        isBotOnLeft = self.isOnLeft
        if(self.wasOnLeft != isBotOnLeft):
            if isBotOnLeft:
               self.SetControlsOnLeft()
            else:       #bot is on the right
                self.SetControlsOnRight()
            self.Release()
        self.wasOnLeft = isBotOnLeft

    def SetControlsOnLeft(self):
        self.back = self.controls[Buttons.BUTTON_LEFT]
        self.forward = self.controls[Buttons.BUTTON_RIGHT]
        self.right = self.controls[Buttons.BUTTON_DOWN]
        self.left = self.controls[Buttons.BUTTON_UP]

    def SetControlsOnRight(self):
        self.back = self.controls[Buttons.BUTTON_RIGHT]
        self.forward = self.controls[Buttons.BUTTON_LEFT]
        self.right = self.controls[Buttons.BUTTON_UP]
        self.left = self.controls[Buttons.BUTTON_DOWN]

    def TapBack(self):
        self.TapButton(self.back)

    def TapForward(self):
        self.TapButton(self.forward)

    def TapDown(self):
        self.TapButton(self.controls[Buttons.BUTTON_DOWN])

    def TapUp(self):
        self.TapButton(self.controls[Buttons.BUTTON_UP])

    def TapRight(self):
        self.TapButton(self.right)

    def TapLeft(self):
        self.TapButton(self.left)

    def Tap1(self):
        self.TapButton(self.controls[Buttons.BUTTON_1])

    def Tap2(self):
        self.TapButton(self.controls[Buttons.BUTTON_2])

    def Tap3(self):
        self.TapButton(self.controls[Buttons.BUTTON_3])

    def Tap4(self):
        self.TapButton(self.controls[Buttons.BUTTON_4])

    def TapAccept(self):
        self.TapButton(self.controls[Buttons.BUTTON_ACCEPT])

    def TapSelect(self):
        self.TapButton(self.controls[Buttons.BUTTON_SELECT])

    def TapRageArt(self):
        self.TapButton(self.controls[Buttons.BUTTON_RB])

    def HoldBack(self):
        self.HoldButton(self.back)

    def HoldDown(self):
        self.HoldButton(self.controls[Buttons.BUTTON_DOWN])

    def HoldUp(self):
        self.HoldButton(self.controls[Buttons.BUTTON_UP])

    def HoldForward(self):
        self.HoldButton(self.forward)

    def Hold1(self):
        self.HoldButton(self.controls[Buttons.BUTTON_1])

    def Hold2(self):
        self.HoldButton(self.controls[Buttons.BUTTON_2])

    def Hold3(self):
        self.HoldButton(self.controls[Buttons.BUTTON_3])

    def Hold4(self):
        self.HoldButton(self.controls[Buttons.BUTTON_4])

    def HoldRage(self):
        self.HoldButton(self.controls[Buttons.BUTTON_RB])

    def ReleaseForward(self):
        self.ReleaseButton(self.forward)

    def ReleaseUp(self):
        self.ReleaseButton(self.controls[Buttons.BUTTON_UP])

    def ReleaseBack(self):
        self.ReleaseButton(self.back)

    def ReleaseDown(self):
        self.ReleaseButton(self.controls[Buttons.BUTTON_DOWN])

    def Release1(self):
        self.ReleaseButton(self.controls[Buttons.BUTTON_1])

    def Release2(self):
        self.ReleaseButton(self.controls[Buttons.BUTTON_2])

    def Release3(self):
        self.ReleaseButton(self.controls[Buttons.BUTTON_3])

    def Release4(self):
        self.ReleaseButton(self.controls[Buttons.BUTTON_4])

    def ReleaseRage(self):
        self.ReleaseButton(self.controls[Buttons.BUTTON_RB])

    def ResetPractice(self):
        self.TapAccept()
        self.TapSelect()

    def ReleaseButton(self, button):
        self.ReleaseKeyIfActive(button)
        if button in self.heldKeys:
            self.heldKeys.remove(button)

    def TapButton(self, button):
        if not button in self.releasedKeys:
            self.PressKeyIfActive(button)
            self.tappedKeys.append(button)
            self.releasedKeyJailTime = 0

    def HoldButton(self, button):
        if not button in self.heldKeys:
            self.PressKeyIfActive(button)
            self.heldKeys.append(button)

    def Update(self, isTekkenActiveWindow, isOnLeft):
        self.isTekkenActiveWindow = isTekkenActiveWindow
        self.isOnLeft = isOnLeft
        self.checkFacing()

        if isTekkenActiveWindow and not self.performedInitialKeyRelease:
            self.Release()
            self.performedInitialKeyRelease = True

        else:
            self.releasedKeyJailTime -= 1
            if self.releasedKeyJailTime <= 0:
                self.releasedKeys = []
                for button in self.tappedKeys:
                    self.ReleaseKeyIfActive(button)
                    self.releasedKeys.append(button)
                    if button in self.heldKeys:
                        self.heldKeys.remove(button)
                self.tappedKeys = []

    def Release(self):
        if (self.isTekkenActiveWindow):
            self.heldKeys = []
            self.ReleaseAllButtons()

    def PressKeyIfActive(self, hexKeyCode):
        if (self.isTekkenActiveWindow):
            ArtificalKeyboard.PressKey(hexKeyCode)

    def ReleaseKeyIfActive(self, hexKeyCode):
        if (self.isTekkenActiveWindow):
            ArtificalKeyboard.ReleaseKey(hexKeyCode)



    def ReleaseAllButtons(self):
        #print("releasing all buttons")
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_1])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_2])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_3])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_4])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_UP])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_DOWN])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_LEFT])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_RIGHT])
        ArtificalKeyboard.ReleaseKey(self.controls[Buttons.BUTTON_RB])


