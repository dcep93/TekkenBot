import pickle
import signal
import sys
import time

from . import GameReader

class Recorder(GameReader.GameReader):
    def __init__(self, pickle_dest):
        super().__init__()
        self.pickle_dest = pickle_dest
        self.reset(False)
        signal.signal(signal.SIGINT, lambda _,__: self.save_and_quit())

    def reset(self, active=None):
        if active is not None:
            self.active = active
        self.all_datas = []
        self.num_datas = 0

    def get_updated_state(self, rollback_frame):
        game_snapshot = super().get_updated_state(rollback_frame)
        if self.active:
            self.record_data(rollback_frame == 0, game_snapshot)
        return game_snapshot

    def record_data(self, new_update, game_snapshot):
        self.num_datas += 1
        if new_update:
            now = time.time()
            self.all_datas.append((now, [game_snapshot]))
        else:
            self.all_datas[-1][1].append(game_snapshot)

    def dump(self):
        self.active = False
        print('writing', self.num_datas, len(self.all_datas))
        with open(self.pickle_dest, 'wb') as fh:
            pickle.dump(self.all_datas, fh)
        self.reset()

    def save_and_quit(self):
        self.dump()
        sys.exit(0)

class Reader(GameReader.GameReader):
    def __init__(self, pickle_src, fast):
        super().__init__()
        self.pickle_src = pickle_src
        self.fast = fast

        print('loading', self.pickle_src, self.fast)
        with open(self.pickle_src, 'rb') as fh:
            self.all_datas = pickle.load(fh)

        if not self.all_datas:
            raise Exception("no data in pickle")

        self.offset = time.time() - self.load()

    def load(self):
        timestamp, self.datas = self.all_datas.pop(0)
        return timestamp

    def get_update_wait_ms(self, _):
        if len(self.all_datas) == 0:
            print("done with pickle")
            if self.fast:
                sys.exit(0)
            return -1

        next_timestamp = self.load()
        if self.fast:
            return 0
        wait_s = next_timestamp + self.offset - time.time()
        wait_ms = max(int(wait_s * 1000), 0)
        return wait_ms

    def get_updated_state(self, _):
        if len(self.datas) == 0:
            return None
        return self.datas.pop(0)
