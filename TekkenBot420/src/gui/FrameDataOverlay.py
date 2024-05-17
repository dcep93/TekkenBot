from ..gui import t_tkinter
from ..frame_data import Builder, Entry, Hook
from ..game_parser import GameLog, GameReader, MoveInfoEnums
from ..misc import Path, Windows
from ..record import Record, Replay

import enum
import typing


class FrameDataOverlay:
    def __init__(self) -> None:
        self.geometry: typing.Optional[str] = None
        self.unknown = ''
        self.max_lines = 6
        self.col_max_length = 12
        self.sizes: typing.Dict[Entry.DataColumns, int] = {
            Entry.DataColumns.hit_outcome: 25,
        }
        self.visible = True

        self.toplevel = t_tkinter.Toplevel()

        self.background_color = ColorSchemeEnum.background.value
        self.tranparency_color = self.background_color
        self.toplevel.configure(background=self.tranparency_color)

        #

        self.entries: typing.List[Entry.Entry] = []
        self.column_names_string: typing.Optional[str] = None
        self.init_tkinter()
        self.populate_column_names()

    def handle_fa(self, entry: Entry.Entry) -> None:
        if entry.get(Entry.DataColumns.block) is None:
            fa_str = "-"
        else:
            fa_str = entry.get(Entry.DataColumns.fa, "-")
        try:
            fa = int(fa_str)
        except ValueError:
            fa = 0
        if fa <= -15:
            color = ColorSchemeEnum.advantage_very_punishible
        elif fa <= -10:
            color = ColorSchemeEnum.advantage_punishible
        elif fa <= 0:
            color = ColorSchemeEnum.advantage_slight_minus
        else:
            color = ColorSchemeEnum.advantage_plus
        self.fa_label.configure(background=color.value)
        self.fa_var.set(fa_str)

    def update_state(self, game_log: GameLog.GameLog) -> None:
        self.read_player_state(True, game_log)
        self.read_player_state(False, game_log)

    def get_geometry(self, tekken_rect: typing.Any) -> typing.Tuple[int, int]:
        x = (tekken_rect.right + tekken_rect.left) / \
            2 - self.toplevel.winfo_width() / 2
        y = tekken_rect.bottom - self.toplevel.winfo_height()
        return x, y

    def init_tkinter(self) -> None:
        self.style = t_tkinter.Style()
        self.style.theme_use('alt')
        self.style.configure('.', background=self.background_color)
        self.style.configure(
            '.', foreground=ColorSchemeEnum.advantage_text.value)
        self.style.configure('TFrame', background=self.tranparency_color)

        self.create_padding_frame()
        self.text = self.create_textbox()
        self.create_padding_frame()
        self.fa_var = t_tkinter.StringVar()
        self.fa_label = self.create_frame_advantage_label()
        # self.add_buttons()

        self.text.tag_config("p1", foreground=ColorSchemeEnum.p1_text.value)
        self.text.tag_config("p2", foreground=ColorSchemeEnum.p2_text.value)

    def print_f(self, entry: Entry.Entry, is_p1: typing.Optional[bool] = None) -> None:
        if len(self.entries) == 0:
            print(self.column_names_string)

        self.scroll()

        self.entries.append(entry)

        self.handle_fa(entry)

        Hook.handle_entry(entry)

        text_tag = 'p1' if is_p1 else 'p2'
        out = self.get_prefix(is_p1) + self.get_frame_data_string(entry)
        print(out)

        out += "\n"
        self.text.insert("end", out, text_tag)

    def create_padding_frame(self) -> None:
        padding = t_tkinter.Frame(self.toplevel, width=10)
        padding.pack(side=t_tkinter.LEFT)

    def create_frame_advantage_label(self) -> typing.Any:
        frame_advantage_label = t_tkinter.Label(self.toplevel, textvariable=self.fa_var, font=(
            "Courier New", 44), width=4, anchor='c', borderwidth=1, relief='ridge')  # type: ignore
        frame_advantage_label.pack(side=t_tkinter.LEFT)
        return frame_advantage_label

    def create_textbox(self) -> typing.Any:
        textbox = t_tkinter.Text(self.toplevel, font=(
            "Courier New", 10), highlightthickness=0, pady=0, relief='flat')
        textbox.pack(side=t_tkinter.LEFT)
        textbox.configure(background=self.background_color)
        textbox.configure(foreground=ColorSchemeEnum.system_text.value)
        return textbox

    def add_buttons(self) -> None:
        frame = t_tkinter.Frame(self.toplevel)
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color,
                                 text="record single", command=Record.record_single).pack(fill='x')
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color,
                                 text="record both", command=Record.record_both).pack(fill='x')
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color,
                                 text="end recording", command=Record.record_end).pack(fill='x',)
        t_tkinter.tkinter.Button(frame, pady=0, highlightbackground=self.background_color,
                                 text="replay", command=Replay.replay).pack(fill='x')
        frame.pack(side=t_tkinter.LEFT)

    @staticmethod
    def get_prefix(is_p1: typing.Optional[bool]) -> str:
        if is_p1 is None:
            player_name = '  '
        else:
            player_name = "p1" if is_p1 else "p2"
        return "%s: " % player_name

    def get_value(self, entry: Entry.Entry, col: Entry.DataColumns) -> str:
        if col in entry and entry[col] is not None:
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

    def get_frame_data_string(self, entry: Entry.Entry) -> str:
        values = [self.get_value(entry, col) for col in Entry.DataColumns if col not in [
            Entry.DataColumns.is_player,
        ]]
        return '|'.join(values)

    def scroll(self) -> None:
        if len(self.entries) > 0:
            latest = self.entries[-1]
            if latest.get(Entry.DataColumns.hit_outcome) in [
                MoveInfoEnums.HitOutcome.JUGGLE.name,
                MoveInfoEnums.HitOutcome.SCREW.name,
            ]:
                self.pop_entry(len(self.entries) - 1)

        while len(self.entries) >= self.max_lines:
            self.pop_entry(0)

    def pop_entry(self, index: int) -> None:
        offset = 2
        self.entries.pop(index)
        start = "%0.1f" % (index + offset)
        end = "%0.1f" % (index + offset + 1)
        self.text.delete(start, end)

    def populate_column_names(self) -> None:
        columns_entry = {col: col.name for col in Entry.DataColumns}
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

    def read_player_state(self, is_p1: bool, game_log: GameLog.GameLog) -> None:
        # ignore the fact that some moves have multiple active frames
        if game_log.is_starting_attack(is_p1):
            entry = Builder.build(game_log, is_p1)
        else:
            throw_break_string = game_log.get_throw_break(is_p1)
            if throw_break_string:
                entry = {
                    Entry.DataColumns.move_id: throw_break_string,
                }
            else:
                return
        entry[Entry.DataColumns.time] = self.get_time(game_log, is_p1)
        self.print_f(entry, is_p1)

    def get_time(self, game_log: GameLog.GameLog, is_p1: bool) -> str:
        return str(game_log.state_log[-1].frame_count)
        # return '%3d/%3d' % (
        #     game_log.get(not is_p1, 1).frames_til_attack,
        #     game_log.get_free_frames(not is_p1)
        # )

    def update_location(self, game_reader: GameReader.GameReader) -> None:
        if Windows.w.valid:
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
            self.toplevel.after(20, lambda: self.update_location(game_reader))

    def show(self) -> None:
        self.toplevel.deiconify()
        self.visible = True

    def hide(self) -> None:
        self.toplevel.withdraw()
        self.visible = False


class FullscreenTekkenRect:
    def __init__(self, toplevel: typing.Any) -> None:
        self.left = 0
        self.right = toplevel.winfo_screenwidth()
        self.top = 0
        self.bottom = toplevel.winfo_screenheight()


@enum.unique
class ColorSchemeEnum(enum.Enum):
    background = 'gray10'
    p1_text = '#586E75'
    p2_text = '#93A1A1'
    system_text = 'lawn green'
    advantage_plus = 'DodgerBlue2'
    advantage_slight_minus = 'ivory2'
    advantage_safe_minus = 'ivory3'
    advantage_punishible = 'orchid2'
    advantage_very_punishible = 'deep pink'
    advantage_text = 'black'
