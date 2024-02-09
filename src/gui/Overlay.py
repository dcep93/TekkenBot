import abc
import enum

from . import t_tkinter
from misc import Path
from misc.Windows import w as Windows

@enum.unique
class ColorSchemeEnum(enum.Enum):
    background = 'gray10'
    transparent = 'white'
    p1_text = '#93A1A1'
    p2_text = '#586E75'
    system_text = 'lawn green'
    advantage_plus = 'DodgerBlue2'
    advantage_slight_minus = 'ivory2'
    advantage_safe_minus = 'ivory3'
    advantage_punishible = 'orchid2'
    advantage_very_punishible = 'deep pink'
    advantage_text = 'black'

class Overlay:
    padding = 15
    geometry = None

    @abc.abstractmethod
    def update_state(self):
        pass

    @abc.abstractmethod
    def get_geometry(self):
        pass

    def __init__(self):
        self.visible = True

        window_name = self.__class__.__name__
        print("Launching {}".format(window_name))

        self.toplevel = t_tkinter.Toplevel()

        self.toplevel.wm_title(window_name)
        self.toplevel.iconbitmap(Path.path('./img/tekken_bot_close.ico'))
        self.toplevel.overrideredirect(True)

        self.background_color = ColorSchemeEnum.background.value
        self.tranparency_color = self.background_color
        self.toplevel.configure(background=self.tranparency_color)

        self.toplevel.attributes("-topmost", True)

    def update_location(self, game_reader):
        if Windows.valid:
            tekken_rect = game_reader.get_window_rect()
        else:
            tekken_rect = FullscreenTekkenRect(self.toplevel)
        geometry = None
        if tekken_rect is not None:
            x, y = self.get_geometry(tekken_rect)
            geometry = '+%d+%d' % (x, y)
            self.toplevel.geometry(geometry)
            if not self.visible:
                self.show()

        elif self.visible:
            self.hide()

        if geometry != self.geometry:
            self.geometry = geometry
            self.toplevel.after(20, self.update_location(game_reader))

    def show(self):
        self.toplevel.deiconify()
        self.visible = True

    def hide(self):
        self.toplevel.withdraw()
        self.visible = False

class FullscreenTekkenRect:
    def __init__(self, toplevel):
        self.left = 0
        self.right = toplevel.winfo_screenwidth()
        self.top = 0
        self.bottom = toplevel.winfo_screenheight()
