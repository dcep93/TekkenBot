"""
Our abstract overlay class provides shared tools for our overlays
"""

import abc
import enum
import platform

import misc.Path

from . import t_tkinter

class DisplaySettings(enum.Enum):
    overlay_on_bottom = enum.auto()
    overlay_as_draggable_window = enum.auto()
    only_appears_when_Tekken_7_has_focus = enum.auto()
    transparent_background = enum.auto()
    tiny_live_frame_data_numbers = enum.auto()

class ColorSchemeEnum(enum.Enum):
    background = enum.auto()
    transparent = enum.auto()
    p1_text = enum.auto()
    p2_text = enum.auto()
    system_text = enum.auto()
    advantage_plus = enum.auto()
    advantage_slight_minus = enum.auto()
    advantage_safe_minus = enum.auto()
    advantage_punishible = enum.auto()
    advantage_very_punishible = enum.auto()
    advantage_text = enum.auto()

class CurrentColorScheme:
    scheme = {
        ColorSchemeEnum.background : 'gray10',
        ColorSchemeEnum.transparent: 'white',
        ColorSchemeEnum.p1_text: '#93A1A1',
        ColorSchemeEnum.p2_text: '#586E75',
        ColorSchemeEnum.system_text: 'lawn green',
        ColorSchemeEnum.advantage_plus: 'DodgerBlue2',
        ColorSchemeEnum.advantage_slight_minus: 'ivory2',
        ColorSchemeEnum.advantage_safe_minus: 'ivory2',
        ColorSchemeEnum.advantage_punishible: 'orchid2',
        ColorSchemeEnum.advantage_very_punishible: 'deep pink',
        ColorSchemeEnum.advantage_text: 'black',
    }

class Overlay:
    def __init__(self, master, xy_size):
        window_name = self.get_name()
        print("Launching {}".format(window_name))
        self.master = master

        self.set_config()

        self.overlay_visible = False
        self.toplevel = t_tkinter.Toplevel()

        self.toplevel.wm_title(window_name)

        self.toplevel.attributes("-topmost", True)

        self.background_color = CurrentColorScheme.scheme[ColorSchemeEnum.background]

        self.tranparency_color = self.background_color
        self.toplevel.configure(background=self.tranparency_color)

        self.toplevel.iconbitmap(misc.Path.path('assets/tekken_bot_close.ico'))
        if not self.is_draggable_window:
            self.toplevel.overrideredirect(True)

        self.w, self.h = xy_size

        self.toplevel.geometry('%sx%s' % (self.w, self.h))

    def get_name(self):
        return self.__class__.__name__

    def set_config(self):
        g = self.master.tekken_config.get_property
        self.is_draggable_window = g(DisplaySettings.overlay_as_draggable_window, False)
        self.is_minimize_on_lost_focus = g(DisplaySettings.only_appears_when_Tekken_7_has_focus, True)
        self.is_transparency = g(DisplaySettings.transparent_background, 'Windows-7' not in platform.platform())
        self.is_overlay_on_top = not g(DisplaySettings.overlay_on_bottom, False)

    def update_location(self):
        if not self.is_draggable_window:
            tekken_rect = self.state.gameReader.GetWindowRect()
            if tekken_rect != None:
                x = (tekken_rect.right + tekken_rect.left) / 2 - self.w / 2
                if self.is_overlay_on_top:
                    y = tekken_rect.top
                else:
                    y = tekken_rect.bottom - self.h - 10
                self.toplevel.geometry('%dx%d+%d+%d' % (self.w, self.h, x, y))
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
        ReloadableConfig.reload()
        self.toplevel.deiconify()
        self.overlay_visible = True
