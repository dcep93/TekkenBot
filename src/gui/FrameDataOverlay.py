"""
A transparent frame data display that sits on top of Tekken.exe in windowed or borderless mode.
"""

import enum
import sys

from . import Overlay
from . import t_tkinter

from sidecar import FrameDataListener

@enum.unique
class DataColumns(enum.Enum):
    comm = 'input command'
    id = 'internal move id number'
    name = 'internal move name'
    type = 'attack type'
    st = 'startup frames'
    blo = 'frame advantage on block'
    hit = 'frame advantage on hit'
    ch = 'frame advantage on counter hit'
    act = 'active frame connected on / total active frames'
    T = 'how well move tracks during startup'
    tot = 'total number of frames in move'
    rec = 'frames before attacker can act'
    opp = 'frames before defender can act'
    notes = 'additional move properties'

class Printer:
    col_max_length = 8
    def __init__(self, widget, style, fa_p1_var, fa_p2_var):
        self.widget = widget
        self.fa_p1_var = fa_p1_var
        self.fa_p2_var = fa_p2_var
        self.style = style

        self.columns_to_print = None

        self.widget.tag_config("p1", foreground=Overlay.ColorSchemeEnum.p1_text.value)
        self.widget.tag_config("p2", foreground=Overlay.ColorSchemeEnum.p2_text.value)

        self.style.configure('.', background=Overlay.ColorSchemeEnum.advantage_slight_minus.value)

    def set_columns_to_print(self, booleans_for_columns):
        self.columns_to_print = booleans_for_columns
        self.populate_column_names()

    def populate_column_names(self):
        column_names = ''
        for enum in DataColumns:
            col_name = enum.name
            col_len = len(col_name)
            if self.columns_to_print[enum]:
                needed_spaces = self.col_max_length - col_len
                if col_len < self.col_max_length:
                    spaces_before = " " * int(needed_spaces / 2)
                    spaces_after = " " * (needed_spaces - len(spaces_before))
                    col_name = spaces_before + col_name + spaces_after
                column_names += '|%s' % col_name

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
            return Overlay.ColorSchemeEnum.advantage_plus

    def print(self, frameDataEntry):
        print(frameDataEntry)

        lines = int(self.widget.index('end-1c').split('.')[0])
        max_lines = 5
        if lines > max_lines:
            r = lines - max_lines
            for _ in range(r):
                self.widget.configure(state="normal")
                self.widget.delete('2.0', '3.0')
                self.widget.configure(state="disabled")

        fa = frameDataEntry.currentFrameAdvantage

        if fa != frameDataEntry.unknown:
            background = self.get_background(int(fa))
            self.style.configure('.', background=background)

        if frameDataEntry.isP1:
            self.fa_p1_var.set(fa)
            text_tag = 'p1'
        else:
            self.fa_p2_var.set(fa)
            text_tag = 'p2'

        print(self.columns_to_print)
        out = ""
        for col in data.split('|'):
            if self.columns_to_print[col]:
                col_value = col.replace(' ', '')
                col_value_len = len(col_value)

                if col_value_len < self.col_max_length:
                    needed_spaces = self.col_max_length - col_value_len
                    col_value = '%s%s%s' % (' ' * ((needed_spaces+1) / 2), col_value, ' ' * (needed_spaces / 2))
                
                out += '|%s' % col_value

        print("\n" + data)

        out += "\n"
        self.widget.configure(state="normal")
        self.widget.insert("end", out, text_tag)
        self.widget.configure(state="disabled")
        self.widget.see('0.0')
        self.widget.yview('moveto', '.02')

class FrameDataOverlay(Overlay.Overlay):
    def __init__(self, master, state):
        super().__init__(master, (1021, 86))

        self.init_tkinter()

        self.listener = FrameDataListener.FrameDataListener(self.printer)
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
        self.fa_p1_var, fa_p1_label = self.create_frame_advantage_label(1)
        self.fa_p2_var, fa_p2_label = self.create_frame_advantage_label(5)

        self.l_margin = self.create_padding_frame(0)
        self.r_margin = self.create_padding_frame(6)
        self.l_seperator = self.create_padding_frame(2)
        self.r_seperator = self.create_padding_frame(4)

        self.text = self.create_textbox(3)

        self.printer = Printer(self.text, style, self.fa_p1_var, self.fa_p2_var)

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
        frame_advantage_var.set('?')
        frame_advantage_label = t_tkinter.Label(self.toplevel, textvariable=frame_advantage_var, font=("Consolas", 44), width=4, anchor='c',
                                        borderwidth=1, relief='ridge')
        frame_advantage_label.grid(row=0, column=col)
        return frame_advantage_var, frame_advantage_label

    def create_textbox(self, col):
        textbox = t_tkinter.Text(self.toplevel, font=("Consolas", 11), wrap=t_tkinter.NONE, highlightthickness=0, pady=0, relief='flat')
        textbox.grid(row=0, column=col, rowspan=2, sticky=t_tkinter.NSEW)
        textbox.configure(background=self.background_color)
        textbox.configure(foreground=Overlay.ColorSchemeEnum.system_text.value)
        return textbox

    def update_column_to_print(self, enum, value):
        self.printer.columns_to_print[enum] = value
        self.printer.populate_column_names()
        self.master.tekken_config.set_property(enum, value)
        self.master.tekken_config.write()
