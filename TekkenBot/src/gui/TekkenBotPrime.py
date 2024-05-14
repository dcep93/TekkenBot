from ..gui import t_tkinter, FrameDataOverlay
from ..frame_data import Database
from ..game_parser import GameLog, GameReader, ScriptedGame
from ..misc import Flags, Path

import os
import sys
import time
import traceback

class TekkenBotPrime(t_tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.text = init_tk(self)
        self.geometry('1600x420+0+0')

        self.game_log = GameLog.GameLog()
        if Flags.Flags.pickle_dest is not None:
            game_reader = ScriptedGame.Recorder()
        elif Flags.Flags.pickle_src is not None:
            game_reader = ScriptedGame.Reader()
        else:
            game_reader = GameReader.GameReader()
        self.game_reader = game_reader
        self.game_reader.test_failure()
        self.overlay = FrameDataOverlay.FrameDataOverlay()

        self.update()
        if Flags.Flags.pickle_src is None:
            self.update_restarter()

    def update(self):
        now = time.time()
        self.last_update = now
        try:
            self.game_log.update(self.game_reader, self.overlay)
        except:
            print(traceback.format_exc())
            if Flags.Flags.debug:
                import os
                os._exit(0)
        finally:
            after = time.time()

            elapsed_ms = 1000*(after - now)
            wait_ms = self.game_reader.get_update_wait_ms(elapsed_ms)
            if wait_ms >= 0:
                self.after(wait_ms, self.update)

    def update_restarter(self):
        restart_seconds = 10
        if self.last_update + restart_seconds < time.time():
            print("something broke? restarting")
            self.update()
        self.after(1000 * restart_seconds, self.update_restarter)

t = TekkenBotPrime()
