import sys

class Flags:
    pickle_src = None
    pickle_dest = None
    fast = False
    no_movelist = False

def handle():
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
        elif arg == '--no-movelist':
            Flags.no_movelist = True
        elif arg.startswith('-'):
            print('Flag not recognized', arg)
            exit()
        else:
            temp_argv.append(arg)
    sys.argv = temp_argv
