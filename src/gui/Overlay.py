"""
Our abstract overlay class provides shared tools for our overlays
"""

import abc
import enum
import platform

import misc.ConfigReader
import misc.Path

from . import t_tkinter

class DisplaySettings(enum.Enum):
    overlay_on_bottom = -1
    overlay_as_draggable_window = 0
    only_appears_when_Tekken_7_has_focus = 1
    transparent_background = 2
    tiny_live_frame_data_numbers = 3

class ColorSchemeEnum(enum.Enum):
    background = 0
    transparent = 1
    p1_text = 2
    p2_text = 3
    system_text = 4
    advantage_plus = 5
    advantage_slight_minus = 6
    advantage_safe_minus = 7
    advantage_punishible = 8
    advantage_very_punishible = 9
    advantage_text = 10

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
    def get_name(self):
        return self.__class__.__name__

    def initialize(self, master, xy_size):
        self.master = master

        window_name = self.get_name()
        print("Launching {}".format(window_name))
        is_windows_7 = 'Windows-7' in platform.platform()

        g = self.master.tekken_config.get_property
        self.is_draggable_window = g(DisplaySettings.overlay_as_draggable_window, False)
        self.is_minimize_on_lost_focus = g(DisplaySettings.only_appears_when_Tekken_7_has_focus, True)
        self.is_transparency = g(DisplaySettings.transparent_background, not is_windows_7)
        self.is_overlay_on_top = not g(DisplaySettings.overlay_on_bottom, False)

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
