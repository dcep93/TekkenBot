import sys
import traceback

sys.path.append('src')

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
        print(traceback.format_exc())
        print(e)
        # todo test for exe
        if not sys.__stdout__.isatty():
            input()

# pyinstaller seems to ignore second level imports
# dont need to call this function, just need
# to have the import statements there I guess
# https://stackoverflow.com/questions/7436132/pyinstaller-spec-file-importerror-no-module-named-blah
def import_for_pyinstaller():
    import tkinter
    import tkinter.ttk
    import ctypes
    import ctypes.wintypes
