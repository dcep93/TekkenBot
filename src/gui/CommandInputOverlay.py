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
    length = 90
    silence_after_n = 30
    extra_padding = 25

    w = 1800
    h = 86

    def get_geometry(self, tekken_rect):
        x = (tekken_rect.right + tekken_rect.left) / 2  - self.toplevel.winfo_width() / 2
        y = tekken_rect.top + self.padding + self.extra_padding
        return x, y

    def update_state(self, game_log):
        last_state = game_log.state_log[-1]
        time_d = last_state.frame_count % 100
        player = last_state.p1 if game_log.is_player_player_one else last_state.p2
        input_state = player.get_input_state()

        if self.last_n_were_same(input_state):
            color = 'white'
            if self.stored_inputs[-1][-1] == color:
                return
        else:
            color = self.color_from_cancel_booleans(player)
        self.update_input(time_d, input_state, color)

    def __init__(self):
        super().__init__()
        self.text_ids = None

        self.stored_inputs = []
        self.init_canvas()

    def init_canvas(self):
        self.canvas = t_tkinter.Canvas(self.toplevel, width=self.w, height=self.h, bg='black', highlightthickness=0, relief='flat')

        self.canvas.pack()

        self.text_ids = [self.build_text_ids(i) for i in range(self.length)]

    def build_text_ids(self, index):
        step = self.w / self.length
        num_xs = 4
        x0 = index * step
        x = [x0 + int(i*step / num_xs) for i in range(num_xs)]
        self.canvas.create_line(x[0], 0, x[0], self.h, fill="red")
        time_id = self.canvas.create_text(x[2], 8, text=str(index+1), fill='snow')
        dir_id = self.canvas.create_text(x[2], 30, fill='snow', font=("Consolas", 20))
        atk_id = self.canvas.create_text(x[2], 55, fill='snow', font=("Consolas", 12))
        cancel_id = self.canvas.create_rectangle(x[1], 70, x[3], self.h - 5)
        return {
            'time': time_id,
            'direction': dir_id,
            'attack': atk_id,
            'cancel': cancel_id
        }

    def last_n_were_same(self, input_state):
        if len(self.stored_inputs) < self.silence_after_n:
            return False
        for i in range(self.silence_after_n):
            if self.stored_inputs[-i-1][1] != input_state:
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

    def update_input(self, *args):
        self.stored_inputs.append(args)
        if len(self.stored_inputs) >= self.length:
            self.stored_inputs = self.stored_inputs[-self.length:]
            for i, old_args in enumerate(self.stored_inputs):
                self.update_canvas_with_input(i, *old_args)

    def update_canvas_with_input(self, i, time_d, input_state, cancel):
        ids = self.text_ids[i]
        direction_code, attack_code, _ = input_state
        self.canvas.itemconfig(ids['time'], text=time_d)
        self.canvas.itemconfig(ids['direction'], text=symbol_map[direction_code])
        self.canvas.itemconfig(ids['attack'], text=attack_code.name.replace('x', '').replace('N', ''))
        self.canvas.itemconfig(ids['cancel'], fill=cancel)
