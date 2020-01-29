import pickle
import signal
import time

from misc import Flags
from . import GameReader
from . import MovelistParser

class Recorder(GameReader.GameReader):
    all_datas = []
    num_datas = 0
    active = True

    def __init__(self, pickle_dest):
        print("recording to %s" % pickle_dest)
        super().__init__()
        signal.signal(signal.SIGINT, lambda _,__: self.save_and_quit(pickle_dest))

    def GetUpdatedState(self, rollback_frame):
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
        MovelistParser.__getstate__ = self.movelistparser_getstate
        print('writing', cls.num_datas, len(cls.all_datas))
        with open(pickle_dest, 'wb') as fh:
            pickle.dump(cls.all_datas, fh)
        exit(1)

    # intended to assign as a different class method
    def movelistparser_getstate(movelistparser):
        state = movelistparser.__dict__.copy()
        state['bytes'] = state['bytes'].value
        return state

class Reader(GameReader.GameReader):
    def __init__(self, pickle_src):
        print("loading from %s" % pickle_src)
        super().__init__()

        cls = self.__class__
        with open(pickle_src, 'rb') as fh:
            cls.all_datas = pickle.load(fh)

        if not cls.all_datas:
            print("no data in pickle")
            exit(1)

        cls.offset = time.time() - cls.load()

    @classmethod
    def load(cls):
        timestamp, cls.datas = cls.all_datas.pop(0)
        return timestamp

    @classmethod
    def getUpdateWaitMs(cls, _):
        if len(cls.all_datas) == 0: return -1

        next_timestamp = cls.load()
        if Flags.Flags.fast: return 0
        wait_s = next_timestamp + cls.offset - time.time()
        wait_ms = max(int(wait_s * 1000), 0)
        return wait_ms

    @classmethod
    def GetUpdatedState(cls, _):
        return cls.datas.pop(0)
