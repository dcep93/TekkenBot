"""
A transparent frame data display that sits on top of Tekken.exe in windowed or borderless mode.
"""

import enum
import sys

from . import Overlay
from . import t_tkinter

@enum.unique
class DataColumns(enum.Enum):
    input = 'input command'
    move_id = 'internal move id number'
    move_str = 'internal move name'
    hit_type = 'attack type'
    startup = 'startup frames'
    on_block = 'frame advantage on block'
    on_normal_hit = 'frame advantage on hit'
    on_counter_hit = 'frame advantage on counter hit'
    recovery = 'total number of frames in move'
    hit_recovery = 'frames before attacker can act'
    block_recovery = 'frames before defender can act'

class Printer:
    col_max_length = 15
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
        for col in DataColumns:
            if self.columns_to_print[col]:
                col_name = col.name
                col_len = len(col_name)
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

    def print(self, isP1, frameDataEntry, floated, fa):
        lines = int(self.widget.index('end-1c').split('.')[0])
        max_lines = 5
        if lines > max_lines:
            r = lines - max_lines
            for _ in range(r):
                self.widget.configure(state="normal")
                self.widget.delete('2.0', '3.0')
                self.widget.configure(state="disabled")

        if not floated and fa != frameDataEntry.unknown:
            background = self.get_background(int(fa))
            self.style.configure('.', background=background)

        if isP1:
            self.fa_p1_var.set(fa)
            text_tag = 'p1'
        else:
            self.fa_p2_var.set(fa)
            text_tag = 'p2'

        columns = [col.name for col in DataColumns if self.columns_to_print[col]]
        out = frameDataEntry.getString(columns)
        playerName = "p1" if isP1 else "p2"
        print("%s: %s / NOW:%s" % (playerName, out, fa))

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









import collections

from game_parser.MoveInfoEnums import AttackType
from game_parser.MoveInfoEnums import ComplexMoveStates

class FrameDataListener:
    def __init__(self, printer):
        FrameDataEntry.printColumns()
        self.listeners = [PlayerListener(i, printer) for i in [True, False]]

    def update(self, gameState):
        for listener in self.listeners:
            listener.Update(gameState)

class PlayerListener:
    def __init__(self, isP1, printer):
        self.isP1 = isP1
        self.printer = printer

        self.active_frame_wait = 1

    def Update(self, gameState):
        if self.ShouldDetermineFrameData(gameState):
            self.DetermineFrameData(gameState)

    def ShouldDetermineFrameData(self, gameState):
        if gameState.get(not self.isP1).IsBlocking() or gameState.get(not self.isP1).IsGettingHit() or gameState.get(not self.isP1).IsInThrowing() or gameState.get(not self.isP1).IsBeingKnockedDown() or gameState.get(not self.isP1).IsGettingWallSplatted():
            if gameState.DidIdChangeXMovesAgo(not self.isP1, self.active_frame_wait) or gameState.DidTimerInterruptXMovesAgo(not self.isP1, self.active_frame_wait):
                    return True
        return False

    def DetermineFrameData(self, gameState):
        is_recovering_before_long_active_frame_move_completes = (gameState.get(not self.isP1).recovery - gameState.get(not self.isP1).move_timer == 0)
        gameState.Rewind(self.active_frame_wait)

        if (self.active_frame_wait < gameState.get(self.isP1).GetActiveFrames() + 1) and not is_recovering_before_long_active_frame_move_completes:
            self.active_frame_wait += 1
        else:
            self.DetermineFrameDataHelper(gameState)
            self.active_frame_wait = 1
        gameState.Unrewind()

    def DetermineFrameDataHelper(self, gameState):
        frameDataEntry = self.buildFrameDataEntry(gameState)
        fa = frameDataEntry.fa

        globalFrameDataEntry = frameDataEntries[frameDataEntry.move_id]
        
        floated = gameState.WasJustFloated(not self.isP1)
        globalFrameDataEntry.record(frameDataEntry, floated)

        self.printer.print(self.isP1, frameDataEntry, floated, fa)

    def buildFrameDataEntry(self, gameState):
        move_id = gameState.get(self.isP1).move_id

        frameDataEntry = FrameDataEntry()

        frameDataEntry.move_id = move_id
        frameDataEntry.startup = gameState.get(self.isP1).startup
        frameDataEntry.activeFrames = gameState.get(self.isP1).GetActiveFrames()
        frameDataEntry.hit_type = AttackType(gameState.get(self.isP1).attack_type).name + ("_THROW" if gameState.get(self.isP1).IsAttackThrow() else "")
        frameDataEntry.recovery = gameState.get(self.isP1).recovery
        frameDataEntry.input = gameState.GetCurrentMoveString(self.isP1)

        gameState.Unrewind()

        time_till_recovery_p1 = gameState.get(self.isP1).GetFramesTillNextMove()
        time_till_recovery_p2 = gameState.get(not self.isP1).GetFramesTillNextMove()

        raw_fa = time_till_recovery_p2 - time_till_recovery_p1

        frameDataEntry.fa = frameDataEntry.WithPlusIfNeeded(raw_fa)

        if gameState.get(not self.isP1).IsBlocking():
            frameDataEntry.on_block = frameDataEntry.fa
        else:
            if gameState.get(not self.isP1).IsGettingCounterHit():
                frameDataEntry.on_counter_hit = frameDataEntry.fa
            else:
                frameDataEntry.on_normal_hit = frameDataEntry.fa

        frameDataEntry.hit_recovery = time_till_recovery_p1
        frameDataEntry.block_recovery = time_till_recovery_p2

        frameDataEntry.move_str = gameState.GetCurrentMoveName(self.isP1)

        gameState.Rewind(self.active_frame_wait)

        return frameDataEntry

# not the best organization, but it works
class FrameDataEntry:
    unknown = '??'
    prefix_length = 4
    columns = [
        'input',
        'move_id',
        'move_str',
        'hit_type',
        'startup',
        'on_block',
        'on_normal_hit',
        'on_counter_hit',
        'recovery',
        'hit_recovery',
        'block_recovery'
    ]
    paddings = {'input': 16, 'move_str': 11}

    def __init__(self):
        self.input = self.unknown
        self.move_id = self.unknown
        self.move_str = self.unknown
        self.hit_type = self.unknown
        self.startup = self.unknown
        self.on_block = self.unknown
        self.on_normal_hit = self.unknown
        self.on_counter_hit = self.unknown
        self.recovery = self.unknown
        self.hit_recovery = self.unknown
        self.block_recovery = self.unknown

        self.fa = self.unknown

    @classmethod
    def printColumns(cls):
        # todo
        return
        obj = cls()
        for col in cls.columns:
            obj.__setattr__(col, col)
        string = obj.getString()
        prefix = " " * cls.prefix_length
        print(prefix + string)

    @staticmethod
    def WithPlusIfNeeded(value):
        v = str(value)
        if value >= 0:
            return '+' + v
        else:
            return v

    def getValue(self, field):
        return str(self.__getattribute__(field))

    def getPaddedField(self, field):
        v = self.getValue(field)
        diff = len(field) - len(v)
        if field in self.paddings: diff += self.paddings[field]
        if diff <= 0: return v
        before = int(diff / 2)
        after = diff - before
        return (' ' * before) + v + (' ' * after)

    def getString(self, columns=None):
        if columns is None: columns = self.columns
        values = [self.getPaddedField(i) for i in columns]
        return '|'.join(values)

class GlobalFrameDataEntry:
    def __init__(self):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))

    def record(self, frameDataEntry, floated):
        for field in frameDataEntry.columns:
            self.recordField(field, frameDataEntry, floated)

    def recordField(self, field, frameDataEntry, floated):
        v = frameDataEntry.getValue(field)
        most_common = v
        if v == frameDataEntry.unknown:
            max_count = 0
        else:
            if floated:
                max_count = 0
            else:
                max_count = self.counts[field][v] + 1
                self.counts[field][v] = max_count
        for record, count in self.counts[field].items():
            if count > max_count:
                most_common = record
                max_count = count
        if most_common != v:
            if v == frameDataEntry.unknown:
                new_v = most_common
            else:
                new_v = "(%s)" % (most_common)
            frameDataEntry.__setattr__(field, new_v)

frameDataEntries = collections.defaultdict(GlobalFrameDataEntry)
