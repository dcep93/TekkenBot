import os
import time
import sys

from . import t_tkinter, OverlayFamily
from frame_data import Database
from game_parser import GameLog, GameReader, ScriptedGame
from misc import Flags, Path
from record import Shared

class TekkenBotPrime(t_tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.init_tk()
        self.print_folder()

        self.game_log = Shared.Shared.game_log = GameLog.GameLog()
        if Flags.Flags.pickle_dest is not None:
            game_reader = ScriptedGame.Recorder(Flags.Flags.pickle_dest)
        elif Flags.Flags.pickle_src is not None:
            game_reader = ScriptedGame.Reader(Flags.Flags.pickle_src, Flags.Flags.fast)
        else:
            game_reader = GameReader.GameReader()
        self.game_reader = Shared.Shared.game_reader = game_reader
        self.overlay_family = OverlayFamily.OverlayFamily()

        Database.populate_database()

        self.update()

    def init_tk(self):
        self.wm_title("dcep93/TekkenBot")
        self.iconbitmap(Path.path('./img/tekken_bot_close.ico'))

        self.text = t_tkinter.Text(self, wrap="word")
        stdout = sys.stdout
        sys.stdout = TextRedirector(self.text, stdout, "stdout")
        stderr = sys.stderr
        sys.stderr = TextRedirector(self.text, stderr, "stderr")
        self.text.tag_configure("stderr", foreground="#b22222")

        self.text.pack(fill=t_tkinter.BOTH)

        self.geometry('1720x420')

    def update(self):
        game_reader = self.game_reader
        now = time.time()
        self.last_update = now
        self.update_restarter()
        self.game_log.update(game_reader, self.overlay_family)
        after = time.time()

        elapsed_ms = after - now
        wait_ms = game_reader.get_update_wait_ms(elapsed_ms)
        if wait_ms >= 0:
            self.after(wait_ms, self.update)

    def update_restarter(self):
        restart_seconds = 10
        if self.last_update + restart_seconds < time.time():
            print("something broke? restarting")
            self.update()
        self.after(1000 * restart_seconds, self.update_restarter)

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
