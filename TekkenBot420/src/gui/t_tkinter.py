from ..misc import Path

import sys
import typing

from tkinter import *
import tkinter as _tkinter

tkinter = _tkinter

valid = False
try:
    from tkinter.ttk import *  # type: ignore
    valid = True
except ModuleNotFoundError:
    pass


class TextRedirector:
    def __init__(self, widget: typing.Any, stdout: typing.Any, tag: str = "stdout") -> None:
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


def init_tk(tk: Tk, **kwargs: int) -> Text:
    tk.wm_title("dcep93/TekkenBot")
    tk.iconbitmap(Path.path('./img/favicon.ico'))

    text = Text(tk, wrap="word")
    sys.stdout = TextRedirector(text, sys.stdout, "stdout")
    sys.stderr = TextRedirector(text, sys.stderr, "stderr")
    text.tag_configure("stderr", foreground="#b22222")

    text.pack(fill=BOTH, **kwargs)  # type: ignore

    return text
