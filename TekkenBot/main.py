from .src.gui import TekkenBotPrime
from .src.misc import Flags, recorded_sha

import sys
import traceback

def main():
    print("https://github.com/dcep93/TekkenBot")
    print("sha:", recorded_sha.sha)
    Flags.handle()
    app = TekkenBotPrime.TekkenBotPrime()
    app.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if sys.__stdout__ and sys.__stdout__.isatty():
            raise e
        else:
            print(traceback.format_exc())
            print(e)
            print("died")

# pyinstaller seems to ignore imports in child scripts
# dont need to call this function, just need
# to have the import statements there I guess
# https://stackoverflow.com/questions/7436132/pyinstaller-spec-file-importerror-no-module-named-blah
def import_for_pyinstaller():
    import tkinter
    import tkinter.ttk
    import ctypes
    import ctypes.wintypes
