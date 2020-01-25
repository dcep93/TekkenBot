import pickle
import signal
import time

from misc import Flags

class Recorder:
    recording = False
    all_datas = []
    num_datas = 0

    @classmethod
    def record(cls):
        print('recording')
        cls.recording = True
        signal.signal(signal.SIGINT, lambda _,__: cls.save_and_quit())

    @classmethod
    def record_data(cls, new_update, gameData):
        cls.num_datas += 1
        print('data', cls.num_datas, len(cls.all_datas))
        if new_update:
            now = time.time()
            cls.all_datas.append((now, [gameData]))
        else:
            cls.all_datas[-1][1].append(gameData)

    @classmethod
    def save_and_quit(cls):
        print('writing')
        with open(Flags.Flags.pickle_dest, 'wb') as fh:
            pickle.dump(cls.all_datas, fh)
        exit(1)

class ScriptedGameReader:
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
                time.sleep(wait)
                last_abs = now
            last_ref = timestamp

            self.datas = datas

            gui.tekken_state.Update()
            gui.update_overlay()

    def GetUpdatedState(self, buffer=None):
        return self.datas.pop(0)
