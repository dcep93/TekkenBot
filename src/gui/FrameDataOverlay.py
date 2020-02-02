"""
A transparent frame data display that sits on top of Tekken.exe in windowed or borderless mode.
"""

from . import Overlay, t_tkinter
from frame_data import FrameDataEntry

class FrameDataOverlay(Overlay.Overlay):
    unknown = '??'
    col_max_length = 10

    def __init__(self, master, state):
        super().__init__(master, state, (1400, 128))

        self.listeners = [PlayerListener(i, self.print_f) for i in [True, False]]
        self.entries = []
        self.columns_to_print = None
        self.init_tkinter()

    def update_state(self):
        for listener in self.listeners:
            listener.update(self.state)

    def init_tkinter(self):
        self.style = t_tkinter.Style()
        self.style.theme_use('alt')
        self.style.configure('.', background=self.background_color)
        self.style.configure('.', foreground=Overlay.ColorSchemeEnum.advantage_text.value)

        t_tkinter.Grid.columnconfigure(self.toplevel, 0, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 1, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 2, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 3, weight=1)
        t_tkinter.Grid.columnconfigure(self.toplevel, 4, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 5, weight=0)
        t_tkinter.Grid.columnconfigure(self.toplevel, 6, weight=0)
        t_tkinter.Grid.rowconfigure(self.toplevel, 0, weight=1)
        t_tkinter.Grid.rowconfigure(self.toplevel, 1, weight=0)

        self.style.configure('TFrame', background=self.tranparency_color)
        self.fa_var = self.create_frame_advantage_label(1)

        self.l_margin = self.create_padding_frame(0)
        self.r_margin = self.create_padding_frame(5)
        self.l_seperator = self.create_padding_frame(2)
        self.r_seperator = self.create_padding_frame(4)

        self.text = self.create_textbox(3)
        self.text.tag_config("p1", foreground=Overlay.ColorSchemeEnum.p1_text.value)
        self.text.tag_config("p2", foreground=Overlay.ColorSchemeEnum.p2_text.value)

        self.text.delete("1.0", "end")
        self.set_columns_to_print(self.master.tekken_config.get_all(FrameDataEntry.DataColumns, True))

    def print_f(self, is_p1, frame_data_entry):
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
        self.text.insert("end", out, text_tag)

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
        self.columns_to_print[enum] = value
        self.populate_column_names()
        self.master.tekken_config.set_property(enum, value)
        self.master.tekken_config.write()

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

    def get_frame_data_string(self, frame_data_entry):
        values = [self.get_value(frame_data_entry, col) for col in FrameDataEntry.DataColumns if self.columns_to_print[col]]
        return '|'.join(values)

    def get_scroll_index(self):
        for entry in self.entries[1:]:
            if not entry[FrameDataEntry.DataColumns.guaranteed]:
                return 0
        return 1

    def scroll(self):
        max_lines = 6
        offset = 2
        while len(self.entries) >= max_lines:
            index = self.get_scroll_index()
            self.entries.pop(index)
            start = "%0.1f" % (index + offset)
            end = "%0.1f" % (index + offset + 1)
            self.text.delete(start, end)

    def populate_column_names(self):
        columns_entry = {col:col.name for col in FrameDataEntry.DataColumns}
        column_names = self.get_frame_data_string(columns_entry)
        prefix = self.get_prefix(True)
        spaces = " " * len(prefix)

        print(spaces + column_names)

        self.text.delete("1.0", "2.0")
        self.text.insert("1.0", column_names + '\n')

    def set_columns_to_print(self, booleans_for_columns):
        self.columns_to_print = booleans_for_columns
        self.populate_column_names()

class PlayerListener:
    def __init__(self, is_p1, print_f):
        self.is_p1 = is_p1
        self.print_f = print_f

        self.active_frame_wait = 1

    def update(self, game_state):
        if game_state.is_landing_attack(self.is_p1) and game_state.did_id_or_timer_change(not self.is_p1, self.active_frame_wait):
            is_recovering_before_long_active_frame_move_completes = (game_state.get(not self.is_p1).recovery - game_state.get(not self.is_p1).move_timer == 0)
            game_state.rewind(self.active_frame_wait)

            if (self.active_frame_wait < game_state.get(self.is_p1).get_active_frames() + 1) and not is_recovering_before_long_active_frame_move_completes:
                self.active_frame_wait += 1
            else:
                frame_data_entry = FrameDataEntry.build(game_state, self.is_p1, self.active_frame_wait)
                self.print_f(self.is_p1, frame_data_entry)
                self.active_frame_wait = 1

            game_state.unrewind()
