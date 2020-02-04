import sys

class Flags:
    pickle_src = None
    pickle_dest = None
    fast = None
    generate_pkl = None
    generate_wait_s = None

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
        elif arg == '--generate':
            Flags.generate_pkl = sys.argv.pop(0)
        elif arg == '--generate-wait-s':
            generate_wait_s = sys.argv.pop(0)
            Flags.generate_wait_s = int(generate_wait_s)
        else:
            temp_argv.append(arg)
    sys.argv = temp_argv
