import enum
import os
import time
import sys

from . import Overlay, CommandInputOverlay, FrameDataOverlay, t_tkinter
from frame_data import Database, DataColumns
from game_parser import GameState
from misc import ConfigReader, Flags, Globals, Path
from record import Record, Replay

class TekkenBotPrime(t_tkinter.Tk):
    def __init__(self):
        super().__init__()

        print("Tekken Bot Starting...")

        self.overlay = None
        self.overlay_var = None
        self.mode = None
        self.last_update = None

        self.init_tk()
        self.init_config()
        self.init_view()

        self.print_folder()

        Database.try_to_populate_database()

        Globals.Globals.tekken_state = GameState.GameState()

        self.init_frame_data()

        self.update()
        self.update_restarter()

    def init_tk(self):
        self.wm_title("dcep93/TekkenBot")
        self.iconbitmap(Path.path('./img/tekken_bot_close.ico'))

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
        self.tekken_config = ConfigReader.ConfigReader('tekken_bot')

    def init_view(self):
        self.add_menu_cascade()
        self.add_columns_cascade()
        self.add_display_cascade()
        self.add_mode_cascade()
        self.configure_grid()

    def add_menu_cascade(self):
        tekken_bot_menu = t_tkinter.Menu(self.menu, tearoff=False)
        Globals.Globals.master = self
        tekken_bot_menu.add_command(label="record single", command=Record.record_single)
        tekken_bot_menu.add_command(label="record both", command=Record.record_both)
        tekken_bot_menu.add_command(label="end recording", command=Record.record_end)
        tekken_bot_menu.add_command(label="replay", command=Replay.replay)
        self.menu.add_cascade(label="Tekken Bot", menu=tekken_bot_menu)

    def add_columns_cascade(self):
        column_menu = t_tkinter.Menu(self.menu, tearoff=False)
        all_checked = self.tekken_config.get_all(DataColumns.DataColumns, True)
        for col in DataColumns.DataColumns:
            checked = all_checked[col]
            name = "%s (%s)" % (col.name, col.value)
            self.add_checkbox(column_menu, col, name, checked, self.changed_columns)
        self.menu.add_cascade(label='Columns', menu=column_menu)

    def add_display_cascade(self):
        display_menu = t_tkinter.Menu(self.menu, tearoff=False)
        all_checked = self.tekken_config.get_all(Overlay.DisplaySettings, None)
        for setting in Overlay.DisplaySettings:
            checked = all_checked[setting]
            self.add_checkbox(display_menu, setting, setting.value, checked, self.changed_display)
        self.menu.add_cascade(label="Display", menu=display_menu)

    def add_mode_cascade(self):
        overlay_mode_menu = t_tkinter.Menu(self.menu, tearoff=False)
        self.overlay_var = t_tkinter.StringVar()
        for mode in OverlayMode:
            label = mode.value
            command = (lambda i: lambda: self.changed_mode(i))(mode)
            overlay_mode_menu.add_radiobutton(label=label, variable=self.overlay_var, value=mode, command=command)
        self.menu.add_cascade(label="Mode", menu=overlay_mode_menu)
        self.mode = OverlayMode.FrameData

    def configure_grid(self):
        self.text.grid(row=2, column=0, columnspan=2, sticky=t_tkinter.NSEW)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.geometry('1720x420')

    def add_checkbox(self, menu, enum, display_string, default_value, button_command):
        var = t_tkinter.BooleanVar()
        var.set(bool(default_value))
        menu.add_checkbutton(label=display_string, onvalue=True, offvalue=False, variable=var, command=lambda: button_command(enum, var))

    def changed_mode(self, mode):
        self.stop_overlay()
        self.mode = mode
        if self.mode != OverlayMode.Off:
            self.start_overlay()

    def changed_display(self, prop, var):
        if self.overlay is not None:
            self.tekken_config.set_property(prop, var.get())
            self.tekken_config.write()
        self.reboot_overlay()

    def stop_overlay(self):
        if self.overlay is not None:
            self.overlay.toplevel.destroy()
            self.overlay = None

    def start_overlay(self):
        overlay = overlay_mode_to_overlay[self.mode]
        if overlay is not None:
            self.overlay = overlay()
            self.overlay.hide()

    def reboot_overlay(self):
        self.stop_overlay()
        self.start_overlay()

    def update(self):
        now = time.time()
        self.last_update = now
        Globals.Globals.tekken_state.update(self.overlay)
        after = time.time()

        if self.overlay is not None:
            self.overlay.update_location()

        elapsed_ms = after - now
        wait_ms = Globals.Globals.game_reader.get_update_wait_ms(elapsed_ms)
        if wait_ms >= 0:
            self.after(wait_ms, self.update)

    def update_restarter(self):
        restart_seconds = 10
        if self.last_update + restart_seconds < time.time():
            print("something broke? restarting")
            self.update()
        self.after(1000 * restart_seconds, self.update_restarter)

    def on_closing(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.destroy()

    def changed_columns(self, col, var):
        if self.mode == OverlayMode.FrameData:
            self.overlay.update_column_to_print(col, var.get())

    def init_frame_data(self):
        self.overlay_var.set(OverlayMode.FrameData)
        self.changed_mode(OverlayMode.FrameData)

    def print_folder(self):
        main = os.path.abspath(sys.argv[0])
        folder = os.path.basename(os.path.dirname(main))
        if folder.startswith('Tekken'):
            print(folder)

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

overlay_mode_to_overlay = {
    OverlayMode.Off: None,
    OverlayMode.FrameData: FrameDataOverlay.FrameDataOverlay,
    OverlayMode.CommandInput: CommandInputOverlay.CommandInputOverlay,
}
