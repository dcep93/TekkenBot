import pickle

from . import Database
from misc import Flags
# will create a pickle of Database.histories
# will consume that pickle and http://rbnorway.org/t7-frame-data/ to build a csv
class Generator:
    def __init__(self, gui):
        self.gui = gui

    def record(self):
        print("writing Database.History pickle to %s" % Flags.Flags.generate_pkl)
        histories = {move_id: dict(history.counts) for move_id, history in Database.histories.items()}
        with open(Flags.Flags.generate_pkl, 'wb') as fh:
            pickle.dump(histories, fh)
        self.gui.after(1000 * Flags.Flags.generate_wait_s, self.record)

    @staticmethod
    def build_csv():
        pass
