import os
import time
import sys

from . import t_tkinter
from misc import Globals, Path

class TekkenBotPrime(t_tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.init_tk()
        self.print_folder()

        Globals.Globals.init()
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
        now = time.time()
        self.last_update = now
        self.update_restarter()
        Globals.Globals.game_log.update()
        after = time.time()

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
