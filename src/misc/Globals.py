from frame_data import Database
from game_parser import GameLog, GameReader, ScriptedGame
from gui import FrameDataOverlay
from misc import Flags

class Globals:
    master = None
    game_log = None
    game_reader = None
    overlay = None

    @classmethod
    def init(cls, master):
        cls.master = master
        cls.game_log = GameLog.GameLog()

        if Flags.Flags.pickle_dest is not None:
            game_reader = ScriptedGame.Recorder()
        elif Flags.Flags.pickle_src is not None:
            game_reader = ScriptedGame.Reader()
        else:
            game_reader = GameReader.GameReader()
        cls.game_reader = game_reader

        cls.overlay = FrameDataOverlay.FrameDataOverlay()

        Database.populate_database()

