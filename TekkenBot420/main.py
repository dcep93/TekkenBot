import sys
import traceback

if __name__ == "__main__":
    try:
        from src.main import main
        main.main()
    except Exception as e:
        print(traceback.format_exc())
        print(e)
        print("died")
        input()

# pyinstaller seems to ignore imports in child scripts
# dont need to call this function, just need
# to have the import statements there I guess
# https://stackoverflow.com/questions/7436132/pyinstaller-spec-file-importerror-no-module-named-blah


def import_for_pyinstaller() -> None:
    import tkinter
    import tkinter.ttk
    import ctypes
    import ctypes.wintypes
