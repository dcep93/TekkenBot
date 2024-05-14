from ..misc import Path

import sys
import typing

valid = False
Tk = typing.Any
Text = typing.Any
try:
    from tkinter import *
    from tkinter.ttk import * # type: ignore
    import tkinter
    valid = True
except ModuleNotFoundError:
    pass

class TextRedirector:
    def __init__(self, widget: typing.Any, stdout: typing.Any, tag:str="stdout") -> None:
        self.widget = widget
        self.stdout = stdout
        self.tag = tag

    def write(self, s: str) -> None:
        self.widget.configure(state="normal")
        self.widget.insert("end", s, (self.tag,))
        self.widget.configure(state="disabled")
        self.widget.see('end')
        if self.stdout:
            self.stdout.write(s)

    def flush(self) -> None:
        pass

def init_tk(tk: Tk) -> Text:
    tk.wm_title("dcep93/TekkenBot")
    tk.iconbitmap(Path.path('./img/tekken_bot_close.ico'))

    text = Text(tk, wrap="word")
    sys.stdout = TextRedirector(text, sys.stdout, "stdout") # type: ignore
    sys.stderr = TextRedirector(text, sys.stderr, "stderr") # type: ignore
    text.tag_configure("stderr", foreground="#b22222")

    text.pack(fill=BOTH)
    return text
