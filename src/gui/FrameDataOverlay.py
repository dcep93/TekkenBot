"""
A transparent frame data display that sits on top of Tekken.exe in windowed or borderless mode.
"""

from . import Overlay, t_tkinter
from frame_data import FrameDataEntry

# todo trim
class Printer:
    unknown = '??'
    col_max_length = 10
    def __init__(self, widget, style, fa_var):
        self.widget = widget
        self.fa_var = fa_var
        self.style = style

        self.columns_to_print = None

        self.widget.tag_config("p1", foreground=Overlay.ColorSchemeEnum.p1_text.value)
        self.widget.tag_config("p2", foreground=Overlay.ColorSchemeEnum.p2_text.value)

        self.style.configure('.', background=Overlay.ColorSchemeEnum.advantage_slight_minus.value)

        self.entries = []

    def set_columns_to_print(self, booleans_for_columns):
        self.columns_to_print = booleans_for_columns
        self.populate_column_names()

    def populate_column_names(self):
        columns_entry = {col:col.name for col in FrameDataEntry.DataColumns}
        column_names = self.get_frame_data_string(columns_entry)
        prefix = self.get_prefix(True)
        spaces = " " * len(prefix)

        print(spaces + column_names)

        self.widget.delete("1.0", "2.0")
        self.widget.insert("1.0", column_names + '\n')

    @staticmethod
    def get_background(fa):
        try:
            fa = int(fa)
        except ValueError:
            return Overlay.ColorSchemeEnum.advantage_plus.value
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

    @staticmethod
    def get_prefix(is_p1):
        player_name = "p1" if is_p1 else "p2"
        return "%s: " % player_name

    def scroll(self):
        max_lines = 6
        offset = 2
        while len(self.entries) >= max_lines:
            index = self.get_scroll_index()
            self.entries.pop(index)
            start = "%0.1f" % (index + offset)
            end = "%0.1f" % (index + offset + 1)
            self.widget.delete(start, end)

    def get_scroll_index(self):
        for entry in self.entries[1:]:
            if not entry[FrameDataEntry.DataColumns.guaranteed]:
                return 0
        return 1

    def print(self, is_p1, frame_data_entry):
        self.scroll()

        self.entries.append(frame_data_entry)
        fa = frame_data_entry[FrameDataEntry.DataColumns.fa]

        background = self.get_background(fa)
        self.style.configure('.', background=background)

        self.fa_var.set(fa)
        text_tag = 'p1' if is_p1 else 'p2'

        out = self.get_frame_data_string(frame_data_entry)
        prefix = self.get_prefix(is_p1)
        print("%s%s / %s" % (prefix, out, fa))

        out += "\n"
        self.widget.insert("end", out, text_tag)

    def get_frame_data_string(self, frame_data_entry):
        values = [self.get_value(frame_data_entry, col) for col in FrameDataEntry.DataColumns if self.columns_to_print[col]]
        return '|'.join(values)

    def get_value(self, frame_data_entry, col):
        if col in frame_data_entry:
            value = str(frame_data_entry[col])
        else:
            value = self.unknown

        size = self.col_max_length
        diff = size - len(value)
        if diff <= 0:
            return value[:size]
        before = int(diff / 2)
        after = diff - before
        return (' ' * before) + value + (' ' * after)

class FrameDataOverlay(Overlay.Overlay):
    def __init__(self, master, state):
        super().__init__(master, state, (1400, 128))

        self.init_tkinter()

        self.listeners = [PlayerListener(i, self.printer) for i in [True, False]]

    def update_state(self):
        for listener in self.listeners:
            listener.update(self.state)

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

        self.text.delete("1.0", "end")
        self.printer.set_columns_to_print(self.master.tekken_config.get_all(FrameDataEntry.DataColumns, True))

    def create_padding_frame(self, col):
        padding = t_tkinter.Frame(self.toplevel, width=10)
        padding.grid(row=0, column=col, rowspan=2, sticky=t_tkinter.NSEW)
        return padding

    def create_frame_advantage_label(self, col):
        frame_advantage_var = t_tkinter.StringVar()
        frame_advantage_label = t_tkinter.Label(self.toplevel, textvariable=frame_advantage_var,
            font=("Courier New", 44), width=4, anchor='c', borderwidth=1, relief='ridge')
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

class PlayerListener:
    def __init__(self, is_p1, printer):
        self.is_p1 = is_p1
        self.printer = printer

        self.active_frame_wait = 1

    def update(self, game_state):
        if game_state.is_landing_attack(self.is_p1) and game_state.did_id_or_timer_change(not self.is_p1, self.active_frame_wait):
            is_recovering_before_long_active_frame_move_completes = (game_state.get(not self.is_p1).recovery - game_state.get(not self.is_p1).move_timer == 0)
            game_state.rewind(self.active_frame_wait)

            if (self.active_frame_wait < game_state.get(self.is_p1).get_active_frames() + 1) and not is_recovering_before_long_active_frame_move_completes:
                self.active_frame_wait += 1
            else:
                frame_data_entry = FrameDataEntry.build(game_state, self.is_p1, self.active_frame_wait)
                self.printer.print(self.is_p1, frame_data_entry)
                self.active_frame_wait = 1

            game_state.unrewind()
