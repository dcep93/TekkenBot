# bad

"""
A transparent frame data display that sits on top of Tekken.exe in windowed or borderless mode.
"""

import enum
import tkinter
import tkinter.ttk
import sys

from . import Overlay

class DataColumns(enum.Enum):
    XcommX = 0
    XidX = 1
    name = 3
    XtypeXX = 4
    XstX = 5
    bloX = 6
    hitX = 7
    XchXX = 8
    act = 9
    T = 10
    tot = 11
    rec = 12
    opp = 13
    notes = 14

DataColumnsToMenuNames = {
    DataColumns.XcommX : 'input command',
    DataColumns.XidX : 'internal move id number',
    DataColumns.name: 'internal move name',
    DataColumns.XtypeXX: 'attack type',
    DataColumns.XstX: 'startup frames',
    DataColumns.bloX: 'frame advantage on block',
    DataColumns.hitX: 'frame advantage on hit',
    DataColumns.XchXX: 'frame advantage on counter hit',
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

        self.columns_to_print = {i: True for i in DataColumns}

        self.widget.tag_config("p1", foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.p1_text])
        self.widget.tag_config("p2", foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.p2_text])

        self.style.configure('.', background=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_slight_minus])

    def set_columns_to_print(self, booleans_for_columns):
        self.columns_to_print = booleans_for_columns
        self.populate_column_names()

    def populate_column_names(self):
        column_names = ''
        for i, enum in enumerate(DataColumns):
            col_name = enum.name.replace('X', '')
            col_len = len(col_name)
            if self.columns_to_print[i]:
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
    def __init__(self, master, launcher):
        self.initialize(master, (1021, 86))
        self.launcher = launcher

        self.show_live_framedata = self.tekken_config.get_property(Overlay.DisplaySettings.tiny_live_frame_data_numbers, True)

        style = tkinter.ttk.Style()
        style.theme_use('alt')
        style.configure('.', background=self.background_color)
        style.configure('.', foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.advantage_text])

        # ???
        tkinter.Grid.columnconfigure(self.toplevel, 0, weight=0)
        tkinter.Grid.columnconfigure(self.toplevel, 1, weight=0)
        tkinter.Grid.columnconfigure(self.toplevel, 2, weight=0)
        tkinter.Grid.columnconfigure(self.toplevel, 3, weight=1)
        tkinter.Grid.columnconfigure(self.toplevel, 4, weight=0)
        tkinter.Grid.columnconfigure(self.toplevel, 5, weight=0)
        tkinter.Grid.columnconfigure(self.toplevel, 6, weight=0)
        tkinter.Grid.rowconfigure(self.toplevel, 0, weight=1)
        tkinter.Grid.rowconfigure(self.toplevel, 1, weight=0)

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
        self.redirector.set_columns_to_print(self.get_data_columns())

        self.text.configure(state="disabled")

    def get_data_columns(self):
        return [self.tekken_config.get_property(enum, True) for enum in DataColumns]

    def create_padding_frame(self, col):
        padding = tkinter.ttk.Frame(self.toplevel, width=10)
        padding.grid(row=0, column=col, rowspan=2, sticky=tkinter.N + tkinter.S + tkinter.W + tkinter.E)
        return padding

    def create_live_recovery(self, parent, col):
        live_recovery_var = tkinter.StringVar()
        live_recovery_var.set('??')
        live_recovery_label = tkinter.Label(parent, textvariable=live_recovery_var, font=("Segoe UI", 12), width=5, anchor='c')
        live_recovery_label.place(rely=0.0, relx=0.0, x=4, y=4, anchor=tkinter.NW)
        return live_recovery_var

    def create_frame_advantage_label(self, col):
        frame_advantage_var = tkinter.StringVar()
        frame_advantage_var.set('?')
        frame_advantage_label = tkinter.Label(self.toplevel, textvariable=frame_advantage_var, font=("Consolas", 44), width=4, anchor='c',
                                        borderwidth=1, relief='ridge')
        frame_advantage_label.grid(row=0, column=col)
        return frame_advantage_var, frame_advantage_label

    def create_attack_type_label(self, col):
        attack_type_var = tkinter.StringVar()
        attack_type_var.set('?')
        attack_type_label = tkinter.Label(self.toplevel, textvariable=attack_type_var, font=("Verdana", 12), width=10, anchor='c',
                                    borderwidth=4, relief='ridge')
        attack_type_label.grid(row=1, column=col)
        return attack_type_var

    def create_textbox(self, col):
        textbox = tkinter.Text(self.toplevel, font=("Consolas", 11), wrap=tkinter.NONE, highlightthickness=0, pady=0, relief='flat')
        textbox.grid(row=0, column=col, rowspan=2, sticky=tkinter.N + tkinter.S + tkinter.W + tkinter.E)
        textbox.configure(background=self.background_color)
        textbox.configure(foreground=Overlay.CurrentColorScheme.scheme[Overlay.ColorSchemeEnum.system_text])
        return textbox

    def update_state(self):
        if self.show_live_framedata:
            if len(self.launcher.gameState.stateLog) > 1:
                l_recovery = str(self.launcher.gameState.GetOppFramesTillNextMove() - self.launcher.gameState.GetBotFramesTillNextMove())
                r_recovery = str(self.launcher.gameState.GetBotFramesTillNextMove() - self.launcher.gameState.GetOppFramesTillNextMove())
                if not '-' in l_recovery:
                    l_recovery = '+' + l_recovery
                
                if not '-' in r_recovery:
                    r_recovery = '+' + r_recovery
                self.l_live_recovery.set(l_recovery)
                self.r_live_recovery.set(r_recovery)


    def set_columns_to_print(self, columns_to_print):
        self.redirector.set_columns_to_print(columns_to_print)

    def update_column_to_print(self, enum, value):
        self.tekken_config.set_property(enum, value)
        self.write_config_file()
