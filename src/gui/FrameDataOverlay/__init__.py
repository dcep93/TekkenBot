"""
A transparent frame data display that sits on top of Tekken.exe in windowed or borderless mode.
"""

import sys

from .. import Overlay
from .. import t_tkinter

from .Listener import *
from .FrameDataEntry import *

class Printer:
    unknown = '??'
    col_max_length = 10
    altColSizes = {}
    def __init__(self, widget, style, fa_var):
        self.widget = widget
        self.fa_var = fa_var
        self.style = style

        self.columns_to_print = None

        self.widget.tag_config("p1", foreground=Overlay.ColorSchemeEnum.p1_text.value)
        self.widget.tag_config("p2", foreground=Overlay.ColorSchemeEnum.p2_text.value)

        self.style.configure('.', background=Overlay.ColorSchemeEnum.advantage_slight_minus.value)

    def set_columns_to_print(self, booleans_for_columns):
        self.columns_to_print = booleans_for_columns
        self.populate_column_names()

    def populate_column_names(self):
        columnsEntry = {col:col.name for col in DataColumns}
        column_names = self.getFrameDataString(columnsEntry)
        prefix = self.getPrefix(True)
        spaces = " " * len(prefix)

        print(spaces + column_names)

        self.widget.configure(state="normal")
        self.widget.delete("1.0", "2.0")
        self.widget.insert("1.0", column_names + '\n')
        self.widget.configure(state="disabled")

    def get_background(self, fa):
        if fa <= -14:
            return Overlay.ColorSchemeEnum.advantage_very_punishible.value
        elif fa <= -10:
            return Overlay.ColorSchemeEnum.advantage_punishible.value
        elif fa <= -5:
            return Overlay.ColorSchemeEnum.advantage_safe_minus.value
        elif fa < 0:
            return Overlay.ColorSchemeEnum.advantage_slight_minus.value
        else:
            return Overlay.ColorSchemeEnum.advantage_plus.value

    def getPrefix(self, isP1):
        playerName = "p1" if isP1 else "p2"
        return "%s: " % playerName

    def print(self, isP1, frameDataEntry, floated, fa):
        lines = int(self.widget.index('end-1c').split('.')[0])
        max_lines = 5
        if lines > max_lines:
            r = lines - max_lines
            for _ in range(r):
                self.widget.configure(state="normal")
                self.widget.delete('2.0', '3.0')
                self.widget.configure(state="disabled")

        if not floated and fa is not None:
            background = self.get_background(int(fa))
            self.style.configure('.', background=background)

        self.fa_var.set(fa)
        text_tag = 'p1' if isP1 else 'p2'

        out = self.getFrameDataString(frameDataEntry)
        prefix = self.getPrefix(isP1)
        print("%s%s / NOW:%s" % (prefix, out, fa))

        out += "\n"
        self.widget.configure(state="normal")
        self.widget.insert("end", out, text_tag)
        self.widget.configure(state="disabled")
        self.widget.see('0.0')
        self.widget.yview('moveto', '.02')

    def getFrameDataString(self, frameDataEntry):
        values = [self.getValue(frameDataEntry, col) for col in DataColumns if self.columns_to_print[col]]
        return '|'.join(values)

    def getValue(self, frameDataEntry, col):
        if col in frameDataEntry:
            value = str(frameDataEntry[col])
        else:
            value = self.unknown
        
        if col in self.altColSizes:
            size = self.altColSizes[col]
        else:
            size = self.col_max_length
        diff = size - len(value)
        if diff <= 0: return value[:size]
        before = int(diff / 2)
        after = diff - before
        return (' ' * before) + value + (' ' * after)

class FrameDataOverlay(Overlay.Overlay):
    def __init__(self, master, state):
        super().__init__(master, (1400, 128))

        self.init_tkinter()

        self.listener = FrameDataListener(self.printer)
        self.state = state

    def update_state(self):
        self.listener.update(self.state)

    def init_tkinter(self):
        style = t_tkinter.Style()
        style.theme_use('alt')
        style.configure('.', background=self.background_color)
        style.configure('.', foreground=Overlay.ColorSchemeEnum.advantage_text.value)

        t_tkinter.Grid.columnconfigure(self.toplevel, 0, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 1, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 2, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 3, weight=1)
        t_tkinter.Grid.columnconfigure(self.toplevel, 4, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 5, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 6, weight=0)
        t_tkinter.Grid.rowconfigure(self.toplevel, 0, weight=1)
        t_tkinter.Grid.rowconfigure(self.toplevel, 1, weight=0)

        style.configure('TFrame', background=self.tranparency_color)
        self.fa_var = self.create_frame_advantage_label(1)

        self.l_margin = self.create_padding_frame(0)
        self.r_margin = self.create_padding_frame(5)
        self.l_seperator = self.create_padding_frame(2)
        self.r_seperator = self.create_padding_frame(4)

        self.text = self.create_textbox(3)

        self.printer = Printer(self.text, style, self.fa_var)

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.printer.set_columns_to_print(self.master.tekken_config.get_all(DataColumns, True))

        self.text.configure(state="disabled")

    def create_padding_frame(self, col):
        padding = t_tkinter.Frame(self.toplevel, width=10)
        padding.grid(row=0, column=col, rowspan=2, sticky=t_tkinter.NSEW)
        return padding

    def create_frame_advantage_label(self, col):
        frame_advantage_var = t_tkinter.StringVar()
        frame_advantage_label = t_tkinter.Label(self.toplevel, textvariable=frame_advantage_var, font=("Courier New", 44), width=4, anchor='c',
                                        borderwidth=1, relief='ridge')
        frame_advantage_label.grid(row=0, column=col)
        return frame_advantage_var

    def create_textbox(self, col):
        textbox = t_tkinter.Text(self.toplevel, font=("Courier New", 14), wrap=t_tkinter.NONE, highlightthickness=0, pady=0, relief='flat')
        textbox.grid(row=0, column=col, rowspan=2, sticky=t_tkinter.NSEW)
        textbox.configure(background=self.background_color)
        textbox.configure(foreground=Overlay.ColorSchemeEnum.system_text.value)
        return textbox

    def update_column_to_print(self, enum, value):
        self.printer.columns_to_print[enum] = value
        self.printer.populate_column_names()
        self.master.tekken_config.set_property(enum, value)
        self.master.tekken_config.write()
