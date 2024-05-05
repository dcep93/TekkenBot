import os
import time
import sys

import traceback

from . import t_tkinter, FrameDataOverlay
from frame_data import Database
from game_parser import GameLog, GameReader, ScriptedGame
from misc import Flags, Path, Shared

class TekkenBotPrime(t_tkinter.Tk):
    def __init__(self):
        super().__init__()
        init_tk(self)
        self.geometry('1600x420+0+0')

        Shared.Shared.game_log = GameLog.GameLog()
        if Flags.Flags.pickle_dest is not None:
            game_reader = ScriptedGame.Recorder()
        elif Flags.Flags.pickle_src is not None:
            game_reader = ScriptedGame.Reader()
        else:
            game_reader = GameReader.GameReader()
        Shared.Shared.game_reader = game_reader
        self.overlay = FrameDataOverlay.FrameDataOverlay()

        Database.initialize()

        self.update()
        if Flags.Flags.pickle_src is None:
            self.update_restarter()

    def update(self):
        game_reader = Shared.Shared.game_reader
        now = time.time()
        self.last_update = now
        try:
            Shared.Shared.game_log.update(game_reader, self.overlay)
        except:
            print(traceback.format_exc())
            if Flags.Flags.debug:
                import os
                os._exit(0)
        finally:
            after = time.time()

            elapsed_ms = 1000*(after - now)
            wait_ms = game_reader.get_update_wait_ms(elapsed_ms)
            if wait_ms >= 0:
                self.after(wait_ms, self.update)

    def update_restarter(self):
        restart_seconds = 10
        if self.last_update + restart_seconds < time.time():
            print("something broke? restarting")
            self.update()
        self.after(1000 * restart_seconds, self.update_restarter)

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
        if self.stdout:
            self.stdout.write(s)

    def flush(self):
        pass

def init_tk(tk):
    tk.wm_title("dcep93/TekkenBot")
    tk.iconbitmap(Path.path('./img/tekken_bot_close.ico'))

    text = t_tkinter.Text(tk, wrap="word")
    stdout = sys.stdout
    sys.stdout = TextRedirector(text, stdout, "stdout")
    stderr = sys.stderr
    sys.stderr = TextRedirector(text, stderr, "stderr")
    text.tag_configure("stderr", foreground="#b22222")

    text.pack(fill=t_tkinter.BOTH)
