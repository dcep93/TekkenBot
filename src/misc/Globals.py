from frame_data import Database
from game_parser import GameLog, GameReader, ScriptedGame
from gui import OverlayFamily
from misc import Flags

class Globals:
    game_log = None
    game_reader = None
    overlay_family = None
    after = None

    @classmethod
    def init(cls, after):
        cls.after = after

        cls.game_log = GameLog.GameLog()

        if Flags.Flags.pickle_dest is not None:
            game_reader = ScriptedGame.Recorder(Flags.Flags.pickle_dest)
        elif Flags.Flags.pickle_src is not None:
            game_reader = ScriptedGame.Reader(Flags.Flags.pickle_src, Flags.Flags.fast)
        else:
            game_reader = GameReader.GameReader()
        cls.game_reader = game_reader

        cls.overlay_family = OverlayFamily.OverlayFamily()

        Database.populate_database()

