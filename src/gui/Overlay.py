import abc
import enum

from . import t_tkinter
from misc import ConfigReader, Globals, Path
from misc.Windows import w as Windows

@enum.unique
class DisplaySettings(enum.Enum):
    overlay_on_bottom = 'overlay on bottom'
    overlay_as_draggable_window = 'overlay as draggable window'
    only_appears_when_Tekken_7_has_focus = 'only appears when Tekken 7 has focus'

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

        self.set_config()

        self.overlay_visible = False
        self.toplevel = t_tkinter.Toplevel()

        self.toplevel.wm_title(window_name)

        self.toplevel.attributes("-topmost", True)

        self.background_color = ColorSchemeEnum.background.value

        self.tranparency_color = self.background_color
        self.toplevel.configure(background=self.tranparency_color)

        self.toplevel.iconbitmap(Path.path('./img/tekken_bot_close.ico'))
        if not self.is_draggable_window:
            self.toplevel.overrideredirect(True)

        self.w, self.h = xy_size

        self.toplevel.geometry('%sx%s' % (self.w, self.h))

    def get_name(self):
        return self.__class__.__name__

    def set_config(self):
        g = Globals.Globals.master.tekken_config.get_property
        self.is_draggable_window = g(DisplaySettings.overlay_as_draggable_window, False)
        self.is_minimize_on_lost_focus = g(DisplaySettings.only_appears_when_Tekken_7_has_focus, True)
        self.is_overlay_on_bottom = g(DisplaySettings.overlay_on_bottom, True)

    def update_location(self):
        if not Windows.valid:
            return
        if not self.is_draggable_window:
            tekken_rect = Globals.Globals.game_reader.get_window_rect()
            if tekken_rect is not None:
                x = (tekken_rect.right + tekken_rect.left) / 2  - self.toplevel.winfo_width() / 2
                if self.is_overlay_on_bottom:
                    y = tekken_rect.bottom - self.toplevel.winfo_height() - 20
                else:
                    y = tekken_rect.top
                geometry = '+%d+%d' % (x, y)
                self.toplevel.geometry(geometry)
                if not self.overlay_visible:
                    self.show()
            else:
                if self.overlay_visible:
                    self.hide()

    @abc.abstractmethod
    def update_state(self):
        pass

    def hide(self):
        if self.is_minimize_on_lost_focus and not self.is_draggable_window:
            self.toplevel.withdraw()
            self.overlay_visible = False

    def show(self):
        ConfigReader.ReloadableConfig.reload()
        self.toplevel.deiconify()
        self.overlay_visible = True
