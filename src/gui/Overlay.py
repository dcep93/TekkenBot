import abc
import enum

from . import t_tkinter
from misc import Globals, Path
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
    def __init__(self, xy_size):
        window_name = self.get_name()
        print("Launching {}".format(window_name))

        self.visible = False
        self.toplevel = t_tkinter.Toplevel()

        self.toplevel.wm_title(window_name)

        self.toplevel.attributes("-topmost", True)

        self.background_color = ColorSchemeEnum.background.value

        self.tranparency_color = self.background_color
        self.toplevel.configure(background=self.tranparency_color)

        self.toplevel.iconbitmap(Path.path('./img/tekken_bot_close.ico'))
        self.toplevel.overrideredirect(True)

        self.w, self.h = xy_size

        self.toplevel.geometry('%sx%s' % (self.w, self.h))

    def get_name(self):
        return self.__class__.__name__

    def update(self):
        self.update_state()
        self.update_location()

    @abc.abstractmethod
    def update_state(self):
        pass

    def update_location(self):
        bottom = True
        if not Windows.valid:
            return
        padding = 20
        tekken_rect = Globals.Globals.game_reader.get_window_rect()
        if tekken_rect is not None:
            x = (tekken_rect.right + tekken_rect.left) / 2  - self.toplevel.winfo_width() / 2
            if bottom:
                y = tekken_rect.bottom - self.toplevel.winfo_height() - padding
            else:
                y = tekken_rect.top + padding + 20
            geometry = '+%d+%d' % (x, y)
            self.toplevel.geometry(geometry)
            if not self.visible:
                self.show()
        else:
            self.hide()

    def show(self):
        self.toplevel.deiconify()
        self.visible = True

    def hide(self):
        self.toplevel.withdraw()
        self.visible = False
