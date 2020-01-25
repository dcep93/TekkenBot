import pickle
import signal
import time

from misc import Flags

from . import TekkenGameReader

class Recorder(TekkenGameReader.TekkenGameReader):
    all_datas = []
    num_datas = 0
    active = True

    def __init__(self):
        super().__init__()
        signal.signal(signal.SIGINT, lambda _,__: self.save_and_quit())

    def GetUpdatedState(self, rollback_frame = 0):
        gameData = super().GetUpdatedState(rollback_frame)
        if self.active: self.record_data(rollback_frame == 0, gameData)
        return gameData

    @classmethod
    def record_data(cls, new_update, gameData):
        cls.num_datas += 1
        if new_update:
            now = time.time()
            cls.all_datas.append((now, [gameData]))
        else:
            cls.all_datas[-1][1].append(gameData)

    @classmethod
    def save_and_quit(cls):
        cls.active = False
        print('writing', cls.num_datas, len(cls.all_datas))
        with open(Flags.Flags.pickle_dest, 'wb') as fh:
            pickle.dump(cls.all_datas, fh)
        exit(1)

class ScriptedGameReader(TekkenGameReader.TekkenGameReader):
    def replay(self, gui):
        with open(Flags.Flags.pickle_src, 'rb') as fh:
            all_datas = pickle.load(fh)

        gui.tekken_state.gameReader = self

        last_ref = None
        last_abs = time.time()
        for timestamp, datas in all_datas:
            if last_ref is not None:
                total_wait = timestamp - last_ref
                now = time.time()
                wait = total_wait - (now - last_abs)
                if wait > 0: time.sleep(wait)
                last_abs = now
            last_ref = timestamp

            self.datas = datas

            gui.tekken_state.Update()
            gui.update_overlay()

    def GetUpdatedState(self, buffer=None):
        return self.datas.pop(0)
