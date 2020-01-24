import pickle
import signal
import time

class Recorder:
    recording = False
    pickle_dest = None
    all_datas = []

    @classmethod
    def record(cls, pickle_dest):
        cls.recording = True
        cls.pickle_dest = pickle_dest
        signal.signal(signal.SIGQUIT, cls.save_and_quit)

    @classmethod
    def record_data(cls, new_update, gameData):
        if new_update:
            now = time.time()
            cls.all_datas.append((now, [gameData]))
        else:
            cls.all_datas[-1][1].append(gameData)

    @classmethod
    def save_and_quit(cls):
        with open(cls.pickle_dest, 'w') as fh:
            pickle.dump(cls.all_datas, fh)
        exit(1)

class ScriptedGameReader:
    def replay(self, gui):
        with open(self.pickle_src) as fh:
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
