from . import Overlay
from . import tkinter
from game_parser.MoveInfoEnums import InputDirectionCodes
from game_parser.MoveInfoEnums import InputAttackCodes

symbol_map = {
    InputDirectionCodes.u : '↑',
    InputDirectionCodes.uf: '↗',
    InputDirectionCodes.f: '→',
    InputDirectionCodes.df: '↘',
    InputDirectionCodes.d: '↓',
    InputDirectionCodes.db: '↙',
    InputDirectionCodes.b: '←',
    InputDirectionCodes.ub: '↖',
    InputDirectionCodes.N: '★',
    InputDirectionCodes.NULL: '!'
}

class CommandInputOverlay(Overlay.Overlay):
    length = 60
    def __init__(self, master, state):
        self.initialize(master, (1200, 86))

        self.state = state

        self.stored_inputs = []

        self.init_canvas()

    def init_canvas(self):
        self.canvas = tkinter.Canvas(self.toplevel, width=self.w, height=self.h, bg='black', highlightthickness=0, relief='flat')

        self.canvas.pack()

        self.step = self.w / self.length
        for i in range(self.length):
            self.canvas.create_text(i * self.step + (self.step / 2), 8, text = str(i), fill='snow')
            self.canvas.create_line(i * self.step, 0, i * self.step, self.h, fill="red")

    def update_state(self):
        Overlay.Overlay.update_state(self)
        last_state = self.state.stateLog[-1]
        if last_state.is_player_player_one:
            player = last_state.bot
        else:
            player = last_state.opp
        
        input_state = player.GetInputState()
        color = self.color_from_cancel_booleans(player)
        self.update_input(input_state, color)

    def color_from_cancel_booleans(self, obj):
        if obj.is_parry_1:
            fill_color = 'orange'
        elif obj.is_parry_2:
            fill_color = 'yellow'
        elif obj.is_bufferable:
            fill_color = 'MediumOrchid1'
        elif obj.is_cancelable:
            fill_color = 'SteelBlue1'
        else:
            fill_color = 'firebrick1'
        return fill_color

    def update_input(self, input_state, cancel_color):
        input_tag = "inputs"
        self.stored_inputs.append((input_state,cancel_color))
        if len(self.stored_inputs) >= self.length:
            self.stored_inputs = self.stored_inputs[-self.length:]
            if input_state != self.stored_inputs[-2]:
                self.canvas.delete(input_tag)
                for i, stored_input_and_cancel in enumerate(self.stored_inputs):
                    stored_input, stored_cancel = stored_input_and_cancel
                    self.update_canvas_with_input(i, stored_input, stored_cancel)

    def update_canvas_with_input(i, self, stored_input, stored_cancel):
        direction_code, attack_code, rage_flag = stored_input
        posn = i * self.step + (self.step / 2)
        self.canvas.create_text(posn, 30, text=CommandInputOverlay.symbol_map[direction_code], fill='snow',  font=("Consolas", 20), tag=input_tag)
        self.canvas.create_text(posn, 55, text=attack_code.name.replace('x', '').replace('N', ''), fill='snow',  font=("Consolas", 12), tag=input_tag)
        x0 = i * self.step + 4
        x1 = x0 + self.step - 8
        self.canvas.create_rectangle(x0, 70, x1, self.h - 5, fill=self.stored_cancel, tag=input_tag)
