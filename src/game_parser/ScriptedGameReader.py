import pickle
import signal
import time

from . import TekkenGameReader

class Recorder(TekkenGameReader.TekkenGameReader):
    all_datas = []
    num_datas = 0
    active = True

    def __init__(self, pickle_dest):
        super().__init__()
        signal.signal(signal.SIGINT, lambda _,__: self.save_and_quit(pickle_dest))

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
    def save_and_quit(cls, pickle_dest):
        cls.active = False
        print('writing', cls.num_datas, len(cls.all_datas))
        with open(pickle_dest, 'wb') as fh:
            pickle.dump(cls.all_datas, fh)
        exit(1)

class ScriptedGameReader(TekkenGameReader.TekkenGameReader):
    def replay(self, gui, pickle_src):
        with open(pickle_src, 'rb') as fh:
            self.all_datas = pickle.load(fh)

        if not self.all_datas:
            print("no data in pickle")
            exit(1)

        self.gui = gui

        print("replaying")

        self.offset = time.time() - self.all_datas[0][0]

        self.update()

    def update(self):
        timestamp, datas = self.all_datas.pop(0)

        self.datas = datas

        self.gui.tekken_state.Update()
        self.gui.update_overlay()

        if len(self.all_datas) > 0:
            next_timestamp = self.all_datas[0][0]
            wait_s = next_timestamp + self.offset - time.time()
            wait_ms = max(int(wait_s * 1000), 0)
            self.gui.after(wait_ms, self.update)

    def GetUpdatedState(self, buffer=None):
        return self.datas.pop(0)
