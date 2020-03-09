from . import Overlay, t_tkinter
from frame_data import DataColumns, Entry
from game_parser import MoveInfoEnums
from misc import Flags, Globals

DAMAGE_CMD = 'DMG'

class FrameDataOverlay(Overlay.Overlay):
    unknown = '??'
    col_max_length = 10
    max_lines = 6
    sizes = {
        DataColumns.DataColumns.cmd: 18,
        DataColumns.DataColumns.startup: 14,
        DataColumns.DataColumns.block: 12,
        DataColumns.DataColumns.normal: 12,
        DataColumns.DataColumns.counter: 12,
    }

    def __init__(self):
        super().__init__((1400, 128))

        self.listeners = [PlayerListener(i, self.print_f) for i in [True, False]]
        self.entries = []
        self.columns_to_print = None
        self.column_names_string = None
        self.init_tkinter()

    def update_state(self):
        for listener in self.listeners:
            listener.update()

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
        self.set_columns_to_print(Globals.Globals.master.tekken_config.get_all(DataColumns.DataColumns, True))

    def print_f(self, is_p1, entry):
        self.scroll()
        entry[DataColumns.DataColumns.time] = self.get_time()

        self.entries.append(entry)

        fa = None
        if DataColumns.DataColumns.fa in entry:
            fa = entry[DataColumns.DataColumns.fa]

            background = self.get_background(fa)
            self.style.configure('.', background=background)

            self.fa_var.set(fa)

        text_tag = 'p1' if is_p1 else 'p2'

        out = self.get_frame_data_string(entry)
        out = self.get_prefix(is_p1) + out

        self.print_helper(out, fa)

        out += "\n"
        self.text.insert("end", out, text_tag)

    def print_helper(self, out, fa):
        if self.column_names_string is not None:
            print(self.column_names_string)
            self.column_names_string = None
        print("%s / %s" % (out, fa))

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
        textbox = t_tkinter.Text(self.toplevel, font=("Courier New", 10), highlightthickness=0, pady=0, relief='flat')
        textbox.grid(row=0, column=col, rowspan=2, sticky=t_tkinter.NSEW)
        textbox.configure(background=self.background_color)
        textbox.configure(foreground=Overlay.ColorSchemeEnum.system_text.value)
        return textbox

    def update_column_to_print(self, enum, value):
        self.columns_to_print[enum] = value
        self.populate_column_names()
        Globals.Globals.master.tekken_config.set_property(enum, value)
        Globals.Globals.master.tekken_config.write()

    @staticmethod
    def get_background(fa):
        try:
            fa = int(fa)
        except (ValueError, TypeError):
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

    def get_time(self):
        now = Globals.Globals.tekken_state.state_log[-1].frame_count
        if len(self.entries) > 0:
            prev_raw = self.entries[-1][DataColumns.DataColumns.time]
            parts = prev_raw.split('/')
            prev = int(parts[0])
        else:
            prev = 0
        diff = now - prev
        return '%d/%3d' % (now, diff)

    def get_value(self, entry, col):
        if col in entry:
            value = str(entry[col])
        else:
            value = self.unknown

        size = self.sizes[col] if col in self.sizes else self.col_max_length
        diff = size - len(value)
        if diff <= 0:
            return value[:size]
        before = int(diff / 2)
        after = diff - before
        return (' ' * before) + value + (' ' * after)

    def get_frame_data_string(self, entry):
        values = [self.get_value(entry, col) for col in DataColumns.DataColumns if self.columns_to_print[col]]
        return '|'.join(values)

    def scroll(self):
        if len(self.entries) > 0:
            if self.entries[-1][DataColumns.DataColumns.cmd] == DAMAGE_CMD:
                self.pop_entry(len(self.entries) - 1)

        while len(self.entries) >= self.max_lines:
            self.pop_entry(0)

    def pop_entry(self, index):
        offset = 2
        self.entries.pop(index)
        start = "%0.1f" % (index + offset)
        end = "%0.1f" % (index + offset + 1)
        self.text.delete(start, end)

    def populate_column_names(self):
        columns_entry = {col:col.name for col in DataColumns.DataColumns}
        column_names = self.get_frame_data_string(columns_entry)
        prefix = self.get_prefix(True)
        spaces = " " * len(prefix)
        string = spaces + column_names

        self.column_names_string = string

        self.text.config(width=len(string), height=self.max_lines+1)
        self.toplevel.geometry('')

        self.text.delete("1.0", "2.0")
        self.text.insert("1.0", string + '\n')

    def set_columns_to_print(self, booleans_for_columns):
        self.columns_to_print = booleans_for_columns
        self.populate_column_names()

class PlayerListener:
    def __init__(self, is_p1, print_f):
        self.is_p1 = is_p1
        self.print_f = print_f

    def update(self):
        # ignore the fact that some moves have multiple active frames
        if Globals.Globals.tekken_state.is_starting_attack(self.is_p1):
            entry = Entry.build(self.is_p1)
            self.print_f(self.is_p1, entry)
        else:
            throw_break_string = self.get_throw_break()
            if throw_break_string:
                entry = {
                    DataColumns.DataColumns.cmd: throw_break_string,
                }
                self.print_f(self.is_p1, entry)
            elif self.just_lost_health():
                entry = {
                    DataColumns.DataColumns.health: Entry.get_remaining_health_string(Globals.Globals.tekken_state),
                    DataColumns.DataColumns.cmd: DAMAGE_CMD,
                }
                self.print_f(self.is_p1, entry)


    def get_throw_break(self):
        frames_to_break = 19
        state = Globals.Globals.tekken_state.get(not self.is_p1)
        throw_tech = state.throw_tech
        if throw_tech == MoveInfoEnums.ThrowTechs.NONE:
            return False
        
        current_buttons = state.get_input_state()[1].name
        if '1' not in current_buttons and '2' not in current_buttons:
            return False

        i = 1
        while True:
            state = Globals.Globals.tekken_state.get(not self.is_p1, i)
            if state.throw_tech == MoveInfoEnums.ThrowTechs.NONE:
                relevant = current_buttons.replace('x3', '').replace('x4', '')
                throw_break = MoveInfoEnums.InputAttackCodes[relevant]
                break_string = throw_break.name.replace('x', '')
                throw_break_string = '%s break: %d/%d' % (break_string, i-1, frames_to_break)
                return throw_break_string
            buttons = state.get_input_state()[1].name
            if '1' in buttons or '2' in buttons:
                return False
            i += 1

    def just_lost_health(self):
        prev_state = Globals.Globals.tekken_state.get(not self.is_p1, 2)
        if prev_state is None:
            return False
        next_state = Globals.Globals.tekken_state.get(not self.is_p1, 1)
        return next_state.damage_taken != prev_state.damage_taken
