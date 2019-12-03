import enum
import time
import sys

from . import Overlay as ovr
from . import FrameDataOverlay as fdo
from . import CommandInputOverlay as cio

from . import tkinter

import misc.Path
import windows

import launcher._FrameDataLauncher

# todo
# Frame specific stuff

class TekkenBotPrime(tkinter.Tk):
    def __init__(self):
        self.overlay = None

        self.init_tk()
        print("Tekken Bot Starting...")
        self.add_menu_cascade()
        self.add_columns_cascade()
        self.add_display_cascade()
        self.add_mode_cascade()
        self.configure_grid()
        self.update_launcher()
        self.overlay.hide()

    def init_tk(self):
        tkinter.Tk.__init__(self)
        self.wm_title("dcep93/TekkenBot")
        self.iconbitmap(misc.Path.path('src/assets/tekken_bot_close.ico'))

        self.menu = tkinter.Menu(self)
        self.configure(menu=self.menu)

        self.text = tkinter.Text(self, wrap="word")
        stdout = sys.stdout
        sys.stdout = TextRedirector(self.text, stdout, "stdout")
        stderr = sys.stderr
        sys.stderr = TextRedirector(self.text, stderr, "stderr")
        self.text.tag_configure("stderr", foreground="#b22222")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_menu_cascade(self):
        self.launcher = launcher._FrameDataLauncher.FrameDataLauncher(False)

        self.overlay = fdo.FrameDataOverlay(self, self.launcher)

        tekken_bot_menu = tkinter.Menu(self.menu)

        self.menu.add_cascade(label="Tekken Bot", menu=tekken_bot_menu)

    def add_columns_cascade(self):
        self.checkbox_dict = {}
        column_menu = tkinter.Menu(self.menu)
        for i, enum in enumerate(fdo.DataColumns):
            checked = self.overlay.redirector.columns_to_print[i]
            name = "{} ({})".format(enum.name.replace('X', ' ').strip(), fdo.DataColumnsToMenuNames[enum])
            self.add_checkbox(column_menu, enum, name, checked, self.changed_columns)
        self.menu.add_cascade(label='Columns', menu=column_menu)

    def add_display_cascade(self):
        display_menu = tkinter.Menu(self.menu)
        for enum in ovr.DisplaySettings:
            default = self.overlay.tekken_config.get_property(enum, False)
            self.add_checkbox(display_menu, enum, enum.name, default, self.changed_display)
        self.menu.add_cascade(label="Display", menu=display_menu)

    def add_mode_cascade(self):
        overlay_mode_menu = tkinter.Menu(self.menu)
        self.overlay_var = tkinter.StringVar()
        for mode in OverlayMode:
            label = OverlayModeToDisplayName[mode]
            command = lambda: self.changed_mode(self.overlay_var.get())
            overlay_mode_menu.add_radiobutton(label=label,variable=self.overlay_var,value=mode.name,command=command)
        self.menu.add_cascade(label="Mode", menu=overlay_mode_menu)
        self.mode = OverlayMode.FrameData

    def configure_grid(self):
        self.text.grid(row = 2, column = 0, columnspan=2, sticky=tkinter.N+tkinter.S+tkinter.E+tkinter.W)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.geometry(str(920) + 'x' + str(720))

    def add_checkbox(self, menu, lookup_key, display_string, default_value, button_command):
        var = tkinter.BooleanVar()
        var.set(default_value)
        self.checkbox_dict[lookup_key] = var
        menu.add_checkbutton(label=display_string, onvalue=True, offvalue=False, variable=var, command = button_command)

    def changed_mode(self, mode):
        self.stop_overlay()
        self.mode = OverlayMode[mode]
        if self.mode != OverlayMode.Off:
            self.start_overlay()

    def changed_columns(self):
        if self.mode == OverlayMode.FrameData:
            generated_columns = [self.checkbox_dict[enum].get() for enum in fdo.DataColumns]
            self.overlay.set_columns_to_print(generated_columns)

    def changed_display(self):
        for enum in ovr.DisplaySettings:
            var = self.checkbox_dict[enum]
            if self.overlay != None:
                self.overlay.tekken_config.set_property(enum, var.get())
        if self.overlay != None:
            self.overlay.tekken_config.write()
        self.reboot_overlay()

    def stop_overlay(self):
        if self.overlay != None:
            self.overlay.toplevel.destroy()
            self.overlay = None

    def start_overlay(self):
        if self.mode == OverlayMode.FrameData:
            self.overlay = fdo.FrameDataOverlay(self, self.launcher)
            self.overlay.hide()
        if self.mode == OverlayMode.CommandInput:
            self.overlay = cio.CommandInputOverlay(self, self.launcher)
            self.overlay.hide()

    def reboot_overlay(self):
        self.stop_overlay()
        self.start_overlay()

    def update_launcher(self):
        if not windows.valid:
            print('Mac')
            return
        time1 = time.time()
        successful_update = self.launcher.Update()

        if self.overlay != None:
            self.overlay.update_location()
            if successful_update:
                self.overlay.update_state()
        time2 = time.time()
        if self.launcher.gameState.gameReader.HasWorkingPID():
            elapsed_time = 1000 * (time2 - time1)
            wait = max(2, 8 - int(round(elapsed_time)))
        else:
            wait = 1000
        self.after(wait, self.update_launcher)

    def on_closing(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.destroy()

class TextRedirector(object):
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

class OverlayMode(enum.Enum):
    Off = 0
    FrameData = 1
    #Timeline = 2
    CommandInput = 3

OverlayModeToDisplayName = {
    OverlayMode.Off : 'Off',
    OverlayMode.FrameData: 'Frame Data',
    OverlayMode.CommandInput: 'Command Inputs (and cancel window)',
}
