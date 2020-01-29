import enum
import time
import sys

from . import Overlay as ovr
from . import FrameDataOverlay as fdo
from . import CommandInputOverlay as cio

from . import t_tkinter

import game_parser.GameState

import misc.Path
import windows

class TekkenBotPrime(t_tkinter.Tk):
    def __init__(self):
        super().__init__()

        print("Tekken Bot Starting...")

        self.overlay = None

        self.init_tk()
        self.init_config()
        self.init_view()

        self.tekken_state = game_parser.GameState.GameState()

        self.init_frame_data()

        self.update()

    def init_tk(self):
        self.wm_title("dcep93/TekkenBot")
        self.iconbitmap(misc.Path.path('assets/tekken_bot_close.ico'))

        self.menu = t_tkinter.Menu(self)
        self.configure(menu=self.menu)

        self.text = t_tkinter.Text(self, wrap="word")
        stdout = sys.stdout
        sys.stdout = TextRedirector(self.text, stdout, "stdout")
        stderr = sys.stderr
        sys.stderr = TextRedirector(self.text, stderr, "stderr")
        self.text.tag_configure("stderr", foreground="#b22222")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_config(self):
        self.tekken_config = misc.ConfigReader.ConfigReader('tekken_bot')

    def init_view(self):
        self.add_menu_cascade()
        self.add_columns_cascade()
        self.add_display_cascade()
        self.add_mode_cascade()
        self.configure_grid()

    def add_menu_cascade(self):
        tekken_bot_menu = t_tkinter.Menu(self.menu)
        self.menu.add_cascade(label="Tekken Bot", menu=tekken_bot_menu)

    def add_columns_cascade(self):
        column_menu = t_tkinter.Menu(self.menu)
        all_checked = self.tekken_config.get_all(fdo.DataColumns, True)
        for enum in fdo.DataColumns:
            checked = all_checked[enum]
            name = "%s (%s)" % (enum.name, enum.value)
            self.add_checkbox(column_menu, enum, name, checked, self.changed_columns)
        self.menu.add_cascade(label='Columns', menu=column_menu)

    def add_display_cascade(self):
        display_menu = t_tkinter.Menu(self.menu)
        all_checked = self.tekken_config.get_all(ovr.DisplaySettings, False)
        for enum in ovr.DisplaySettings:
            checked = all_checked[enum]
            self.add_checkbox(display_menu, enum, enum.value, checked, self.changed_display)
        self.menu.add_cascade(label="Display", menu=display_menu)

    def add_mode_cascade(self):
        overlay_mode_menu = t_tkinter.Menu(self.menu)
        self.overlay_var = t_tkinter.StringVar()
        for mode in OverlayMode:
            label = mode.value
            command = (lambda i: lambda: self.changed_mode(i))(mode)
            overlay_mode_menu.add_radiobutton(label=label,variable=self.overlay_var,value=mode,command=command)
        self.menu.add_cascade(label="Mode", menu=overlay_mode_menu)
        self.mode = OverlayMode.FrameData

    def configure_grid(self):
        self.text.grid(row=2, column=0, columnspan=2, sticky=t_tkinter.NSEW)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.geometry('1020x420')

    def add_checkbox(self, menu, enum, display_string, default_value, button_command):
        var = t_tkinter.BooleanVar()
        var.set(default_value)
        menu.add_checkbutton(label=display_string, onvalue=True, offvalue=False, variable=var, command=lambda: button_command(enum, var))

    def changed_mode(self, mode):
        self.stop_overlay()
        self.mode = mode
        if self.mode != OverlayMode.Off:
            self.start_overlay()

    def changed_display(self, enum, var):
        if self.overlay is not None:
            self.tekken_config.set_property(enum, var.get())
            self.tekken_config.write()
        self.reboot_overlay()

    def stop_overlay(self):
        if self.overlay != None:
            self.overlay.toplevel.destroy()
            self.overlay = None

    def start_overlay(self):
        overlay = OverlayModeToOverlay[self.mode]
        if overlay is not None:
            self.overlay = overlay(self, self.tekken_state)
            self.overlay.hide()

    def reboot_overlay(self):
        self.stop_overlay()
        self.start_overlay()

    def update(self):
        now = time.time()
        successful_update = self.tekken_state.Update()
        after = time.time()

        if self.overlay != None:
            self.overlay.update_location()
            if successful_update:
                self.overlay.update_state()

        elapsed_ms = after - now
        wait_ms = self.tekken_state.gameReader.getUpdateWaitMs(elapsed_ms)
        if wait_ms >= 0: self.after(wait_ms, self.update)

    def on_closing(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.destroy()

    def changed_columns(self, enum, var):
        if self.mode == OverlayMode.FrameData:
            self.overlay.update_column_to_print(enum, var.get())

    def init_frame_data(self):
        self.overlay_var.set(OverlayMode.FrameData)
        self.changed_mode(OverlayMode.FrameData)

class TextRedirector:
    def __init__(self, widget, stdout, tag="stdout"):
        self.widget = widget
        self.stdout = stdout
        self.tag = tag

    def write(self, s):
        self.widget.configure(state="normal")
        self.widget.insert("end", s, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see('end')
        self.stdout.write(s)

    def flush(self):
        pass

@enum.unique
class OverlayMode(enum.Enum):
    Off = 'Off'
    FrameData = 'Frame Data'
    CommandInput = 'Command Inputs (and cancel window)'

OverlayModeToOverlay = {
    OverlayMode.Off: None,
    OverlayMode.FrameData: fdo.FrameDataOverlay,
    OverlayMode.CommandInput: cio.CommandInputOverlay,
}
