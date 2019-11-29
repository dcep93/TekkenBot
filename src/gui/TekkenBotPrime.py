from tkinter import *
from tkinter.ttk import *
from . import FrameDataOverlay as fdo
from . import Overlay as ovr
from . import TimelineOverlay as tlo
from . import CommandInputOverlay as cio
from . import MatchStatOverlay as mso
from . import DebugInfoOverlay as dio
from misc import ConfigReader
from launcher._FrameDataLauncher import FrameDataLauncher
import time
from enum import Enum
from misc.Path import path
import misc.VersionChecker
import webbrowser

class TekkenBotPrime(Tk):
    def __init__(self):
        self.overlay = None

        self.init_tk()
        self.print_readme()
        self.add_menu_cascade()
        self.add_columns_cascade()
        self.add_display_cascade()
        self.add_color_schema_cascade()
        self.add_mode_cascade()
        self.add_version_cascade()
        self.configure_grid()
        self.update_launcher()
        self.overlay.hide()

    def init_tk(self):
        Tk.__init__(self)
        self.wm_title("dcep93/TekkenBot")
        self.iconbitmap('./TekkenData/tekken_bot_close.ico')

        self.color_scheme_config = ConfigReader.ConfigReader("color_scheme")

        self.menu = Menu(self)
        self.configure(menu=self.menu)

        self.text = Text(self, wrap="word")
        self.stdout = sys.stdout
        sys.stdout = TextRedirector(self.text, self.stdout, "stdout")
        self.stderr = sys.stderr
        sys.stderr = TextRedirector(self.text, self.stderr, "stderr")
        self.text.tag_configure("stderr", foreground="#b22222")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def print_readme(self):
        try:
            with open(path + "TekkenData/tekken_bot_readme.txt") as fr:
                lines = fr.readlines()
            for line in lines: print(line.strip())
        except:
            print("Error reading readme file.")

    def add_menu_cascade(self):
        print("Tekken Bot Starting...")
        self.launcher = FrameDataLauncher(False)

        self.overlay = fdo.FrameDataOverlay(self, self.launcher)

        self.tekken_bot_menu = Menu(self.menu)

        self.menu.add_cascade(label="Tekken Bot", menu=self.tekken_bot_menu)

    def add_columns_cascade(self):
        self.checkbox_dict = {}
        self.column_menu = Menu(self.menu)
        for i, enum in enumerate(fdo.DataColumns):
            bool = self.overlay.redirector.columns_to_print[i]
            self.add_checkbox(self.column_menu, enum, "{} ({})".format(enum.name.replace('X', ' ').strip(), fdo.DataColumnsToMenuNames[enum]), bool, self.changed_columns)
        self.menu.add_cascade(label='Columns', menu=self.column_menu)

    def add_display_cascade(self):
        self.display_menu = Menu(self.menu)
        for enum in ovr.DisplaySettings:
            default = self.overlay.tekken_config.get_property(ovr.DisplaySettings.config_name(), enum.name, False)
            self.add_checkbox(self.display_menu, enum, enum.name, default, self.changed_display)
        self.menu.add_cascade(label="Display", menu=self.display_menu)

    def add_color_schema_cascade(self):
        self.color_scheme_menu = Menu(self.menu)
        self.scheme_var = StringVar()
        for section in self.color_scheme_config.parser.sections():
            if section not in ("Comments", "Current"):
                self.color_scheme_menu.add_radiobutton(label=section, variable=self.scheme_var, value=section, command=lambda : self.changed_color_scheme(self.scheme_var.get()))
        self.menu.add_cascade(label="Color Scheme", menu=self.color_scheme_menu)

    def add_mode_cascade(self):
        self.overlay_mode_menu = Menu(self.menu)
        self.overlay_var = StringVar()
        for mode in OverlayMode:
            self.overlay_mode_menu.add_radiobutton(label=OverlayModeToDisplayName[mode], variable=self.overlay_var, value=mode.name, command=lambda : self.changed_mode(self.overlay_var.get()))
        self.menu.add_cascade(label="Mode", menu=self.overlay_mode_menu)
        self.mode = OverlayMode.FrameData

    def add_version_cascade(self):
        self.tekken_bot_menu = Menu(self.menu)
        self.menu.add_cascade(label="Version", menu=self.tekken_bot_menu)

    def configure_grid(self):
        self.text.grid(row = 2, column = 0, columnspan=2, sticky=N+S+E+W)
        #self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        #self.grid_columnconfigure(1, weight=1)

        self.geometry(str(920) + 'x' + str(720))

    def add_checkbox(self, menu, lookup_key, display_string, default_value, button_command):
        var = BooleanVar()
        var.set(default_value)
        self.checkbox_dict[lookup_key] = var
        menu.add_checkbutton(label=display_string, onvalue=True, offvalue=False, variable=var, command = button_command)

    def changed_color_scheme(self, section, do_reboot=True):
        for enum in fdo.ColorSchemeEnum:
            fdo.CurrentColorScheme.dict[enum] = self.color_scheme_config.get_property(section, enum.name, fdo.CurrentColorScheme.dict[enum])
            self.color_scheme_config.set_property("Current", enum.name, fdo.CurrentColorScheme.dict[enum])
        self.color_scheme_config.write()
        if do_reboot:
            self.reboot_overlay()

    def changed_mode(self, mode):
        self.stop_overlay()
        self.mode = OverlayMode[mode]
        if self.mode != OverlayMode.Off:
            self.start_overlay()

    def changed_columns(self):
        generated_columns = []
        for enum in fdo.DataColumns:
            var = self.checkbox_dict[enum]
            generated_columns.append(var.get())
            if self.mode == OverlayMode.FrameData:
                self.overlay.update_column_to_print(enum, var.get())
        if self.mode == OverlayMode.FrameData:
            self.overlay.set_columns_to_print(generated_columns)

    def changed_display(self):
        for enum in ovr.DisplaySettings:
            var = self.checkbox_dict[enum]
            if self.overlay != None:
                self.overlay.tekken_config.set_property(ovr.DisplaySettings.config_name(), enum.name, var.get())
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
        if self.mode == OverlayMode.PunishCoach:
            self.overlay = pco.PunishCoachOverlay(self, self.launcher)
            self.overlay.hide()
        if self.mode == OverlayMode.MatchupRecord:
            self.overlay = mso.MatchStatOverlay(self, self.launcher)
            self.overlay.hide()
        if self.mode == OverlayMode.DebugInfo:
            self.overlay = dio.DebugInfoOverlay(self, self.launcher)
            self.overlay.hide()

    def reboot_overlay(self):
        self.stop_overlay()
        self.start_overlay()

    def update_launcher(self):
        time1 = time.time()
        successful_update = self.launcher.Update()

        if self.overlay != None:
            self.overlay.update_location()
            if successful_update:
                self.overlay.update_state()
        time2 = time.time()
        elapsed_time = 1000 * (time2 - time1)
        if self.launcher.gameState.gameReader.HasWorkingPID():
            self.after(max(2, 8 - int(round(elapsed_time))), self.update_launcher)
        else:
            self.after(1000, self.update_launcher)

    def on_closing(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
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

class OverlayMode(Enum):
    Off = 0
    FrameData = 1
    #Timeline = 2
    CommandInput = 3

OverlayModeToDisplayName = {
    OverlayMode.Off : 'Off',
    OverlayMode.FrameData: 'Frame Data',
    OverlayMode.CommandInput: 'Command Inputs (and cancel window)',
}
