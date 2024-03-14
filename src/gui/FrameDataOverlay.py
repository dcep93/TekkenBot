from . import t_tkinter
from frame_data import Database, DataColumns, Entry
from game_parser import MoveInfoEnums
from misc import Path
from misc.Windows import w as Windows
from record import Record, Replay, Shared

DAMAGE_CMD = 'DMG'

class FrameDataOverlay():
    padding = 15
    geometry = None
    unknown = '???'
    max_lines = 6
    last_time = None
    col_max_length = 10
    sizes = {
        DataColumns.DataColumns.move_id: 18,
        DataColumns.DataColumns.startup: 14,
        DataColumns.DataColumns.block: 12,
    }

    def __init__(self):
        self.visible = True

        window_name = self.__class__.__name__
        print("Launching {}".format(window_name))

        self.toplevel = t_tkinter.Toplevel()

        self.toplevel.wm_title(window_name)
        self.toplevel.iconbitmap(Path.path('./img/tekken_bot_close.ico'))
        self.toplevel.overrideredirect(True)

        self.background_color = ColorSchemeEnum.background.value
        self.tranparency_color = self.background_color
        self.toplevel.configure(background=self.tranparency_color)

        self.toplevel.attributes("-topmost", True)

        #

        self.entries = []
        self.column_names_string = None
        self.init_tkinter()
        self.populate_column_names()

        Shared.Shared.frame_data_overlay = self

    def update_state(self, game_log):
        self.read_player_state(True, game_log)
        self.read_player_state(False, game_log)

    def get_geometry(self, tekken_rect):
        x = (tekken_rect.right + tekken_rect.left) / 2  - self.toplevel.winfo_width() / 2
        y = tekken_rect.bottom - self.toplevel.winfo_height() - self.padding
        return x,y

    def init_tkinter(self):
        self.style = t_tkinter.Style()
        self.style.theme_use('alt')
        self.style.configure('.', background=self.background_color)
        self.style.configure('.', foreground=Overlay.ColorSchemeEnum.advantage_text.value)
        self.style.configure('TFrame', background=self.tranparency_color)

        # self.create_padding_frame()
        # self.fa_var = self.create_frame_advantage_label()
        self.create_padding_frame()
        self.text = self.create_textbox()
        self.create_padding_frame()
        self.create_padding_frame()
        self.add_buttons()

        self.text.tag_config("p1", foreground=Overlay.ColorSchemeEnum.p1_text.value)
        self.text.tag_config("p2", foreground=Overlay.ColorSchemeEnum.p2_text.value)

    def print_f(self, entry, is_p1=None):
        if len(self.entries) == 0:
            print(self.column_names_string)

        self.scroll()

        self.entries.append(entry)

        # TODO hook
        # if DataColumns.DataColumns.fa in entry:
        #     fa = entry[DataColumns.DataColumns.fa]
        #     background = self.get_background(fa)
        #     self.style.configure('.', background=background)
        #     self.fa_var.set(fa)
        # else:
        #     fa = None
        #     self.style.configure('.', background=self.background_color)
        #     self.fa_var.set("")

        text_tag = 'p1' if is_p1 else 'p2'
        out = self.get_prefix(is_p1) + self.get_frame_data_string(entry)
        print(out)

        out += "\n"
        self.text.insert("end", out, text_tag)

    def create_padding_frame(self):
        padding = t_tkinter.Frame(self.toplevel, width=10)
        padding.pack(side=t_tkinter.LEFT)

    def create_frame_advantage_label(self):
        frame_advantage_var = t_tkinter.StringVar()
        frame_advantage_label = t_tkinter.Label(self.toplevel, textvariable=frame_advantage_var,
            font=("Courier New", 44), width=4, anchor='c', borderwidth=1, relief='ridge')
        frame_advantage_label.pack(side=t_tkinter.LEFT)
        return frame_advantage_var

    def create_textbox(self):
        textbox = t_tkinter.Text(self.toplevel, font=("Courier New", 10), highlightthickness=0, pady=0, relief='flat')
        textbox.pack(side=t_tkinter.LEFT)
        textbox.configure(background=self.background_color)
        textbox.configure(foreground=Overlay.ColorSchemeEnum.system_text.value)
        return textbox

    def add_buttons(self):
        frame = t_tkinter.Frame(self.toplevel)
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color, text="record single", command=Record.record_single).pack(fill='x')
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color, text="record both", command=Record.record_both).pack(fill='x')
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color, text="end recording", command=Record.record_end).pack(fill='x')
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color, text="replay", command=Replay.replay).pack(fill='x')
        frame.pack(side=t_tkinter.LEFT)

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
        if is_p1 is None:
            player_name = '  '
        else:
            player_name = "p1" if is_p1 else "p2"
        return "%s: " % player_name

    def get_time(self, game_log):
        now = game_log.state_log[-1].frame_count
        prev = self.last_time if self.last_time is not None else 0
        self.last_time = now
        diff = max(now - prev, 0)
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
        values = [self.get_value(entry, col) for col in DataColumns.DataColumns]
        return '|'.join(values)

    def scroll(self):
        if len(self.entries) > 0:
            if self.entries[-1][DataColumns.DataColumns.move_id] == DAMAGE_CMD:
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
        prefix = self.get_prefix(None)
        spaces = " " * len(prefix)
        string = spaces + column_names

        self.column_names_string = string
        self.entries = []

        self.text.config(width=len(string), height=self.max_lines+1)
        self.toplevel.geometry('')

        self.text.delete("1.0", "2.0")
        self.text.insert("1.0", string + '\n')

    def read_player_state(self, is_p1, game_log):
        # ignore the fact that some moves have multiple active frames
        if game_log.is_starting_attack(is_p1):
            entry = Entry.build(game_log, is_p1)
        else:
            throw_break_string = game_log.get_throw_break(is_p1)
            if throw_break_string:
                entry = {
                    DataColumns.DataColumns.move_id: throw_break_string,
                }
            elif game_log.just_lost_health(not is_p1):
                entry = {
                    DataColumns.DataColumns.health: Entry.get_remaining_health_string(game_log),
                    DataColumns.DataColumns.move_id: DAMAGE_CMD,
                    DataColumns.DataColumns.combo: Entry.get_combo(game_log, is_p1),
                }
            else:
                return
        entry[DataColumns.DataColumns.time] = self.get_time(game_log)
        self.print_f(entry, is_p1)

    def update_location(self, game_reader):
        if Windows.valid:
            tekken_rect = game_reader.get_window_rect()
        else:
            tekken_rect = FullscreenTekkenRect(self.toplevel)
        geometry = None
        if tekken_rect is not None:
            x, y = self.get_geometry(tekken_rect)
            geometry = '+%d+%d' % (x, y)
            self.toplevel.geometry(geometry)
            if not self.visible:
                self.show()

        elif self.visible:
            self.hide()

        if geometry != self.geometry:
            self.geometry = geometry
            self.toplevel.after(20, self.update_location(game_reader))

    def show(self):
        self.toplevel.deiconify()
        self.visible = True

    def hide(self):
        self.toplevel.withdraw()
        self.visible = False


class FullscreenTekkenRect:
    def __init__(self, toplevel):
        self.left = 0
        self.right = toplevel.winfo_screenwidth()
        self.top = 0
        self.bottom = toplevel.winfo_screenheight()

@enum.unique
class ColorSchemeEnum(enum.Enum):
    background = 'gray10'
    p1_text = '#93A1A1'
    p2_text = '#586E75'
    system_text = 'lawn green'
    advantage_plus = 'DodgerBlue2'
    advantage_slight_minus = 'ivory2'
    advantage_safe_minus = 'ivory3'
    advantage_punishible = 'orchid2'
    advantage_very_punishible = 'deep pink'
    advantage_text = 'black'
