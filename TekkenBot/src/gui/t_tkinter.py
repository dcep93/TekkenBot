# type:ignore

valid = False
try:
    from tkinter import *
    from tkinter.ttk import *
    import tkinter
    valid = True
except ModuleNotFoundError:
    class Tk:
        pass

