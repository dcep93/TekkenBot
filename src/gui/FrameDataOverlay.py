"""
A transparent frame data display that sits on top of Tekken.exe in windowed or borderless mode.
"""

import enum
import sys

from . import Overlay
from . import t_tkinter

from misc import TekkenEncyclopedia

class DataColumns(enum.Enum):
    comm = 0
    id = 1
    name = 3
    type = 4
    st = 5
    blo = 6
    hit = 7
    ch = 8
    act = 9
    T = 10
    tot = 11
    rec = 12
    opp = 13
    notes = 14

DataColumnsToMenuNames = {
    DataColumns.comm : 'input command',
    DataColumns.id : 'internal move id number',
    DataColumns.name: 'internal move name',
    DataColumns.type: 'attack type',
    DataColumns.st: 'startup frames',
    DataColumns.blo: 'frame advantage on block',
    DataColumns.hit: 'frame advantage on hit',
    DataColumns.ch: 'frame advantage on counter hit',
    DataColumns.act: 'active frame connected on / total active frames',
    DataColumns.T: 'how well move tracks during startup',
    DataColumns.tot: 'total number of frames in move',
    DataColumns.rec: 'frames before attacker can act',
    DataColumns.opp: 'frames before defender can act',
    DataColumns.notes: 'additional move properties',
}

class TextRedirector(object):
    col_max_length = 8
    def __init__(self, stdout, widget, style, fa_p1_var, fa_p2_var):
        self.widget = widget
        self.fa_p1_var = fa_p1_var
        self.fa_p2_var = fa_p2_var
        self.style = style

        self.columns_to_print = None

        self.widget.tag_config("p1", foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.p1_text])
        self.widget.tag_config("p2", foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.p2_text])

        self.style.configure('.', background=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_slight_minus])

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
                    col_name = '%s%s%s' % (" " * int(needed_spaces / 2), col_name, " " * int((needed_spaces+1) / 2))
                column_names += '|%s' % col_name
        self.set_first_column(column_names)

    def set_first_column(self, first_column_string):
        self.widget.configure(state="normal")
        self.widget.delete("1.0", "2.0")
        self.widget.insert("1.0", first_column_string + '\n')
        self.widget.configure(state="disabled")

    def get_background(self, fa):
        if fa <= -14:
            return Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_very_punishible]
        elif fa <= -10:
            return Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_punishible]
        elif fa <= -5:
            return Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_safe_minus]
        elif fa < 0:
            return Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_slight_minus]
        else:
            return Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_plus]

    def write(self, output_str):
        exit()
        raise Exception('how does this work')
        lines = int(self.widget.index('end-1c').split('.')[0])
        max_lines = 5
        if lines > max_lines:
            r = lines - max_lines
            for _ in range(r):
                self.widget.configure(state="normal")
                self.widget.delete('2.0', '3.0')
                self.widget.configure(state="disabled")

        if 'NOW:' in output_str:
            data = output_str.split('NOW:')[0]
            fa = output_str.split('NOW:')[1][:3]

            if '?' not in fa:
                background = self.get_background(int(fa))
                self.style.configure('.', background=background)

            if "p1:" in output_str:
                self.fa_p1_var.set(fa)
                data = data.replace('p1:', '')
                text_tag = 'p1'
            else:
                self.fa_p2_var.set(fa)
                data = data.replace('p2:', '')
                text_tag = 'p2'

            if '|' in output_str:
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
        self.initialize(master, (1021, 86))
        self.init_encyclopedia()
        self.state = state

        self.show_live_framedata = self.master.tekken_config.get_property(Overlay.DisplaySettings.tiny_live_frame_data_numbers, True)

        style = t_tkinter.Style()
        style.theme_use('alt')
        style.configure('.', background=self.background_color)
        style.configure('.', foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_text])

        # ???
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

        if self.show_live_framedata:
            self.l_live_recovery = self.create_live_recovery(fa_p1_label, 0)
            self.r_live_recovery = self.create_live_recovery(fa_p2_label, 0)

        self.text = self.create_textbox(3)

        stdout = sys.stdout
        self.redirector = TextRedirector(stdout, self.text, style, self.fa_p1_var, self.fa_p2_var)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.redirector.set_columns_to_print(self.master.tekken_config.get_all(DataColumns, True))

        self.text.configure(state="disabled")

    def create_padding_frame(self, col):
        padding = t_tkinter.Frame(self.toplevel, width=10)
        padding.grid(row=0, column=col, rowspan=2, sticky=t_tkinter.NESW)
        return padding

    def create_live_recovery(self, parent, col):
        live_recovery_var = t_tkinter.StringVar()
        live_recovery_var.set('??')
        live_recovery_label = t_tkinter.Label(parent, textvariable=live_recovery_var, font=("Segoe UI", 12), width=5, anchor='c')
        live_recovery_label.place(rely=0.0, relx=0.0, x=4, y=4, anchor=t_tkinter.NW)
        return live_recovery_var

    def create_frame_advantage_label(self, col):
        frame_advantage_var = t_tkinter.StringVar()
        frame_advantage_var.set('?')
        frame_advantage_label = t_tkinter.Label(self.toplevel, textvariable=frame_advantage_var, font=("Consolas", 44), width=4, anchor='c',
                                        borderwidth=1, relief='ridge')
        frame_advantage_label.grid(row=0, column=col)
        return frame_advantage_var, frame_advantage_label

    def create_textbox(self, col):
        textbox = t_tkinter.Text(self.toplevel, font=("Consolas", 11), wrap=t_tkinter.NONE, highlightthickness=0, pady=0, relief='flat')
        textbox.grid(row=0, column=col, rowspan=2, sticky=t_tkinter.NESW)
        textbox.configure(background=self.background_color)
        textbox.configure(foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.system_text])
        return textbox

    def update_state(self):
        self.update_encyclopedia()
        if self.show_live_framedata:
            if len(self.state.stateLog) > 1:
                recovery = self.state.get_recovery()
                if recovery == 0:
                    l_recovery = r_recovery = '+0'
                elif recovery > 0:
                    l_recovery = '+%s' % recovery
                    r_recovery = str(recovery)
                else:
                    l_recovery = str(recovery)
                    r_recovery = '+%s' % recovery
                self.l_live_recovery.set(l_recovery)
                self.r_live_recovery.set(r_recovery)

    def init_encyclopedia(self):
        self.cyclopedia_p1 = TekkenEncyclopedia.TekkenEncyclopedia(True)
        self.cyclopedia_p2 = TekkenEncyclopedia.TekkenEncyclopedia(False)

    def update_encyclopedia(self):
        self.cyclopedia_p1.Update(self.state)
        self.cyclopedia_p2.Update(self.state)

    def update_column_to_print(self, enum, value):
        self.redirector.columns_to_print[enum] = value
        self.redirector.populate_column_names()
        self.master.tekken_config.set_property(enum, value)
        self.master.tekken_config.write()
