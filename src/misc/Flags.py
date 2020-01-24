import sys

import game_parser.ScriptedGameReader

def handle():
    while sys.argv:
        arg = sys.argv.pop(0)
        if arg == '--src':
            pickle_src = sys.argv.pop(0)
            game_parser.ScriptedGameReader.ScriptedGameReader.pickle_src = pickle_src
        elif arg == '--dest':
            pickle_src = sys.argv.pop(0)
            game_parser.ScriptedGameReader.Recorder.pickle_dest = pickle_dest
