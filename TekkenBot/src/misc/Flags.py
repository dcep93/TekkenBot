import sys

class Flags:
    pickle_src = ""
    pickle_dest = ""
    fast = False
    debug = False

def handle() -> None:
    temp_argv = []
    while sys.argv:
        arg = sys.argv.pop(0)
        if arg == '--src':
            pickle_src = sys.argv.pop(0)
            Flags.pickle_src = pickle_src
        elif arg == '--dest':
            pickle_dest = sys.argv.pop(0)
            Flags.pickle_dest = pickle_dest
        elif arg == '--fast':
            Flags.fast = True
        elif arg == '--debug':
            Flags.debug = True
        elif arg.startswith('-'):
            print('Flag not recognized', arg)
            exit()
        else:
            temp_argv.append(arg)
    sys.argv = temp_argv
