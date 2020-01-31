import sys

class Flags:
    pickle_src = None
    pickle_dest = None
    fast = None

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
            fast_raw = sys.argv.pop(0)
            Flags.fast = int(fast_raw)
        else:
            temp_argv.append(arg)
    sys.argv = temp_argv
