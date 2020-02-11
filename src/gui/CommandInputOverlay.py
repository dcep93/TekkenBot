from . import Overlay, t_tkinter
from game_parser.MoveInfoEnums import InputDirectionCodes

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
    input_tag = "inputs"
    silence_after_n = 10

    def __init__(self, master, state):
        super().__init__(master, state, (1200, 86))

        self.stored_inputs = []

        self.init_canvas()

    def init_canvas(self):
        self.canvas = t_tkinter.Canvas(self.toplevel, width=self.w, height=self.h, bg='black', highlightthickness=0, relief='flat')

        self.canvas.pack()

        self.step = self.w / self.length
        for i in range(self.length):
            self.canvas.create_text(i * self.step + (self.step / 2), 8, text=str(i), fill='snow')
            self.canvas.create_line(i * self.step, 0, i * self.step, self.h, fill="red")

    def update_state(self):
        last_state = self.state.state_log[-1]
        player = last_state.p1 if last_state.is_player_player_one else last_state.p2

        input_state = player.get_input_state()

        if self.last_n_were_same(input_state):
            color = 'white'
            if self.stored_inputs[-1][1] == color:
                return
        else:
            color = self.color_from_cancel_booleans(player)
        self.update_input(input_state, color)

    def last_n_were_same(self, input_state):
        if len(self.stored_inputs) < self.silence_after_n:
            return False
        for i in range(self.silence_after_n):
            if self.stored_inputs[-i-1][0] != input_state:
                return False
        return True

    @staticmethod
    def color_from_cancel_booleans(player):
        if player.is_parry_1:
            fill_color = 'orange'
        elif player.is_parry_2:
            fill_color = 'yellow'
        elif player.is_bufferable:
            fill_color = 'MediumOrchid1'
        elif player.is_cancelable:
            fill_color = 'SteelBlue1'
        else:
            fill_color = 'firebrick1'
        return fill_color

    def update_input(self, input_state, cancel_color):
        self.stored_inputs.append((input_state, cancel_color))
        if len(self.stored_inputs) >= self.length:
            self.stored_inputs = self.stored_inputs[-self.length:]
            if input_state != self.stored_inputs[-2]:
                self.canvas.delete(self.input_tag)
                for i, (stored_input, stored_cancel) in enumerate(self.stored_inputs):
                    self.update_canvas_with_input(i, stored_input, stored_cancel)

    def update_canvas_with_input(self, i, stored_input, stored_cancel):
        direction_code, attack_code, _ = stored_input
        posn = i * self.step + (self.step / 2)
        self.canvas.create_text(posn, 30, text=symbol_map[direction_code], fill='snow', font=("Consolas", 20), tag=self.input_tag)
        self.canvas.create_text(posn, 55, text=attack_code.name.replace('x', '').replace('N', ''), fill='snow', font=("Consolas", 12), tag=self.input_tag)
        x0 = i * self.step + 4
        x1 = x0 + self.step - 8
        self.canvas.create_rectangle(x0, 70, x1, self.h - 5, fill=stored_cancel, tag=self.input_tag)
