import sys

sys.path.append('src')

import traceback

from gui import TekkenBotPrime
from misc import Flags

def main():
    Flags.handle()
    app = TekkenBotPrime.TekkenBotPrime()
    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # todo test for exe
        if sys.__stdout__.isatty():
            raise e
        else:
            print(traceback.format_exc())
            print(e)
            print("died")
        input()

# pyinstaller seems to ignore imports in child scripts
# dont need to call this function, just need
# to have the import statements there I guess
# https://stackoverflow.com/questions/7436132/pyinstaller-spec-file-importerror-no-module-named-blah
def import_for_pyinstaller():
    import tkinter
    import tkinter.ttk
    import ctypes
    import ctypes.wintypes
